import factory
from factory.django import DjangoModelFactory
from faker import Faker

from accounts.models import User
from clients.models import Client, Vehicle
from orders.models import WorkOrder, WorkOrderItem, WorkOrderPart
from services.models import ServiceCategory, Service, SparePart
from notifications.models import NotificationTemplate, Notification

fake = Faker('ru_RU')


# ─── User factories ──────────────────────────────────────────

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    is_active = True
    role = 'client'


class AdminUserFactory(UserFactory):
    role = 'admin'
    is_staff = True


class MechanicUserFactory(UserFactory):
    role = 'mechanic'


class ClientUserFactory(UserFactory):
    role = 'client'


# ─── Client / Vehicle ────────────────────────────────────────

class ClientFactory(DjangoModelFactory):
    class Meta:
        model = Client

    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    patronymic = factory.LazyFunction(lambda: fake.middle_name())
    phone = factory.Sequence(lambda n: f'+7900{n:07d}')
    email = factory.LazyAttribute(lambda o: f'{o.first_name.lower()}@example.com')
    consent_personal_data = True


class VehicleFactory(DjangoModelFactory):
    class Meta:
        model = Vehicle

    client = factory.SubFactory(ClientFactory)
    make = factory.Iterator(['Toyota', 'BMW', 'Hyundai', 'Kia', 'Volkswagen'])
    model = factory.Iterator(['Camry', 'X5', 'Solaris', 'Rio', 'Polo'])
    year = 2022
    license_plate = factory.Sequence(lambda n: f'А{n:03d}БВ777')
    mileage = 50000


# ─── Services ─────────────────────────────────────────────────

class ServiceCategoryFactory(DjangoModelFactory):
    class Meta:
        model = ServiceCategory

    name = factory.Sequence(lambda n: f'Категория {n}')
    sort_order = factory.Sequence(lambda n: n)


class ServiceFactory(DjangoModelFactory):
    class Meta:
        model = Service

    category = factory.SubFactory(ServiceCategoryFactory)
    name = factory.Sequence(lambda n: f'Услуга {n}')
    base_price = factory.LazyFunction(lambda: fake.pydecimal(left_digits=4, right_digits=2, positive=True, min_value=500, max_value=15000))
    estimated_duration = 60


class SparePartFactory(DjangoModelFactory):
    class Meta:
        model = SparePart

    name = factory.Sequence(lambda n: f'Запчасть {n}')
    part_number = factory.Sequence(lambda n: f'PN-{n:05d}')
    manufacturer = factory.Iterator(['Bosch', 'Brembo', 'Mann', 'Gates', 'Denso'])
    price = factory.LazyFunction(lambda: fake.pydecimal(left_digits=4, right_digits=2, positive=True, min_value=100, max_value=10000))
    quantity_in_stock = 20
    min_stock_level = 5


# ─── Orders ───────────────────────────────────────────────────

class WorkOrderFactory(DjangoModelFactory):
    class Meta:
        model = WorkOrder

    client = factory.SubFactory(ClientFactory)
    vehicle = factory.LazyAttribute(lambda o: VehicleFactory(client=o.client))
    description = factory.LazyFunction(lambda: fake.sentence(nb_words=6))
    status = 'new'


class WorkOrderItemFactory(DjangoModelFactory):
    class Meta:
        model = WorkOrderItem

    work_order = factory.SubFactory(WorkOrderFactory)
    service = factory.SubFactory(ServiceFactory)
    quantity = 1
    price = factory.LazyAttribute(lambda o: o.service.base_price)


class WorkOrderPartFactory(DjangoModelFactory):
    class Meta:
        model = WorkOrderPart

    work_order = factory.SubFactory(WorkOrderFactory)
    spare_part = factory.SubFactory(SparePartFactory)
    quantity = 1
    price_per_unit = factory.LazyAttribute(lambda o: o.spare_part.price)


# ─── Notifications ────────────────────────────────────────────

class NotificationTemplateFactory(DjangoModelFactory):
    class Meta:
        model = NotificationTemplate

    name = factory.Sequence(lambda n: f'template_{n}')
    event_type = 'order_ready'
    channel = 'email'
    subject_template = 'Заказ №{order_number}'
    body_template = 'Здравствуйте, {client_name}! Заказ {order_number} на {vehicle_info} готов. Сумма: {total_cost}. Статус: {qr_url}. Тел: {workshop_phone}'
    is_active = True


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    client = factory.SubFactory(ClientFactory)
    channel = 'email'
    event_type = 'order_ready'
    subject = 'Test subject'
    body = 'Test body'
    status = 'pending'
