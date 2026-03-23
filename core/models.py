from django.db import models


class Detail(models.Model):
    detail_id = models.BigAutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'detail'
        managed = False

    def __str__(self):
        return self.nom


class PlanAbonnementDetail(models.Model):
    id = models.BigAutoField(primary_key=True)
    plan = models.ForeignKey('PlanAbonnement', on_delete=models.CASCADE, db_column='plan_id')
    detail = models.ForeignKey('Detail', on_delete=models.CASCADE, db_column='detail_id')

    class Meta:
        db_table = 'plan_abonnement_detail'
        managed = False
        unique_together = ('plan', 'detail')


class PlanAbonnement(models.Model):
    id = models.BigAutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=3, blank=True, null=True)
    duree_jours = models.IntegerField()
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    actif = models.BooleanField(null=True, blank=True)
    date_creation = models.DateTimeField(null=True, blank=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    tier = models.CharField(max_length=50, null=True, blank=True)
    commission_evenement = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    intervalle = models.CharField(max_length=50, null=True, blank=True)

    details = models.ManyToManyField('Detail', through='PlanAbonnementDetail', related_name='plans')

    class Meta:
        db_table = 'plan_abonnement'
        managed = False

    def __str__(self):
        return self.nom


class Facture(models.Model):
    id = models.BigAutoField(primary_key=True)
    numero_facture = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey('compte.Compte', on_delete=models.CASCADE, db_column='user_id')
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2)
    montant_tva = models.DecimalField(max_digits=10, decimal_places=2)
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=50)
    client_nom = models.CharField(max_length=255, null=True, blank=True)
    client_email = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    pdf_url = models.TextField(null=True, blank=True)
    date_creation = models.DateTimeField(null=True, blank=True)
    date_emission = models.DateTimeField(null=True, blank=True)
    date_paiement = models.DateTimeField(null=True, blank=True)
    mollie_payment_id = models.CharField(max_length=255, null=True, blank=True)
    payment_provider = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'facture'
        managed = False
