from django.contrib import admin
from django.utils.html import format_html
from .models import WorkOrder, WorkOrderItem, WorkOrderPart, WorkOrderStatusHistory


class WorkOrderItemInline(admin.TabularInline):
    model = WorkOrderItem
    extra = 0
    fields = ('service', 'quantity', 'price', 'subtotal', 'notes')
    readonly_fields = ('subtotal',)


class WorkOrderPartInline(admin.TabularInline):
    model = WorkOrderPart
    extra = 0
    fields = ('spare_part', 'quantity', 'price_per_unit', 'subtotal', 'notes')
    readonly_fields = ('subtotal',)


class StatusHistoryInline(admin.TabularInline):
    model = WorkOrderStatusHistory
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'comment', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'client', 'vehicle', 'status_badge',
        'assigned_mechanic', 'final_cost', 'created_at',
    )
    list_filter = ('status', 'assigned_mechanic', 'created_at')
    search_fields = (
        'order_number', 'client__last_name', 'client__first_name',
        'client__phone', 'vehicle__license_plate',
    )
    readonly_fields = (
        'order_number', 'total_services_cost', 'total_parts_cost',
        'total_cost', 'final_cost', 'created_at', 'started_at',
        'completed_at', 'delivered_at',
    )
    inlines = [WorkOrderItemInline, WorkOrderPartInline, StatusHistoryInline]
    raw_id_fields = ('client', 'vehicle')
    ordering = ('-created_at',)

    fieldsets = (
        ('Основное', {
            'fields': (
                'order_number', 'client', 'vehicle',
                'assigned_mechanic', 'status',
            ),
        }),
        ('Описание', {
            'fields': ('description', 'diagnosis', 'recommendations'),
        }),
        ('Стоимость', {
            'fields': (
                'total_services_cost', 'total_parts_cost',
                'total_cost', 'discount_percent', 'final_cost',
            ),
        }),
        ('Даты', {
            'fields': (
                'estimated_completion', 'created_at',
                'started_at', 'completed_at', 'delivered_at',
            ),
        }),
        ('QR', {
            'fields': ('qr_code',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Статус')
    def status_badge(self, obj):
        colors = {
            'new': '#1a73e8', 'diagnostics': '#0dcaf0',
            'approved': '#6c757d', 'in_progress': '#ffc107',
            'waiting_parts': '#ea4335', 'completed': '#34a853',
            'ready': '#34a853', 'delivered': '#212529',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;'
            'border-radius:4px;font-size:0.8em;">{}</span>',
            color, obj.get_status_display(),
        )
