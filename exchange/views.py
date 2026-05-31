#Copyright (c) 2026 Daniel Mendoza (HierroEnLinea). Licensed under the MIT License.
from django.shortcuts import render, redirect
from .models import Product, DailyRate
from .logic import calcular_ajuste_prediccion, proyectar_tasas_futuro, proyectar_escenario_personalizado, generar_grafico_base64
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponse
from django.template.loader import get_template
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
from django.contrib.admin.views.decorators import staff_member_required
from datetime import date
from django.contrib import messages
import numpy as np
from django.conf import settings  # <--- IMPORTANTE: Importar settings
import json


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.as_p: # Validamos que el formulario sea correcto
            if form.is_valid():# <--- ESTE es el método correcto                 
                user = form.save()
                login(request, user) # Lo logueamos automáticamente al registrarse
                return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

#================= Dashboard 2 ============================

# Dashboard2 alternativo
def dashboard2(request):
    return render(request, 'exchange/dashboard2.html')

#============================================================

# La Home es pública (para atraer clientes)
def home(request):
    tasas = DailyRate.objects.all().order_by('-date')[:7]
    return render(request, 'exchange/home.html', {
        'tasa_hoy': tasas.first() if tasas.exists() else None,
        'historico': tasas
    })

#====================================================================================
# El Dashboard ahora es PRIVADO
@login_required
def dashboard(request):
    tasas_qs = DailyRate.objects.all().order_by('-date')[:91]
    if not tasas_qs.exists():
        return render(request, 'exchange/dashboard.html', {'error': 'Sin datos'})

    tasas_cron = tasas_qs[::-1] # Orden cronológico
    
    # REGRESIÓN DE 91 DÍAS ORIGINAL (Tu lógica intacta de una sola ala)
    bcv_list = [float(t.bcv_rate) for t in tasas_cron]
    binance_list = [float(t.binance_rate) for t in tasas_cron]
    x = np.arange(1, len(bcv_list) + 1)
    
    m_bcv, b_bcv = np.polyfit(x, bcv_list, 1)
    m_bin, b_bin = np.polyfit(x, binance_list, 1)


    # TRAPAMOS EL G15 REAL QUE CALCULA TU FUNCIÓN EN LOGIC.PY (VALOR MEDIO ADIMENSIONAL)

    tasas_recientes_45 = tasas_cron[-45:]     
    g15_real_valor = calcular_ajuste_prediccion(tasas_recientes_45)

    #g15_real_valor = calcular_ajuste_prediccion(tasas_cron)
    
    # Candado estricto: Si el mercado tiende a la baja, el factor nunca será menor a 1.00
    if g15_real_valor < 1.00:
        g15_real_valor = 1.00


    # --- BIFURCACIÓN DE ENTORNOS EN TIEMPO REAL ---
    grafico_data = None
    datos_grafico_json = "{}" # JSON vacío por defecto

    if settings.DEBUG:
        # 💻 EN LAPTOP: Mantenemos lógica actual intacta
        grafico_data = generar_grafico_base64(tasas_cron)
    else:

        # 🚀 EN HETZNER (PROD): Activamos el JSON ultra-ligero de milisegundos
        datos_grafico_json = json.dumps({
            'fechas': [t.date.strftime('%d/%m') for t in tasas_cron],
            'bcv': bcv_list,
            'binance': binance_list
        })  

    # Preparar la tabla de análisis (Últimos 15 días)
    analisis_data = []
    for t in tasas_qs[:15]:
        gap_pct = float(t.gap_percentage) * 100
        analisis_data.append({
            'fecha': t.date,
            'bcv': t.bcv_rate,
            'binance': t.binance_rate,
            'gap': round(gap_pct, 4),
        })

    return render(request, 'exchange/dashboard.html', {
        'analisis': analisis_data,
        'proy': {
            'm_bcv': m_bcv, 'b_bcv': b_bcv,
            'm_bin': m_bin, 'b_bin': b_bin,
        },
        'g15_real': g15_real_valor, # El escudo purificado
        'tasa_actual': tasas_qs.first(),
        'es_produccion': not settings.DEBUG, # <--- Enviamos esta bandera al HTML
        'grafico_offline': grafico_data,
        'datos_grafico': datos_grafico_json,     # Se enviará sólo en Hetzner  
    })

    #=====================================================================================

