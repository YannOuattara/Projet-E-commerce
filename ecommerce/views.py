from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from decimal import Decimal
from .models import Produit, Panier, ElementPanier, Commande, LigneCommande, Categorie, Etiquette, Favoris, Review
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .utils import envoyer_email_nouvelle_commande, envoyer_email_confirmation_commande, envoyer_email_details_commande

# Redirection après login selon le rôle
def custom_login_redirect(request):
    """Redirige l'utilisateur selon son rôle après connexion"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'profil'):
            if request.user.profil.est_vendeur():
                return redirect('ecommerce:profil_vendeur_prive')
            elif request.user.profil.est_client():
                return redirect('ecommerce:profil_client')
    return redirect('ecommerce:index')

def index(request):
    featured_products = Produit.objects.filter(disponible=True).select_related('vendeur', 'categorie').prefetch_related('etiquettes').order_by('-date_creation')[:6]
    return render(request, 'ecommerce/index.html', {
        'featured_cars': featured_products  # Garde le nom pour compatibilité template
    })

def services(request):
    return render(request, 'ecommerce/services.html')

def car(request):
    """Vue pour la liste des produits (ancien 'car')"""
    return render(request, 'ecommerce/car.html')

def car_single(request, car_id):
    """Vue pour un produit unique (ancien 'car_single')"""
    produit = get_object_or_404(Produit, id=car_id) 
    
    # Récupérer les avis
    reviews = produit.reviews.select_related('utilisateur').order_by('-date_creation')
    
    # Calculer la note moyenne et le nombre d'avis
    average_rating = produit.get_average_rating()
    total_reviews = produit.get_total_reviews()
    
    # Vérifier si l'utilisateur peut laisser un avis
    can_review = produit.can_user_review(request.user)
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = reviews.filter(utilisateur=request.user).exists()
    
    return render(request, 'ecommerce/car_single.html', {
        'car': produit,
        'reviews': reviews,
        'average_rating': average_rating,
        'total_reviews': total_reviews,
        'can_review': can_review,
        'user_has_reviewed': user_has_reviewed,
    })

def car_list(request):
    """Vue avec pagination pour la liste des produits"""
    # Si l'utilisateur est un vendeur connecté, filtrer uniquement ses produits
    if request.user.is_authenticated and hasattr(request.user, 'profil') and request.user.profil.est_vendeur():
        products_list = Produit.objects.filter(vendeur=request.user, disponible=True).select_related('vendeur', 'categorie').prefetch_related('etiquettes').order_by('-date_creation')
    else:
        products_list = Produit.objects.filter(disponible=True).select_related('vendeur', 'categorie').prefetch_related('etiquettes').order_by('-date_creation')
    
    paginator = Paginator(products_list, 6)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except:
        products = paginator.page(1)
    page_number = products.number
    max_pages = paginator.num_pages
    if max_pages <= 5:
        page_range = range(1, max_pages + 1)
    else:
        if page_number <= 3:
            page_range = range(1, 6)
        elif page_number > max_pages - 3:
            page_range = range(max_pages - 4, max_pages + 1)
        else:
            page_range = range(page_number - 2, page_number + 3)
    
    # Récupérer les favoris de l'utilisateur connecté
    user_favoris = []
    if request.user.is_authenticated and hasattr(request.user, 'profil') and request.user.profil.est_client():
        user_favoris = Favoris.objects.filter(utilisateur=request.user).values_list('produit', flat=True)
    
    return render(request, 'ecommerce/car.html', {
        'cars': products,  # Garde le nom pour compatibilité template
        'page_range': page_range,
        'user_favoris': user_favoris
    })

def ajouter_au_panier(request, car_id):
    """Ajouter un produit au panier (car_id = product_id pour compatibilité URL)"""
    produit = get_object_or_404(Produit, id=car_id)
    if request.user.is_authenticated:
        panier, created = Panier.objects.get_or_create(utilisateur=request.user)
        panier.ajouter_produit(produit)
        messages.success(request, f"{produit.nom} a été ajouté au panier !")
    else:
        if 'panier' not in request.session:
            request.session['panier'] = {}
        panier_session = request.session['panier']
        if str(car_id) in panier_session:
            panier_session[str(car_id)]['quantite'] += 1
        else:
            panier_session[str(car_id)] = {
                'quantite': 1,
                'name': produit.nom,
                'price': str(produit.prix)
            }
        request.session.modified = True
        messages.success(request, f"{produit.nom} a été ajouté au panier (session) !")
    return redirect('ecommerce:panier')

def panier(request):
    if request.user.is_authenticated:
        panier, created = Panier.objects.get_or_create(utilisateur=request.user)
        elements = panier.elements.select_related('produit__vendeur', 'produit__categorie').prefetch_related('produit__etiquettes').all()
        total = panier.get_total()
    else:
        panier_session = request.session.get('panier', {})
        elements = [
            {
                'produit': {
                    'id': int(prod_id),
                    'nom': item['name'],
                    'prix': float(item['price'])
                },
                'quantite': item['quantite'],
                'sous_total': float(item['price']) * item['quantite']
            }
            for prod_id, item in panier_session.items()
        ]
        total = sum(item['sous_total'] for item in elements)

    return render(request, 'ecommerce/panier.html', {
        'elements': elements,
        'total': total,
        'is_authenticated': request.user.is_authenticated,
        'etape': 1
    })

@require_POST
def mettre_a_jour_panier(request):
    produit_id = request.POST.get('car_id')  # Garde 'car_id' pour compatibilité
    try:
        quantite = int(request.POST.get('quantite', 1) or 0)
    except (ValueError, TypeError):
        quantite = 0
        messages.error(request, "Valeur invalide.")

    if request.user.is_authenticated:
        panier = Panier.objects.get(utilisateur=request.user)
        element = get_object_or_404(ElementPanier, panier=panier, produit_id=produit_id)
        element.quantite = quantite
        if quantite == 0:
            element.delete()
            messages.success(request, "Article retiré du panier.")
        else:
            element.save()
            messages.success(request, "Panier mis à jour !")
    else:
        panier_session = request.session.get('panier', {})
        if produit_id in panier_session:
            if quantite == 0:
                del panier_session[produit_id]
                messages.success(request, "Article retiré du panier.")
            else:
                panier_session[produit_id]['quantite'] = quantite
                messages.success(request, "Panier mis à jour !")
            request.session['panier'] = panier_session
            request.session.modified = True

    return redirect('ecommerce:panier')

@require_POST
def supprimer_du_panier(request, car_id):
    """Supprimer un produit du panier (car_id = product_id pour compatibilité URL)"""
    if request.user.is_authenticated:
        panier = Panier.objects.get(utilisateur=request.user)
        produit = get_object_or_404(Produit, id=car_id)
        panier.supprimer_produit(produit)
    else:
        panier_session = request.session.get('panier', {})
        if str(car_id) in panier_session:
            del panier_session[str(car_id)]
            request.session['panier'] = panier_session
            request.session.modified = True

    messages.success(request, "Article supprimé du panier !")
    return redirect('ecommerce:panier')

def informations_client(request):
    if not request.user.is_authenticated:
        return redirect('account_login')

    panier = Panier.objects.get(utilisateur=request.user)
    total = panier.get_total()
    if request.method == 'POST':
        # Stocker les informations client dans la session (exemple simplifié)
        request.session['client_info'] = {
            'nom': request.POST.get('nom'),
            'email': request.POST.get('email'),
            'telephone': request.POST.get('telephone'),
            'adresse': request.POST.get('adresse')
        }
        return redirect('ecommerce:mode_expedition')
    
    return render(request, 'ecommerce/informations_client.html', {
        'total': total,
        'etape': 2  # Étape 2 : Informations Client
    })

def mode_expedition(request):
    if not request.user.is_authenticated:
        return redirect('account_login')

    panier = Panier.objects.get(utilisateur=request.user)
    total = panier.get_total()
    if request.method == 'POST':
        request.session['mode_expedition'] = request.POST.get('mode_expedition')
        return redirect('ecommerce:payer')
    
    return render(request, 'ecommerce/mode_expedition.html', {
        'total': total,
        'etape': 3  # Étape 3 : Mode d'Expédition
    })

def payer(request):
    if not request.user.is_authenticated:
        return redirect('account_login')
    
    panier = Panier.objects.get(utilisateur=request.user)
    total = panier.get_total()
    
    # Récupérer les informations depuis la session
    client_info = request.session.get('client_info', {})
    mode_expedition = request.session.get('mode_expedition', 'standard')
    
    if request.method == 'POST':
        methode_paiement = request.POST.get('methode_paiement')
        
        # Créer la commande réelle
        try:
            commande = Commande.objects.create(
                client=request.user,
                montant_total=total,
                adresse_livraison=client_info.get('adresse', ''),
                telephone=client_info.get('telephone', '')
            )
            
            # Ajouter les lignes de commande
            elements = panier.elements.all()
            for element in elements:
                LigneCommande.objects.create(
                    commande=commande,
                    produit=element.produit,
                    quantite=element.quantite,
                    prix_unitaire=element.produit.prix
                )
                
                # Mettre à jour le stock
                element.produit.stock -= element.quantite
                element.produit.save()
            
            # Vider le panier
            panier.vider()
            
            # Nettoyer la session
            if 'client_info' in request.session:
                del request.session['client_info']
            if 'mode_expedition' in request.session:
                del request.session['mode_expedition']
            
            messages.success(request, f"Commande #{commande.numero_commande} créée avec succès !")
            
            # Envoyer un email au vendeur pour notifier la nouvelle commande
            envoyer_email_nouvelle_commande(commande)
            
            # Envoyer un email au client avec les détails de sa commande
            envoyer_email_details_commande(commande)
            
            return redirect('ecommerce:complete')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création de la commande : {str(e)}")
    
    return render(request, 'ecommerce/paiement.html', {
        'total': total,
        'etape': 4  # Étape 4 : Facturation et Paiement
    })

def complete(request):
    if not request.user.is_authenticated:
        return redirect('account_login')
    
    return render(request, 'ecommerce/complete.html', {
        'etape': 5  # Étape 5 : Complété
    })

# ===== VENDOR VIEWS =====

def est_vendeur(user):
    """Vérifie si l'utilisateur est un vendeur"""
    return hasattr(user, 'profil') and user.profil.est_vendeur()

