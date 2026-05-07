import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView

from accounts.mixins import AdminRequiredMixin, StaffRequiredMixin
from clients.models import Vehicle
from services.models import Service, SparePart
from .forms import (
    WorkOrderCreateForm, WorkOrderUpdateForm,
    WorkOrderItemForm, WorkOrderPartForm, OrderFilterForm,
)
from .models import WorkOrder, WorkOrderItem, WorkOrderPart, STATUS_TRANSITIONS


# ─── List ─────────────────────────────────────────────────────

class WorkOrderListView(StaffRequiredMixin, ListView):
    model = WorkOrder
    template_name = 'orders/workorder_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        qs = WorkOrder.objects.select_related('client', 'vehicle', 'assigned_mechanic')

        # Mechanic sees only assigned orders
        if self.request.user.is_mechanic:
            qs = qs.filter(assigned_mechanic=self.request.user)

        # Search
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(order_number__icontains=q)
                | Q(client__first_name__icontains=q)
                | Q(client__last_name__icontains=q)
                | Q(vehicle__license_plate__icontains=q)
            )

        # Status filter
        statuses = self.request.GET.getlist('status')
        if statuses:
            qs = qs.filter(status__in=statuses)

        # Mechanic filter
        mechanic = self.request.GET.get('mechanic')
        if mechanic:
            qs = qs.filter(assigned_mechanic_id=mechanic)

        # Date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = OrderFilterForm(self.request.GET)
        ctx['view_mode'] = self.request.GET.get('view', 'table')
        return ctx


class WorkOrderKanbanView(StaffRequiredMixin, TemplateView):
    template_name = 'orders/workorder_kanban.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = WorkOrder.objects.select_related('client', 'vehicle', 'assigned_mechanic')
        if self.request.user.is_mechanic:
            qs = qs.filter(assigned_mechanic=self.request.user)

        # Exclude final statuses from kanban
        qs = qs.exclude(status__in=['delivered', 'cancelled'])
        columns = []
        for value, label in WorkOrder.Status.choices:
            if value in ('delivered', 'cancelled'):
                continue
            columns.append({
                'status': value,
                'label': label,
                'orders': qs.filter(status=value),
            })
        ctx['columns'] = columns
        return ctx


# ─── Create ───────────────────────────────────────────────────

class WorkOrderCreateView(AdminRequiredMixin, CreateView):
    model = WorkOrder
    form_class = WorkOrderCreateForm
    template_name = 'orders/workorder_create.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Заказ-наряд {self.object.order_number} создан.')
        return redirect(self.object.get_absolute_url())


class ClientVehiclesAjaxView(StaffRequiredMixin, View):
    """AJAX: return vehicles for a given client."""

    def get(self, request):
        client_id = request.GET.get('client_id')
        if not client_id:
            return JsonResponse({'vehicles': []})
        vehicles = Vehicle.objects.filter(client_id=client_id).values(
            'id', 'make', 'model', 'year', 'license_plate',
        )
        return JsonResponse({'vehicles': list(vehicles)})


# ─── Detail ───────────────────────────────────────────────────

class WorkOrderDetailView(StaffRequiredMixin, DetailView):
    model = WorkOrder
    template_name = 'orders/workorder_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return WorkOrder.objects.select_related(
            'client', 'vehicle', 'assigned_mechanic',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order = self.object
        ctx['items'] = order.items.select_related('service').all()
        ctx['parts'] = order.parts.select_related('spare_part').all()
        ctx['history'] = order.status_history.select_related('changed_by').all()
        ctx['allowed_transitions'] = STATUS_TRANSITIONS.get(order.status, [])
        ctx['status_labels'] = dict(WorkOrder.Status.choices)
        ctx['status_labels_json'] = json.dumps(dict(WorkOrder.Status.choices), ensure_ascii=False)
        ctx['item_form'] = WorkOrderItemForm()
        ctx['part_form'] = WorkOrderPartForm()
        ctx['services_json'] = json.dumps([
            {'id': s.id, 'name': str(s.name), 'price': str(s.base_price), 'category': s.category.name}
            for s in Service.objects.filter(is_active=True).select_related('category')
        ], ensure_ascii=False)
        ctx['parts_json'] = json.dumps([
            {'id': p.id, 'name': p.name, 'price': str(p.price),
             'stock': p.quantity_in_stock, 'part_number': p.part_number}
            for p in SparePart.objects.filter(is_active=True)
        ], ensure_ascii=False)
        return ctx


