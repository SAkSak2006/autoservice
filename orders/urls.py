from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.WorkOrderListView.as_view(), name='list'),
    path('create/', views.WorkOrderCreateView.as_view(), name='create'),
    path('kanban/', views.WorkOrderKanbanView.as_view(), name='kanban'),
    path('ajax/client-vehicles/', views.ClientVehiclesAjaxView.as_view(), name='client_vehicles'),
    path('<int:pk>/', views.WorkOrderDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.WorkOrderUpdateView.as_view(), name='edit'),
    path('<int:pk>/status/', views.WorkOrderStatusChangeView.as_view(), name='status_change'),
    path('<int:pk>/print/', views.WorkOrderPrintView.as_view(), name='print'),
    path('<int:pk>/add-service/', views.AddServiceView.as_view(), name='add_service'),
    path('<int:pk>/add-part/', views.AddPartView.as_view(), name='add_part'),
    path('<int:pk>/remove-service/<int:item_pk>/', views.RemoveServiceView.as_view(), name='remove_service'),
    path('<int:pk>/remove-part/<int:item_pk>/', views.RemovePartView.as_view(), name='remove_part'),
    path('check/<str:order_number>/', views.OrderCheckView.as_view(), name='check'),
    path('<int:pk>/qr/', views.WorkOrderQRView.as_view(), name='qr'),
    path('api/check/<str:order_number>/', views.OrderCheckAPIView.as_view(), name='api_check'),
]
