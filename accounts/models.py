from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


phone_validator = RegexValidator(
    regex=r'^\+7\d{10}$',
    message='Введите номер в формате +7XXXXXXXXXX',
)


def default_notification_preferences():
    return {"email": True, "telegram": False, "sms": False}


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        MECHANIC = 'mechanic', 'Механик'
        CLIENT = 'client', 'Клиент'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
        verbose_name='Роль',
    )
    patronymic = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Отчество',
    )
    phone = models.CharField(
        max_length=12,
        unique=True,
        blank=True,
        null=True,
        validators=[phone_validator],
        verbose_name='Телефон',
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        verbose_name='Аватар',
    )
    telegram_chat_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='Telegram Chat ID',
    )
    notification_preferences = models.JSONField(
        default=default_notification_preferences,
        verbose_name='Настройки уведомлений',
    )
    consent_personal_data = models.BooleanField(
        default=False,
        verbose_name='Согласие на обработку ПД',
    )
    consent_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата согласия',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.get_full_name()} ({self.get_role_display()})'

    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        return ' '.join(p for p in parts if p)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_mechanic(self):
        return self.role == self.Role.MECHANIC

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    def get_preferred_channels(self):
        prefs = self.notification_preferences or {}
        return [ch for ch, enabled in prefs.items() if enabled]

    def save(self, *args, **kwargs):
        if self.consent_personal_data and not self.consent_date:
            self.consent_date = timezone.now()
        super().save(*args, **kwargs)