# ─── Update ───────────────────────────────────────────────────

class WorkOrderUpdateView(StaffRequiredMixin, UpdateView):
    model = WorkOrder
    form_class = WorkOrderUpdateForm
    template_name = 'orders/workorder_update.html'

    def form_valid(self, form):
        messages.success(self.request, 'Заказ-наряд обновлён.')
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


# ─── Status Change (AJAX) ────────────────────────────────────

@method_decorator(csrf_protect, name='dispatch')
class WorkOrderStatusChangeView(StaffRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)
        new_status = request.POST.get('new_status', '')
        comment = request.POST.get('comment', '')

        if not order.can_transition_to(new_status):
            return JsonResponse({
                'success': False,
                'error': f'Переход в статус «{new_status}» невозможен.',
            }, status=400)

        try:
            order.transition_to(new_status, request.user, comment)
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

        return JsonResponse({
            'success': True,
            'new_status': order.status,
            'new_status_display': order.get_status_display(),
            'badge_class': order.get_status_badge_class(),
            'allowed_transitions': STATUS_TRANSITIONS.get(order.status, []),
        })


# ─── Add Service (AJAX) ──────────────────────────────────────

class AddServiceView(StaffRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)

        try:
            service_id = int(request.POST.get('service_id', 0))
            quantity = int(request.POST.get('quantity', 1))
            price = Decimal(request.POST.get('price', '0'))
        except (ValueError, InvalidOperation):
            return JsonResponse({'success': False, 'error': 'Неверные данные.'}, status=400)

        service = get_object_or_404(Service, pk=service_id, is_active=True)

        item = WorkOrderItem(
            work_order=order,
            service=service,
            quantity=quantity,
            price=price or service.base_price,
        )
        item.save()

        return JsonResponse({
            'success': True,
            'item': {
                'id': item.id,
                'service_name': service.name,
                'quantity': item.quantity,
                'price': str(item.price),
                'subtotal': str(item.subtotal),
            },
            'totals': {
                'services': str(order.total_services_cost),
                'parts': str(order.total_parts_cost),
                'total': str(order.total_cost),
                'final': str(order.final_cost),
            },
        })


class RemoveServiceView(StaffRequiredMixin, View):
    def post(self, request, pk, item_pk):
        item = get_object_or_404(WorkOrderItem, pk=item_pk, work_order_id=pk)
        item.delete()
        order = get_object_or_404(WorkOrder, pk=pk)
        return JsonResponse({
            'success': True,
            'totals': {
                'services': str(order.total_services_cost),
                'parts': str(order.total_parts_cost),
                'total': str(order.total_cost),
                'final': str(order.final_cost),
            },
        })


# ─── Add Part (AJAX) ─────────────────────────────────────────

class AddPartView(StaffRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)

        try:
            spare_part_id = int(request.POST.get('spare_part_id', 0))
            quantity = int(request.POST.get('quantity', 1))
            price = Decimal(request.POST.get('price_per_unit', '0'))
        except (ValueError, InvalidOperation):
            return JsonResponse({'success': False, 'error': 'Неверные данные.'}, status=400)

        spare_part = get_object_or_404(SparePart, pk=spare_part_id, is_active=True)

        part = WorkOrderPart(
            work_order=order,
            spare_part=spare_part,
            quantity=quantity,
            price_per_unit=price or spare_part.price,
        )
        try:
            part.save()
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

        return JsonResponse({
            'success': True,
            'item': {
                'id': part.id,
                'part_name': spare_part.name,
                'quantity': part.quantity,
                'price_per_unit': str(part.price_per_unit),
                'subtotal': str(part.subtotal),
                'stock_remaining': spare_part.quantity_in_stock,
            },
            'totals': {
                'services': str(order.total_services_cost),
                'parts': str(order.total_parts_cost),
                'total': str(order.total_cost),
                'final': str(order.final_cost),
            },
        })


