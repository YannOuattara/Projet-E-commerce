from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

# Profil utilisateur avec rôles
class ProfilUtilisateur(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('vendeur', 'Vendeur'),
        ('client', 'Client'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    approved = models.BooleanField(default=True, verbose_name="Approuvé")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    # Champs spécifiques aux vendeurs
    company_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom de l'entreprise")
    business_description = models.TextField(blank=True, null=True, verbose_name="Description de l'activité")
    business_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Type d'activité")
    id_document = models.FileField(upload_to='vendeurs/id_documents/', blank=True, null=True, verbose_name="Pièce d'identité")
    
    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def est_vendeur(self):
        return self.role == 'vendeur' and self.approved
    
    def est_client(self):
        return self.role == 'client'
    
    def est_admin(self):
        return self.role == 'admin'

# Signal pour créer automatiquement un profil lors de la création d'un utilisateur
@receiver(post_save, sender=User)
def creer_profil_utilisateur(sender, instance, created, **kwargs):
    if created:
        # Le rôle sera géré dans le CustomSignupForm
        # Ici on crée juste le profil par défaut si il n'existe pas
        ProfilUtilisateur.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def sauvegarder_profil_utilisateur(sender, instance, **kwargs):
    if hasattr(instance, 'profil'):
        instance.profil.save()


class Categorie(models.Model):
    TYPE_CHOICES = [
        ('type_vehicule', 'Type de véhicule'),
        ('marque', 'Marque'),
        ('carburant', 'Carburant'),
        ('segment', 'Segment'),
        ('etat', 'État'),
        ('annee', 'Année'),
        ('prix', 'Prix'),
    ]
    
    type_categorie = models.CharField(max_length=20, choices=TYPE_CHOICES, default='type_vehicule', verbose_name="Type de catégorie")
    nom = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return f"{self.get_type_categorie_display()} - {self.nom}"


class Etiquette(models.Model):
    TYPE_CHOICES = [
        ('caracteristiques_speciales', 'Caractéristiques spéciales'),
        ('promotions', 'Promotions'),
        ('equipements_cles', 'Équipements clés'),
        ('usage', 'Usage'),
        ('avantages', 'Avantages'),
        ('etat_particulier', 'État particulier'),
    ]
    
    type_etiquette = models.CharField(max_length=30, choices=TYPE_CHOICES, default='caracteristiques_speciales', verbose_name="Type d'étiquette")
    nom = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name = "Étiquette"
        verbose_name_plural = "Étiquettes"
    
    def __str__(self):
        return f"{self.get_type_etiquette_display()} - {self.nom}"

class Produit(models.Model):
    vendeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='produits', limit_choices_to={'profil__role': 'vendeur', 'profil__approved': True})
    nom = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True, related_name='produits')
    etiquettes = models.ManyToManyField(Etiquette, blank=True, related_name='produits')
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    stock = models.IntegerField(default=0)
    disponible = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    # Champs spécifiques aux voitures
    marque = models.CharField(max_length=100, blank=True, null=True, default='', verbose_name="Marque")
    modele = models.CharField(max_length=100, blank=True, null=True, default='', verbose_name="Modèle")
    annee_fabrication = models.PositiveIntegerField(blank=True, null=True, default=None, verbose_name="Année de fabrication")
    kilometrage = models.PositiveIntegerField(blank=True, null=True, default=None, verbose_name="Kilométrage")
    CARBURANT_CHOICES = [
        ('essence', 'Essence'),
        ('diesel', 'Diesel'),
        ('electrique', 'Électrique'),
        ('hybride', 'Hybride'),
    ]
    carburant = models.CharField(max_length=20, choices=CARBURANT_CHOICES, blank=True, null=True, default=None, verbose_name="Carburant")
    TRANSMISSION_CHOICES = [
        ('manuelle', 'Manuelle'),
        ('automatique', 'Automatique'),
    ]
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, blank=True, null=True, default=None, verbose_name="Transmission")
    nombre_portes = models.PositiveIntegerField(blank=True, null=True, default=None, verbose_name="Nombre de portes")
    nombre_places = models.PositiveIntegerField(blank=True, null=True, default=None, verbose_name="Nombre de places")
    ETAT_CHOICES = [
        ('neuf', 'Neuf'),
        ('occasion', 'Occasion'),
        ('reconditionne', 'Reconditionné'),
    ]
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES, blank=True, null=True, default=None, verbose_name="État")
    equipements = models.JSONField(blank=True, null=True, default=list, verbose_name="Équipements", help_text="Liste des équipements (ex: ['Climatisation', 'GPS'])")
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['disponible', '-date_creation']),
            models.Index(fields=['vendeur', '-date_creation']),
        ]
    
    def __str__(self):
        return f"{self.nom} - {self.vendeur.username}"
    
    def est_en_stock(self):
        return self.stock > 0 and self.disponible
    
    def get_average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(review.note for review in reviews) / reviews.count(), 1)
        return 0
    
    def get_total_reviews(self):
        return self.reviews.count()
    
    def can_user_review(self, user):
        """Vérifie si l'utilisateur peut laisser un avis (a acheté le produit et commande confirmée)"""
        if not user.is_authenticated:
            return False
        # Vérifier si l'utilisateur a une commande confirmée contenant ce produit
        return Commande.objects.filter(
            client=user,
            statut__in=['confirmee', 'en_preparation', 'expediee', 'livree'],  # Permettre dès confirmation
            lignes_commande__produit=self
        ).exists()