@login_required
@user_passes_test(est_vendeur)
def vendeur_dashboard(request):
    """Tableau de bord du vendeur"""
    # Récupérer les commandes contenant des produits du vendeur
    commandes = Commande.objects.filter(lignes_commande__produit__vendeur=request.user).distinct()
    
    # Statistiques
    total_ventes = sum(c.montant_total for c in commandes if c.statut != 'annulee')
    nb_commandes = commandes.count()
    nb_produits = Produit.objects.filter(vendeur=request.user).count()
    
    return render(request, 'ecommerce/vendeur/dashboard.html', {
        'commandes': commandes[:10],  # Dernières 10 commandes
        'total_ventes': total_ventes,
        'nb_commandes': nb_commandes,
        'nb_produits': nb_produits
    })

@login_required
@user_passes_test(est_vendeur)
def vendeur_commandes(request):
    """Vue pour voir toutes les commandes du vendeur"""
    commandes = Commande.objects.filter(lignes_commande__produit__vendeur=request.user).distinct().order_by('-date_commande')
    
    # Filtrer par statut si demandé
    statut_filter = request.GET.get('statut')
    if statut_filter:
        commandes = commandes.filter(statut=statut_filter)
    
    return render(request, 'ecommerce/vendeur/commandes.html', {
        'commandes': commandes
    })

