import pytest

from tests.factories import (
    AdminUserFactory, MechanicUserFactory, ClientUserFactory,
    ClientFactory, VehicleFactory,
    ServiceCategoryFactory, ServiceFactory, SparePartFactory,
    WorkOrderFactory,
)


@pytest.fixture
def admin_user(db):
    return AdminUserFactory()


@pytest.fixture
def mechanic_user(db):
    return MechanicUserFactory()


@pytest.fixture
def client_user(db):
    return ClientUserFactory()


@pytest.fixture
def sample_client(db):
    return ClientFactory()


@pytest.fixture
def sample_vehicle(sample_client):
    return VehicleFactory(client=sample_client)


@pytest.fixture
def sample_category(db):
    return ServiceCategoryFactory(name='Двигатель')


@pytest.fixture
def sample_service(sample_category):
    return ServiceFactory(category=sample_category, base_price=2500, estimated_duration=40)


@pytest.fixture
def sample_spare_part(db):
    return SparePartFactory(price=850, quantity_in_stock=20, min_stock_level=5)


@pytest.fixture
def sample_work_order(sample_client, sample_vehicle):
    return WorkOrderFactory(client=sample_client, vehicle=sample_vehicle, status='new')
