from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from allauth.account.forms import SignupForm
from allauth.account.adapter import get_adapter
from allauth.account import signals
from django.db import transaction
from .models import ProfilUtilisateur


class CustomSignupForm(SignupForm):
    """Formulaire d'inscription personnalisé avec choix du rôle"""
    
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('vendeur', 'Vendeur'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label='Je souhaite :',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        initial='client'
    )
    
    first_name = forms.CharField(
        max_length=30,
        label='Prénom',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre prénom'
        }),
        required=False
    )
    
    last_name = forms.CharField(
        max_length=30,
        label='Nom',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom'
        }),
        required=False
    )
    
    # Champs spécifiques aux vendeurs
    company_name = forms.CharField(
        max_length=100,
        label='Nom de l\'entreprise',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de votre entreprise'
        }),
        required=False
    )
    
    business_description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Décrivez votre activité',
            'rows': 3
        }),
        label='Description de l\'activité',
        required=False
    )
    
    business_type = forms.CharField(
        max_length=100,
        label='Type d\'activité',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Vente de voitures, Concessionnaire...'
        }),
        required=False
    )
    
    id_document = forms.FileField(
        label='Pièce d\'identité',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file'
        }),
        help_text='Téléchargez une copie de votre pièce d\'identité (carte d\'identité, passeport, etc.)',
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Masquer les champs vendeur par défaut
        self.fields['company_name'].widget.attrs['style'] = 'display: none;'
        self.fields['business_description'].widget.attrs['style'] = 'display: none;'
        self.fields['business_type'].widget.attrs['style'] = 'display: none;'
        self.fields['id_document'].widget.attrs['style'] = 'display: none;'
    
    @transaction.atomic
    def save(self, request):
        # Sauvegarder l'utilisateur
        user = super().save(request)
        
        # Récupérer le rôle choisi
        role = self.cleaned_data.get('role', 'client')
        
        # Créer ou mettre à jour le profil avec le rôle choisi
        profil, created = ProfilUtilisateur.objects.get_or_create(
            user=user,
            defaults={
                'role': role,
                'approved': role != 'vendeur',  # Vendeurs non approuvés par défaut
            }
        )
        
        if not created:
            profil.role = role
            profil.approved = role != 'vendeur'
            profil.save()
        
        # Sauvegarder les champs spécifiques aux vendeurs si rôle vendeur
        if role == 'vendeur':
            profil.company_name = self.cleaned_data.get('company_name')
            profil.business_description = self.cleaned_data.get('business_description')
            profil.business_type = self.cleaned_data.get('business_type')
            if self.cleaned_data.get('id_document'):
                profil.id_document = self.cleaned_data.get('id_document')
            profil.save()
        
        return user


class EmailForm(forms.Form):
    """Formulaire pour rechercher par email"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )

