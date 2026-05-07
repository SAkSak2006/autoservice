from django.contrib import admin
from django.utils.html import format_html
from .models import NotificationTemplate, Notification


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'channel', 'is_active')
    list_filter = ('event_type', 'channel', 'is_active')
    search_fields = ('name', 'body_template')
    list_editable = ('is_active',)


@admin.action(description='Повторить отправку')
def retry_send(modeladmin, request, queryset):
    from .tasks import send_notification_task
    for n in queryset.filter(status='failed'):
        n.status = 'pending'
        n.retry_count = 0
        n.error_message = ''
        n.save(update_fields=['status', 'retry_count', 'error_message'])
        send_notification_task.delay(n.id)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'channel', 'event_type', 'status_badge', 'sent_at', 'created_at')
    list_filter = ('status', 'channel', 'event_type', 'created_at')
    search_fields = ('client__last_name', 'client__phone', 'subject', 'body')
    readonly_fields = ('client', 'work_order', 'channel', 'event_type', 'subject', 'body',
                       'status', 'sent_at', 'error_message', 'retry_count', 'created_at')
    ordering = ('-created_at',)
    actions = [retry_send]

    @admin.display(description='Статус')
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107', 'sent': '#34a853',
            'failed': '#ea4335', 'delivered': '#1a73e8',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:3px;font-size:0.8em;">{}</span>',
            color, obj.get_status_display(),
        )
