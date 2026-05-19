from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Заполняет базу тестовыми данными'

    def handle(self, *args, **options):
        self._create_users()
        self._create_services()
        self._create_parts()
        self._create_clients()
        self._create_notification_templates()
        self._create_orders()
        self.stdout.write(self.style.SUCCESS('База успешно заполнена тестовыми данными!'))

    def _create_users(self):
        from accounts.models import User

        if not User.objects.filter(username='admin').exists():
            u = User.objects.create_superuser(
                username='admin',
                email='admin@autoservice.ru',
                password='Admin1234!',
                first_name='Администратор',
                last_name='Системы',
            )
            u.role = 'admin'
            u.save(update_fields=['role'])
            self.stdout.write('  Создан суперпользователь: admin / Admin1234!')
        else:
            User.objects.filter(username='admin').update(role='admin')

        if not User.objects.filter(username='mechanic1').exists():
            u = User.objects.create_user(
                username='mechanic1',
                email='mechanic1@autoservice.ru',
                password='Mech1234!',
                first_name='Иван',
                last_name='Петров',
            )
            u.role = 'mechanic'
            u.save(update_fields=['role'])
            self.stdout.write('  Создан механик: mechanic1 / Mech1234!')
        else:
            User.objects.filter(username='mechanic1').update(role='mechanic')

        if not User.objects.filter(username='mechanic2').exists():
            u = User.objects.create_user(
                username='mechanic2',
                email='mechanic2@autoservice.ru',
                password='Mech1234!',
                first_name='Сергей',
                last_name='Иванов',
            )
            u.role = 'mechanic'
            u.save(update_fields=['role'])
            self.stdout.write('  Создан механик: mechanic2 / Mech1234!')
        else:
            User.objects.filter(username='mechanic2').update(role='mechanic')

    def _create_services(self):
        from services.models import ServiceCategory, Service

        categories = [
            {'name': 'Техническое обслуживание', 'icon': 'fa-wrench', 'sort_order': 1},
            {'name': 'Двигатель', 'icon': 'fa-cog', 'sort_order': 2},
            {'name': 'Тормозная система', 'icon': 'fa-circle-stop', 'sort_order': 3},
            {'name': 'Подвеска и рулевое', 'icon': 'fa-car', 'sort_order': 4},
            {'name': 'Электрика', 'icon': 'fa-bolt', 'sort_order': 5},
            {'name': 'Кузовные работы', 'icon': 'fa-paint-roller', 'sort_order': 6},
            {'name': 'Шиномонтаж', 'icon': 'fa-tire', 'sort_order': 7},
        ]

        created_cats = {}
        for cat_data in categories:
            cat, _ = ServiceCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'icon': cat_data['icon'], 'sort_order': cat_data['sort_order']},
            )
            created_cats[cat_data['name']] = cat

        services = [
            ('Техническое обслуживание', 'Замена масла и фильтра', 1500, 30),
            ('Техническое обслуживание', 'ТО-1 (15 000 км)', 4500, 120),
            ('Техническое обслуживание', 'ТО-2 (30 000 км)', 7500, 180),
            ('Техническое обслуживание', 'Замена воздушного фильтра', 500, 20),
            ('Техническое обслуживание', 'Замена салонного фильтра', 500, 15),
            ('Двигатель', 'Диагностика двигателя', 1000, 60),
            ('Двигатель', 'Замена ремня ГРМ', 5000, 240),
            ('Двигатель', 'Промывка инжекторов', 3000, 90),
            ('Двигатель', 'Замена свечей зажигания', 1200, 45),
            ('Тормозная система', 'Замена тормозных колодок (ось)', 2000, 60),
            ('Тормозная система', 'Замена тормозных дисков (ось)', 3500, 90),
            ('Тормозная система', 'Прокачка тормозной системы', 1500, 45),
            ('Подвеска и рулевое', 'Замена амортизатора', 2500, 90),
            ('Подвеска и рулевое', 'Замена шаровой опоры', 2000, 60),
            ('Подвеска и рулевое', 'Развал-схождение', 1500, 60),
            ('Электрика', 'Диагностика электрики', 1500, 60),
            ('Электрика', 'Замена аккумулятора', 800, 20),
            ('Электрика', 'Ремонт генератора', 4000, 180),
            ('Шиномонтаж', 'Шиномонтаж (4 колеса)', 1600, 40),
            ('Шиномонтаж', 'Балансировка (4 колеса)', 1200, 30),
        ]

        for cat_name, svc_name, price, duration in services:
            Service.objects.get_or_create(
                name=svc_name,
                category=created_cats[cat_name],
                defaults={'base_price': Decimal(str(price)), 'estimated_duration': duration},
            )
        self.stdout.write(f'  Создано {len(services)} услуг')

    def _create_parts(self):
        from services.models import SparePart

        parts = [
            ('Масло моторное 5W-40 (1л)', 'OIL-5W40', 'Castrol', 450, 50, 10, 'л'),
            ('Фильтр масляный', 'FLT-OIL-01', 'Mann', 350, 30, 10, 'шт'),
            ('Фильтр воздушный', 'FLT-AIR-01', 'Mann', 500, 20, 5, 'шт'),
            ('Фильтр салонный', 'FLT-CAB-01', 'Filtron', 400, 20, 5, 'шт'),
            ('Свечи зажигания (к-т 4шт)', 'SPK-NGK-04', 'NGK', 1200, 15, 5, 'к-т'),
            ('Тормозные колодки передние', 'BRK-PAD-F', 'Bosch', 1800, 15, 5, 'к-т'),
            ('Тормозные колодки задние', 'BRK-PAD-R', 'Bosch', 1400, 15, 5, 'к-т'),
            ('Тормозной диск передний', 'BRK-DSC-F', 'TRW', 2500, 8, 3, 'шт'),
            ('Тормозная жидкость DOT-4 (0.5л)', 'BRK-FLD-DOT4', 'ATE', 300, 20, 5, 'л'),
            ('Ремень ГРМ', 'ENG-BELT-01', 'Gates', 2200, 5, 2, 'шт'),
            ('Амортизатор передний', 'SUS-SHCK-F', 'KYB', 3500, 6, 2, 'шт'),
            ('Аккумулятор 60Ah', 'ELC-BAT-60', 'Varta', 5500, 5, 2, 'шт'),
            ('Антифриз G12 (1л)', 'CLT-G12-1L', 'Febi', 250, 30, 10, 'л'),
            ('Шаровая опора', 'SUS-BALL-01', 'Lemförder', 1500, 8, 3, 'шт'),
        ]

        for name, part_number, manufacturer, price, qty, min_qty, unit in parts:
            SparePart.objects.get_or_create(
                part_number=part_number,
                defaults={
                    'name': name,
                    'manufacturer': manufacturer,
                    'price': Decimal(str(price)),
                    'quantity_in_stock': qty,
                    'min_stock_level': min_qty,
                    'unit': unit,
                },
            )
        self.stdout.write(f'  Создано {len(parts)} запчастей')

    def _create_clients(self):
        from clients.models import Client, Vehicle
        from django.utils import timezone

        clients_data = [
            {
                'first_name': 'Александр', 'last_name': 'Новиков', 'patronymic': 'Сергеевич',
                'phone': '+79161234567', 'email': 'novikov@mail.ru',
                'vehicles': [
                    {'make': 'Toyota', 'model': 'Camry', 'year': 2020,
                     'license_plate': 'А123ВС77', 'color': 'Белый', 'mileage': 45000},
                ],
            },
            {
                'first_name': 'Мария', 'last_name': 'Козлова', 'patronymic': 'Ивановна',
                'phone': '+79261234567', 'email': 'kozlova@gmail.com',
                'vehicles': [
                    {'make': 'Volkswagen', 'model': 'Polo', 'year': 2019,
                     'license_plate': 'В456ГД77', 'color': 'Серебристый', 'mileage': 62000},
                    {'make': 'Kia', 'model': 'Sportage', 'year': 2022,
                     'license_plate': 'Е789ЖЗ99', 'color': 'Чёрный', 'mileage': 18000},
                ],
            },
            {
                'first_name': 'Дмитрий', 'last_name': 'Соколов', 'patronymic': 'Андреевич',
                'phone': '+79031234567', 'email': 'sokolov@yandex.ru',
                'vehicles': [
                    {'make': 'Lada', 'model': 'Vesta', 'year': 2021,
                     'license_plate': 'И012КЛ50', 'color': 'Синий', 'mileage': 33000},
                ],
            },
            {
                'first_name': 'Елена', 'last_name': 'Морозова', 'patronymic': 'Петровна',
                'phone': '+79171234567', 'email': 'morozova@mail.ru',
                'vehicles': [
                    {'make': 'Hyundai', 'model': 'Solaris', 'year': 2018,
                     'license_plate': 'М345НО77', 'color': 'Красный', 'mileage': 78000},
                ],
            },
            {
                'first_name': 'Павел', 'last_name': 'Волков', 'patronymic': 'Николаевич',
                'phone': '+79521234567', 'email': 'volkov@gmail.com',
                'vehicles': [
                    {'make': 'BMW', 'model': '3 Series', 'year': 2017,
                     'license_plate': 'П678РС77', 'color': 'Чёрный', 'mileage': 95000},
                ],
            },
        ]

        for cd in clients_data:
            client, created = Client.objects.get_or_create(
                phone=cd['phone'],
                defaults={
                    'first_name': cd['first_name'],
                    'last_name': cd['last_name'],
                    'patronymic': cd['patronymic'],
                    'email': cd['email'],
                    'consent_personal_data': True,
                    'consent_date': timezone.now(),
                },
            )
            for vd in cd['vehicles']:
                Vehicle.objects.get_or_create(
                    license_plate=vd['license_plate'],
                    defaults={**vd, 'client': client},
                )
        self.stdout.write(f'  Создано {len(clients_data)} клиентов')

    def _create_notification_templates(self):
        from notifications.models import NotificationTemplate

        templates = [
            {
                'name': 'Telegram: заказ создан',
                'event_type': 'order_created',
                'channel': 'telegram',
                'body_template': (
                    '🔧 <b>Заказ принят!</b>\n\n'
                    '📋 Номер: <b>{order_number}</b>\n'
                    '🚗 Автомобиль: {vehicle_info}\n\n'
                    'Мы приступим к работе в ближайшее время.\n'
                    'Вопросы: {workshop_phone}'
                ),
            },
            {
                'name': 'Telegram: статус изменён',
                'event_type': 'status_changed',
                'channel': 'telegram',
                'body_template': (
                    '🔔 <b>Статус заказа обновлён</b>\n\n'
                    '📋 Заказ: <b>{order_number}</b>\n'
                    '🚗 {vehicle_info}\n'
                    '📊 Статус: <b>{status}</b>\n\n'
                    'Вопросы: {workshop_phone}'
                ),
            },
            {
                'name': 'Telegram: заказ готов',
                'event_type': 'order_ready',
                'channel': 'telegram',
                'body_template': (
                    '🏁 <b>Ваш автомобиль готов!</b>\n\n'
                    '📋 Заказ: <b>{order_number}</b>\n'
                    '🚗 {vehicle_info}\n'
                    '💰 Итого: <b>{total_cost} ₽</b>\n\n'
                    'Ждём вас для получения!\n'
                    'Вопросы: {workshop_phone}'
                ),
            },
            {
                'name': 'Telegram: заказ выдан',
                'event_type': 'order_delivered',
                'channel': 'telegram',
                'body_template': (
                    '✅ <b>Спасибо за визит!</b>\n\n'
                    '📋 Заказ {order_number} закрыт.\n'
                    '🚗 {vehicle_info}\n\n'
                    'Будем рады видеть вас снова!\n'
                    '{workshop_phone}'
                ),
            },
            {
                'name': 'Telegram: напоминание о ТО',
                'event_type': 'maintenance_reminder',
                'channel': 'telegram',
                'body_template': (
                    '⚙️ <b>Напоминание о техобслуживании</b>\n\n'
                    'Здравствуйте, {client_name}!\n\n'
                    '🚗 {vehicle_info}\n\n'
                    'Прошло более 6 месяцев с последнего визита.\n'
                    'Рекомендуем пройти плановое ТО.\n\n'
                    'Запись: {workshop_phone}'
                ),
            },
        ]

        count = 0
        for t in templates:
            _, created = NotificationTemplate.objects.get_or_create(
                event_type=t['event_type'],
                channel=t['channel'],
                defaults={'name': t['name'], 'body_template': t['body_template']},
            )
            if created:
                count += 1
        self.stdout.write(f'  Создано {count} шаблонов уведомлений')

    def _create_orders(self):
        from accounts.models import User
        from clients.models import Client, Vehicle
        from orders.models import WorkOrder, WorkOrderItem, WorkOrderPart
        from services.models import Service, SparePart

        if WorkOrder.objects.exists():
            self.stdout.write('  Заказ-наряды уже существуют, пропускаю')
            return

        admin = User.objects.filter(username='admin').first()
        mechanic1 = User.objects.filter(username='mechanic1').first()
        mechanic2 = User.objects.filter(username='mechanic2').first()

        clients = list(Client.objects.all())
        if not clients:
            return

        oil_service = Service.objects.filter(name='Замена масла и фильтра').first()
        to1_service = Service.objects.filter(name='ТО-1 (15 000 км)').first()
        brake_service = Service.objects.filter(name='Замена тормозных колодок (ось)').first()
        diag_service = Service.objects.filter(name='Диагностика двигателя').first()
        timing_service = Service.objects.filter(name='Замена ремня ГРМ').first()

        oil_filter = SparePart.objects.filter(part_number='FLT-OIL-01').first()
        oil = SparePart.objects.filter(part_number='OIL-5W40').first()
        brake_pads = SparePart.objects.filter(part_number='BRK-PAD-F').first()
        timing_belt = SparePart.objects.filter(part_number='ENG-BELT-01').first()

        # Order 1 — delivered
        c1 = clients[0]
        v1 = c1.vehicles.first()
        if v1 and oil_service:
            o1 = WorkOrder.objects.create(
                client=c1, vehicle=v1,
                description='Плановая замена масла и фильтра.',
                assigned_mechanic=mechanic1,
                status='delivered',
                diagnosis='Масло потемнело, замена необходима.',
                started_at=timezone.now() - timezone.timedelta(days=7),
                completed_at=timezone.now() - timezone.timedelta(days=7),
                delivered_at=timezone.now() - timezone.timedelta(days=6),
            )
            if oil_service:
                WorkOrderItem.objects.create(work_order=o1, service=oil_service, price=oil_service.base_price)
            if oil_filter and oil:
                WorkOrderPart.objects.create(work_order=o1, spare_part=oil_filter, quantity=1, price_per_unit=oil_filter.price)
                WorkOrderPart.objects.create(work_order=o1, spare_part=oil, quantity=4, price_per_unit=oil.price)
            o1.recalculate_totals()

        # Order 2 — in_progress
        if len(clients) > 1:
            c2 = clients[1]
            v2 = c2.vehicles.first()
            if v2 and to1_service:
                o2 = WorkOrder.objects.create(
                    client=c2, vehicle=v2,
                    description='ТО-1 по регламенту 15 000 км.',
                    assigned_mechanic=mechanic2,
                    status='in_progress',
                    started_at=timezone.now() - timezone.timedelta(hours=2),
                    estimated_completion=timezone.now() + timezone.timedelta(hours=2),
                )
                WorkOrderItem.objects.create(work_order=o2, service=to1_service, price=to1_service.base_price)
                o2.recalculate_totals()

        # Order 3 — approved (waiting to start)
        if len(clients) > 2:
            c3 = clients[2]
            v3 = c3.vehicles.first()
            if v3 and brake_service and brake_pads:
                o3 = WorkOrder.objects.create(
                    client=c3, vehicle=v3,
                    description='Скрип при торможении, проверить колодки.',
                    assigned_mechanic=mechanic1,
                    status='approved',
                    diagnosis='Тормозные колодки изношены до минимума, замена необходима.',
                    estimated_completion=timezone.now() + timezone.timedelta(hours=4),
                )
                WorkOrderItem.objects.create(work_order=o3, service=brake_service, price=brake_service.base_price)
                WorkOrderPart.objects.create(work_order=o3, spare_part=brake_pads, quantity=1, price_per_unit=brake_pads.price)
                o3.recalculate_totals()

        # Order 4 — diagnostics
        if len(clients) > 3:
            c4 = clients[3]
            v4 = c4.vehicles.first()
            if v4 and diag_service:
                o4 = WorkOrder.objects.create(
                    client=c4, vehicle=v4,
                    description='Двигатель троит на холодную, расход топлива увеличился.',
                    assigned_mechanic=mechanic2,
                    status='diagnostics',
                )
                WorkOrderItem.objects.create(work_order=o4, service=diag_service, price=diag_service.base_price)
                o4.recalculate_totals()

        # Order 5 — new
        if len(clients) > 4:
            c5 = clients[4]
            v5 = c5.vehicles.first()
            if v5:
                WorkOrder.objects.create(
                    client=c5, vehicle=v5,
                    description='Плановое ТО, замена ремня ГРМ (пробег 95 000 км).',
                    status='new',
                )

        self.stdout.write(f'  Создано {WorkOrder.objects.count()} заказ-нарядов')
