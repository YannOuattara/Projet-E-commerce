from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    ProfilUtilisateur, Categorie, Etiquette, Produit, 
    Commande, LigneCommande, Panier, 
    ElementPanier, Paiement, Review
)


# Inline pour le profil utilisateur dans l'admin User
class ProfilUtilisateurInline(admin.StackedInline):
    model = ProfilUtilisateur
    can_delete = False
    verbose_name_plural = 'Profil'
    fk_name = 'user'


# Étendre l'admin User pour inclure le profil
class UserAdmin(BaseUserAdmin):
    inlines = (ProfilUtilisateurInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profil__role')
    
    def get_role(self, obj):
        return obj.profil.get_role_display() if hasattr(obj, 'profil') else 'N/A'
    get_role.short_description = 'Rôle'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'approved', 'telephone', 'date_creation')
    list_filter = ('role', 'approved', 'date_creation')
    search_fields = ('user__username', 'user__email', 'telephone')
    readonly_fields = ('date_creation',)
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user', 'role', 'approved')
        }),
        ('Informations de contact', {
            'fields': ('telephone', 'adresse')
        }),
        ('Informations vendeur', {
            'fields': ('company_name', 'business_description', 'business_type', 'id_document'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )
    actions = ['approve_sellers', 'reject_sellers']
    
    def approve_sellers(self, request, queryset):
        # Approuver seulement les vendeurs
        updated = queryset.filter(role='vendeur').update(approved=True)
        self.message_user(request, f'{updated} vendeur(s) approuvé(s).')
    approve_sellers.short_description = "Approuver les vendeurs sélectionnés"
    
    def reject_sellers(self, request, queryset):
        # Refuser seulement les vendeurs (mettre approved=False)
        updated = queryset.filter(role='vendeur').update(approved=False)
        self.message_user(request, f'{updated} vendeur(s) refusé(s).')
    reject_sellers.short_description = "Refuser les vendeurs sélectionnés"


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('type_categorie', 'nom', 'slug')
    list_filter = ('type_categorie',)
    prepopulated_fields = {'slug': ('nom',)}
    search_fields = ('nom',)


@admin.register(Etiquette)
class EtiquetteAdmin(admin.ModelAdmin):
    list_display = ('type_etiquette', 'nom', 'slug')
    list_filter = ('type_etiquette',)
    prepopulated_fields = {'slug': ('nom',)}
    search_fields = ('nom',)


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'vendeur', 'prix', 'stock', 'disponible', 'categorie', 'marque', 'modele', 'etat', 'date_creation')
    list_filter = ('disponible', 'categorie', 'date_creation', 'vendeur', 'marque', 'etat', 'carburant', 'transmission')
    search_fields = ('nom', 'description', 'vendeur__username', 'marque', 'modele')
    filter_horizontal = ('etiquettes',)
    readonly_fields = ('date_creation', 'date_modification')
    fieldsets = (
        ('Informations générales', {
            'fields': ('vendeur', 'nom', 'description', 'prix')
        }),
        ('Classification', {
            'fields': ('categorie', 'etiquettes')
        }),
        ('Informations véhicule', {
            'fields': ('marque', 'modele', 'annee_fabrication', 'kilometrage', 'carburant', 'transmission', 'nombre_portes', 'nombre_places', 'etat', 'equipements'),
            'classes': ('collapse',)
        }),
        ('Stock et disponibilité', {
            'fields': ('stock', 'disponible', 'image')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Si l'utilisateur est un vendeur, ne montrer que ses produits
        if hasattr(request.user, 'profil') and request.user.profil.est_vendeur():
            return qs.filter(vendeur=request.user)
        return qs
    
    def save_model(self, request, obj, form, change):
        # Si nouveau produit et vendeur non défini, utiliser l'utilisateur actuel
        if not change and hasattr(request.user, 'profil') and request.user.profil.est_vendeur():
            obj.vendeur = request.user
        super().save_model(request, obj, form, change)


class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 0
    readonly_fields = ('get_sous_total',)
    
    def get_sous_total(self, obj):
        if obj and obj.pk:
            try:
                return f"{obj.get_sous_total()} €"
            except (TypeError, AttributeError):
                return "0 €"
        return "0 €"
    get_sous_total.short_description = 'Sous-total'


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('numero_commande', 'client', 'statut', 'montant_total', 'date_commande', 'afficher_vendeurs')
    list_filter = ('statut', 'date_commande')
    search_fields = ('numero_commande', 'client__username', 'client__email')
    readonly_fields = ('numero_commande', 'date_commande', 'date_modification', 'montant_total', 'afficher_vendeurs')
    inlines = [LigneCommandeInline]
    fieldsets = (
        ('Informations commande', {
            'fields': ('numero_commande', 'client', 'statut')
        }),
        ('Détails livraison', {
            'fields': ('adresse_livraison', 'telephone', 'notes')
        }),
        ('Montant et vendeurs', {
            'fields': ('montant_total', 'afficher_vendeurs')
        }),
        ('Dates', {
            'fields': ('date_commande', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def afficher_vendeurs(self, obj):
        vendeurs = obj.get_vendeurs()
        return ', '.join([v.username for v in vendeurs]) if vendeurs else 'N/A'
    afficher_vendeurs.short_description = 'Vendeurs concernés'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Si l'utilisateur est un vendeur, montrer uniquement les commandes contenant ses produits
        if hasattr(request.user, 'profil') and request.user.profil.est_vendeur():
            return qs.filter(lignes_commande__produit__vendeur=request.user).distinct()
        return qs


@admin.register(LigneCommande)
class LigneCommandeAdmin(admin.ModelAdmin):
    list_display = ('commande', 'produit', 'quantite', 'prix_unitaire', 'get_sous_total')
    list_filter = ('commande__date_commande',)
    search_fields = ('commande__numero_commande', 'produit__nom')
    
    def get_sous_total(self, obj):
        try:
            return f"{obj.get_sous_total()} €"
        except (TypeError, AttributeError):
            return "0 €"
    get_sous_total.short_description = 'Sous-total'


class ElementPanierInline(admin.TabularInline):
    model = ElementPanier
    extra = 0
    readonly_fields = ('get_sous_total',)
    
    def get_sous_total(self, obj):
        if obj and obj.pk:
            try:
                return f"{obj.get_sous_total()} €"
            except (TypeError, AttributeError):
                return "0 €"
        return "0 €"
    get_sous_total.short_description = 'Sous-total'


@admin.register(Panier)
class PanierAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'date_creation', 'get_total_panier', 'nombre_articles')
    search_fields = ('utilisateur__username',)
    readonly_fields = ('date_creation', 'date_modification', 'get_total_panier')
    inlines = [ElementPanierInline]
    
    def get_total_panier(self, obj):
        return f"{obj.get_total()} €"
    get_total_panier.short_description = 'Total'
    
    def nombre_articles(self, obj):
        return obj.elements.count()
    nombre_articles.short_description = 'Nb articles'


@admin.register(ElementPanier)
class ElementPanierAdmin(admin.ModelAdmin):
    list_display = ('panier', 'produit', 'quantite', 'date_ajout', 'get_sous_total')
    list_filter = ('date_ajout',)
    search_fields = ('panier__utilisateur__username', 'produit__nom')
    
    def get_sous_total(self, obj):
        try:
            return f"{obj.get_sous_total()} €"
        except (TypeError, AttributeError):
            return "0 €"
    get_sous_total.short_description = 'Sous-total'


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('reference', 'commande', 'montant', 'methode_paiement', 'statut', 'date_paiement')
    list_filter = ('statut', 'methode_paiement', 'date_paiement')
    search_fields = ('reference', 'commande__numero_commande')
    readonly_fields = ('reference', 'date_paiement')
    actions = ['marquer_effectue', 'marquer_echoue']
    
    def marquer_effectue(self, request, queryset):
        updated = queryset.update(statut='effectue')
        self.message_user(request, f'{updated} paiement(s) marqué(s) comme effectué(s).')
    marquer_effectue.short_description = "Marquer comme effectué"
    
    def marquer_echoue(self, request, queryset):
        updated = queryset.update(statut='echoue')
        self.message_user(request, f'{updated} paiement(s) marqué(s) comme échoué(s).')
    marquer_echoue.short_description = "Marquer comme échoué"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'produit', 'note', 'date_creation')
    list_filter = ('note', 'date_creation', 'produit__vendeur')
    search_fields = ('utilisateur__username', 'produit__nom', 'commentaire')
    readonly_fields = ('date_creation',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('utilisateur', 'produit', 'note', 'commentaire')
        }),
        ('Dates', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )


# Personnalisation du site admin
admin.site.site_header = "Administration Drive Shop"
admin.site.site_title = "Drive Shop Admin"
admin.site.index_title = "Gestion de la plateforme e-commerce"