class RemovePartView(StaffRequiredMixin, View):
    def post(self, request, pk, item_pk):
        part = get_object_or_404(WorkOrderPart, pk=item_pk, work_order_id=pk)
        part.delete()
        order = get_object_or_404(WorkOrder, pk=pk)
        return JsonResponse({
            'success': True,
            'totals': {
                'services': str(order.total_services_cost),
                'parts': str(order.total_parts_cost),
                'total': str(order.total_cost),
                'final': str(order.final_cost),
            },
        })


# ─── Print ────────────────────────────────────────────────────

class WorkOrderPrintView(StaffRequiredMixin, DetailView):
    model = WorkOrder
    template_name = 'orders/workorder_print.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['items'] = self.object.items.select_related('service').all()
        ctx['parts'] = self.object.parts.select_related('spare_part').all()
        return ctx


# ─── Public status check (no auth) ───────────────────────────

class OrderCheckView(DetailView):
    model = WorkOrder
    template_name = 'orders/order_check.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Build progress steps
        steps = [
            ('new', 'Принят', 'fas fa-inbox'),
            ('diagnostics', 'Диагностика', 'fas fa-search'),
            ('in_progress', 'В работе', 'fas fa-wrench'),
            ('completed', 'Выполнен', 'fas fa-check'),
            ('ready', 'Готов', 'fas fa-flag-checkered'),
            ('delivered', 'Выдан', 'fas fa-handshake'),
        ]
        status_order = [s[0] for s in steps]
        current_idx = status_order.index(self.object.status) if self.object.status in status_order else -1
        progress = []
        for i, (code, label, icon) in enumerate(steps):
            state = 'done' if i < current_idx else ('current' if i == current_idx else 'pending')
            progress.append({'code': code, 'label': label, 'icon': icon, 'state': state})
        ctx['progress'] = progress
        ctx['is_cancelled'] = self.object.status == 'cancelled'
        return ctx


# ─── QR code download ────────────────────────────────────────

class WorkOrderQRView(StaffRequiredMixin, View):
    """Return QR code as PNG image."""

    def get(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)

        if order.qr_code:
            # Serve existing file
            return HttpResponse(order.qr_code.read(), content_type='image/png')

        # Generate on-the-fly
        from .services import generate_qr_image_bytes
        png_bytes = generate_qr_image_bytes(order)
        return HttpResponse(png_bytes, content_type='image/png')


# ─── Public JSON API for status check ────────────────────────

class OrderCheckAPIView(View):
    """Public JSON endpoint for order status (no auth)."""

    def get(self, request, order_number):
        order = get_object_or_404(WorkOrder, order_number=order_number)

        # Calculate progress percent
        status_sequence = [
            'new', 'diagnostics', 'approved', 'in_progress',
            'waiting_parts', 'completed', 'ready', 'delivered',
        ]
        if order.status in status_sequence:
            idx = status_sequence.index(order.status)
            progress = int((idx / (len(status_sequence) - 1)) * 100)
        elif order.status == 'cancelled':
            progress = 0
        else:
            progress = 0

        data = {
            'order_number': order.order_number,
            'vehicle_info': f'{order.vehicle.make} {order.vehicle.model} ({order.vehicle.license_plate})',
            'status': order.status,
            'status_display': order.get_status_display(),
            'progress_percent': progress,
            'estimated_completion': (
                order.estimated_completion.isoformat() if order.estimated_completion else None
            ),
            'total_cost': str(order.final_cost) if order.status in (
                'completed', 'ready', 'delivered',
            ) else None,
        }
        return JsonResponse(data)