# La Lista de Precios ahora es PRIVADA
@login_required
def lista_precios_cashea(request):
    # 1. Obtenemos la data del mercado (último trimestre)
    tasas_qs = DailyRate.objects.all().order_by('-date')[:91]
    if not tasas_qs.exists():
        return render(request, 'exchange/lista_precios_cashea.html', {'error': 'No hay tasas cargadas.'})
    
    tasas_cronologicas = tasas_qs[::-1]
    
    # A. Las Tasas de HOY (Para el contado)
    tasa_reciente = tasas_qs[0]
    tasa_bcv_hoy = float(tasa_reciente.bcv_rate)
    tasa_binance_hoy = float(tasa_reciente.binance_rate)
    
    # B. Las Tasas del FUTURO y Factor G15 (Regresiones)
    bcv_futuro, binance_futuro = proyectar_tasas_futuro(tasas_cronologicas)
    g15 = calcular_ajuste_prediccion(tasas_cronologicas)

    #productos = Product.objects.all()
    productos = Product.objects.filter(user=request.user)
    lista_calculada = []
    
    for p in productos:
        # --- BASES DE CÁLCULO ---
        # Si hay oferta en base de datos, manda la oferta, si no, el normal.
        repo_usd = float(p.cost_usd_offer) if p.cost_usd_offer else float(p.cost_usd_normal)
        base_cashea_modelo = float(p.price_cashea_base_offer) if p.price_cashea_base_offer else float(p.price_cashea_base)

        # --- TASAS Y PROTECCIÓN ---
        precio_contado_bcv = (repo_usd * tasa_binance_hoy) / tasa_bcv_hoy
        
        def proyectar(base):
            return (base * binance_futuro / bcv_futuro) * g15

        # 1. CASHEA FULL (Sin IGTF todavía para el cálculo del descuento)
        precio_item_dolar_bcv = (base_cashea_modelo * binance_futuro / bcv_futuro) * g15
        precio_item_dolar_bcv_50 = precio_item_dolar_bcv / 2
        
        # 2. CÁLCULO DEL DESCUENTO (Puro, sobre el valor del ítem)
        # Descuento = (Diferencia entre Proyectado y Base) / Proyectado
        descuento_decimal = (precio_item_dolar_bcv - base_cashea_modelo) / precio_item_dolar_bcv
        
        # 3. INICIALES (Aquí es donde entra el IGTF)
        inicial_full = precio_item_dolar_bcv_50 * 1.018 # Mitad + IGTF
        
        # Inicial con Descuento (Tu lógica: Inicial_Dcto = Inicial * (1 - Desc))
        inicial_con_dcto = inicial_full * (1 - descuento_decimal)
        
        # PVP FINAL (Mitad neta + Inicial con su respectivo tratamiento)
        pvp_full = precio_item_dolar_bcv_50 + inicial_full # Esto da tus 163.78
        pvp_cashea_dcto = precio_item_dolar_bcv_50 + inicial_con_dcto            

        lista_calculada.append({
            'sku': p.sku,
            'nombre': p.name,
            'contado_usd_efectivo': repo_usd,
            #'contado_bs_bcv': round(precio_contado_bcv * tasa_bcv_hoy, 2),
            'contado_bs_bcv': "{:,.2f}".format(precio_contado_bcv * tasa_bcv_hoy).replace(",", "X").replace(".", ",").replace("X", "."),
            'contado_usd_bcv_hoy': round(precio_contado_bcv, 2), # Este es el que mostraremos grande
            'full_cashea': round(inicial_full + precio_item_dolar_bcv_50, 2), # Bloque Full
            'inicial_full': round(inicial_full, 2), # Bloque Full
            'cuota_full': round(precio_item_dolar_bcv_50 / 3, 2), # Bloque Full
            'pvp_cashea_dcto': round(pvp_cashea_dcto, 2), # Bloque Descuento (Inicial en Divisa)
            'inicial_dcto': round(inicial_con_dcto, 2),# Bloque Descuento (Inicial en Divisa)
            'cuota_dcto': round(precio_item_dolar_bcv_50 / 3, 2),# Bloque Descuento (Inicial en Divisa)
        })
        # --- DEBUG INDUSTRIAL: CÁLCULO DE DESCUENTO EN INICIAL ---
        # if p.sku == 'LAMHN29012202400': # Tu producto de prueba
        #     print(f"\n" + "🔬" + "━"*40)
        #     print(f"PRODUCTO: {p.name}")
        #     print(f"Precio Protegido (100%): {precio_item_dolar_bcv:.2f}")
        #     print(f"Descuento Aplicado (%):  {(descuento_decimal * 100):.2f}%")
        #     print(f"--- DESGLOSE CASHEA DCTO (INICIAL DIVISA) ---")
        #     print(f"Inicial SIN Dcto (c/IGTF): {inicial_full:.2f}")
        #     print(f"Monto Descontado ($):     {(inicial_full * descuento_decimal):.2f}")
        #     print(f"Inicial CON Dcto ($):     {inicial_con_dcto:.2f}")
        #     print(f"PVP FINAL REBAJADO:      {pvp_cashea_dcto:.2f}")
        #     print("━"*40 + "\n")

    return render(request, 'exchange/lista_precios_cashea.html', {
        'items': lista_calculada,
        'bcv_f': round(bcv_futuro, 2),
        'binance_f': round(binance_futuro, 2),
        'g15': round(g15, 4),
        'bcv_h': tasa_bcv_hoy
    })

