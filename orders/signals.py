from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import WorkOrder, WorkOrderStatusHistory


@receiver(pre_save, sender=WorkOrder)
def track_status_change(sender, instance, **kwargs):
    """Track status changes and auto-fill date fields via signal."""
    if instance.pk is None:
        return  # New object, skip
    if getattr(instance, '_skip_history', False):
        return  # Skip when transition_to() handles it

    try:
        old = WorkOrder.objects.get(pk=instance.pk)
    except WorkOrder.DoesNotExist:
        return

    if old.status != instance.status:
        from django.utils import timezone
        now = timezone.now()

        # Auto-fill date fields
        if instance.status == WorkOrder.Status.IN_PROGRESS and not instance.started_at:
            instance.started_at = now
        elif instance.status == WorkOrder.Status.COMPLETED:
            instance.completed_at = now
        elif instance.status == WorkOrder.Status.DELIVERED:
            instance.delivered_at = now
