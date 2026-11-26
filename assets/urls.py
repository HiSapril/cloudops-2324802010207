from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('snapshots/', views.snapshots_view, name='snapshots'),
    path('snapshots/<int:snapshot_id>/delete/', views.delete_snapshot_view, name='delete_snapshot'),
    path('admin-overview/', views.admin_overview_view, name='admin_overview'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('export/csv/', views.export_csv_view, name='export_csv'),
    path('asset/<int:asset_id>/delete/', views.delete_asset_view, name='delete_asset'),
    path('asset/<int:asset_id>/toggle-power/', views.toggle_power_view, name='toggle_power'),
]