class Commande(models.Model):
    STATUT_CHOICES = [
        ('en_attente_confirmation', 'En attente de confirmation'),
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('en_preparation', 'En préparation'),
        ('expediee', 'Expédiée'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
    ]
    
    numero_commande = models.CharField(max_length=100, unique=True, editable=False)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commandes', limit_choices_to={'profil__role': 'client'})
    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default='en_attente_confirmation')
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    adresse_livraison = models.TextField()
    telephone = models.CharField(max_length=20)
    notes = models.TextField(blank=True, null=True)
    date_commande = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_commande']
    
    def save(self, *args, **kwargs):
        if not self.numero_commande:
            self.numero_commande = f"CMD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_commande} - {self.client.username}"
    
    def calculer_total(self):
        total = sum(item.get_sous_total() for item in self.lignes_commande.all())
        self.montant_total = total
        self.save()
        return total
    
    def get_vendeurs(self):
        """Retourne la liste des vendeurs concernés par cette commande"""
        vendeurs = set()
        for ligne in self.lignes_commande.all():
            vendeurs.add(ligne.produit.vendeur)
        return list(vendeurs)

class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='lignes_commande')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"
    
    def get_sous_total(self):
        if self.prix_unitaire is None:
            return 0
        return self.quantite * self.prix_unitaire
    
    def __str__(self):
        return f"{self.produit.nom} x {self.quantite}"

class Panier(models.Model):
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name='panier')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"

    def ajouter_produit(self, produit, quantite=1):
        element, created = ElementPanier.objects.get_or_create(panier=self, produit=produit)
        if created:
            element.quantite = quantite
        else:
            element.quantite += quantite
        element.save()

    def supprimer_produit(self, produit):
        ElementPanier.objects.filter(panier=self, produit=produit).delete()

    def vider(self):
        ElementPanier.objects.filter(panier=self).delete()

    def get_total(self):
        return sum(element.get_sous_total() for element in self.elements.all())

    def __str__(self):
        return f"Panier de {self.utilisateur.username}"

class ElementPanier(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='elements')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.IntegerField(default=1)
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Élément du panier"
        verbose_name_plural = "Éléments du panier"
        unique_together = ('panier', 'produit')

    def get_sous_total(self):
        if self.produit and self.produit.prix:
            return self.produit.prix * self.quantite
        return 0

class Favoris(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoris')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='favoris_produit')
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Favoris"
        verbose_name_plural = "Favoris"
        unique_together = ('utilisateur', 'produit')
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.produit.nom}"

class Paiement(models.Model):
    METHODE_CHOICES = [
        ('carte', 'Carte Bancaire'),
        ('paypal', 'PayPal'),
        ('virement', 'Virement Bancaire'),
        ('especes', 'Espèces'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('effectue', 'Effectué'),
        ('echoue', 'Échoué'),
        ('rembourse', 'Remboursé'),
    ]
    
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE, related_name='paiement')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    methode_paiement = models.CharField(max_length=50, choices=METHODE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    reference = models.CharField(max_length=100, unique=True, editable=False)
    date_paiement = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"PAY-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def traiter_paiement(self):
        self.statut = 'effectue'
        self.save()

    def annuler_paiement(self):
        self.statut = 'echoue'
        self.save()

    def __str__(self):
        return f"Paiement {self.reference} - {self.montant}€"

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 étoile'),
        (2, '2 étoiles'),
        (3, '3 étoiles'),
        (4, '4 étoiles'),
        (5, '5 étoiles'),
    ]
    
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='reviews')
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', limit_choices_to={'profil__role': 'client'})
    note = models.IntegerField(choices=RATING_CHOICES, verbose_name="Note")
    commentaire = models.TextField(blank=True, null=True, verbose_name="Commentaire")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        unique_together = ('produit', 'utilisateur')  # Un avis par utilisateur par produit
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Avis de {self.utilisateur.username} sur {self.produit.nom} - {self.note} étoiles"