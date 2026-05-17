import requests
from bs4 import BeautifulSoup

def get_bcv_rate():
    url = "https://bcv.org.ve"
    try:
        # El BCV a veces bloquea peticiones simples, simulamos un navegador
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos el contenedor del Dólar
        rate_element = soup.find('div', id='dolar').find('strong')
        rate_text = rate_element.text.strip().replace(',', '.')
        return float(rate_text)
    except Exception as e:
        print(f"Error al obtener tasa BCV: {e}")
        return None

print(f"La tasa actual del BCV es: {get_bcv_rate()}")
