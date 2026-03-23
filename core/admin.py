from django.contrib import admin
from .models import (
    PlanAbonnement,
    Facture,
    Detail,
    PlanAbonnementDetail,
)


class PlanAbonnementDetailInline(admin.TabularInline):
    model = PlanAbonnementDetail
    extra = 1


@admin.register(PlanAbonnement)
class PlanAbonnementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix', 'devise', 'duree_jours', 'actif', 'date_creation')
    list_filter = ('actif',)
    search_fields = ('nom', 'stripe_price_id')
    readonly_fields = ('date_creation',)
    inlines = [PlanAbonnementDetailInline]


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('numero_facture', 'user', 'statut', 'montant_ttc', 'payment_provider', 'date_emission')
    list_filter = ('statut', 'date_emission', 'payment_provider')
    search_fields = ('numero_facture', 'user__username', 'user__email', 'mollie_payment_id')


@admin.register(Detail)
class DetailAdmin(admin.ModelAdmin):
    list_display = ('detail_id', 'nom')
    search_fields = ('nom',)

