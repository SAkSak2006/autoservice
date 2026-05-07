from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from clients.models import Client, Vehicle
from services.models import Service, SparePart


# ─── Status transition matrix ────────────────────────────────

STATUS_TRANSITIONS = {
    'new': ['diagnostics', 'in_progress', 'cancelled'],
    'diagnostics': ['approved', 'cancelled'],
    'approved': ['in_progress', 'cancelled'],
    'in_progress': ['waiting_parts', 'completed', 'cancelled'],
    'waiting_parts': ['in_progress'],
    'completed': ['ready'],
    'ready': ['delivered'],
    'delivered': [],
    'cancelled': [],
}

STATUS_BADGE_CLASSES = {
    'new': 'bg-primary',
    'diagnostics': 'bg-info',
    'approved': 'bg-secondary',
    'in_progress': 'bg-warning text-dark',
    'waiting_parts': 'bg-danger',
    'completed': 'bg-success',
    'ready': 'bg-success badge-pulse',
    'delivered': 'bg-dark',
    'cancelled': 'bg-secondary text-decoration-line-through',
}


class WorkOrder(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        DIAGNOSTICS = 'diagnostics', 'Диагностика'
        APPROVED = 'approved', 'Согласован с клиентом'
        IN_PROGRESS = 'in_progress', 'В работе'
        WAITING_PARTS = 'waiting_parts', 'Ожидает запчасти'
        COMPLETED = 'completed', 'Выполнен'
        READY = 'ready', 'Готов к выдаче'
        DELIVERED = 'delivered', 'Выдан клиенту'
        CANCELLED = 'cancelled', 'Отменён'

    order_number = models.CharField(
        max_length=20, unique=True, editable=False, verbose_name='Номер заказа',
    )
    client = models.ForeignKey(
        Client, on_delete=models.PROTECT, related_name='orders', verbose_name='Клиент',
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT, related_name='orders', verbose_name='Автомобиль',
    )
    assigned_mechanic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'mechanic'},
        related_name='assigned_orders',
        verbose_name='Мастер',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW, verbose_name='Статус',
    )

    # Description
    description = models.TextField(verbose_name='Описание проблемы')
    diagnosis = models.TextField(blank=True, verbose_name='Диагноз')
    recommendations = models.TextField(blank=True, verbose_name='Рекомендации')

    # Cost
    total_services_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Сумма услуг',
    )
    total_parts_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Сумма запчастей',
    )
    total_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Итого',
    )
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name='Скидка (%)',
    )
    final_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Итого со скидкой',
    )

    # Dates
    estimated_completion = models.DateTimeField(
        null=True, blank=True, verbose_name='Ожидаемая дата готовности',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Начат')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Завершён')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='Выдан')

    # QR
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, verbose_name='QR-код')

    class Meta:
        verbose_name = 'Заказ-наряд'
        verbose_name_plural = 'Заказ-наряды'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_number} — {self.client}'

    def get_absolute_url(self):
        return reverse('orders:detail', kwargs={'pk': self.pk})

    # ── Auto-number generation ──

    def _generate_order_number(self):
        today = timezone.localdate()
        prefix = f'ЗН-{today:%Y%m%d}-'
        last = (
            WorkOrder.objects
            .filter(order_number__startswith=prefix)
            .order_by('-order_number')
            .values_list('order_number', flat=True)
            .first()
        )
        if last:
            seq = int(last.split('-')[-1]) + 1
        else:
            seq = 1
        return f'{prefix}{seq:03d}'

    # ── Cost recalculation ──

    def recalculate_totals(self):
        from django.db.models import Sum
        svc = self.items.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        prt = self.parts.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        self.total_services_cost = svc
        self.total_parts_cost = prt
        self.total_cost = svc + prt
        self.final_cost = self.total_cost * (Decimal('1') - self.discount_percent / Decimal('100'))
        self.save(update_fields=[
            'total_services_cost', 'total_parts_cost', 'total_cost', 'final_cost',
        ])

    # ── Status transitions ──

    def can_transition_to(self, new_status):
        allowed = STATUS_TRANSITIONS.get(self.status, [])
        return new_status in allowed

    def transition_to(self, new_status, user, comment=''):
        if not self.can_transition_to(new_status):
            raise ValidationError(
                f'Переход из «{self.get_status_display()}» в «{new_status}» невозможен.'
            )
        old_status = self.status
        self.status = new_status
        now = timezone.now()

        if new_status == self.Status.IN_PROGRESS and not self.started_at:
            self.started_at = now
        elif new_status == self.Status.COMPLETED:
            self.completed_at = now
        elif new_status == self.Status.DELIVERED:
            self.delivered_at = now

        # Save without triggering signal-based history (we create it explicitly)
        self._skip_history = True
        self.save()
        self._skip_history = False

        WorkOrderStatusHistory.objects.create(
            work_order=self,
            from_status=old_status,
            to_status=new_status,
            changed_by=user,
            comment=comment,
        )

        # Dispatch notifications
        try:
            from notifications.services import NotificationService
            if new_status == self.Status.READY:
                NotificationService.dispatch_order_ready(self)
            elif new_status not in (self.Status.CANCELLED,):
                NotificationService.dispatch_status_changed(self)
        except Exception:
            pass  # Don't break status transition if notifications fail

    def get_status_badge_class(self):
        return STATUS_BADGE_CLASSES.get(self.status, 'bg-secondary')

    def get_qr_url(self):
        return f'{settings.SITE_URL}/orders/check/{self.order_number}/'

    # ── Save ──

    def save(self, *args, **kwargs):
        is_new = not self.pk
        if not self.order_number:
            self.order_number = self._generate_order_number()

        # Recalc final_cost from total_cost and discount
        if self.total_cost:
            self.final_cost = self.total_cost * (Decimal('1') - self.discount_percent / Decimal('100'))

        super().save(*args, **kwargs)

        # Generate QR code after first save (needs pk and order_number)
        if is_new and not self.qr_code:
            from .services import generate_qr_code
            generate_qr_code(self)
            super().save(update_fields=['qr_code'])


