import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back_office.settings')
django.setup()

from django.contrib.auth.models import User

u, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@meetvoice.fr',
        'is_staff': True,
        'is_superuser': True,
    }
)
u.set_password('78454qqs8a78ae87a8e7a8787a8ea8e7')
u.email = 'admin@meetvoice.fr'
u.is_staff = True
u.is_superuser = True
u.save()
print('Admin created' if created else 'Admin updated')
