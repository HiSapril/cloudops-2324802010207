from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import api_views

router = DefaultRouter()
router.register(r'assets', api_views.CloudAssetViewSet, basename='api-assets')
router.register(r'snapshots', api_views.StorageSnapshotViewSet, basename='api-snapshots')

urlpatterns = [
    path('health/', api_views.health_check_api, name='api-health'),
    path('auth/token/', obtain_auth_token, name='api-token-auth'),
    path('', include(router.urls)),
]
