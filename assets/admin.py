from django.contrib import admin
from .models import CloudAsset, StorageSnapshot


@admin.register(CloudAsset)
class CloudAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip_address', 'provider', 'region', 'os_type', 'cpu_cores', 'ram_gb', 'cost_monthly', 'status', 'owner', 'created_at')
    list_filter = ('provider', 'status', 'os_type', 'created_at')
    search_fields = ('name', 'ip_address', 'region', 'owner__username')


@admin.register(StorageSnapshot)
class StorageSnapshotAdmin(admin.ModelAdmin):
    list_display = ('name', 'storage_type', 'bucket_region', 'size_mb', 'status', 'asset', 'owner', 'created_at')
    list_filter = ('storage_type', 'status', 'created_at')
    search_fields = ('name', 'bucket_region', 'notes', 'owner__username')
