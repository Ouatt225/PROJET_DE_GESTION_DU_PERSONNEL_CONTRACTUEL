from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_alter_department_options_and_more'),
    ]

    operations = [
        # 1. Ajouter le nouveau champ password_encrypted
        migrations.AddField(
            model_name='passwordrecord',
            name='password_encrypted',
            field=models.CharField(
                default='',
                max_length=500,
                verbose_name='Mot de passe (chiffré)'
            ),
            preserve_default=False,
        ),
    ]
