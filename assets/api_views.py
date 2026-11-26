from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from .models import CloudAsset, StorageSnapshot
from .serializers import CloudAssetSerializer, StorageSnapshotSerializer


def is_admin_user(user):
    return bool(user and (user.is_staff or user.is_superuser))


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check_api(request):
    """Endpoint kiểm tra sức khỏe API cho Uptime Kuma (status.duc.id.vn)."""
    return Response({
        'status': 'ok',
        'service': 'cloudops-api',
        'mssv': '2324802010207',
        'domain': 'api.duc.id.vn',
    })


class CloudAssetViewSet(viewsets.ModelViewSet):
    serializer_class = CloudAssetSerializer

    def get_queryset(self):
        qs = CloudAsset.objects.select_related('owner')
        if not is_admin_user(self.request.user):
            qs = qs.filter(owner=self.request.user)
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(ip_address__icontains=search) |
                Q(region__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class StorageSnapshotViewSet(viewsets.ModelViewSet):
    serializer_class = StorageSnapshotSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = StorageSnapshot.objects.select_related('owner', 'asset')
        if not is_admin_user(self.request.user):
            qs = qs.filter(owner=self.request.user)
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(bucket_region__icontains=search) |
                Q(notes__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
