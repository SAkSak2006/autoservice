from django.db import models


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Иконка Font Awesome')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Категория услуг'
        verbose_name_plural = 'Категории услуг'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='Категория',
    )
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='Базовая цена (руб.)',
    )
    estimated_duration = models.PositiveIntegerField(verbose_name='Время выполнения (мин.)')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['category__sort_order', 'name']

    def __str__(self):
        return f'{self.name} — {self.base_price:,.0f} \u20bd (~{self.get_duration_display()})'

    def get_duration_display(self):
        hours, minutes = divmod(self.estimated_duration, 60)
        if hours and minutes:
            return f'{hours}ч {minutes}мин'
        if hours:
            return f'{hours}ч'
        return f'{minutes} мин'


class SparePart(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    part_number = models.CharField(max_length=50, blank=True, verbose_name='Артикул')
    manufacturer = models.CharField(max_length=100, blank=True, verbose_name='Производитель')
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='Цена за ед. (руб.)',
    )
    quantity_in_stock = models.PositiveIntegerField(default=0, verbose_name='Остаток на складе')
    min_stock_level = models.PositiveIntegerField(default=5, verbose_name='Мин. остаток')
    unit = models.CharField(max_length=20, default='шт', verbose_name='Единица измерения')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлена')

    class Meta:
        verbose_name = 'Запчасть'
        verbose_name_plural = 'Запчасти'
        ordering = ['name']

    def __str__(self):
        pn = f' ({self.part_number})' if self.part_number else ''
        return f'{self.name}{pn} — {self.price:,.0f} \u20bd'

    def is_low_stock(self):
        return self.quantity_in_stock <= self.min_stock_level
