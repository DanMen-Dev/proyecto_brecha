# 🏗️ Brecha Cero (SaaS de Blindaje Financiero & Pricing Predictivo)

![Python](https://shields.io)
![Django](https://shields.io)
![NumPy](https://shields.io)
![Licencia](https://shields.io)

## 1. Propósito del Sistema y Problemática Macroeconómica
En economías con brecha cambiaria y alta volatilidad, los modelos de financiamiento de consumo masivo como el **Compre Ahora, Pague Después (BNPL / Esquema Cashea)** exponen a las pequeñas y medianas empresas (PyMEs) a un **riesgo crítico de descapitalización**. 

Al vender productos con un ciclo de cobro a 42 días bajo la tasa oficial (BCV), los comercios reciben flujos futuros de caja en bolívares que, debido a la fluctuación impredecible de la brecha con el costo real de reposición (Tasa Binance/Paralelo), se devalúan antes de la cobranza. Esto impide a las PyMEs recomprar el material al mayorista, destruyendo su inventario físico y sus márgenes de ganancia.

**HierroEnLinea** es un middleware FinTech predictivo que actúa como un escudo financiero. La plataforma analiza la serie histórica de tasas, proyecta el comportamiento del mercado al horizonte de cobro y genera **matrices de cotización multiescenario en tiempo real**, asegurando la reposición total del inventario quincena a quincena.

---

## 2. Arquitectura Técnica y Stack Tecnológico
El software fue diseñado bajo criterios estrictos de **resiliencia local y autonomía de red**, garantizando su funcionamiento óptimo incluso en entornos de infraestructura inestable o con restricciones de conectividad (Bypass total de CDNs externas):

*   **Backend:** Django 6.0 / Python 3.13 (Arquitectura MVC y capa lógica desacoplada).
*   **Base de Datos:** SQLite (Modelado relacional optimizado mediante indexación por fechas).
*   **Capa Matemática:** NumPy (Motor científico para procesamiento matricial de regresiones).
*   **Generación de Reportes:** ReportLab (Compilación nativa de binarios PDF directamente en la memoria del servidor).
*   **Visualización Analítica:** Matplotlib (Generación offline de curvas de tendencia renderizadas en HTML mediante inyección de cadenas en formato Base64).
*   **Frontend:** HTML5 / CSS3 / JavaScript Estricto (Diseño modular e interactivo basado en Flexbox nativo).

---

## 3. Lógica de Negocio y Algoritmos Core (El "Veneno" Matemático)

### A. Proyección de Tasas por Mínimos Cuadrados
La plataforma no especula con los precios; aplica rigor estadístico. El sistema extrae el QuerySet de los últimos 91 días de datos consolidados del mercado e ignora celdas nulas mediante filtros de control. Utilizando el método de **Mínimos Cuadrados Ordinarios (MCO)** a través de `np.polyfit`, calcula de forma analítica las ecuaciones de la recta ($y = mx + b$) para la Tasa BCV y la Tasa Binance de forma independiente.

El script calcula un **eje X futuro ($x_{\text{futuro}} = 91 + \text{días}$)** para proyectar los valores nominales exactos al día 105, 119 o 133 (horizonte máximo de protección de 42 días), obteniendo las variables `bcv_f` y `bin_f`.

### B. Factor de Cobertura Causal (G15)
El factor **G15** representa el valor medio proyectado del GAP cambiario intertemporal. Evalúa la ecuación de la recta de la brecha desde el punto de partida hasta el día de la cobranza futura, devolviendo un coeficiente adimensional que blinda la estructura de costos, dado por la recta ($y = mx + b$) y evaluado en el dia 23 aprox luego del dia O o dia de venta.

### C. Matriz de Pricing Multiescenario
Para cada artículo del inventario, la app calcula en milisegundos 4 estructuras de precios en paralelo:
1.  **Contado Cash ($):** Precio base real ancla en divisas en taquilla.
2.  **Contado BCV ($):** Paridad pura indexada a la tasa oficial spot de hoy para liquidación inmediata:
$$\text{Precio Contado BCV} = \frac{\text{Costo USD} \times \text{Tasa Binance Hoy}}{\text{Tasa BCV Hoy}}$$
3.  **Cashea FULL ($):** Blindaje completo aplicado al financiamiento del precio de lista base:
$$\text{Precio Protegido Full} = \frac{\text{Base Cashea} \times \text{Binance Futuro}}{\text{BCV Futuro}} \times \text{Factor G15}$$
4.  **Cashea DCTO ($):** Aplica la tasa de descuento de la promoción y recarga el impuesto del IGTF (1.8%) única y exclusivamente sobre la fracción del pago inicial en taquilla, aislando la mitad financiada que viaja al futuro:
$$\text{PVP Dcto} = \left(\frac{\text{Precio Protegido Offer}}{2}\right) + \left[\left(\frac{\text{Precio Protegido Offer}}{2}\right) \times 1.018 \times (1 - \text{Descuento})\right]$$

---

## 4. Funcionalidades del Mínimo Viable Tecnológico (MVP)
*   **Autenticación & Roles:** Sistema de control de acceso privado restringido mediante decoradores `@login_required`.
*   **Dashboard Interactivo:** Calculadora dinámica multiescenario que actualiza las 4 estructuras de precios en horizontal de forma instantánea mediante JavaScript y hereda las constantes del backend.
*   **Gráficos Offline:** Renderizado automático de la tendencia del GAP cambiario sin requerir scripts ni dependencias de servidores externos.
*   **Carga Masiva (Pipeline de Datos):** Módulo de importación de inventario vía archivos CSV purificado por un script limpiador de datos latinos (conversión automática de comas a puntos decimales y manejo de valores nulos).
*   **Exportador Industrial:** Generación de listas de precios corporativas en PDF con formateo de celdas estricto para evitar desbordes tipográficos en los nombres de los materiales.

---

## 5. Arquitectura de Monetización (Esquema SaaS Pro)
La plataforma implementa un modelo **Freemium con pasarela de activación por conciliación manual (Pago Móvil / P2P)** adaptado a la realidad transaccional venezolana:
*   **Plan Free (Gancho de Conversión):** Registro gratuito con acceso ilimitado al Dashboard de control y simulador individual para cotizaciones rápidas.
*   **Plan PRO (Monetización):** Bloqueo por permisos en el backend (`Profile.is_pro`) y Paywall estético interactivo (Modal) en el frontend. Desbloquea la carga masiva de CSV, el Monitor de Lista Web completo y la exportación de PDFs imprimibles. El administrador aprueba las solicitudes de suscripción en lote desde la consola de control al verificar la referencia bancaria.

---

## 6. Instrucciones de Instalación y Despliegue Local

1. Clonar el repositorio:
   ```bash
   git clone https://github.com
   cd proyecto_brecha
   ```

2. Activar el entorno virtual e instalar las dependencias científicas y de reporte:
   ```bash
   venv\Scripts\activate
   pip install django pandas numpy reportlab matplotlib
   ```

3. Ejecutar las migraciones relacionales y de perfiles:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Cargar el inventario de prueba de 20 artículos:
   ```bash
   python ejecutar_carga.py
   ```

5. Iniciar el servidor local de desarrollo:
   ```bash
   python manage.py runserver
   ```
   Acceder en el navegador a: `http://127.0.0`

---
LICENSE

Copyright (c) 2026 Daniel Mendoza (Brecha Cero). Licensed under the MIT License.

*Desarrollado con rigor matemático e ingeniería de software para la sostenibilidad empresarial.*