#============================================================================

@login_required 
def exportar_precios_pdf(request):
    # Verificación de Permisos SaaS
    if not request.user.is_staff and not getattr(request.user.profile, 'is_pro', False):
        messages.error(request, "⚠️ La función de exportación PDF requiere una suscripción activa a HierroEnLinea PRO.")
        return redirect('dashboard')

    # Lógica de tasas y regresión de ReportLab
    tasas_qs = DailyRate.objects.all().order_by('-date')[:91]
    tasas_cron = tasas_qs[::-1]
    bcv_f, binance_f = proyectar_tasas_futuro(tasas_cron)
    g15 = calcular_ajuste_prediccion(tasas_cron)
    tasa_bcv_h = float(tasas_qs[0].bcv_rate)
    tasa_bin_h = float(tasas_qs[0].binance_rate)

    productos = Product.objects.all()
    
    # 1. Definimos los Encabezados (Tus 4 columnas importantes)
    data = [[
        'PRODUCTO', 
        'Contado\n(Cash $)', 
        'Contado\n(BCV $)', 
        'Cashea\nFULL ($)', 
        'Cashea\nDCTO ($)'
    ]]
    
    for p in productos:
        # BASES
        repo_usd = float(p.cost_usd_offer) if p.cost_usd_offer else float(p.cost_usd_normal)
        base_cashea_f = float(p.price_cashea_base)
        base_cashea_o = float(p.price_cashea_base_offer) if p.price_cashea_base_offer else float(p.price_cashea_base)
        
        # CÁLCULOS 

        # Precio de Contado pago a tasa BCV
        p_contado_bcv = (repo_usd * tasa_bin_h) / tasa_bcv_h
        
        # Lógica Cashea Full
        p_bs_f_full = base_cashea_f * binance_f
        p_prot_full = (p_bs_f_full / bcv_f) * g15
        pvp_full = p_prot_full
        
        # Lógica Cashea Dcto / Aplica IGTF a la fraccion del pago Inicial
        p_bs_f_offer = base_cashea_o * binance_f
        p_prot_offer = (p_bs_f_offer / bcv_f) * g15
        desc_val = (p_prot_offer - base_cashea_o) / p_prot_offer
        pvp_dcto = (p_prot_offer / 2) + ((p_prot_offer / 2) * (1.018) * (1 - desc_val))
        
        # Inyectamos a la tabla
        data.append([
            p.name[:40], # Limitamos a 40 caracteres para que no se rompa la tabla
            f"${repo_usd:.2f}",
            f"${round(p_contado_bcv, 2)}",
            f"${round(pvp_full, 2)}",
            f"${round(pvp_dcto, 2)}"
        ])

    # --- GENERACIÓN DEL PDF ---
    buffer = BytesIO()
    # Usamos márgenes más pequeños para aprovechar el ancho (Letter es 612 pts)
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # Título y Data de Referencia
    elements.append(Paragraph("HIERRO EN LÍNEA - LISTA DE PRECIOS", styles['Title']))
    elements.append(Paragraph(f"<b>Fecha:</b> {tasas_qs[0].date} | <b>Tasa BCV:</b> Bs. {tasa_bcv_h} | <b>Factor G15:</b> {round(g15, 4)}", styles['Normal']))
    elements.append(Paragraph("<br/>", styles['Normal'])) # Espacio
    
    # Configuración de Ancho de Columnas (Total 550 pts aprox)
    # Producto (250) + 4 precios (75 cada uno)
    col_widths = [250, 75, 75, 75, 75]
    
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a237e")), # Azul marino pro
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # Producto a la izquierda
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'), # Precios al centro
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]), # Filas cebra
    ]))
    
    elements.append(t)
    doc.build(elements)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Lista_Precios_{tasas_qs[0].date}.pdf"'
    response.write(buffer.getvalue())
    return response

