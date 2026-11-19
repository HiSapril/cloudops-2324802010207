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
        # Tự động đồng bộ trường specs từ thông số phần cứng
        self.specs = f"{self.cpu_cores} vCPU / {self.ram_gb} GB RAM / {self.disk_gb} GB SSD"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.ip_address}) - {self.get_status_display()}"
