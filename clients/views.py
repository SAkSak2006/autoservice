from django.contrib import messages
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, View,
)

from accounts.mixins import StaffRequiredMixin
from .forms import ClientForm, VehicleForm, VehicleInlineFormSet, ClientSearchForm, CAR_MAKES
from .models import Client, Vehicle


class ClientListView(StaffRequiredMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        qs = Client.objects.filter(is_active=True).annotate(
            vehicle_count=Count('vehicles'),
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(patronymic__icontains=q)
                | Q(phone__icontains=q)
                | Q(email__icontains=q)
                | Q(vehicles__license_plate__icontains=q)
            ).distinct()

        sort = self.request.GET.get('sort', '-created_at')
        allowed_sorts = ['last_name', '-last_name', 'created_at', '-created_at', 'phone']
        if sort in allowed_sorts:
            qs = qs.order_by(sort)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_form'] = ClientSearchForm(self.request.GET)
        ctx['current_sort'] = self.request.GET.get('sort', '-created_at')
        return ctx


class ClientCreateView(StaffRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новый клиент'
        ctx['car_makes'] = CAR_MAKES
        if self.request.POST:
            ctx['vehicle_formset'] = VehicleInlineFormSet(self.request.POST, prefix='vehicles')
        else:
            ctx['vehicle_formset'] = VehicleInlineFormSet(prefix='vehicles')
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        vehicle_formset = ctx['vehicle_formset']
        if vehicle_formset.is_valid():
            self.object = form.save()
            vehicle_formset.instance = self.object
            vehicle_formset.save()
            messages.success(self.request, f'Клиент {self.object.get_full_name()} создан.')
            return redirect(self.object.get_absolute_url())
        # Formset invalid — re-render with errors
        return self.render_to_response(ctx)

    def form_invalid(self, form):
        ctx = self.get_context_data(form=form)
        return self.render_to_response(ctx)

    def get_success_url(self):
        return reverse('clients:detail', kwargs={'pk': self.object.pk})


class ClientDetailView(StaffRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['vehicles'] = self.object.vehicles.all()
        ctx['active_orders'] = self.object.get_active_orders()
        # All orders for history tab
        ctx['all_orders'] = self.object.orders.all().order_by('-created_at') if hasattr(self.object, 'orders') else []
        return ctx


class ClientUpdateView(StaffRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Редактирование: {self.object.get_full_name()}'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Данные клиента обновлены.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('clients:detail', kwargs={'pk': self.object.pk})


class ClientDeleteView(StaffRequiredMixin, View):
    """Soft delete — set is_active=False."""

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        client.is_active = False
        client.save(update_fields=['is_active'])
        messages.success(request, f'Клиент {client.get_full_name()} удалён.')
        return redirect('clients:list')


# ─── Vehicle views ───────────────────────────────────────────

class VehicleCreateView(StaffRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'clients/vehicle_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.client_obj = get_object_or_404(Client, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['client'] = self.client_obj
        ctx['title'] = f'Добавить авто — {self.client_obj.get_full_name()}'
        ctx['car_makes'] = CAR_MAKES
        return ctx

    def form_valid(self, form):
        form.instance.client = self.client_obj
        messages.success(self.request, 'Автомобиль добавлен.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('clients:detail', kwargs={'pk': self.client_obj.pk})


class VehicleUpdateView(StaffRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'clients/vehicle_form.html'
    pk_url_kwarg = 'vehicle_pk'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['client'] = self.object.client
        ctx['title'] = f'Редактирование: {self.object}'
        ctx['car_makes'] = CAR_MAKES
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Данные автомобиля обновлены.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('clients:detail', kwargs={'pk': self.object.client.pk})


class VehicleDeleteView(StaffRequiredMixin, View):
    def post(self, request, pk, vehicle_pk):
        vehicle = get_object_or_404(Vehicle, pk=vehicle_pk, client__pk=pk)
        client_pk = vehicle.client.pk
        vehicle.delete()
        messages.success(request, 'Автомобиль удалён.')
        return redirect('clients:detail', pk=client_pk)
