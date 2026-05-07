from io import BytesIO

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile


def generate_qr_code(work_order):
    """Generate a QR code linking to the public order status page."""
    url = f'{settings.SITE_URL}/orders/check/{work_order.order_number}/'

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='#1a73e8', back_color='white')

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    filename = f'qr_{work_order.order_number}.png'
    work_order.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)


def generate_qr_image_bytes(work_order):
    """Return QR code as raw PNG bytes (for inline responses)."""
    url = f'{settings.SITE_URL}/orders/check/{work_order.order_number}/'

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='#1a73e8', back_color='white')

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()