@login_required
@user_passes_test(est_vendeur)
def vendeur_produits(request):
    """Liste des produits du vendeur"""
    produits = Produit.objects.filter(vendeur=request.user).order_by('-date_creation')
    return render(request, 'ecommerce/vendeur/produits.html', {
        'produits': produits
    })

@login_required
@user_passes_test(est_vendeur)
def vendeur_creer_produit(request):
    """Créer un nouveau produit (vendeur seulement)"""
    categories = Categorie.objects.all()
    etiquettes = Etiquette.objects.all()
    
    if request.method == 'POST':
        try:
            # Validation des données
            nom = request.POST.get('nom', '').strip()
            if not nom:
                messages.error(request, "Le nom du produit est requis.")
                return redirect('ecommerce:vendeur_creer_produit')
            
            try:
                prix = Decimal(request.POST.get('prix', 0))
                if prix <= 0:
                    messages.error(request, "Le prix doit être supérieur à 0.")
                    return redirect('ecommerce:vendeur_creer_produit')
            except (ValueError, TypeError):
                messages.error(request, "Prix invalide.")
                return redirect('ecommerce:vendeur_creer_produit')
            
            try:
                stock = int(request.POST.get('stock', 0))
                if stock < 0:
                    messages.error(request, "Le stock ne peut pas être négatif.")
                    return redirect('ecommerce:vendeur_creer_produit')
            except (ValueError, TypeError):
                messages.error(request, "Stock invalide.")
                return redirect('ecommerce:vendeur_creer_produit')
            
            produit = Produit.objects.create(
                vendeur=request.user,
                nom=nom,
                description=request.POST.get('description'),
                prix=prix,
                categorie_id=request.POST.get('categorie') if request.POST.get('categorie') else None,
                stock=stock,
                disponible=request.POST.get('disponible') == 'on',
                # Champs spécifiques aux voitures
                marque=request.POST.get('marque') or '',
                modele=request.POST.get('modele') or '',
                annee_fabrication=request.POST.get('annee_fabrication') or None,
                kilometrage=request.POST.get('kilometrage') or None,
                carburant=request.POST.get('carburant') or None,
                transmission=request.POST.get('transmission') or None,
                nombre_portes=request.POST.get('nombre_portes') or None,
                nombre_places=request.POST.get('nombre_places') or None,
                etat=request.POST.get('etat') or None
            )
            
            # Gérer les équipements (convertir la chaîne en liste)
            equipements_str = request.POST.get('equipements', '').strip()
            if equipements_str:
                # Séparer par virgules et nettoyer les espaces
                equipements_list = [eq.strip() for eq in equipements_str.split(',') if eq.strip()]
                produit.equipements = equipements_list
                produit.save()
            
            # Gérer l'image
            if 'image' in request.FILES:
                produit.image = request.FILES['image']
                produit.save()
            
            # Ajouter les étiquettes
            etiquettes_ids = request.POST.getlist('etiquettes')
            for etiquette_id in etiquettes_ids:
                try:
                    etiquette = Etiquette.objects.get(id=etiquette_id)
                    produit.etiquettes.add(etiquette)
                except Etiquette.DoesNotExist:
                    pass
            
            messages.success(request, f"Produit '{produit.nom}' créé avec succès !")
            return redirect('ecommerce:vendeur_produits')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création : {str(e)}")
    
    return render(request, 'ecommerce/vendeur/creer_produit.html', {
        'categories': categories,
        'etiquettes': etiquettes
    })

