from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse


class CustomAccountAdapter(DefaultAccountAdapter):
    """Adapter personnalisé pour gérer la redirection selon le rôle"""
    
    def get_login_redirect_url(self, request):
        """Redirige l'utilisateur selon son rôle après connexion"""
        if request.user.is_authenticated:
            if hasattr(request.user, 'profil'):
                if request.user.profil.est_vendeur():
                    return '/vendeur/dashboard/'  # Correction : pas de /ecommerce/
                elif request.user.profil.est_client():
                    return '/car/'  # Correction : pas de /ecommerce/
        return '/'
    
    def get_signup_redirect_url(self, request):
        """Redirige après inscription"""
        if request.user.is_authenticated:
            if hasattr(request.user, 'profil'):
                if request.user.profil.est_vendeur():
                    return '/vendeur/dashboard/'  # Correction : pas de /ecommerce/
                elif request.user.profil.est_client():
                    return '/car/'  # Correction : pas de /ecommerce/
        return '/'

    def send_mail(self, template_prefix, email, context):
        """Envoie les emails de confirmation avec URL d'activation correcte"""
        if 'key' in context:
            # Construire l'URL d'activation avec le domaine du site
            site = Site.objects.get_current()
            protocol = 'https' if settings.SECURE_SSL_REDIRECT else 'http'
            activate_url = f"{protocol}://{site.domain}{reverse('account_confirm_email', kwargs={'key': context['key']})}"
            context['activate_url'] = activate_url
        super().send_mail(template_prefix, email, context)

