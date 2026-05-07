import asyncio
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Run the Telegram bot in polling mode (development).'

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            raise CommandError(
                'TELEGRAM_BOT_TOKEN is not set. '
                'Add it to your .env file.'
            )

        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO,
        )

        self.stdout.write(self.style.SUCCESS('Starting Telegram bot in polling mode...'))

        from notifications.telegram_bot import create_bot_application
        app = create_bot_application(token)

        # Python 3.12+ may not have a default event loop in MainThread
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        app.run_polling(drop_pending_updates=True)