@login_required
@user_passes_test(est_vendeur)
def vendeur_modifier_produit(request, produit_id):
    """Modifier un produit existant (vendeur seulement)"""
    produit = get_object_or_404(Produit, id=produit_id, vendeur=request.user)
    categories = Categorie.objects.all()
    etiquettes = Etiquette.objects.all()
    
    if request.method == 'POST':
        try:
            # Validation des données
            nom = request.POST.get('nom', '').strip()
            if not nom:
                messages.error(request, "Le nom du produit est requis.")
                return redirect('ecommerce:vendeur_modifier_produit', produit_id=produit.id)
            
            try:
                prix = Decimal(request.POST.get('prix'))
                if prix <= 0:
                    messages.error(request, "Le prix doit être supérieur à 0.")
                    return redirect('ecommerce:vendeur_modifier_produit', produit_id=produit.id)
            except (ValueError, TypeError):
                messages.error(request, "Prix invalide.")
                return redirect('ecommerce:vendeur_modifier_produit', produit_id=produit.id)
            
            try:
                stock = int(request.POST.get('stock', 0))
                if stock < 0:
                    messages.error(request, "Le stock ne peut pas être négatif.")
                    return redirect('ecommerce:vendeur_modifier_produit', produit_id=produit.id)
            except (ValueError, TypeError):
                messages.error(request, "Stock invalide.")
                return redirect('ecommerce:vendeur_modifier_produit', produit_id=produit.id)
            
            produit.nom = nom
            produit.description = request.POST.get('description')
            produit.prix = prix
            produit.categorie_id = request.POST.get('categorie') if request.POST.get('categorie') else None
            produit.stock = stock
            produit.disponible = request.POST.get('disponible') == 'on'
            
            # Champs spécifiques aux voitures
            produit.marque = request.POST.get('marque') or ''
            produit.modele = request.POST.get('modele') or ''
            produit.annee_fabrication = request.POST.get('annee_fabrication') or None
            produit.kilometrage = request.POST.get('kilometrage') or None
            produit.carburant = request.POST.get('carburant') or None
            produit.transmission = request.POST.get('transmission') or None
            produit.nombre_portes = request.POST.get('nombre_portes') or None
            produit.nombre_places = request.POST.get('nombre_places') or None
            produit.etat = request.POST.get('etat') or None
            
            # Gérer les équipements (convertir la chaîne en liste)
            equipements_str = request.POST.get('equipements', '').strip()
            if equipements_str:
                # Séparer par virgules et nettoyer les espaces
                equipements_list = [eq.strip() for eq in equipements_str.split(',') if eq.strip()]
                produit.equipements = equipements_list
            else:
                produit.equipements = []
            
            # Gérer l'image
            if 'image' in request.FILES:
                produit.image = request.FILES['image']
            
            produit.save()
            
            # Mettre à jour les étiquettes
            produit.etiquettes.clear()
            etiquettes_ids = request.POST.getlist('etiquettes')
            for etiquette_id in etiquettes_ids:
                try:
                    etiquette = Etiquette.objects.get(id=etiquette_id)
                    produit.etiquettes.add(etiquette)
                except Etiquette.DoesNotExist:
                    pass
            
            messages.success(request, f"Produit '{produit.nom}' modifié avec succès !")
            return redirect('ecommerce:vendeur_produits')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification : {str(e)}")
    
    # Étiquettes déjà sélectionnées
    etiquettes_selectionnees = produit.etiquettes.all()
    
    return render(request, 'ecommerce/vendeur/modifier_produit.html', {
        'produit': produit,
        'categories': categories,
        'etiquettes': etiquettes,
        'etiquettes_selectionnees': etiquettes_selectionnees
    })

