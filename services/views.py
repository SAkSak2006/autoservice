from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from accounts.mixins import StaffRequiredMixin
from .forms import ServiceCategoryForm, ServiceForm, SparePartForm
from .models import ServiceCategory, Service, SparePart


# ─── ServiceCategory ─────────────────────────────────────────

class ServiceCategoryListView(StaffRequiredMixin, ListView):
    model = ServiceCategory
    template_name = 'services/category_list.html'
    context_object_name = 'categories'


class ServiceCategoryCreateView(StaffRequiredMixin, CreateView):
    model = ServiceCategory
    form_class = ServiceCategoryForm
    template_name = 'services/category_form.html'
    success_url = reverse_lazy('services:category_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новая категория'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Категория создана.')
        return super().form_valid(form)


class ServiceCategoryUpdateView(StaffRequiredMixin, UpdateView):
    model = ServiceCategory
    form_class = ServiceCategoryForm
    template_name = 'services/category_form.html'
    success_url = reverse_lazy('services:category_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Редактирование: {self.object.name}'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Категория обновлена.')
        return super().form_valid(form)


# ─── Service ─────────────────────────────────────────────────

class ServiceListView(StaffRequiredMixin, ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'

    def get_queryset(self):
        return Service.objects.filter(is_active=True).select_related('category')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        categories = ServiceCategory.objects.filter(is_active=True).prefetch_related('services')
        ctx['categories'] = categories
        return ctx


class ServiceCreateView(StaffRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'
    success_url = reverse_lazy('services:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новая услуга'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Услуга создана.')
        return super().form_valid(form)


class ServiceUpdateView(StaffRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'
    success_url = reverse_lazy('services:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Редактирование: {self.object.name}'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Услуга обновлена.')
        return super().form_valid(form)


class ServiceDeleteView(StaffRequiredMixin, DeleteView):
    model = Service
    success_url = reverse_lazy('services:list')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save(update_fields=['is_active'])
        messages.success(self.request, 'Услуга удалена.')
        return self.render_to_response(self.get_context_data())

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save(update_fields=['is_active'])
        messages.success(request, 'Услуга удалена.')
        from django.shortcuts import redirect
        return redirect(self.success_url)


# ─── SparePart ───────────────────────────────────────────────

class SparePartListView(StaffRequiredMixin, ListView):
    model = SparePart
    template_name = 'services/sparepart_list.html'
    context_object_name = 'parts'
    paginate_by = 30

    def get_queryset(self):
        qs = SparePart.objects.filter(is_active=True)
        q = self.request.GET.get('q', '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(part_number__icontains=q)
                | Q(manufacturer__icontains=q)
            )
        return qs


class SparePartCreateView(StaffRequiredMixin, CreateView):
    model = SparePart
    form_class = SparePartForm
    template_name = 'services/sparepart_form.html'
    success_url = reverse_lazy('services:parts')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новая запчасть'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Запчасть добавлена.')
        return super().form_valid(form)


class SparePartUpdateView(StaffRequiredMixin, UpdateView):
    model = SparePart
    form_class = SparePartForm
    template_name = 'services/sparepart_form.html'
    success_url = reverse_lazy('services:parts')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Редактирование: {self.object.name}'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Запчасть обновлена.')
        return super().form_valid(form)


class SparePartDeleteView(StaffRequiredMixin, DeleteView):
    model = SparePart
    success_url = reverse_lazy('services:parts')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save(update_fields=['is_active'])
        messages.success(request, 'Запчасть удалена.')
        from django.shortcuts import redirect
        return redirect(self.success_url)
