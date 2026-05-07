from django.contrib import admin
from django.utils.html import format_html
from .models import ServiceCategory, Service, SparePart


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0
    fields = ('name', 'base_price', 'estimated_duration', 'is_active')


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'sort_order', 'is_active', 'service_count')
    list_editable = ('sort_order', 'is_active')
    ordering = ('sort_order',)
    inlines = [ServiceInline]

    @admin.display(description='Услуг')
    def service_count(self, obj):
        return obj.services.count()


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'estimated_duration', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('base_price', 'is_active')


@admin.action(description='Пополнить склад (+10 шт.)')
def restock(modeladmin, request, queryset):
    for part in queryset:
        part.quantity_in_stock += 10
        part.save(update_fields=['quantity_in_stock'])


@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = ('name', 'part_number', 'manufacturer', 'price', 'stock_indicator', 'unit', 'is_active')
    list_filter = ('is_active', 'manufacturer')
    search_fields = ('name', 'part_number', 'manufacturer')
    list_editable = ('price', 'is_active')
    actions = [restock]

    @admin.display(description='Остаток')
    def stock_indicator(self, obj):
        if obj.is_low_stock():
            return format_html(
                '<span style="color:#ea4335;font-weight:bold;">'
                '&#9888; {} / {}</span>',
                obj.quantity_in_stock, obj.min_stock_level,
            )
        return format_html(
            '<span style="color:#34a853;">{}</span>',
            obj.quantity_in_stock,
        )
