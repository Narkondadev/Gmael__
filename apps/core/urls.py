from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_email, name='search_email'),
    path('add-inbox/', views.add_inbox_view, name='add_inbox'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/toggle/<int:pk>/', views.toggle_pin_status, name='toggle_pin'),
    path('dashboard/delete/<int:pk>/', views.delete_pin, name='delete_pin'),
    path('dashboard/domain/<int:pk>/', views.update_domain_filter, name='update_domain'),
    path('client-login/', views.client_login, name='client_login'),
    path('client-settings/', views.client_settings, name='client_settings'),
    path('client-logout/', views.client_logout, name='client_logout'),
]


