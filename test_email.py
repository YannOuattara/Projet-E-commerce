#!/usr/bin/env python
"""
Script de test pour vérifier le système d'envoi d'emails
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Drive_Shop.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    """Test d'envoi d'email simple"""
    try:
        send_mail(
            subject='Test DriveShop - Email System',
            message='Ceci est un test du système d\'email de DriveShop.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['yanncedricemmanuelo@gmail.com'],  # Email de test
            fail_silently=False,
        )
        print("✅ Email de test envoyé avec succès !")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email de test : {str(e)}")
        return False

if __name__ == '__main__':
    print("🧪 Test du système d'envoi d'emails...")
    success = test_email()
    if success:
        print("🎉 Le système d'email fonctionne correctement !")
    else:
        print("⚠️ Problème avec le système d'email.")
        sys.exit(1)
