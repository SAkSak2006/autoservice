import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import Client, Vehicle


class VehicleInline(admin.TabularInline):
    model = Vehicle
    extra = 0
    fields = ('make', 'model', 'year', 'license_plate', 'vin', 'color', 'mileage')


class HasAccountFilter(admin.SimpleListFilter):
    title = 'наличие аккаунта'
    parameter_name = 'has_account'

    def lookups(self, request, model_admin):
        return [('yes', 'Есть аккаунт'), ('no', 'Нет аккаунта')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(user__isnull=False)
        if self.value() == 'no':
            return queryset.filter(user__isnull=True)


@admin.action(description='Экспорт выбранных клиентов в CSV')
def export_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="clients.csv"'
    response.write('\ufeff')  # BOM for Excel
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Фамилия', 'Имя', 'Отчество', 'Телефон', 'Email', 'Авто', 'Создан'])
    for c in queryset.prefetch_related('vehicles'):
        vehicles = ', '.join(str(v) for v in c.vehicles.all())
        writer.writerow([
            c.last_name, c.first_name, c.patronymic,
            c.phone, c.email, vehicles,
            c.created_at.strftime('%d.%m.%Y'),
        ])
    return response


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone', 'email', 'has_account', 'is_active', 'created_at')
    list_filter = (HasAccountFilter, 'is_active', 'created_at', 'consent_personal_data')
    search_fields = ('first_name', 'last_name', 'patronymic', 'phone', 'email', 'vehicles__license_plate')
    ordering = ('-created_at',)
    inlines = [VehicleInline]
    actions = [export_csv]

    @admin.display(boolean=True, description='Аккаунт')
    def has_account(self, obj):
        return obj.user is not None


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'year', 'license_plate', 'client', 'mileage')
    list_filter = ('make', 'year')
    search_fields = ('make', 'model', 'license_plate', 'vin', 'client__last_name')
    raw_id_fields = ('client',)
