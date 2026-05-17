import os
import django
import pandas as pd

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from exchange.models import DailyRate

def importar_desde_csv(file_path):
    # Cargamos el archivo
    df = pd.read_csv(file_path)
    
    # Normalizamos nombres de columnas (minúsculas y sin espacios)
    df.columns = [c.lower().strip() for c in df.columns]
    
    print("Columnas listas:", df.columns.tolist())

    for index, row in df.iterrows():
        try:
            # Procesamos la fecha con el formato correcto para Venezuela (DD/MM)
            #fecha_dt = pd.to_datetime(row['date'], dayfirst=True, errors='coerce')
            # Si en tu Excel la fecha es 04/05/2026 (4 de mayo)
            fecha_dt = pd.to_datetime(row['date'], format='%d/%m/%Y', errors='coerce')
            
            # CAMBIO AQUÍ: pd.isna en lugar de pd.isnat
            if pd.isna(fecha_dt):
                continue
                
            fecha_actual = fecha_dt.date()

            # Guardamos en la base de datos
            obj, created = DailyRate.objects.update_or_create(
                date=fecha_actual,
                defaults={
                    'bcv_rate': row['tasa_bcv'],
                    'binance_rate': row['tasa_binance'],
                    'gap_percentage': row['gap_percentage']
                }
            )
            print(f"{'✅ Creado' if created else '🔄 Actualizado'}: {fecha_actual}")

        except Exception as e:
            print(f"❌ Error en fila {index}: {e}")

if __name__ == "__main__":
    # Asegúrate de que el nombre del archivo coincida con el tuyo
    importar_desde_csv('datos_historicos.csv')
