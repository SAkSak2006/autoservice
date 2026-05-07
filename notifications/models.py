from django.db import models

from clients.models import Client


class NotificationTemplate(models.Model):
    class EventType(models.TextChoices):
        ORDER_CREATED = 'order_created', 'Заказ создан'
        STATUS_CHANGED = 'status_changed', 'Статус изменён'
        ORDER_READY = 'order_ready', 'Заказ готов к выдаче'
        ORDER_DELIVERED = 'order_delivered', 'Заказ выдан'
        MAINTENANCE_REMINDER = 'maintenance_reminder', 'Напоминание о ТО'
        CUSTOM = 'custom', 'Пользовательское'

    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        TELEGRAM = 'telegram', 'Telegram'
        SMS = 'sms', 'SMS'

    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    event_type = models.CharField(
        max_length=30, choices=EventType.choices, verbose_name='Тип события',
    )
    channel = models.CharField(
        max_length=20, choices=Channel.choices, verbose_name='Канал',
    )
    subject_template = models.CharField(
        max_length=200, blank=True, verbose_name='Тема (для email)',
    )
    body_template = models.TextField(
        verbose_name='Шаблон текста',
        help_text='Переменные: {client_name}, {vehicle_info}, {order_number}, '
                  '{status}, {total_cost}, {qr_url}, {workshop_phone}',
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Шаблон уведомления'
        verbose_name_plural = 'Шаблоны уведомлений'
        unique_together = ('event_type', 'channel')
        ordering = ['event_type', 'channel']

    def __str__(self):
        return f'{self.name} ({self.get_channel_display()})'


class Notification(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        SENT = 'sent', 'Отправлено'
        FAILED = 'failed', 'Ошибка'
        DELIVERED = 'delivered', 'Доставлено'

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='notifications',
        verbose_name='Клиент',
    )
    work_order = models.ForeignKey(
        'orders.WorkOrder', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications', verbose_name='Заказ-наряд',
    )
    channel = models.CharField(
        max_length=20, choices=NotificationTemplate.Channel.choices,
        verbose_name='Канал',
    )
    event_type = models.CharField(max_length=30, verbose_name='Тип события')
    subject = models.CharField(max_length=200, blank=True, verbose_name='Тема')
    body = models.TextField(verbose_name='Текст')
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
        verbose_name='Статус',
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Отправлено')
    error_message = models.TextField(blank=True, verbose_name='Ошибка')
    retry_count = models.PositiveIntegerField(default=0, verbose_name='Попытки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_channel_display()} → {self.client} [{self.get_status_display()}]'
