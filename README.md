# Drive_Shop

Une plateforme e-commerce complète pour la vente de véhicules, développée avec Django.

## Description

Drive_Shop est une application web e-commerce spécialisée dans la vente de voitures neuves et d'occasion. La plateforme permet aux vendeurs de lister leurs véhicules avec des spécifications détaillées et aux clients de parcourir, rechercher et acheter des véhicules en ligne.

## Fonctionnalités principales

### Pour les clients
- **Parcourir les véhicules** : Catalogue complet avec filtres par marque, modèle, année, prix, etc.
- **Recherche avancée** : Trouver rapidement le véhicule idéal
- **Gestion du panier** : Ajouter/supprimer des véhicules, calcul automatique des totaux
- **Système de favoris** : Sauvegarder les véhicules préférés
- **Commandes et paiements** : Processus de commande sécurisé avec suivi des statuts
- **Avis et notations** : Système de reviews pour les véhicules achetés
- **Profils utilisateurs** : Gestion des informations personnelles

### Pour les vendeurs
- **Gestion des annonces** : Ajouter, modifier et supprimer des véhicules
- **Spécifications détaillées** : Marque, modèle, année, kilométrage, carburant, transmission, équipements
- **Gestion du stock** : Suivi des disponibilités
- **Suivi des ventes** : Historique des commandes et paiements
- **Profils vendeur** : Informations d'entreprise et documents d'identification

### Pour les administrateurs
- **Interface d'administration** : Gestion complète via Django Admin (avec Jazzmin)
- **Gestion des utilisateurs** : Approbation des comptes vendeurs
- **Gestion des catégories** : Organisation des véhicules par type, marque, etc.
- **Suivi des commandes** : Gestion des statuts et expéditions

## Technologies utilisées

- **Backend** : Django 5.1.7
- **Base de données** : SQLite (développement) / PostgreSQL (production recommandé)
- **Frontend** : HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentification** : Django Allauth
- **API** : Django REST Framework
- **Formulaires** : Django Crispy Forms avec Bootstrap 5
- **Images** : Pillow pour le traitement des images
- **Tests** : Pytest et pytest-django
- **Interface admin** : Django Jazzmin

## Installation

### Prérequis
- Python 3.8+
- pip
- Git

### Étapes d'installation

1. **Cloner le repository**
```bash
git clone <url-du-repository>
cd Drive_Shop
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer la base de données**
```bash
python manage.py migrate
```

5. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

6. **Lancer le serveur de développement**
```bash
python manage.py runserver
```

L'application sera accessible sur http://127.0.0.1:8000

## Configuration

### Variables d'environnement
Créer un fichier `.env` à la racine du projet avec :
```
SECRET_KEY=votre-cle-secrete
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Configuration email (optionnel)
Pour activer l'envoi d'emails :
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe
```

## Utilisation

### Interface administrateur
- Accès : `/admin/`
- Utiliser les identifiants du superutilisateur créé

### Interface vendeur/client
- Inscription : Créer un compte et sélectionner le rôle approprié
- Pour les vendeurs : Attendre l'approbation de l'administrateur
