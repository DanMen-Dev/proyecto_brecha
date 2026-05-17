import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from exchange.models import DailyRate
# Importamos tu función mock
from scrapper_binance import get_rates_mock 

def actualizar():
    data = get_rates_mock() # Trae los 500.46 y 657.00
    
    tasa_bcv = data['bcv']
    tasa_binance = data['binance']
    gap = (tasa_binance / tasa_bcv) - 1

    obj, created = DailyRate.objects.update_or_create(
        date=date.today(),
        defaults={
            'bcv_rate': tasa_bcv,
            'binance_rate': tasa_binance,
            'gap_percentage': gap
        }
    )
    print(f"✅ Base de datos actualizada con tasas de hoy: BCV {tasa_bcv}")

if __name__ == "__main__":
    actualizar()
