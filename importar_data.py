import os
import django
import pandas as pd
import numpy as np

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from exchange.models import DailyRate

def importar_desde_csv(file_path):
    if not os.path.exists(file_path):
        print(f"❌ No encuentro el archivo {file_path}")
        return

    # 1. Cargamos el CSV y ordenamos de PASADO a PRESENTE (Cronológico obligado para ventana móvil)
    df = pd.read_csv(file_path)
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Convertimos la fecha y ordenamos cronológicamente
    df['date_parsed'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['date_parsed']).sort_values('date_parsed').reset_index(drop=True)

    print("🚀 Procesando matriz cronológica con ventana móvil de 14 días...")

    for i in range(len(df)):
        try:
            row = df.iloc[i]
            fecha_actual = row['date_parsed'].date()

            # Limpieza de tasas nominales
            t_bcv = float(str(row['tasa_bcv']).replace(',', '.').strip())
            t_bin = float(str(row['tasa_binance']).replace(',', '.').strip())

            # --- RÉPLICA EXACTA DE TU ALGORITMO DE VARIACIÓN INTERTEMPORAL ---
            # Si hay menos de 14 días de historia hacia atrás, usamos el gap por defecto o el del CSV
            if i >= 14:
                row_pasada = df.iloc[i - 14]
                t_bcv_pasada = float(str(row_pasada['tasa_bcv']).replace(',', '.').strip())
                t_bin_pasada = float(str(row_pasada['tasa_binance']).replace(',', '.').strip())

                # Variación de tasas entre el día (i-14) y el día (i)
                var_bcv = t_bcv / t_bcv_pasada
                var_bin = t_bin / t_bin_pasada

                # Tu GAP adimensional de VBA: Variacion Binance / Variacion BCV (Oscila cerca de 1)
                gap_calculado = var_bin / var_bcv
            else:
                # Si no hay 14 días previos, intentamos leer lo que traiga el CSV o dejamos 1.0 (Sin variación)
                gap_csv = row.get('gap_percentage')
                if pd.isna(gap_csv) or str(gap_csv).strip() == "" or str(gap_csv).lower() == "nan":
                    gap_calculated_base = (t_bin / t_bcv) - 1
                    # Lo normalizamos a escala adimensional si es un porcentaje crudo alto
                    gap_calculado = 1.0 + gap_calculated_base if gap_calculated_base < 1 else gap_calculated_base
                else:
                    gap_calculado = float(str(gap_csv).replace(',', '.').strip())

            # --- PERSISTENCIA EN BASE DE DATOS ---
            obj, created = DailyRate.objects.update_or_create(
                date=fecha_actual,
                defaults={
                    'bcv_rate': t_bcv,
                    'binance_rate': t_bin,
                    'gap_percentage': gap_calculado # Guardamos tu índice adimensional real
                }
            )
            
            # Formateamos el print en consola según tu criterio: mayor a 1 depreciación, menor a 1 cierre
            status = "⚠️ BRECHA EXPANDE" if gap_calculado > 1.0 else "📉 BRECHA COMPRIME"
            print(f"{'✅ Creado' if created else '🔄 Actualizado'}: {fecha_actual} | Índice GAP: {gap_calculado:.4f} ({status})")

        except Exception as e:
            print(f"❌ Error en registro índice {i}: {e}")

    print("\n🏁 Pipeline de Variación Intertemporal Concluido.")

if __name__ == "__main__":
    importar_desde_csv('datos_historicos.csv')

