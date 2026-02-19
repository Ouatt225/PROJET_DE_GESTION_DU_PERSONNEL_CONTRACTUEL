"""
Data migration : chiffre toutes les valeurs existantes de password_plain
vers le nouveau champ password_encrypted, puis supprime password_plain.
"""
from django.db import migrations


def encrypt_existing(apps, schema_editor):
    from api.encryption import encrypt_password

    PasswordRecord = apps.get_model('api', 'PasswordRecord')
    for record in PasswordRecord.objects.all():
        plain = record.password_plain or ''
        record.password_encrypted = encrypt_password(plain) if plain else ''
        record.save(update_fields=['password_encrypted'])


def reverse_encrypt(apps, schema_editor):
    """Annulation : déchiffre password_encrypted → password_plain."""
    from api.encryption import decrypt_password

    PasswordRecord = apps.get_model('api', 'PasswordRecord')
    for record in PasswordRecord.objects.all():
        record.password_plain = decrypt_password(record.password_encrypted)
        record.save(update_fields=['password_plain'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_rename_password_plain_to_encrypted'),
    ]

    operations = [
        # Chiffrer les données existantes
        migrations.RunPython(encrypt_existing, reverse_code=reverse_encrypt),

        # Supprimer l'ancien champ en clair
        migrations.RemoveField(
            model_name='passwordrecord',
            name='password_plain',
        ),
    ]
