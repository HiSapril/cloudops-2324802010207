from django.db import models
from django.contrib.auth.models import User


class CloudAsset(models.Model):
    STATUS_CHOICES = [
        ('running', 'Đang hoạt động'),
        ('stopped', 'Đã dừng'),
        ('maintenance', 'Bảo trì'),
    ]

    PROVIDER_CHOICES = [
        ('aws', 'Amazon Web Services (AWS)'),
        ('gcp', 'Google Cloud Platform (GCP)'),
        ('azure', 'Microsoft Azure'),
        ('digitalocean', 'DigitalOcean'),
        ('local_vps', 'Private Cloud / On-Premise'),
    ]

    OS_CHOICES = [
        ('ubuntu', 'Ubuntu 24.04 LTS'),
        ('debian', 'Debian 12'),
        ('rocky', 'Rocky Linux 9'),
        ('windows', 'Windows Server 2022'),
        ('alpine', 'Alpine Linux'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cloud_assets', verbose_name='Chủ sở hữu')
    name = models.CharField(max_length=150, verbose_name='Tên máy chủ')
    ip_address = models.CharField(max_length=45, verbose_name='Địa chỉ IP Public/Private')

    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default='aws', verbose_name='Nhà cung cấp Cloud')
    os_type = models.CharField(max_length=30, choices=OS_CHOICES, default='ubuntu', verbose_name='Hệ điều hành')
    region = models.CharField(max_length=60, default='ap-southeast-1 (Singapore)', verbose_name='Vùng triển khai (Region)')

    cpu_cores = models.PositiveIntegerField(default=2, verbose_name='Số vCPU')
    ram_gb = models.PositiveIntegerField(default=4, verbose_name='Dung lượng RAM (GB)')
    disk_gb = models.PositiveIntegerField(default=50, verbose_name='Ổ cứng SSD (GB)')
    cost_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=20.00, verbose_name='Chi phí ước tính ($/tháng)')

    specs = models.CharField(max_length=255, blank=True, verbose_name='Mô tả cấu hình')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running', verbose_name='Trạng thái')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày khởi tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Cập nhật lần cuối')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tài nguyên Cloud'
        verbose_name_plural = 'Danh sách Tài nguyên Cloud'

    def save(self, *args, **kwargs):
        self.specs = f"{self.cpu_cores} vCPU / {self.ram_gb} GB RAM / {self.disk_gb} GB SSD"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.ip_address}) - {self.get_status_display()}"


class StorageSnapshot(models.Model):
    """Đối tượng nghiệp vụ 2: Kho lưu trữ cấu hình & bản sao lưu (có upload tệp)."""

    STORAGE_TYPE_CHOICES = [
        ('config', 'Tệp cấu hình hạ tầng'),
        ('db_backup', 'Bản sao lưu CSDL'),
        ('vm_snapshot', 'Snapshot máy ảo'),
        ('log_archive', 'Lưu trữ nhật ký hệ thống'),
    ]

    STATUS_CHOICES = [
        ('available', 'Sẵn sàng'),
        ('archived', 'Đã lưu trữ'),
        ('restoring', 'Đang khôi phục'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='storage_snapshots', verbose_name='Chủ sở hữu')
    asset = models.ForeignKey(
        CloudAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='snapshots',
        verbose_name='Máy chủ liên kết',
    )
    name = models.CharField(max_length=150, verbose_name='Tên bản lưu trữ')
    storage_type = models.CharField(max_length=25, choices=STORAGE_TYPE_CHOICES, default='config', verbose_name='Loại lưu trữ')
    bucket_region = models.CharField(max_length=60, default='vn-hcm-01 (ESXi Local)', verbose_name='Vùng lưu trữ')
    size_mb = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='Dung lượng (MB)')
    config_file = models.FileField(upload_to='snapshots/%Y/%m/', blank=True, null=True, verbose_name='Tệp đính kèm')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='Trạng thái')
    notes = models.TextField(blank=True, max_length=500, verbose_name='Ghi chú')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Cập nhật lần cuối')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bản lưu trữ & Snapshot'
        verbose_name_plural = 'Danh sách Bản lưu trữ & Snapshot'

    def save(self, *args, **kwargs):
        if self.config_file and hasattr(self.config_file, 'size') and self.config_file.size:
            self.size_mb = round(self.config_file.size / (1024 * 1024), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_storage_type_display()})"
