from django.db import models
import uuid


class Compte(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    numberPhone = models.CharField(max_length=20, null=True, blank=True, db_column='numberPhone')
    prenom = models.CharField(max_length=150)
    nom = models.CharField(max_length=150)
    sexe = models.CharField(max_length=20)
    date_de_naissance = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    ville = models.CharField(max_length=100, null=True, blank=True)
    code_postal = models.CharField(max_length=10, null=True, blank=True)
    taille = models.IntegerField(null=True, blank=True)
    poids = models.CharField(max_length=50, null=True, blank=True)
    yeux = models.CharField(max_length=50, null=True, blank=True)
    hair_color = models.CharField(max_length=50, null=True, blank=True)
    smoke = models.CharField(max_length=50, null=True, blank=True)
    alcool = models.CharField(max_length=50, null=True, blank=True)
    situation = models.CharField(max_length=50, null=True, blank=True)
    enfant = models.CharField(max_length=50, null=True, blank=True)
    religion = models.CharField(max_length=100, null=True, blank=True)
    education = models.CharField(max_length=100, null=True, blank=True)
    metier = models.CharField(max_length=100, null=True, blank=True)
    recherche = models.CharField(max_length=100, null=True, blank=True)
    ethnique = models.CharField(max_length=50, null=True, blank=True)
    shilhouette = models.CharField(max_length=50, null=True, blank=True)
    glasses = models.CharField(max_length=50, null=True, blank=True)
    sport = models.CharField(max_length=50, null=True, blank=True)
    animaux = models.CharField(max_length=50, null=True, blank=True)
    hair_style = models.CharField(max_length=50, null=True, blank=True)
    facial_hair = models.CharField(max_length=50, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    pays = models.CharField(max_length=100, null=True, blank=True)
    departement = models.CharField(max_length=100, null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)
    age_min = models.IntegerField(null=True, blank=True)
    age_max = models.IntegerField(null=True, blank=True)
    ouverture = models.CharField(max_length=50, null=True, blank=True)
    house = models.CharField(max_length=50, null=True, blank=True)
    audio = models.CharField(max_length=500, null=True, blank=True)
    avatar = models.CharField(max_length=500, null=True, blank=True)
    thumbnail = models.CharField(max_length=500, null=True, blank=True)
    is_online = models.BooleanField(default=False, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False, null=True, blank=True)
    statut = models.CharField(max_length=50, null=True, blank=True)
    en_couple = models.BooleanField(default=False, blank=True)
    credit = models.IntegerField(default=0, null=True, blank=True)
    abonnement = models.CharField(max_length=50, default='gratuit', null=True, blank=True)
    is_member = models.BooleanField(default=False, blank=True)
    is_staff = models.BooleanField(default=False, blank=True)
    is_admin = models.BooleanField(default=False, blank=True)
    chartre = models.BooleanField(default=False, blank=True)
    cgu = models.BooleanField(default=False, blank=True)
    cookie = models.BooleanField(default=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(null=True, blank=True)
    ghost = models.BooleanField(default=False, null=True, blank=True)
    evenement = models.TextField(null=True, blank=True)
    geog = models.TextField(null=True, blank=True)
    is_user_online = models.BooleanField(default=False, null=True, blank=True)
    boost = models.BooleanField(default=False, null=True, blank=True)
    referral_code = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'compte_compte'
        managed = False

    def __str__(self):
        return self.username


class Caractere(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caractere = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'compte_caractere'
        managed = False

    def __str__(self):
        return self.caractere


class Hobie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hobie = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'compte_hobie'
        managed = False

    def __str__(self):
        return self.hobie


class Langue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    langue = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'compte_langue'
        managed = False

    def __str__(self):
        return self.langue


class PreferenceEthnique(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'compte_preferenceethnique'
        managed = False

    def __str__(self):
        return self.nom


class Tendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tendance = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'compte_tendance'
        managed = False

    def __str__(self):
        return self.tendance


class Film(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    film = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'compte_film'
        managed = False

    def __str__(self):
        return self.film


class Musique(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    musique = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'compte_musique'
        managed = False

    def __str__(self):
        return self.musique


class Photo(models.Model):
    id = models.BigAutoField(primary_key=True)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    photos = models.TextField(default='')
    type_photo = models.CharField(max_length=50, default='')
    ordre = models.IntegerField(default=0)
    est_active = models.BooleanField(default=True)
    is_nsfw = models.BooleanField(default=False)
    is_nsfw_checked = models.BooleanField(default=False)
    is_shocking = models.BooleanField(default=False)
    is_shocking_checked = models.BooleanField(default=False)
    date_ajout = models.DateTimeField(auto_now_add=True)
    thumbnail = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'compte_photo'
        managed = False

    def __str__(self):
        return f"Photo {self.id}"


class PhotoLike(models.Model):
    id = models.BigAutoField(primary_key=True)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, db_column='photo_id')
    user = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='user_id')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compte_photo_like'
        managed = False


class PhotoComment(models.Model):
    id = models.BigAutoField(primary_key=True)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, db_column='photo_id')
    auteur = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='auteur_id')
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    parent_comment = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, db_column='parent_comment_id')
    signale = models.BooleanField(default=False, null=True, blank=True)
    raison_signalement = models.TextField(null=True, blank=True)
    date_signalement = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compte_photo_comment'
        managed = False


class ProfileComment(models.Model):
    id = models.BigAutoField(primary_key=True)
    auteur = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='comments_written', db_column='auteur_id')
    profil_utilisateur = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='comments_received', db_column='profil_utilisateur_id')
    contenu = models.TextField()
    statut = models.CharField(max_length=50, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_moderation = models.DateTimeField(null=True, blank=True)
    parent_comment = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, db_column='parent_comment_id')
    signale = models.BooleanField(default=False, null=True, blank=True)
    raison_signalement = models.TextField(null=True, blank=True)
    date_signalement = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compte_profilecomment'
        managed = False


