"""
Signaux Django pour la gestion automatique des alarmes de congés.

Lorsqu'un congé passe au statut 'approved', deux alarmes sont créées :
  - 7 jours avant le début du congé (rappel anticipé pour le manager).
  - La veille du début du congé (rappel de dernière minute).

Si l'un des deux trigger_date tombe dans le passé, l'alarme est quand même
créée (trigger_date peut être antérieure à today) afin de ne pas la manquer ;
elle apparaîtra immédiatement dans la liste des alarmes dues.
"""

import logging
from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Leave, LeaveNotification

logger = logging.getLogger('api')


@receiver(post_save, sender=Leave)
def create_leave_notifications(sender, instance, **kwargs):
    """Crée les alarmes de rappel quand un congé est approuvé.

    Appelé automatiquement après chaque sauvegarde d'un objet Leave.
    N'agit que si le statut est 'approved'.
    Utilise get_or_create pour éviter les doublons en cas de multi-save.

    Args:
        sender: La classe Leave.
        instance (Leave): L'instance sauvegardée.
        **kwargs: Arguments supplémentaires (created, raw, etc.).
    """
    if instance.status != 'approved':
        return

    # Alarme J-7
    trigger_7days = instance.start_date - timedelta(days=7)
    notif_7, created_7 = LeaveNotification.objects.get_or_create(
        leave=instance,
        notification_type=LeaveNotification.TYPE_7DAYS,
        defaults={'trigger_date': trigger_7days},
    )
    if created_7:
        logger.info(
            "Alarme J-7 créée pour congé #%s (trigger: %s)",
            instance.pk, trigger_7days,
        )

    # Alarme veille (J-1)
    trigger_eve = instance.start_date - timedelta(days=1)
    notif_eve, created_eve = LeaveNotification.objects.get_or_create(
        leave=instance,
        notification_type=LeaveNotification.TYPE_EVE,
        defaults={'trigger_date': trigger_eve},
    )
    if created_eve:
        logger.info(
            "Alarme veille créée pour congé #%s (trigger: %s)",
            instance.pk, trigger_eve,
        )
