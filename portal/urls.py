from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.PortalDashboardView.as_view(), name='dashboard'),
    path('orders/', views.PortalOrderListView.as_view(), name='orders'),
    path('orders/<int:pk>/', views.PortalOrderDetailView.as_view(), name='order_detail'),
    path('vehicles/', views.PortalVehicleListView.as_view(), name='vehicles'),
    path('vehicles/add/', views.PortalVehicleCreateView.as_view(), name='vehicle_add'),
    path('booking/', views.PortalBookingView.as_view(), name='booking'),
    path('booking/slots/', views.BookingSlotsAPIView.as_view(), name='booking_slots'),
    path('settings/', views.PortalSettingsView.as_view(), name='settings'),
    path('offline/', views.PortalOfflineView.as_view(), name='offline'),
]