class WorkOrderItem(models.Model):
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ',
    )
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, verbose_name='Услуга',
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Кол-во')
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='Цена',
    )
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='Сумма',
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')

    class Meta:
        verbose_name = 'Услуга в заказе'
        verbose_name_plural = 'Услуги в заказе'

    def __str__(self):
        return f'{self.service.name} x{self.quantity}'

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.service.base_price
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)
        self.work_order.recalculate_totals()

    def delete(self, *args, **kwargs):
        wo = self.work_order
        super().delete(*args, **kwargs)
        wo.recalculate_totals()


class WorkOrderPart(models.Model):
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name='parts', verbose_name='Заказ',
    )
    spare_part = models.ForeignKey(
        SparePart, on_delete=models.PROTECT, verbose_name='Запчасть',
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Кол-во')
    price_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='Цена за ед.',
    )
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='Сумма',
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')

    class Meta:
        verbose_name = 'Запчасть в заказе'
        verbose_name_plural = 'Запчасти в заказе'

    def __str__(self):
        return f'{self.spare_part.name} x{self.quantity}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not self.price_per_unit:
            self.price_per_unit = self.spare_part.price
        self.subtotal = self.price_per_unit * self.quantity

        if is_new:
            # Check stock
            if self.spare_part.quantity_in_stock < self.quantity:
                raise ValidationError(
                    f'Недостаточно на складе: {self.spare_part.name} '
                    f'(есть {self.spare_part.quantity_in_stock}, нужно {self.quantity})'
                )
            # Deduct from stock
            self.spare_part.quantity_in_stock -= self.quantity
            self.spare_part.save(update_fields=['quantity_in_stock'])
        else:
            # On update: restore old qty, then deduct new
            old = WorkOrderPart.objects.get(pk=self.pk)
            diff = self.quantity - old.quantity
            if diff > 0 and self.spare_part.quantity_in_stock < diff:
                raise ValidationError(
                    f'Недостаточно на складе: {self.spare_part.name} '
                    f'(есть {self.spare_part.quantity_in_stock}, нужно ещё {diff})'
                )
            self.spare_part.quantity_in_stock -= diff
            self.spare_part.save(update_fields=['quantity_in_stock'])

        super().save(*args, **kwargs)
        self.work_order.recalculate_totals()

    def delete(self, *args, **kwargs):
        # Return to stock
        self.spare_part.quantity_in_stock += self.quantity
        self.spare_part.save(update_fields=['quantity_in_stock'])
        wo = self.work_order
        super().delete(*args, **kwargs)
        wo.recalculate_totals()


class WorkOrderStatusHistory(models.Model):
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name='status_history',
        verbose_name='Заказ',
    )
    from_status = models.CharField(max_length=20, verbose_name='Из статуса')
    to_status = models.CharField(max_length=20, verbose_name='В статус')
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        verbose_name='Кем изменён',
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        verbose_name = 'История статуса'
        verbose_name_plural = 'История статусов'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.work_order.order_number}: {self.from_status} → {self.to_status}'
