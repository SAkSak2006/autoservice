from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.action(description='Назначить роль «Механик»')
def make_mechanic(modeladmin, request, queryset):
    queryset.update(role=User.Role.MECHANIC)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'last_name', 'first_name',
        'phone', 'role', 'is_active',
    )
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('first_name', 'last_name', 'patronymic', 'email', 'phone')
    ordering = ('-date_joined',)
    actions = [make_mechanic]

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {
            'fields': (
                'role', 'patronymic', 'phone', 'avatar',
                'telegram_chat_id', 'notification_preferences',
                'consent_personal_data', 'consent_date',
            ),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительно', {
            'fields': ('role', 'first_name', 'last_name', 'patronymic', 'email', 'phone'),
        }),
    )
