from django.urls import path
from .views import index, services, car_list, car_single
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'ecommerce'
urlpatterns = [
    # Pages publiques
    path('', index, name='index'),
    path('services/', services, name='services'),
    path('car/', car_list, name='car'),
    path('car/<int:car_id>/', views.car_single, name='car_single'),
    path('car/<int:produit_id>/soumettre-avis/', views.soumettre_avis, name='soumettre_avis'),

    # Panier et commandes
    path('ajouter-au-panier/<int:car_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/', views.panier, name='panier'),
    path('mettre-a-jour-panier/', views.mettre_a_jour_panier, name='mettre_a_jour_panier'),
    path('supprimer-du-panier/<int:car_id>/', views.supprimer_du_panier, name='supprimer_du_panier'),
    path('informations-client/', views.informations_client, name='informations_client'),
    path('mode-expedition/', views.mode_expedition, name='mode_expedition'),
    path('payer/', views.payer, name='payer'),
    path('complete/', views.complete, name='complete'),

    # Mes commandes
    path('mes-commandes/', views.mes_commandes, name='mes_commandes'),
    path('mes-avis/', views.mes_avis, name='mes_avis'),

    # Favoris
    path('toggle-favorite/<int:produit_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('mes-favoris/', views.mes_favoris, name='mes_favoris'),
    path('supprimer-favori/<int:produit_id>/', views.supprimer_favori, name='supprimer_favori'),

    # Profils
    path('profil-client/', views.profil_client, name='profil_client'),
    path('profil-vendeur-prive/', views.profil_vendeur_prive, name='profil_vendeur_prive'),

    # Espace vendeur
    path('vendeur/dashboard/', views.vendeur_dashboard, name='vendeur_dashboard'),
    path('vendeur/commandes/', views.vendeur_commandes, name='vendeur_commandes'),
    path('vendeur/commandes/confirmer/<int:commande_id>/', views.confirmer_commande, name='confirmer_commande'),
    path('vendeur/produits/', views.vendeur_produits, name='vendeur_produits'),
    path('vendeur/creer-produit/', views.vendeur_creer_produit, name='vendeur_creer_produit'),
    path('vendeur/modifier-produit/<int:produit_id>/', views.vendeur_modifier_produit, name='vendeur_modifier_produit'),
    path('vendeur/supprimer-produit/<int:produit_id>/', views.vendeur_supprimer_produit, name='vendeur_supprimer_produit'),
    path('vendeur/<str:username>/', views.profil_vendeur, name='profil_vendeur'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)