class CompteLike(models.Model):
    id = models.BigAutoField(primary_key=True)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='likes_given', db_column='compte_id')
    like = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='likes_received', db_column='like_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compte_like'
        managed = False


class CompteProfileVue(models.Model):
    id = models.BigAutoField(primary_key=True)
    viewer = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='views_made', db_column='viewer_id')
    viewed = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='views_received', db_column='viewed_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compte_profile_vue'
        managed = False


class CompteBlacklist(models.Model):
    id = models.BigAutoField(primary_key=True)
    bloqueur = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='bloqueur_id', related_name='blacklist_given')
    bloque = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='bloque_id', related_name='blacklist_received')
    date_creation = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compte_blacklist'
        managed = False


class CompteBoost(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='user_id')
    activated_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compte_boost'
        managed = False


class CompteCouple(models.Model):
    id = models.BigAutoField(primary_key=True)
    user1 = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='user1_id', related_name='couple_as_user1')
    user2 = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='user2_id', related_name='couple_as_user2')
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compte_couple'
        managed = False


class SignalementUtilisateur(models.Model):
    id = models.AutoField(primary_key=True)
    signaleur = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='signaleur_id', related_name='signalements_made')
    signale = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='signale_id', related_name='signalements_received')
    motif = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'compte_signalement_utilisateur'
        managed = False


class Video(models.Model):
    id = models.BigAutoField(primary_key=True)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    video_url = models.CharField(max_length=255, null=True, blank=True)
    thumbnail_url = models.CharField(max_length=255, null=True, blank=True)
    titre = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    duree_secondes = models.IntegerField(null=True, blank=True)
    est_active = models.BooleanField(default=True)
    est_publique = models.BooleanField(default=True)
    vues = models.IntegerField(default=0)
    date_ajout = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compte_video'
        managed = False


class VideoComment(models.Model):
    id = models.BigAutoField(primary_key=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, db_column='video_id')
    auteur = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='auteur_id')
    contenu = models.TextField()
    statut = models.CharField(max_length=50, null=True, blank=True)
    parent_comment = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, db_column='parent_comment_id')
    signale = models.BooleanField(default=False, null=True, blank=True)
    raison_signalement = models.TextField(null=True, blank=True)
    date_signalement = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_moderation = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compte_video_comment'
        managed = False


class CompteAttranceGenre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    genre = models.CharField(max_length=50)

    class Meta:
        db_table = 'compte_compte_attirance_genre'
        managed = False


class CompteCaractere(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    caractere = models.ForeignKey(Caractere, on_delete=models.CASCADE, db_column='caractere_id')

    class Meta:
        db_table = 'compte_compte_caractere'
        managed = False


class CompteHobie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    hobie = models.ForeignKey(Hobie, on_delete=models.CASCADE, db_column='hobie_id')

    class Meta:
        db_table = 'compte_compte_hobie'
        managed = False


class CompteLangue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    langue = models.ForeignKey(Langue, on_delete=models.CASCADE, db_column='langue_id')

    class Meta:
        db_table = 'compte_compte_langue'
        managed = False


class ComptePreferenceEthnique(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    preferenceethnique = models.ForeignKey(PreferenceEthnique, on_delete=models.CASCADE, db_column='preferenceethnique_id')

    class Meta:
        db_table = 'compte_compte_preference_ethnique'
        managed = False


class CompteTendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    tendance = models.ForeignKey(Tendance, on_delete=models.CASCADE, db_column='tendance_id')

    class Meta:
        db_table = 'compte_compte_tendance'
        managed = False


class CompteFilm(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    film = models.ForeignKey(Film, on_delete=models.CASCADE, db_column='film_id')

    class Meta:
        db_table = 'compte_compte_style_de_film'
        managed = False


class CompteMusique(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    musique = models.ForeignKey(Musique, on_delete=models.CASCADE, db_column='musique_id')

    class Meta:
        db_table = 'compte_compte_style_de_musique'
        managed = False


class CompteSortie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    preference = models.CharField(max_length=255)

    class Meta:
        db_table = 'compte_compte_preference_de_sortie'
        managed = False


class CompteZonesConfort(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='compte_id')
    zone = models.CharField(max_length=255)

    class Meta:
        db_table = 'compte_compte_zones_confort'
        managed = False


class AbonnementUtilisateur(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Compte, on_delete=models.CASCADE, db_column='user_id')
    plan = models.ForeignKey('core.PlanAbonnement', on_delete=models.CASCADE, db_column='plan_id')
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    statut = models.CharField(max_length=50)
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    renouvellement_auto = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    mollie_customer_id = models.CharField(max_length=255, null=True, blank=True)
    mollie_payment_id = models.CharField(max_length=255, null=True, blank=True)
    mollie_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    mollie_mandate_id = models.CharField(max_length=255, null=True, blank=True)
    payment_provider = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'abonnement_utilisateur'
        managed = False
