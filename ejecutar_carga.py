import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from exchange.models import Product

def cargar_articulos():
    file_path = 'CSV_Export_Productos_Brecha_Cambiaria.csv' 
    df = pd.read_csv(file_path)
    df.columns = [c.lower().strip() for c in df.columns]

    for index, row in df.iterrows():
        try:
            # --- FUNCIÓN DE LIMPIEZA INTERNA ---
            def limpiar_decimal(valor):
                if pd.isna(valor) or str(valor).strip() == "":
                    return None
                # Cambiamos coma por punto y quitamos espacios
                val_str = str(valor).replace(',', '.').strip()
                return float(val_str)

            # Limpiamos los precios antes de mandarlos a Django
            p_normal = limpiar_decimal(row['precio_normal'])
            p_oferta = limpiar_decimal(row['precio_oferta'])
            p_normal_cashea = limpiar_decimal(row['precio_normal_cashea'])
            p_oferta_cashea = limpiar_decimal(row['precio_oferta_cashea'])

            Product.objects.update_or_create(
                sku=str(row['sku']).strip(),
                defaults={
                    'name': row['nombre'].strip(),
                    'cost_usd_normal': p_normal,
                    'cost_usd_offer': p_oferta,
                    'price_cashea_base': p_normal_cashea, 
                    'price_cashea_base_offer': p_oferta_cashea,                   
                    'is_available': True
                }
            )
            print(f"✅ Cargado: {row['sku']}")
        except Exception as e:
            print(f"❌ Error en fila {index} (SKU: {row.get('sku')}): {e}")

if __name__ == "__main__":
    cargar_articulos()            

print("Its Done Bro")
