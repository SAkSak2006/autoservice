import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from orders.models import WorkOrder, WorkOrderItem, WorkOrderPart, STATUS_TRANSITIONS
from tests.factories import (
    ClientFactory, VehicleFactory, ServiceFactory, SparePartFactory,
    WorkOrderFactory, ServiceCategoryFactory, WorkOrderItemFactory,
)


@pytest.mark.django_db
class TestWorkOrderAutoNumber:
    def test_auto_number_generated(self):
        order = WorkOrderFactory()
        assert order.order_number.startswith('ЗН-')
        assert len(order.order_number) == 15  # ЗН-YYYYMMDD-NNN

    def test_sequential_numbers(self):
        o1 = WorkOrderFactory()
        o2 = WorkOrderFactory()
        # Same date prefix, sequential numbers
        assert o1.order_number[:-3] == o2.order_number[:-3]  # same date prefix
        num1 = int(o1.order_number.split('-')[-1])
        num2 = int(o2.order_number.split('-')[-1])
        assert num2 == num1 + 1


@pytest.mark.django_db
class TestWorkOrderStatusTransitions:
    def test_all_valid_transitions(self):
        for from_status, allowed in STATUS_TRANSITIONS.items():
            for to_status in allowed:
                order = WorkOrderFactory(status=from_status)
                assert order.can_transition_to(to_status), \
                    f'{from_status} → {to_status} should be allowed'

    def test_invalid_transitions(self):
        invalid_pairs = [
            ('new', 'completed'),
            ('new', 'ready'),
            ('new', 'delivered'),
            ('diagnostics', 'in_progress'),
            ('in_progress', 'delivered'),
            ('completed', 'in_progress'),
            ('delivered', 'new'),
            ('cancelled', 'new'),
            ('ready', 'in_progress'),
        ]
        for from_status, to_status in invalid_pairs:
            order = WorkOrderFactory(status=from_status)
            assert not order.can_transition_to(to_status), \
                f'{from_status} → {to_status} should NOT be allowed'

    def test_transition_to_sets_dates(self, admin_user):
        order = WorkOrderFactory(status='new')
        order.transition_to('in_progress', admin_user)
        assert order.started_at is not None

        order.transition_to('completed', admin_user)
        assert order.completed_at is not None

        order.transition_to('ready', admin_user)
        order.transition_to('delivered', admin_user)
        assert order.delivered_at is not None

    def test_transition_creates_history(self, admin_user):
        order = WorkOrderFactory(status='new')
        order.transition_to('diagnostics', admin_user, comment='Начало диагностики')
        history = order.status_history.first()
        assert history.from_status == 'new'
        assert history.to_status == 'diagnostics'
        assert history.changed_by == admin_user
        assert history.comment == 'Начало диагностики'

    def test_invalid_transition_raises(self, admin_user):
        order = WorkOrderFactory(status='new')
        with pytest.raises(ValidationError):
            order.transition_to('delivered', admin_user)


@pytest.mark.django_db
class TestWorkOrderTotals:
    def test_recalculate_totals(self):
        cat = ServiceCategoryFactory()
        svc1 = ServiceFactory(category=cat, base_price=Decimal('2500'))
        svc2 = ServiceFactory(category=cat, base_price=Decimal('3000'))
        part = SparePartFactory(price=Decimal('850'), quantity_in_stock=10)

        order = WorkOrderFactory()
        WorkOrderItem.objects.create(work_order=order, service=svc1, quantity=1, price=svc1.base_price)
        WorkOrderItem.objects.create(work_order=order, service=svc2, quantity=2, price=svc2.base_price)
        WorkOrderPart.objects.create(work_order=order, spare_part=part, quantity=1, price_per_unit=part.price)

        order.refresh_from_db()
        assert order.total_services_cost == Decimal('8500.00')  # 2500 + 3000*2
        assert order.total_parts_cost == Decimal('850.00')
        assert order.total_cost == Decimal('9350.00')

    def test_discount_applied(self):
        order = WorkOrderFactory()
        cat = ServiceCategoryFactory()
        svc = ServiceFactory(category=cat, base_price=Decimal('10000'))
        WorkOrderItem.objects.create(work_order=order, service=svc, quantity=1, price=svc.base_price)

        order.refresh_from_db()
        order.discount_percent = Decimal('10')
        order.save()
        order.refresh_from_db()
        assert order.final_cost == Decimal('9000.00')


@pytest.mark.django_db
class TestSparePartStock:
    def test_stock_deduction_on_add(self):
        part = SparePartFactory(quantity_in_stock=20)
        order = WorkOrderFactory()
        WorkOrderPart.objects.create(
            work_order=order, spare_part=part, quantity=3, price_per_unit=part.price,
        )
        part.refresh_from_db()
        assert part.quantity_in_stock == 17

    def test_stock_restored_on_delete(self):
        part = SparePartFactory(quantity_in_stock=20)
        order = WorkOrderFactory()
        op = WorkOrderPart.objects.create(
            work_order=order, spare_part=part, quantity=5, price_per_unit=part.price,
        )
        part.refresh_from_db()
        assert part.quantity_in_stock == 15
        op.delete()
        part.refresh_from_db()
        assert part.quantity_in_stock == 20

    def test_insufficient_stock_raises(self):
        part = SparePartFactory(quantity_in_stock=2)
        order = WorkOrderFactory()
        with pytest.raises(ValidationError):
            WorkOrderPart.objects.create(
                work_order=order, spare_part=part, quantity=5, price_per_unit=part.price,
            )

    def test_is_low_stock(self):
        part = SparePartFactory(quantity_in_stock=5, min_stock_level=5)
        assert part.is_low_stock() is True

        part.quantity_in_stock = 10
        assert part.is_low_stock() is False


@pytest.mark.django_db
class TestClientModel:
    def test_full_name(self):
        client = ClientFactory(last_name='Иванов', first_name='Иван', patronymic='Иванович')
        assert client.get_full_name() == 'Иванов Иван Иванович'

    def test_full_name_no_patronymic(self):
        client = ClientFactory(last_name='Петров', first_name='Пётр', patronymic='')
        assert client.get_full_name() == 'Петров Пётр'

    def test_str_representation(self):
        client = ClientFactory(last_name='Сидоров', first_name='Алексей', patronymic='Сергеевич', phone='+79001234567')
        s = str(client)
        assert 'Сидоров' in s
        assert '+7900' in s


@pytest.mark.django_db
class TestVehicleModel:
    def test_str_representation(self):
        vehicle = VehicleFactory(make='Toyota', model='Camry', year=2020, license_plate='А123БВ777')
        assert str(vehicle) == 'Toyota Camry (2020) А123БВ777'

    def test_get_full_info(self):
        vehicle = VehicleFactory(make='BMW', model='X5', year=2023, license_plate='В456ГД99')
        assert vehicle.get_full_info() == 'BMW X5 2023 В456ГД99'
