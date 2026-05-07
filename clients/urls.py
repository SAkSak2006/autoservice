from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.ClientListView.as_view(), name='list'),
    path('create/', views.ClientCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='delete'),
    # Vehicles
    path('<int:pk>/vehicles/add/', views.VehicleCreateView.as_view(), name='vehicle_add'),
    path('<int:pk>/vehicles/<int:vehicle_pk>/edit/', views.VehicleUpdateView.as_view(), name='vehicle_edit'),
    path('<int:pk>/vehicles/<int:vehicle_pk>/delete/', views.VehicleDeleteView.as_view(), name='vehicle_delete'),
]
