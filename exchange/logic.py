#Copyright (c) 2026 Daniel Mendoza (HierroEnLinea). Licensed under the MIT License.
import numpy as np
import matplotlib
matplotlib.use('Agg') # Evita que intente abrir una ventana gráfica en el servidor
import matplotlib.pyplot as plt
import io
import base64


def calcular_ajuste_prediccion(tasas_queryset):
    registros = list(tasas_queryset)
    y, x = [], []
    
    for i, t in enumerate(registros):
        if t.gap_percentage and t.gap_percentage != 0:
            # NORMALIZAMOS LA ESCALA: Si el dato en la BD está inflado (ej: 108.12),
            # lo dividimos entre 100 para regresarlo a su escala adimensional real (1.0812)
            val_gap = float(t.gap_percentage)
            if val_gap > 10:
                val_gap = val_gap / 100.0
            y.append(val_gap)
            x.append(i + 1)

    if not y: 
        return 1.0294

    y_np, x_np = np.array(y), np.array(x)
    m, b = np.polyfit(x_np, y_np, 1)
    
    # --- AUDITORÍA MATEMÁTICA EN TERMINAL ---
    print("\n" + "="*30)
    print(f"DEBUG MONETIZACIÓN SAAS:")
    print(f"Pendiente de la Brecha (m): {m:.6f}")
    print(f"Intersección Base (b): {b:.6f}")
    print(f"Ecuación del Riesgo: y = {m:.6f}x + {b:.6f}")
    # ----------------------------------------------------

    # EXTIRPACIÓN DEL PROMEDIO ERRÓNEO:
    # Evaluamos la ecuación de la recta de forma directa en el punto máximo de exposición futura (Día 131)
    # Esto elimina el '/ 2' y devuelve el multiplicador puro de cobertura intertemporal
    factor_proteccion_futura = (m * 131) + b
    
    # Candado de resguardo: Si la brecha tiende a cerrarse en el trimestre, el factor nunca será menor a 1.00
    if factor_proteccion_futura < 1.00:
        factor_proteccion_futura = 1.00
        
    print(f"Factor G15 de Seguridad Aplicado: {factor_proteccion_futura:.4f}")
    print("="*30 + "\n")

    return factor_proteccion_futura

    #==================================================================================


def proyectar_tasas_futuro(tasas_queryset):
    # 1. Extraemos las series de datos
    bcv_list = [float(t.bcv_rate) for t in tasas_queryset]
    binance_list = [float(t.binance_rate) for t in tasas_queryset]
    
    x = np.arange(1, len(bcv_list) + 1)
    
    # 2. Regresión para BCV
    m_bcv, b_bcv = np.polyfit(x, bcv_list, 1)
    # y = m*131 + b (Tasa BCV en 42 días)
    tasa_bcv_proyectada = (m_bcv * 131) + b_bcv
    
    # 3. Regresión para Binance
    m_bin, b_bin = np.polyfit(x, binance_list, 1)
    # y = m*131 + b (Tasa Binance en 42 días)
    tasa_binance_proyectada = (m_bin * 131) + b_bin
    
    return tasa_bcv_proyectada, tasa_binance_proyectada

    #=========================================================================================

def calculate_protection_price(base_price, current_bcv, current_binance, factor_dinamico):
    """
    Calcula el precio final usando el factor dinámico de la regresión.
    """
    gap_ratio = float(current_binance) / float(current_bcv)
    
    # Aplicamos fórmula original de VBA con el nuevo factor dinámico
    price_bcv_labeled = (float(base_price) * gap_ratio) * float(factor_dinamico)
    return round(price_bcv_labeled, 2)

    #=========================================================================================
def proyectar_escenario_personalizado(tasas_queryset, dias_a_futuro):
    bcv_list = [float(t.bcv_rate) for t in tasas_queryset]
    binance_list = [float(t.binance_rate) for t in tasas_queryset]
    gap_list = [float(t.gap_percentage) for t in tasas_queryset]
    
    x = np.arange(1, len(bcv_list) + 1)
    dia_objetivo = len(bcv_list) + dias_a_futuro

    # Regresiones Lineales
    m_bcv, b_bcv = np.polyfit(x, bcv_list, 1)
    m_bin, b_bin = np.polyfit(x, binance_list, 1)
    m_gap, b_gap = np.polyfit(x, gap_list, 1)

    return {
        'bcv_f': (m_bcv * dia_objetivo) + b_bcv,
        'binance_f': (m_bin * dia_objetivo) + b_bin,
        'g15_f': (m_gap * dia_objetivo) + b_gap,
        'valor_medio_g15': (b_gap + ((m_gap * dia_objetivo) + b_gap)) / 2
    }

    #===================== Grafica de ejes Simples ======================================

