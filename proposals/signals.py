import logging

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from proposals.models import Proposta


logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=Proposta)
def ao_deletar_proposta(sender, instance, **kwargs):
    logger.info(
        "Proposta removida",
        extra={
            "proposta_id": instance.id,
            "empresa_id": instance.empresa_id,
            "status": instance.status,
        },
    )