@login_required
@user_passes_test(est_vendeur)
def confirmer_commande(request, commande_id):
    """Permettre au vendeur de confirmer ou refuser une commande"""
    commande = get_object_or_404(Commande, id=commande_id)
    
    # Vérifier que le vendeur est concerné par cette commande
    vendeurs_commande = commande.get_vendeurs()
    if request.user not in vendeurs_commande:
        messages.error(request, "Vous n'êtes pas autorisé à gérer cette commande.")
        return redirect('ecommerce:vendeur_commandes')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirmer':
            # Vérifier la disponibilité des produits
            produits_insuffisants = []
            for ligne in commande.lignes_commande.all():
                if ligne.produit.vendeur == request.user and ligne.quantite > ligne.produit.stock:
                    produits_insuffisants.append(f"{ligne.produit.nom} (stock: {ligne.produit.stock})")
            
            if produits_insuffisants:
                messages.error(request, f"Stock insuffisant pour : {', '.join(produits_insuffisants)}")
                return redirect('ecommerce:confirmer_commande', commande_id=commande.id)
            
            # Confirmer la commande et mettre à jour le stock
            commande.statut = 'confirmee'
            commande.save()
            
            # Mettre à jour le stock
            for ligne in commande.lignes_commande.all():
                if ligne.produit.vendeur == request.user:
                    ligne.produit.stock -= ligne.quantite
                    ligne.produit.save()
            
            messages.success(request, f"Commande #{commande.numero_commande} confirmée avec succès !")
            
            # Envoyer un email au client pour notifier la confirmation
            envoyer_email_confirmation_commande(commande)
            
        elif action == 'refuser':
            raison = request.POST.get('raison_refus', '')
            commande.statut = 'annulee'
            commande.notes = f"Refusée par {request.user.username}: {raison}"
            commande.save()
            messages.warning(request, f"Commande #{commande.numero_commande} refusée.")
            
            # Envoyer un email au client pour notifier le refus
            envoyer_email_confirmation_commande(commande)
        
        return redirect('ecommerce:vendeur_commandes')
    
    return render(request, 'ecommerce/vendeur/confirmer_commande.html', {
        'commande': commande
    })