# def generar_grafico_base64(tasas_queryset):  
#     # 1. Extraemos los datos en orden cronológico
#     fechas = [t.date.strftime('%d/%m') for t in tasas_queryset]
#     bcv = [float(t.bcv_rate) for t in tasas_queryset]
#     binance = [float(t.binance_rate) for t in tasas_queryset]

#     # 2. Creamos la figura
#     plt.figure(figsize=(8, 4))
#     plt.plot(fechas, bcv, label='Tasa BCV', color='#0d6efd', linewidth=2)
#     plt.plot(fechas, binance, label='Tasa Binance', color='#dc3545', linewidth=2)
    
#     # Ajustes estéticos limpios
#     plt.title('Evolución de Tasas (Últimos 90 días)', fontsize=12, fontweight='bold')
#     plt.xlabel('Fecha')
#     plt.ylabel('Bs. por USD')
#     plt.legend()
#     plt.grid(True, linestyle='--', alpha=0.5)
    
#     # Reducimos la cantidad de etiquetas en el eje X para que no se amontonen
#     plt.xticks(fechas[::10], rotation=45) 
#     plt.tight_layout()

#     # 3. Guardamos el gráfico en memoria como si fuera un archivo
#     buffer = io.BytesIO()
#     plt.savefig(buffer, format='png')
#     buffer.seek(0)
#     image_png = buffer.getvalue()
#     buffer.close()
#     plt.close()

#     # 4. Lo codificamos a Base64 (Texto plano interpretable por cualquier navegador)
#     grafico_base64 = base64.b64encode(image_png).decode('utf-8')
#     return grafico_base64

    #===================== Grafica de ejes Dobles ======================================

def generar_grafico_base64(tasas_queryset):
    # 1. Extraemos la data completa de la BD (Orden cronológico)
    fechas = [t.date.strftime('%d/%m') for t in tasas_queryset]
    bcv = [float(t.bcv_rate) for t in tasas_queryset]
    binance = [float(t.binance_rate) for t in tasas_queryset]
    gaps = [float(t.gap_percentage) * 100 for t in tasas_queryset] # En porcentaje (ej: 15.4)

    # 2. Configuración de la figura principal (Eje Izquierdo - Tasas en Bs)
    fig, ax1 = plt.subplots(figsize=(9, 4.5))
    
    # Dibujamos las curvas reales de las tasas
    ax1.plot(fechas, bcv, label='Tasa BCV Real', color='#0d6efd', linewidth=2, alpha=0.8)
    ax1.plot(fechas, binance, label='Tasa Binance Real', color='#dc3545', linewidth=2, alpha=0.8)
    ax1.set_ylabel('Tasas de Cambio (Bs.)', fontname='Segoe UI', fontweight='bold', color='#1a237e')
    ax1.tick_params(axis='y', labelcolor='#1a237e')
    
    # 3. CONSTRUCCIÓN DEL TERMÓMETRO (Eje Derecho Secundario - GAP %)
    ax2 = ax1.twinx()
    ax2.plot(fechas, gaps, label='Brecha / GAP (%)', color='#198754', linewidth=1.5, linestyle=':', alpha=0.9)
    ax2.set_ylabel('Brecha Cambiaria - GAP (%)', fontname='Segoe UI', fontweight='bold', color='#198754')
    ax2.tick_params(axis='y', labelcolor='#198754')

    # Ajustes estéticos de alta costura corporativa
    plt.title('Monitor de Cobertura Causal & Termómetro de Brecha (Trimestral)', fontsize=12, fontweight='bold', fontname='Segoe UI', pad=15)
    ax1.set_xlabel('Línea Temporal (Días del Periodo)', fontname='Segoe UI', labelpad=10)
    
    # Unificamos las leyendas de ambos ejes en una sola caja
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#dee2e6')
    
    ax1.grid(True, linestyle='--', alpha=0.4, color='#90a4ae')
    
    # Controlamos el amontonamiento del eje X (Muestra una etiqueta cada 10 días)
    ax1.set_xticks(np.arange(0, len(fechas), 10))
    ax1.set_xticklabels(fechas[::10], rotation=45, style='italic', fontsize=9)
    
    plt.tight_layout()

    # 4. Compresión binaria a texto Base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=110)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()

    return base64.b64encode(image_png).decode('utf-8')