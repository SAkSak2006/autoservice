from django.db import models

from clients.models import Client, Vehicle
from services.models import Service


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает подтверждения'
        CONFIRMED = 'confirmed', 'Подтверждена'
        CANCELLED = 'cancelled', 'Отменена'

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='bookings',
        verbose_name='Клиент',
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name='bookings',
        verbose_name='Автомобиль',
    )
    services = models.ManyToManyField(
        Service, blank=True, related_name='bookings',
        verbose_name='Услуги',
    )
    description = models.TextField(blank=True, verbose_name='Описание проблемы')
    booking_date = models.DateField(verbose_name='Дата записи')
    booking_time = models.TimeField(verbose_name='Время записи')
    estimated_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Ориентировочная стоимость',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
        verbose_name='Статус',
    )
    work_order = models.OneToOneField(
        'orders.WorkOrder', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='booking', verbose_name='Заказ-наряд',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')

    class Meta:
        verbose_name = 'Запись на обслуживание'
        verbose_name_plural = 'Записи на обслуживание'
        ordering = ['-booking_date', '-booking_time']

    def __str__(self):
        return f'{self.client} — {self.booking_date} {self.booking_time}'
