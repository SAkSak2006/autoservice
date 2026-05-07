import pytest

from django.conf import settings
from orders.models import WorkOrder
from tests.factories import WorkOrderFactory


@pytest.mark.django_db
class TestQRCodeGeneration:
    def test_qr_code_generated_on_create(self):
        order = WorkOrderFactory()
        order.refresh_from_db()
        assert order.qr_code, 'QR code should be generated on create'
        assert order.qr_code.name.endswith('.png')

    def test_qr_code_filename(self):
        order = WorkOrderFactory()
        order.refresh_from_db()
        assert order.order_number in order.qr_code.name

    def test_qr_url_contains_order_number(self):
        order = WorkOrderFactory()
        qr_url = order.get_qr_url()
        assert order.order_number in qr_url
        assert '/orders/check/' in qr_url

    def test_qr_code_is_valid_png(self):
        order = WorkOrderFactory()
        order.refresh_from_db()
        # Read file and check PNG magic bytes
        order.qr_code.open('rb')
        header = order.qr_code.read(8)
        order.qr_code.close()
        assert header[:4] == b'\x89PNG', 'File should be a valid PNG'

    def test_qr_download_view(self):
        from django.test import Client as HttpClient
        from tests.factories import AdminUserFactory

        admin = AdminUserFactory()
        order = WorkOrderFactory()
        http = HttpClient()
        http.force_login(admin)

        resp = http.get(f'/orders/{order.pk}/qr/')
        assert resp.status_code == 200
        assert resp['Content-Type'] == 'image/png'
