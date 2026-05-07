import json
from datetime import date, timedelta, time as dtime
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView

from accounts.mixins import ClientRequiredMixin
from clients.models import Client, Vehicle
from clients.forms import CAR_MAKES
from orders.models import WorkOrder, STATUS_TRANSITIONS
from services.models import ServiceCategory, Service
from .forms import PortalVehicleForm, PortalSettingsForm
from .models import Booking


def _get_client(user):
    """Get or create Client linked to user."""
    # 1. Already linked via OneToOne
    try:
        return user.client_profile
    except Client.DoesNotExist:
        pass

    # 2. Find existing Client by phone or email and link
    if user.phone:
        try:
            client = Client.objects.get(phone=user.phone, is_active=True)
            client.user = user
            client.save(update_fields=['user'])
            return client
        except Client.DoesNotExist:
            pass

    if user.email:
        try:
            client = Client.objects.get(email=user.email, user__isnull=True, is_active=True)
            client.user = user
            client.save(update_fields=['user'])
            return client
        except Client.DoesNotExist:
            pass

    # 3. Create new Client with unique phone
    phone = user.phone or f'+7000{user.pk:07d}'
    # Ensure phone doesn't collide
    if Client.objects.filter(phone=phone).exists():
        phone = f'+7000{user.pk:07d}'
        if Client.objects.filter(phone=phone).exists():
            phone = f'+7999{user.pk:07d}'

    return Client.objects.create(
        user=user,
        first_name=user.first_name or 'Клиент',
        last_name=user.last_name or '',
        patronymic=getattr(user, 'patronymic', ''),
        phone=phone,
        email=user.email or '',
    )


# ─── Dashboard ────────────────────────────────────────────────

class PortalDashboardView(ClientRequiredMixin, TemplateView):
    template_name = 'portal/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        client = _get_client(self.request.user)
        ctx['client'] = client

        active = client.orders.filter(
            status__in=['new', 'diagnostics', 'approved', 'in_progress', 'waiting_parts', 'completed', 'ready']
        ).select_related('vehicle').order_by('-created_at')
        ctx['active_orders'] = active
        ctx['ready_orders'] = [o for o in active if o.status == 'ready']
        return ctx


# ─── Orders ───────────────────────────────────────────────────

class PortalOrderListView(ClientRequiredMixin, ListView):
    template_name = 'portal/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        client = _get_client(self.request.user)
        return client.orders.select_related('vehicle').order_by(
            # Active first, then by date
            'status', '-created_at',
        )


class PortalOrderDetailView(ClientRequiredMixin, DetailView):
    template_name = 'portal/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        client = _get_client(self.request.user)
        return client.orders.select_related('vehicle', 'assigned_mechanic')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order = self.object
        ctx['items'] = order.items.select_related('service').all()
        ctx['parts'] = order.parts.select_related('spare_part').all()

        # Progress steps
        steps = [
            ('new', 'Принят'), ('diagnostics', 'Диагностика'),
            ('in_progress', 'В работе'), ('completed', 'Выполнен'),
            ('ready', 'Готов'), ('delivered', 'Выдан'),
        ]
        seq = [s[0] for s in steps]
        idx = seq.index(order.status) if order.status in seq else -1
        ctx['progress'] = [
            {'label': label, 'state': 'done' if i < idx else ('current' if i == idx else 'pending')}
            for i, (code, label) in enumerate(steps)
        ]
        ctx['is_cancelled'] = order.status == 'cancelled'
        return ctx


# ─── Vehicles ─────────────────────────────────────────────────

class PortalVehicleListView(ClientRequiredMixin, ListView):
    template_name = 'portal/vehicle_list.html'
    context_object_name = 'vehicles'

    def get_queryset(self):
        client = _get_client(self.request.user)
        return client.vehicles.all()


class PortalVehicleCreateView(ClientRequiredMixin, CreateView):
    model = Vehicle
    form_class = PortalVehicleForm
    template_name = 'portal/vehicle_form.html'
    success_url = reverse_lazy('portal:vehicles')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['car_makes'] = CAR_MAKES
        return ctx

    def form_valid(self, form):
        form.instance.client = _get_client(self.request.user)
        messages.success(self.request, 'Автомобиль добавлен.')
        return super().form_valid(form)


# ─── Booking ──────────────────────────────────────────────────