#=====================================================================================

@login_required
def cargar_csv(request):
    # Candado SaaS para carga masiva
    if not request.user.is_staff and not getattr(request.user.profile, 'is_pro', False):
        messages.error(request, "⚠️ La carga masiva de inventario por CSV es una característica exclusiva de los planes PRO.")
        return redirect('dashboard')

    if request.method == 'POST' and request.FILES.get('archivo_csv'):
        file = request.FILES['archivo_csv']
        df = pd.read_csv(file)
        df.columns = [c.lower().strip() for c in df.columns]

        for _, row in df.iterrows():
            def clean(val): 
                return float(str(val).replace(',', '.')) if pd.notna(val) and str(val).strip() != "" else None
            
            # USAMOS update_or_create: Busca por usuario y SKU
            Product.objects.update_or_create(
                user=request.user,
                sku=str(row['sku']).strip(),
                defaults={
                    'name': row['nombre'].strip(),
                    'cost_usd_normal': clean(row['precio_normal']),
                    'cost_usd_offer': clean(row['precio_oferta']),
                    'price_cashea_base': clean(row['precio_normal_cashea']) or 0.0,
                    'price_cashea_base_offer': clean(row['precio_oferta_cashea']),
                    'is_available': True
                }
            )
            # Justo antes del return redirect('precios')
        messages.success(request, f"¡Éxito! Se procesaron los productos correctamente.")
        return redirect('precios')
    return render(request, 'exchange/cargar_csv.html')



#========================================================================================
@staff_member_required # Solo para Usuario Admin - Administrador
def actualizar_tasas_manual(request):
    if request.method == 'POST':
        tasa_bcv = float(request.POST.get('bcv'))
        tasa_bin = float(request.POST.get('binance'))
        gap = (tasa_bin / tasa_bcv) - 1
        
        DailyRate.objects.update_or_create(
            date=date.today(),
            defaults={
                'bcv_rate': tasa_bcv,
                'binance_rate': tasa_bin,
                'gap_percentage': gap
            }
        )
        return redirect('dashboard')
    
    return render(request, 'exchange/form_tasas.html')    


@login_required
def solicitar_pro(request):
    if request.method == 'POST':
        ref = request.POST.get('referencia')
        if ref:
            SubscriptionRequest.objects.create(user=request.user, referencia_pago=ref)
            messages.success(request, "💸 Solicitud enviada. Activaremos tu cuenta PRO en menos de 15 minutos al verificar el Pago Móvil.")
        return redirect('dashboard')
    return redirect('dashboard')
