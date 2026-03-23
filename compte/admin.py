from django.contrib import admin
from .models import (
    Compte, Caractere, Hobie, Langue,
    PreferenceEthnique, Tendance, Film, Musique,
    Photo, PhotoLike, PhotoComment, ProfileComment,
    CompteLike, CompteProfileVue,
    CompteBlacklist, CompteBoost, CompteCouple,
    SignalementUtilisateur, Video,
    CompteAttranceGenre, CompteCaractere, CompteHobie, CompteLangue,
    ComptePreferenceEthnique, CompteTendance,
    CompteFilm, CompteMusique, CompteSortie, CompteZonesConfort,
    AbonnementUtilisateur,
)


@admin.register(Compte)
class CompteAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'numberPhone', 'prenom', 'nom', 'sexe', 'ville', 'is_verified', 'is_active', 'abonnement', 'created_at')
    list_filter = ('is_verified', 'is_active', 'sexe', 'abonnement', 'is_member', 'created_at')
    search_fields = ('username', 'email', 'numberPhone', 'prenom', 'nom', 'ville')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_login')

    fieldsets = (
        ('Informations de connexion', {
            'fields': ('id', 'username', 'email', 'numberPhone', 'password', 'last_login')
        }),
        ('Informations personnelles', {
            'fields': ('prenom', 'nom', 'sexe', 'date_de_naissance', 'bio')
        }),
        ('Localisation', {
            'fields': ('adresse', 'ville', 'code_postal', 'departement', 'pays', 'latitude', 'longitude')
        }),
        ('Apparence physique', {
            'fields': ('taille', 'poids', 'yeux', 'hair_color', 'hair_style', 'facial_hair', 'shilhouette', 'glasses')
        }),
        ('Vie personnelle', {
            'fields': ('situation', 'enfant', 'religion', 'education', 'metier', 'en_couple')
        }),
        ('Preferences', {
            'fields': ('recherche', 'ethnique', 'age_min', 'age_max', 'ouverture')
        }),
        ('Style de vie', {
            'fields': ('sport', 'smoke', 'alcool', 'animaux', 'house')
        }),
        ('Abonnement et credits', {
            'fields': ('abonnement', 'credit', 'is_member')
        }),
        ('Medias', {
            'fields': ('avatar', 'thumbnail', 'audio')
        }),
        ('Statuts et permissions', {
            'fields': ('is_verified', 'is_active', 'is_online', 'is_staff', 'is_admin', 'ghost', 'statut')
        }),
        ('Acceptations', {
            'fields': ('chartre', 'cgu', 'cookie')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'date_joined')
        }),
    )


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'compte', 'type_photo', 'ordre', 'est_active', 'is_nsfw', 'is_shocking', 'date_ajout')
    list_filter = ('est_active', 'is_nsfw', 'is_shocking', 'type_photo', 'date_ajout')
    search_fields = ('compte__username', 'compte__email')
    readonly_fields = ('id', 'date_ajout')


@admin.register(PhotoLike)
class PhotoLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'photo', 'user', 'date_creation')
    list_filter = ('date_creation',)
    readonly_fields = ('date_creation',)


@admin.register(PhotoComment)
class PhotoCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'photo', 'auteur', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('auteur__username', 'contenu')
    readonly_fields = ('date_creation', 'date_modification')


@admin.register(ProfileComment)
class ProfileCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'auteur', 'profil_utilisateur', 'statut', 'date_creation')
    list_filter = ('statut', 'date_creation')
    search_fields = ('auteur__username', 'profil_utilisateur__username', 'contenu')
    readonly_fields = ('date_creation', 'date_modification')


@admin.register(CompteLike)
class CompteLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'compte', 'like', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('compte__username', 'like__username')
    readonly_fields = ('created_at',)


@admin.register(CompteProfileVue)
class CompteProfileVueAdmin(admin.ModelAdmin):
    list_display = ('id', 'viewer', 'viewed', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('viewer__username', 'viewed__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CompteBlacklist)
class CompteBlacklistAdmin(admin.ModelAdmin):
    list_display = ('id', 'bloqueur', 'bloque', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('bloqueur__username', 'bloque__username')


@admin.register(CompteBoost)
class CompteBoostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'activated_at', 'expires_at', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)


@admin.register(CompteCouple)
class CompteCoupleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user1__username', 'user2__username')


@admin.register(SignalementUtilisateur)
class SignalementUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('id', 'signaleur', 'signale', 'motif', 'statut', 'date_creation')
    list_filter = ('statut', 'date_creation')
    search_fields = ('signaleur__username', 'signale__username', 'motif')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'compte', 'titre', 'est_active', 'vues', 'date_ajout')
    list_filter = ('est_active', 'est_publique', 'date_ajout')
    search_fields = ('compte__username', 'titre')


@admin.register(AbonnementUtilisateur)
class AbonnementUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'statut', 'date_debut', 'date_fin', 'payment_provider')
    list_filter = ('statut', 'payment_provider', 'date_creation')
    search_fields = ('user__username', 'stripe_customer_id', 'mollie_customer_id')


admin.register(Caractere)(admin.ModelAdmin)
admin.register(Hobie)(admin.ModelAdmin)
admin.register(Langue)(admin.ModelAdmin)
admin.register(PreferenceEthnique)(admin.ModelAdmin)
admin.register(Tendance)(admin.ModelAdmin)
admin.register(Film)(admin.ModelAdmin)
admin.register(Musique)(admin.ModelAdmin)
admin.register(CompteAttranceGenre)(admin.ModelAdmin)
admin.register(CompteCaractere)(admin.ModelAdmin)
admin.register(CompteHobie)(admin.ModelAdmin)
admin.register(CompteLangue)(admin.ModelAdmin)
admin.register(ComptePreferenceEthnique)(admin.ModelAdmin)
admin.register(CompteTendance)(admin.ModelAdmin)
admin.register(CompteFilm)(admin.ModelAdmin)
admin.register(CompteMusique)(admin.ModelAdmin)
admin.register(CompteSortie)(admin.ModelAdmin)
admin.register(CompteZonesConfort)(admin.ModelAdmin)
