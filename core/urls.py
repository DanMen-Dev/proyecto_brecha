from django.contrib import admin
from django.urls import path, include # Agregamos 'include' para los usuarios
from exchange.views import home, dashboard, lista_precios_cashea, register, exportar_precios_pdf, cargar_csv, actualizar_tasas_manual, solicitar_pro 
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve # Librería nativa para servir en producción
from django.urls import re_path
ro

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  # La vitrina pública
    path('register/', register, name='register'), # Nueva ruta
    path('dashboard/', dashboard, name='dashboard'),  # El centro de mando
    path('precios/', lista_precios_cashea, name='precios'), # La lista pro
    
    # Este 'include' activa el Login/Logout automático de Django
    path('accounts/', include('django.contrib.auth.urls')), 
    path('exportar-pdf/', exportar_precios_pdf, name='exportar_pdf'),
    path('cargar-csv/', cargar_csv, name='cargar_csv'),
    path('actualizar-tasas/', actualizar_tasas_manual, name='actualizar_tasas'),
    path('solicitar-pro/', solicitar_pro, name='solicitar_pro'),

    # EL PASAPORTE DE ENTRADA INDUSTRIAL PARA LOS ESTÁTICOS CON DEBUG=FALSE:
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]

