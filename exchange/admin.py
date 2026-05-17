#Copyright (c) 2026 Daniel Mendoza (HierroEnLinea). Licensed under the MIT License.
from django.contrib import admin
from .models import DailyRate  # Importamos modelo
from .models import SubscriptionRequest


@admin.register(DailyRate)
class DailyRateAdmin(admin.ModelAdmin):
    # Esto hace que la tabla en el admin se vea ordenada y profesional
    list_display = ('date', 'bcv_rate', 'binance_rate', 'gap_percentage')
    list_filter = ('date',)
    ordering = ('-date',)

@admin.register(SubscriptionRequest)
class SubscriptionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'referencia_pago', 'fecha_solicitud', 'procesado')
    list_filter = ('procesado',)
    
    # Acción personalizada de ingeniero: Activa al usuario Pro en lote
    actions = ['aprobar_suscripcion']

    def aprobar_suscripcion(self, request, queryset):
        for solicitud in queryset:
            if not solicitud.procesado:
                # Activamos el switch en su perfil
                perfil = solicitud.user.profile
                perfil.is_pro = True
                perfil.save()
                
                solicitud.procesado = True
                solicitud.save()
        self.message_user(request, "🚀 Usuarios activados en el Plan PRO con éxito.")

