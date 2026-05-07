"""
Custom Django email backend using Resend API.
https://resend.com/docs
"""
import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        resend.api_key = getattr(settings, 'RESEND_API_KEY', '')

    def send_messages(self, email_messages):
        if not resend.api_key:
            return 0

        sent = 0
        for msg in email_messages:
            try:
                params = {
                    'from': msg.from_email or settings.DEFAULT_FROM_EMAIL,
                    'to': list(msg.to),
                    'subject': msg.subject,
                    'text': msg.body,
                }

                # If HTML alternative exists, add it
                if hasattr(msg, 'alternatives'):
                    for content, mimetype in msg.alternatives:
                        if mimetype == 'text/html':
                            params['html'] = content
                            break

                resend.Emails.send(params)
                sent += 1
            except Exception as e:
                if not self.fail_silently:
                    raise
        return sent
