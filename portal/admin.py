from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('client', 'vehicle', 'booking_date', 'booking_time', 'status', 'work_order', 'created_at')
    list_filter = ('status', 'booking_date')
    search_fields = ('client__last_name', 'client__phone')
    raw_id_fields = ('client', 'vehicle', 'work_order')
