from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Services
    path('', views.ServiceListView.as_view(), name='list'),
    path('create/', views.ServiceCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ServiceUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ServiceDeleteView.as_view(), name='delete'),
    # Categories
    path('categories/', views.ServiceCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.ServiceCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.ServiceCategoryUpdateView.as_view(), name='category_edit'),
    # Spare parts
    path('parts/', views.SparePartListView.as_view(), name='parts'),
    path('parts/create/', views.SparePartCreateView.as_view(), name='part_create'),
    path('parts/<int:pk>/edit/', views.SparePartUpdateView.as_view(), name='part_edit'),
    path('parts/<int:pk>/delete/', views.SparePartDeleteView.as_view(), name='part_delete'),
]