@login_required
@user_passes_test(est_vendeur)
def vendeur_supprimer_produit(request, produit_id):
    """Supprimer un produit (vendeur seulement)"""
    produit = get_object_or_404(Produit, id=produit_id, vendeur=request.user)
    if request.method == 'POST':
        nom_produit = produit.nom
        produit.delete()
        messages.success(request, f"Produit '{nom_produit}' supprimé !")
        return redirect('ecommerce:vendeur_produits')
    
    return render(request, 'ecommerce/vendeur/confirmer_suppression.html', {
        'produit': produit
    })

@login_required
def mes_commandes(request):
    """Commande de l'utilisateur connecté (client ou vendeur)"""
    print(f"User: {request.user.username}, authenticated: {request.user.is_authenticated}")
    if hasattr(request.user, 'profil') and request.user.profil.est_vendeur():
        commandes = Commande.objects.filter(lignes_commande__produit__vendeur=request.user).distinct().prefetch_related('lignes_commande__produit__vendeur', 'lignes_commande__produit__categorie', 'lignes_commande__produit__etiquettes').order_by('-date_commande')
        print(f"Vendeur orders count: {commandes.count()}")
        # Calculer le total pour le vendeur
        total_commandes = 0
        for commande in commandes:
            for ligne in commande.lignes_commande.all():
                if ligne.produit.vendeur == request.user:
                    total_commandes += ligne.get_sous_total()
    else:
        commandes = Commande.objects.filter(client=request.user).prefetch_related('lignes_commande__produit__vendeur', 'lignes_commande__produit__categorie', 'lignes_commande__produit__etiquettes').order_by('-date_commande')
        print(f"Client orders count: {commandes.count()}")
        print(f"Client role: {request.user.profil.role if hasattr(request.user, 'profil') else 'No profil'}")
        # Calculer le total pour le client
        total_commandes = sum(commande.montant_total for commande in commandes)
    
    return render(request, 'ecommerce/mes_commandes.html', {
        'commandes': commandes,
        'total_commandes': total_commandes
    })

