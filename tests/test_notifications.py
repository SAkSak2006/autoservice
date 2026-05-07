import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from notifications.models import Notification, NotificationTemplate
from notifications.services import NotificationService
from notifications.tasks import send_notification_task
from tests.factories import (
    ClientFactory, WorkOrderFactory, NotificationFactory,
    NotificationTemplateFactory, SparePartFactory,
)


@pytest.mark.django_db
class TestNotificationDispatch:
    def test_dispatch_sends_to_preferred_channels(self):
        client = ClientFactory(
            notification_preferences={'email': True, 'telegram': True, 'sms': False},
            email='test@example.com',
            telegram_chat_id=123456,
        )
        # Create templates for email and telegram
        NotificationTemplateFactory(
            name='email_ready', event_type='order_ready', channel='email',
        )
        NotificationTemplateFactory(
            name='tg_ready', event_type='order_ready', channel='telegram',
        )
        order = WorkOrderFactory(client=client)

        with patch('notifications.services.send_notification_task') as mock_task:
            mock_task.delay = MagicMock()
            notifications = NotificationService.dispatch(
                client=client,
                event_type='order_ready',
                work_order=order,
            )

        assert len(notifications) == 2
        channels = {n.channel for n in notifications}
        assert channels == {'email', 'telegram'}
        assert mock_task.delay.call_count == 2

    def test_dispatch_skips_inactive_template(self):
        client = ClientFactory(notification_preferences={'email': True})
        NotificationTemplateFactory(
            name='inactive', event_type='order_ready', channel='email', is_active=False,
        )
        order = WorkOrderFactory(client=client)

        with patch('notifications.services.send_notification_task'):
            notifications = NotificationService.dispatch(
                client=client,
                event_type='order_ready',
                work_order=order,
            )
        assert len(notifications) == 0

    def test_dispatch_no_channels(self):
        client = ClientFactory(notification_preferences={'email': False, 'telegram': False, 'sms': False})
        notifications = NotificationService.dispatch(client=client, event_type='order_ready')
        assert len(notifications) == 0


@pytest.mark.django_db
class TestTemplateRendering:
    def test_variables_substituted(self):
        client = ClientFactory(first_name='Иван', last_name='Петров')
        order = WorkOrderFactory(client=client)
        order.final_cost = Decimal('15500')
        order.save()

        tpl = NotificationTemplateFactory(
            name='test_render',
            body_template='Клиент: {client_name}, Заказ: {order_number}, Сумма: {total_cost}, Авто: {vehicle_info}, URL: {qr_url}, Тел: {workshop_phone}',
        )

        context = NotificationService._build_context(client, order)
        body = tpl.body_template.format(**context)

        assert 'Петров Иван' in body
        assert order.order_number in body
        assert '15,500' in body or '15500' in body


@pytest.mark.django_db
class TestEmailSending:
    def test_email_notification_sent(self):
        client = ClientFactory(email='client@test.com')
        notification = NotificationFactory(
            client=client,
            channel='email',
            subject='Тест',
            body='Тестовое уведомление',
        )

        with patch('notifications.tasks.EmailMultiAlternatives') as MockEmail:
            mock_instance = MagicMock()
            MockEmail.return_value = mock_instance
            send_notification_task(notification.id)

        MockEmail.assert_called_once()
        call_kwargs = MockEmail.call_args
        assert call_kwargs[1]['to'] == ['client@test.com'] or call_kwargs[0][3] == ['client@test.com']
        mock_instance.send.assert_called_once()

        notification.refresh_from_db()
        assert notification.status == 'sent'


@pytest.mark.django_db
class TestTelegramSending:
    def test_telegram_notification_sent(self, settings):
        settings.TELEGRAM_BOT_TOKEN = 'fake-token'
        client = ClientFactory(telegram_chat_id=123456)
        notification = NotificationFactory(
            client=client,
            channel='telegram',
            body='Тест Telegram',
        )

        with patch('notifications.tasks.requests.post') as mock_post:
            mock_post.return_value = MagicMock(ok=True)
            send_notification_task(notification.id)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json']['chat_id'] == 123456
        assert 'Тест Telegram' in call_args[1]['json']['text']

        notification.refresh_from_db()
        assert notification.status == 'sent'


@pytest.mark.django_db
class TestNotificationRetry:
    def test_retry_on_failure(self):
        client = ClientFactory(email='')  # No email → will fail
        notification = NotificationFactory(client=client, channel='email')

        # Should fail because no email
        send_notification_task(notification.id)

        notification.refresh_from_db()
        assert notification.retry_count >= 1
        assert notification.error_message != ''
