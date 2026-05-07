"""Create test data for manual testing."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoservice.settings.dev')
os.environ['PYTHONIOENCODING'] = 'utf-8'
django.setup()

from clients.models import Client, Vehicle
from orders.models import WorkOrder
from accounts.models import User

cl2 = Client.objects.get(phone='+79003333333')
v3 = Vehicle.objects.get(license_plate='К789МН50')
if WorkOrder.objects.filter(client=cl2).count() == 0:
    o3 = WorkOrder.objects.create(client=cl2, vehicle=v3, description='Planovoe TO-1.', status='new')
    print(f'Order 3 created: {o3.order_number}')

print('--- All Orders ---')
for o in WorkOrder.objects.select_related('client', 'vehicle').all():
    print(f'  {o.order_number} | {o.client.last_name} | {o.vehicle.make} {o.vehicle.model} | {o.status} | {o.final_cost}')
print(f'Total: {WorkOrder.objects.count()}')