@login_required
def toggle_favorite(request, produit_id):
    """Ajouter ou supprimer un produit des favoris"""
    produit = get_object_or_404(Produit, id=produit_id)
    favori, created = Favoris.objects.get_or_create(utilisateur=request.user, produit=produit)
    
    if not created:
        # Le favori existe déjà, on le supprime
        favori.delete()
        messages.success(request, f"{produit.nom} retiré des favoris.")
    else:
        # Nouveau favori ajouté
        messages.success(request, f"{produit.nom} ajouté aux favoris.")
    
    return redirect(request.META.get('HTTP_REFERER', 'ecommerce:car'))

@login_required
def mes_favoris(request):
    """Voir la liste des favoris de l'utilisateur"""
    favoris = Favoris.objects.filter(utilisateur=request.user).select_related('produit').order_by('-date_ajout')
    return render(request, 'ecommerce/mes_favoris.html', {
        'favoris': favoris
    })

@login_required
def supprimer_favori(request, produit_id):
    """Supprimer un produit des favoris"""
    produit = get_object_or_404(Produit, id=produit_id)
    Favoris.objects.filter(utilisateur=request.user, produit=produit).delete()
    messages.success(request, f"{produit.nom} retiré des favoris.")
    return redirect('ecommerce:mes_favoris')

@login_required
def profil_client(request):
    """Vue pour afficher le profil du client connecté"""
    if not hasattr(request.user, 'profil') or not request.user.profil.est_client():
        messages.error(request, "Accès réservé aux clients.")
        return redirect('ecommerce:index')
    
    # Récupérer le panier actuel
    panier, created = Panier.objects.get_or_create(utilisateur=request.user)
    elements_panier = panier.elements.select_related('produit__vendeur', 'produit__categorie').prefetch_related('produit__etiquettes').all()
    total_panier = panier.get_total()
    
    # Récupérer les commandes du client
    commandes = Commande.objects.filter(client=request.user).prefetch_related(
        'lignes_commande__produit__vendeur', 
        'lignes_commande__produit__categorie', 
        'lignes_commande__produit__etiquettes'
    ).order_by('-date_commande')[:5]  # Dernières 5 commandes
    
    # Récupérer les avis du client
    reviews = Review.objects.filter(utilisateur=request.user).select_related('produit__vendeur').order_by('-date_creation')
    
    # Statistiques
    total_commandes = Commande.objects.filter(client=request.user).count()
    total_depense = sum(cmd.montant_total for cmd in Commande.objects.filter(client=request.user))
    
    return render(request, 'ecommerce/profil_client.html', {
        'panier': panier,
        'elements_panier': elements_panier,
        'total_panier': total_panier,
        'commandes': commandes,
        'reviews': reviews,
        'total_commandes': total_commandes,
        'total_depense': total_depense
    })

@login_required
def mes_avis(request):
    """Vue pour afficher tous les avis laissés par le client connecté"""
    if not hasattr(request.user, 'profil') or not request.user.profil.est_client():
        messages.error(request, "Accès réservé aux clients.")
        return redirect('ecommerce:index')
    
    # Récupérer tous les avis du client
    reviews = Review.objects.filter(utilisateur=request.user).select_related('produit__vendeur').order_by('-date_creation')
    
    # Statistiques des avis
    total_reviews = reviews.count()
    average_rating = 0
    if total_reviews > 0:
        average_rating = round(sum(review.note for review in reviews) / total_reviews, 1)
    
    # Répartition par note avec calcul des pourcentages
    rating_distribution = {}
    for i in range(1, 6):
        count = reviews.filter(note=i).count()
        rating_distribution[i] = {
            'count': count,
            'percentage': round((count / total_reviews * 100), 1) if total_reviews > 0 else 0
        }
    
    # Créer une liste de tuples (rating, data) pour faciliter l'accès dans le template
    rating_stats = [(i, rating_distribution[i]) for i in range(1, 6)]
    
    return render(request, 'ecommerce/mes_avis.html', {
        'reviews': reviews,
        'total_reviews': total_reviews,
        'average_rating': average_rating,
        'rating_distribution': rating_distribution,
        'rating_stats': rating_stats
    })