class PortalBookingView(ClientRequiredMixin, TemplateView):
    template_name = 'portal/booking.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        client = _get_client(self.request.user)
        ctx['vehicles'] = client.vehicles.all()
        ctx['categories'] = ServiceCategory.objects.filter(
            is_active=True,
        ).prefetch_related('services')
        ctx['car_makes'] = CAR_MAKES

        # Available dates (next 14 days, excluding Sundays)
        today = date.today()
        dates = []
        for i in range(1, 15):
            d = today + timedelta(days=i)
            if d.weekday() != 6:  # Skip Sunday
                dates.append(d)
        ctx['available_dates'] = dates
        return ctx

    def post(self, request, *args, **kwargs):
        client = _get_client(request.user)

        # Parse form data
        vehicle_id = request.POST.get('vehicle')
        service_ids = request.POST.getlist('services')
        description = request.POST.get('description', '')
        booking_date = request.POST.get('booking_date')
        booking_time = request.POST.get('booking_time')
        consent = request.POST.get('consent')

        if not all([vehicle_id, booking_date, booking_time, consent]):
            messages.error(request, 'Заполните все обязательные поля.')
            return redirect('portal:booking')

        vehicle = get_object_or_404(Vehicle, pk=vehicle_id, client=client)
        services = Service.objects.filter(pk__in=service_ids, is_active=True)
        estimated = services.aggregate(total=Sum('base_price'))['total'] or Decimal('0')

        # Create booking
        booking = Booking.objects.create(
            client=client,
            vehicle=vehicle,
            description=description,
            booking_date=booking_date,
            booking_time=booking_time,
            estimated_cost=estimated,
        )
        booking.services.set(services)

        # Create WorkOrder
        svc_names = ', '.join(s.name for s in services)
        order_desc = description or svc_names or 'Онлайн-запись'
        work_order = WorkOrder.objects.create(
            client=client,
            vehicle=vehicle,
            description=order_desc,
            estimated_completion=None,
        )
        booking.work_order = work_order
        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=['work_order', 'status'])

        # Auto-add selected services as WorkOrderItems
        from orders.models import WorkOrderItem
        for svc in services:
            WorkOrderItem.objects.create(
                work_order=work_order,
                service=svc,
                quantity=1,
                price=svc.base_price,
            )

        # Notify
        try:
            from notifications.services import NotificationService
            NotificationService.dispatch_order_created(work_order)
        except Exception:
            pass

        messages.success(
            request,
            f'Вы записаны на {booking_date} в {booking_time}! '
            f'Заказ-наряд №{work_order.order_number} создан.',
        )
        return redirect('portal:order_detail', pk=work_order.pk)


class BookingSlotsAPIView(ClientRequiredMixin, View):
    """Return available time slots for a given date."""

    def get(self, request):
        date_str = request.GET.get('date')
        if not date_str:
            return JsonResponse({'slots': []})

        # All possible slots 8:00–17:00 (last appointment at 17:00)
        all_slots = [dtime(h, 0) for h in range(8, 18)]

        # Count existing bookings for that date
        booked = set(
            Booking.objects
            .filter(booking_date=date_str, status__in=['pending', 'confirmed'])
            .values_list('booking_time', flat=True)
        )

        slots = []
        for t in all_slots:
            slots.append({
                'time': t.strftime('%H:%M'),
                'available': t not in booked,
            })
        return JsonResponse({'slots': slots})


# ─── Settings ─────────────────────────────────────────────────

class PortalSettingsView(ClientRequiredMixin, TemplateView):
    template_name = 'portal/settings.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        client = _get_client(self.request.user)
        prefs = client.notification_preferences or {}
        ctx['form'] = PortalSettingsForm(initial={
            'first_name': client.first_name,
            'last_name': client.last_name,
            'patronymic': client.patronymic,
            'email': client.email,
            'phone': client.phone,
            'notify_email': prefs.get('email', False),
            'notify_telegram': prefs.get('telegram', False),
            'notify_sms': prefs.get('sms', False),
        })
        ctx['client'] = client
        return ctx

    def post(self, request, *args, **kwargs):
        client = _get_client(request.user)
        form = PortalSettingsForm(request.POST)

        if form.is_valid():
            cd = form.cleaned_data
            client.first_name = cd['first_name']
            client.last_name = cd['last_name']
            client.patronymic = cd['patronymic']
            client.email = cd['email']
            client.phone = cd['phone']
            client.notification_preferences = {
                'email': cd['notify_email'],
                'telegram': cd['notify_telegram'],
                'sms': cd['notify_sms'],
            }
            client.save()
            messages.success(request, 'Настройки сохранены.')
            return redirect('portal:settings')

        return self.render_to_response(self.get_context_data(form=form))


# ─── Offline (PWA) ────────────────────────────────────────────

class PortalOfflineView(TemplateView):
    template_name = 'portal/offline.html'
