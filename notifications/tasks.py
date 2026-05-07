import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)

# Retry delays: 10s, 30s, 90s (exponential-ish)
RETRY_DELAYS = [10, 30, 90]


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_notification_task(self, notification_id):
    """Send a single notification by its ID."""
    from .models import Notification

    try:
        notification = Notification.objects.select_related('client').get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error('Notification %s not found.', notification_id)
        return

    try:
        if notification.channel == 'email':
            _send_email(notification)
        elif notification.channel == 'telegram':
            _send_telegram(notification)
        elif notification.channel == 'sms':
            _send_sms(notification)
        else:
            raise ValueError(f'Unknown channel: {notification.channel}')

        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=['status', 'sent_at'])
        logger.info('Notification %s sent via %s.', notification_id, notification.channel)

    except Exception as exc:
        notification.retry_count += 1
        notification.error_message = str(exc)

        if notification.retry_count >= 3:
            notification.status = Notification.Status.FAILED
            notification.save(update_fields=['status', 'retry_count', 'error_message'])
            logger.error('Notification %s failed after %d retries: %s',
                         notification_id, notification.retry_count, exc)
        else:
            notification.save(update_fields=['retry_count', 'error_message'])
            delay = RETRY_DELAYS[min(notification.retry_count - 1, len(RETRY_DELAYS) - 1)]
            raise self.retry(exc=exc, countdown=delay)


# ─── Email sender ─────────────────────────────────────────────

EMAIL_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <div style="text-align:center;padding:15px 0;border-bottom:2px solid #1a73e8;margin-bottom:20px;">
    <span style="font-size:20px;font-weight:bold;color:#1a73e8;">🔧 AutoService Pro</span>
  </div>
  <div style="line-height:1.6;color:#333;">{body_html}</div>
  <div style="margin-top:30px;padding-top:15px;border-top:1px solid #e0e0e0;
              font-size:12px;color:#999;text-align:center;">
    © {year} АвтоСервис Про | {workshop_phone}
  </div>
</body>
</html>"""


def _send_email(notification):
    """Send email notification with plain text + HTML version."""
    recipient = notification.client.email
    if not recipient:
        raise ValueError('Client has no email address.')

    subject = notification.subject or 'Уведомление от AutoService Pro'
    body_text = notification.body

    # Build HTML version
    body_html = notification.body.replace('\n', '<br>\n')
    html_content = EMAIL_HTML_TEMPLATE.format(
        body_html=body_html,
        year=timezone.now().year,
        workshop_phone='+7 (000) 123-45-67',
    )

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    msg.attach_alternative(html_content, 'text/html')
    msg.send(fail_silently=False)


# ─── Telegram sender ─────────────────────────────────────────

def _send_telegram(notification):
    """Send Telegram notification via Bot API."""
    import requests

    chat_id = notification.client.telegram_chat_id
    if not chat_id:
        raise ValueError('Client has no telegram_chat_id.')

    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise ValueError('TELEGRAM_BOT_TOKEN not configured.')

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    response = requests.post(url, json={
        'chat_id': chat_id,
        'text': notification.body,
        'parse_mode': 'HTML',
    }, timeout=10)

    if not response.ok:
        error_detail = response.text[:200]
        raise Exception(f'Telegram API error {response.status_code}: {error_detail}')


# ─── SMS sender ───────────────────────────────────────────────

def _send_sms(notification):
    """Send SMS via SMS.ru API (stub in development)."""
    import requests

    phone = notification.client.phone
    if not phone:
        raise ValueError('Client has no phone number.')

    api_id = getattr(settings, 'SMSRU_API_ID', '')

    if not api_id:
        # Development stub — just log
        logger.info('[SMS STUB] To: %s | Body: %s', phone, notification.body[:160])
        return

    # Production: SMS.ru API
    response = requests.get('https://sms.ru/sms/send', params={
        'api_id': api_id,
        'to': phone.replace('+', ''),
        'msg': notification.body[:160],
        'json': 1,
    }, timeout=10)

    data = response.json()
    if data.get('status') != 'OK':
        raise Exception(f'SMS.ru error: {data}')


# ─── Periodic: maintenance reminders ─────────────────────────

@shared_task
def check_maintenance_reminders():
    """Daily task: send reminders to clients whose last visit was > 6 months ago."""
    from clients.models import Client
    from orders.models import WorkOrder
    from .models import Notification, NotificationTemplate
    from .services import NotificationService

    six_months_ago = timezone.now() - timedelta(days=180)
    cutoff_reminder = timezone.now() - timedelta(days=30)  # Don't repeat within 30 days

    clients = Client.objects.filter(is_active=True)

    sent_count = 0
    for client in clients:
        # Find last delivered order
        last_order = (
            WorkOrder.objects
            .filter(client=client, status='delivered')
            .order_by('-delivered_at')
            .first()
        )
        if not last_order or not last_order.delivered_at:
            continue

        # Skip if last visit was recent (< 6 months)
        if last_order.delivered_at > six_months_ago:
            continue

        # Skip if we already sent a maintenance reminder recently
        recent_reminder = Notification.objects.filter(
            client=client,
            event_type=NotificationTemplate.EventType.MAINTENANCE_REMINDER,
            created_at__gte=cutoff_reminder,
        ).exists()
        if recent_reminder:
            continue

        # Dispatch reminder
        NotificationService.dispatch(
            client=client,
            event_type=NotificationTemplate.EventType.MAINTENANCE_REMINDER,
            work_order=last_order,  # Context for vehicle_info
        )
        sent_count += 1

    logger.info('Maintenance reminders sent: %d', sent_count)
    return sent_count
