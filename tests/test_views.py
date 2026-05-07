import pytest
from django.test import Client as HttpClient

from orders.models import WorkOrder
from clients.models import Client
from tests.factories import (
    AdminUserFactory, MechanicUserFactory, ClientUserFactory,
    ClientFactory, VehicleFactory, WorkOrderFactory, ServiceCategoryFactory,
)


@pytest.fixture
def http():
    return HttpClient()


@pytest.mark.django_db
class TestAuthRedirects:
    def test_dashboard_requires_login(self, http):
        resp = http.get('/dashboard/')
        assert resp.status_code == 302
        assert '/accounts/login/' in resp.url

    def test_orders_requires_login(self, http):
        resp = http.get('/orders/')
        assert resp.status_code == 302

    def test_clients_requires_login(self, http):
        resp = http.get('/clients/')
        assert resp.status_code == 302


@pytest.mark.django_db
class TestDashboardAccess:
    def test_admin_sees_dashboard(self, http):
        user = AdminUserFactory()
        http.force_login(user)
        resp = http.get('/dashboard/')
        assert resp.status_code == 200

    def test_mechanic_sees_dashboard(self, http):
        user = MechanicUserFactory()
        http.force_login(user)
        resp = http.get('/dashboard/')
        assert resp.status_code == 200  # StaffRequiredMixin allows mechanic

    def test_client_denied_dashboard(self, http):
        user = ClientUserFactory()
        http.force_login(user)
        resp = http.get('/dashboard/')
        assert resp.status_code == 403


@pytest.mark.django_db
class TestOrderViews:
    def test_mechanic_sees_only_assigned_orders(self, http):
        mech = MechanicUserFactory()
        client = ClientFactory()
        vehicle = VehicleFactory(client=client)
        assigned = WorkOrderFactory(client=client, vehicle=vehicle, assigned_mechanic=mech)
        unassigned = WorkOrderFactory()

        http.force_login(mech)
        resp = http.get('/orders/')
        content = resp.content.decode()
        assert assigned.order_number in content
        assert unassigned.order_number not in content

    def test_create_work_order(self, http):
        admin = AdminUserFactory()
        client = ClientFactory()
        vehicle = VehicleFactory(client=client)
        http.force_login(admin)

        resp = http.post('/orders/create/', {
            'client': client.pk,
            'vehicle': vehicle.pk,
            'description': 'Стук в двигателе',
        })
        assert resp.status_code == 302  # redirect to detail
        assert WorkOrder.objects.filter(client=client).exists()

    def test_status_change_ajax(self, http):
        admin = AdminUserFactory()
        order = WorkOrderFactory(status='new')
        http.force_login(admin)

        resp = http.post(f'/orders/{order.pk}/status/', {
            'new_status': 'in_progress',
            'comment': 'Начинаем',
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert data['new_status'] == 'in_progress'

        order.refresh_from_db()
        assert order.status == 'in_progress'

    def test_invalid_status_transition_returns_400(self, http):
        admin = AdminUserFactory()
        order = WorkOrderFactory(status='new')
        http.force_login(admin)

        resp = http.post(f'/orders/{order.pk}/status/', {
            'new_status': 'delivered',
        })
        assert resp.status_code == 400
        assert resp.json()['success'] is False


@pytest.mark.django_db
class TestOrderCheckPublic:
    def test_public_access(self, http):
        order = WorkOrderFactory()
        resp = http.get(f'/orders/check/{order.order_number}/')
        assert resp.status_code == 200
        assert order.order_number in resp.content.decode()

    def test_api_endpoint(self, http):
        order = WorkOrderFactory()
        resp = http.get(f'/orders/api/check/{order.order_number}/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['order_number'] == order.order_number
        assert 'status' in data
        assert 'progress_percent' in data


@pytest.mark.django_db
class TestPortalViews:
    def test_client_sees_only_own_orders(self, http):
        user = ClientUserFactory()
        client = ClientFactory(user=user)
        vehicle = VehicleFactory(client=client)
        own_order = WorkOrderFactory(client=client, vehicle=vehicle)
        other_order = WorkOrderFactory()

        http.force_login(user)
        resp = http.get('/portal/orders/')
        content = resp.content.decode()
        assert own_order.order_number in content
        assert other_order.order_number not in content

    def test_booking_creates_order(self, http):
        user = ClientUserFactory()
        client = ClientFactory(user=user)
        vehicle = VehicleFactory(client=client)
        http.force_login(user)

        resp = http.post('/portal/booking/', {
            'vehicle': vehicle.pk,
            'description': 'Плановое ТО',
            'booking_date': '2026-04-15',
            'booking_time': '10:00',
            'consent': '1',
        })
        assert resp.status_code == 302
        assert WorkOrder.objects.filter(client=client).exists()
