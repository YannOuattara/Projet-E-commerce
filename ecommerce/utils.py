from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Commande


def envoyer_email_nouvelle_commande(commande):
    """
    Envoie un email au vendeur lorsqu'une nouvelle commande est passée
    """
    vendeurs = commande.get_vendeurs()

    for vendeur in vendeurs:
        if vendeur.email:  # Vérifier que le vendeur a une adresse email
            subject = f"Nouvelle commande #{commande.numero_commande} - DriveShop"

            context = {
                'vendeur': vendeur,
                'commande': commande,
                'client': commande.client,
                'lien_validation': f"http://127.0.0.1:8000/vendeur/commandes/"
            }

            message = render_to_string('ecommerce/emails/nouvelle_commande.html', context)

            try:
                send_mail(
                    subject=subject,
                    message='',  # Message texte brut vide car on utilise HTML
                    html_message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[vendeur.email],
                    fail_silently=False,
                )
                print(f"Email envoyé à {vendeur.email} pour la commande #{commande.numero_commande}")
            except Exception as e:
                print(f"Erreur lors de l'envoi d'email à {vendeur.email}: {str(e)}")


def envoyer_email_confirmation_commande(commande):
    """
    Envoie un email au client lorsqu'une commande est confirmée ou refusée
    """
    client = commande.client

    if client.email:
        if commande.statut == 'confirmee':
            subject = f"Votre commande #{commande.numero_commande} a été confirmée - DriveShop"
            template = 'ecommerce/emails/commande_confirmee.html'
        elif commande.statut == 'annulee':
            subject = f"Votre commande #{commande.numero_commande} a été annulée - DriveShop"
            template = 'ecommerce/emails/commande_annulee.html'
        else:
            return  # Ne pas envoyer d'email pour les autres statuts

        context = {
            'client': client,
            'commande': commande,
            'lien_commandes': f"http://127.0.0.1:8000/mes-commandes/"
        }

        message = render_to_string(template, context)

        try:
            send_mail(
                subject=subject,
                message='',  # Message texte brut vide car on utilise HTML
                html_message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                fail_silently=False,
            )
            print(f"Email envoyé à {client.email} pour la commande #{commande.numero_commande}")
        except Exception as e:
            print(f"Erreur lors de l'envoi d'email à {client.email}: {str(e)}")


def envoyer_email_details_commande(commande):
    """
    Envoie un email au client avec tous les détails de sa commande après validation
    """
    client = commande.client

    if client.email:
        subject = f"Détails de votre commande #{commande.numero_commande} - DriveShop"

        context = {
            'client': client,
            'commande': commande,
            'lignes_commande': commande.lignes_commande.select_related('produit__vendeur').all(),
            'lien_commandes': f"http://127.0.0.1:8000/mes-commandes/"
        }

        message = render_to_string('ecommerce/emails/details_commande.html', context)

        try:
            send_mail(
                subject=subject,
                message='',  # Message texte brut vide car on utilise HTML
                html_message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                fail_silently=False,
            )
            print(f"Email de détails envoyé à {client.email} pour la commande #{commande.numero_commande}")
        except Exception as e:
            print(f"Erreur lors de l'envoi d'email de détails à {client.email}: {str(e)}")
