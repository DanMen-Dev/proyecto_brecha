def get_rates_mock():
    # Valores manuales para desbloquear el desarrollo hoy
    # BCV hoy ronda los 48.33 y Binance los 58.50 aprox.
    return {
        "bcv": 500.4606, 
        "binance": 657.0000
    }

if __name__ == "__main__":
    print("🚧 Usando Datos de Emergencia (Mock)...")
    print(get_rates_mock())
