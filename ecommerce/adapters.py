from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


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
        """Envoie les emails de confirmation"""
        # Ajouter l'URL d'activation seulement si la clé existe (pour les emails de confirmation)
        if 'key' in context:
            context['activate_url'] = (
                f"{settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else ''}"
                f"/accounts/confirm-email/{context['key']}/"
            )
        super().send_mail(template_prefix, email, context)