@login_required
def profil_vendeur_prive(request):
    """Vue pour afficher le profil privé du vendeur connecté"""
    if not hasattr(request.user, 'profil') or not request.user.profil.est_vendeur():
        messages.error(request, "Accès réservé aux vendeurs.")
        return redirect('ecommerce:index')
    
    # Statistiques du vendeur
    nb_produits = Produit.objects.filter(vendeur=request.user).count()
    nb_produits_disponibles = Produit.objects.filter(vendeur=request.user, disponible=True).count()
    
    # Commandes concernant les produits du vendeur
    commandes = Commande.objects.filter(lignes_commande__produit__vendeur=request.user).distinct().order_by('-date_commande')[:5]
    
    # Calcul des ventes totales
    total_ventes = 0
    for commande in Commande.objects.filter(lignes_commande__produit__vendeur=request.user).distinct():
        for ligne in commande.lignes_commande.all():
            if ligne.produit.vendeur == request.user:
                total_ventes += ligne.get_sous_total()
    
    return render(request, 'ecommerce/profil_vendeur_prive.html', {
        'vendeur': request.user,
        'nb_produits': nb_produits,
        'nb_produits_disponibles': nb_produits_disponibles,
        'commandes': commandes,
        'total_ventes': total_ventes
    })

@login_required
def profil_vendeur(request, username):
    """Vue pour afficher le profil d'un vendeur approuvé"""
    try:
        vendeur = User.objects.get(username=username)
        if hasattr(vendeur, 'profil') and vendeur.profil.est_vendeur():
            produits = Produit.objects.filter(vendeur=vendeur, disponible=True).order_by('-date_creation')
            return render(request, 'ecommerce/profil_vendeur.html', {
                'vendeur': vendeur,
                'produits': produits
            })
        else:
            # Vendeur non approuvé ou inexistant
            return render(request, 'ecommerce/404.html', status=404)
    except User.DoesNotExist:
        return render(request, 'ecommerce/404.html', status=404)

@login_required
@require_POST
def soumettre_avis(request, produit_id):
    """Permettre à un client de laisser un avis sur un produit"""
    produit = get_object_or_404(Produit, id=produit_id)
    
    # Vérifier que l'utilisateur est un client
    if not hasattr(request.user, 'profil') or not request.user.profil.est_client():
        messages.error(request, "Seuls les clients peuvent laisser des avis.")
        return redirect('ecommerce:car_single', car_id=produit_id)
    
    # Vérifier que l'utilisateur peut laisser un avis
    if not produit.can_user_review(request.user):
        messages.error(request, "Vous devez avoir acheté ce produit et que votre commande soit confirmée pour laisser un avis.")
        return redirect('ecommerce:car_single', car_id=produit_id)
    
    # Vérifier que l'utilisateur n'a pas déjà laissé d'avis
    if Review.objects.filter(produit=produit, utilisateur=request.user).exists():
        messages.error(request, "Vous avez déjà laissé un avis pour ce produit.")
        return redirect('ecommerce:car_single', car_id=produit_id)
    
    # Créer l'avis
    note = request.POST.get('note')
    commentaire = request.POST.get('commentaire', '').strip()
    
    if not note:
        messages.error(request, "Veuillez sélectionner une note.")
        return redirect('ecommerce:car_single', car_id=produit_id)
    
    try:
        note = int(note)
        if note < 1 or note > 5:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, "Note invalide.")
        return redirect('ecommerce:car_single', car_id=produit_id)
    
    Review.objects.create(
        produit=produit,
        utilisateur=request.user,
        note=note,
        commentaire=commentaire if commentaire else None
    )
    
    messages.success(request, "Votre avis a été publié avec succès !")
    return redirect('ecommerce:car_single', car_id=produit_id)