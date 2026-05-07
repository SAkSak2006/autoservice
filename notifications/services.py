import logging

from django.conf import settings

from .models import NotificationTemplate, Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Multi-channel notification dispatcher."""

    WORKSHOP_PHONE = '+7 (000) 123-45-67'

    @classmethod
    def dispatch(cls, client, event_type, work_order=None, extra_context=None):
        """Send notification to all preferred channels of the client."""
        channels = client.get_preferred_channels()
        if not channels:
            logger.info('Client %s has no preferred channels, skipping.', client)
            return []

        notifications = []
        for channel in channels:
            template = NotificationTemplate.objects.filter(
                event_type=event_type, channel=channel, is_active=True,
            ).first()
            if not template:
                logger.debug('No template for event=%s channel=%s', event_type, channel)
                continue

            context = cls._build_context(client, work_order, extra_context)

            try:
                body = template.body_template.format(**context)
                subject = template.subject_template.format(**context) if template.subject_template else ''
            except KeyError as e:
                logger.error('Template variable missing: %s in template %s', e, template.name)
                continue

            notification = Notification.objects.create(
                client=client,
                work_order=work_order,
                channel=channel,
                event_type=event_type,
                subject=subject,
                body=body,
                status=Notification.Status.PENDING,
            )
            notifications.append(notification)

            # Send: try Celery async first, fallback to sync
            try:
                from .tasks import send_notification_task
                send_notification_task.delay(notification.id)
            except Exception:
                # Celery not available — send synchronously
                try:
                    from .tasks import send_notification_task as task_fn
                    task_fn(notification.id)
                except Exception as e:
                    logger.warning('Notification %s send failed: %s', notification.id, e)

        return notifications

    @classmethod
    def _build_context(cls, client, work_order=None, extra_context=None):
        """Build template variable dict."""
        ctx = {
            'client_name': client.get_full_name(),
            'workshop_phone': cls.WORKSHOP_PHONE,
        }
        if work_order:
            ctx.update({
                'order_number': work_order.order_number,
                'vehicle_info': str(work_order.vehicle),
                'status': work_order.get_status_display(),
                'total_cost': f'{work_order.final_cost:,.0f}',
                'qr_url': work_order.get_qr_url(),
            })
        if extra_context:
            ctx.update(extra_context)
        return ctx

    @classmethod
    def dispatch_order_ready(cls, work_order):
        """Shortcut for the key 'order_ready' event."""
        return cls.dispatch(
            client=work_order.client,
            event_type=NotificationTemplate.EventType.ORDER_READY,
            work_order=work_order,
        )

    @classmethod
    def dispatch_order_created(cls, work_order):
        return cls.dispatch(
            client=work_order.client,
            event_type=NotificationTemplate.EventType.ORDER_CREATED,
            work_order=work_order,
        )

    @classmethod
    def dispatch_status_changed(cls, work_order):
        return cls.dispatch(
            client=work_order.client,
            event_type=NotificationTemplate.EventType.STATUS_CHANGED,
            work_order=work_order,
        )
