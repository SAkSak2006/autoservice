from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from accounts.models import User, phone_validator


def default_notification_preferences():
    return {"email": True, "telegram": False, "sms": False}


class Client(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_profile',
        verbose_name='Аккаунт',
    )
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    patronymic = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    phone = models.CharField(
        max_length=20,
        unique=True,
        validators=[phone_validator],
        verbose_name='Телефон',
    )
    email = models.EmailField(blank=True, verbose_name='Email')
    telegram_chat_id = models.BigIntegerField(
        null=True, blank=True, verbose_name='Telegram Chat ID',
    )
    notification_preferences = models.JSONField(
        default=default_notification_preferences,
        verbose_name='Настройки уведомлений',
    )
    consent_personal_data = models.BooleanField(
        default=False, verbose_name='Согласие на обработку ПД',
    )
    consent_date = models.DateTimeField(
        null=True, blank=True, verbose_name='Дата согласия',
    )
    notes = models.TextField(blank=True, verbose_name='Заметки')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']

    def __str__(self):
        initials = self.first_name[0] + '.' if self.first_name else ''
        pat = self.patronymic[0] + '.' if self.patronymic else ''
        return f'{self.last_name} {initials}{pat} ({self.phone})'

    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        return ' '.join(p for p in parts if p)

    def get_vehicles(self):
        return self.vehicles.all()

    def get_active_orders(self):
        return self.orders.filter(
            status__in=['new', 'diagnostics', 'approved', 'in_progress', 'waiting_parts']
        )

    def get_preferred_channels(self):
        prefs = self.notification_preferences or {}
        return [ch for ch, enabled in prefs.items() if enabled]

    def get_absolute_url(self):
        return reverse('clients:detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if self.consent_personal_data and not self.consent_date:
            self.consent_date = timezone.now()
        super().save(*args, **kwargs)


def current_year():
    return timezone.now().year


class Vehicle(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name='Клиент',
    )
    vin = models.CharField(
        max_length=17,
        blank=True,
        verbose_name='VIN-код',
        validators=[
            RegexValidator(
                regex=r'^([A-HJ-NPR-Z0-9]{17})?$',
                message='VIN должен содержать ровно 17 символов (латинские буквы и цифры) или быть пустым.',
            ),
        ],
    )
    make = models.CharField(max_length=50, verbose_name='Марка')
    model = models.CharField(max_length=50, verbose_name='Модель')
    year = models.PositiveIntegerField(
        verbose_name='Год выпуска',
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(current_year() + 1),
        ],
    )
    license_plate = models.CharField(max_length=15, verbose_name='Госномер')
    color = models.CharField(max_length=30, blank=True, verbose_name='Цвет')
    mileage = models.PositiveIntegerField(default=0, verbose_name='Пробег (км)')
    notes = models.TextField(blank=True, verbose_name='Заметки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.make} {self.model} ({self.year}) {self.license_plate}'

    def get_full_info(self):
        return f'{self.make} {self.model} {self.year} {self.license_plate}'
