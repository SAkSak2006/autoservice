from django.core.management.base import BaseCommand, CommandError

from clients.models import Client
from notifications.models import NotificationTemplate
from notifications.services import NotificationService
from orders.models import WorkOrder


class Command(BaseCommand):
    help = 'Send a test notification to a client.'

    def add_arguments(self, parser):
        parser.add_argument('--client-id', type=int, required=True, help='Client ID')
        parser.add_argument('--channel', type=str, default='email',
                            choices=['email', 'telegram', 'sms'],
                            help='Notification channel')
        parser.add_argument('--event', type=str, default='order_ready',
                            choices=[c[0] for c in NotificationTemplate.EventType.choices],
                            help='Event type')
        parser.add_argument('--order-id', type=int, default=None,
                            help='WorkOrder ID (optional)')

    def handle(self, *args, **options):
        try:
            client = Client.objects.get(pk=options['client_id'])
        except Client.DoesNotExist:
            raise CommandError(f'Client with id={options["client_id"]} not found.')

        work_order = None
        if options['order_id']:
            try:
                work_order = WorkOrder.objects.get(pk=options['order_id'])
            except WorkOrder.DoesNotExist:
                raise CommandError(f'WorkOrder with id={options["order_id"]} not found.')

        channel = options['channel']
        event = options['event']

        # Temporarily override client preferences to force the specified channel
        original_prefs = client.notification_preferences
        client.notification_preferences = {channel: True}

        self.stdout.write(
            f'Sending {event} via {channel} to {client.get_full_name()} '
            f'({client.phone})...'
        )

        notifications = NotificationService.dispatch(
            client=client,
            event_type=event,
            work_order=work_order,
        )

        # Restore original preferences (don't save to DB)
        client.notification_preferences = original_prefs

        if notifications:
            for n in notifications:
                self.stdout.write(self.style.SUCCESS(
                    f'  Created notification #{n.id} [{n.status}] via {n.channel}'
                ))
        else:
            self.stdout.write(self.style.WARNING(
                '  No notification was created. Check template exists for '
                f'event={event} channel={channel}.'
            ))
