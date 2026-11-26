import ipaddress
import os
from rest_framework import serializers
from .models import CloudAsset, StorageSnapshot
from .forms import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES


class CloudAssetSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    provider_display = serializers.ReadOnlyField(source='get_provider_display')

    class Meta:
        model = CloudAsset
        fields = [
            'id', 'owner', 'owner_username', 'name', 'ip_address',
            'provider', 'provider_display', 'os_type', 'region',
            'cpu_cores', 'ram_gb', 'disk_gb', 'cost_monthly',
            'specs', 'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'specs', 'created_at', 'updated_at']

    def validate_ip_address(self, value):
        try:
            ipaddress.ip_address(value.strip())
        except ValueError:
            raise serializers.ValidationError('Địa chỉ IP không hợp lệ.')
        return value.strip()

    def validate_cpu_cores(self, value):
        if value < 1 or value > 128:
            raise serializers.ValidationError('Số vCPU phải từ 1 đến 128.')
        return value

    def validate_ram_gb(self, value):
        if value < 1 or value > 1024:
            raise serializers.ValidationError('RAM phải từ 1 đến 1024 GB.')
        return value

    def validate_disk_gb(self, value):
        if value < 10 or value > 10000:
            raise serializers.ValidationError('Ổ cứng SSD phải từ 10 đến 10000 GB.')
        return value


class StorageSnapshotSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    asset_name = serializers.ReadOnlyField(source='asset.name')
    storage_type_display = serializers.ReadOnlyField(source='get_storage_type_display')
    status_display = serializers.ReadOnlyField(source='get_status_display')

    class Meta:
        model = StorageSnapshot
        fields = [
            'id', 'owner', 'owner_username', 'asset', 'asset_name',
            'name', 'storage_type', 'storage_type_display',
            'bucket_region', 'size_mb', 'config_file',
            'status', 'status_display', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def validate_config_file(self, value):
        if value and hasattr(value, 'name'):
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in ALLOWED_UPLOAD_EXTENSIONS:
                raise serializers.ValidationError(f'Định dạng tệp "{ext}" không được phép.')
            if value.size > MAX_UPLOAD_SIZE_BYTES:
                raise serializers.ValidationError('Tệp vượt quá giới hạn 10 MB.')
        return value
