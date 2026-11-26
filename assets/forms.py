import ipaddress
import os
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import CloudAsset, StorageSnapshot

ALLOWED_UPLOAD_EXTENSIONS = {'.conf', '.yaml', '.yml', '.json', '.sql', '.gz', '.zip', '.txt', '.tar'}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class RegisterForm(forms.Form):
    username = forms.CharField(
        label='Tên đăng nhập',
        min_length=3,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập tên đăng nhập (tối thiểu 3 ký tự)',
            'autocomplete': 'username',
            'required': True,
            'minlength': '3',
        })
    )
    email = forms.EmailField(
        label='Địa chỉ Email',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@company.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label='Mật khẩu',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu (tối thiểu 8 ký tự)',
            'autocomplete': 'new-password',
            'required': True,
            'minlength': '8',
        })
    )
    confirm_password = forms.CharField(
        label='Xác nhận mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập lại mật khẩu',
            'autocomplete': 'new-password',
            'required': True,
            'minlength': '8',
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Tên đăng nhập này đã được sử dụng. Vui lòng chọn tên khác!')
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Mật khẩu xác nhận không khớp!')
        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Tên đăng nhập',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập tên đăng nhập',
            'autocomplete': 'username',
            'required': True,
        })
    )
    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu',
            'autocomplete': 'current-password',
            'required': True,
        })
    )


class CloudAssetForm(forms.ModelForm):
    class Meta:
        model = CloudAsset
        fields = [
            'name', 'ip_address', 'provider', 'region',
            'os_type', 'cpu_cores', 'ram_gb', 'disk_gb',
            'cost_monthly', 'status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: prod-api-cluster-01, staging-db-master',
                'required': True,
                'minlength': '2',
                'maxlength': '150',
            }),
            'ip_address': forms.TextInput(attrs={
                'class': 'form-control font-monospace',
                'placeholder': 'Ví dụ: 10.10.10.10 hoặc 54.254.12.34',
                'required': True,
            }),
            'provider': forms.Select(attrs={'class': 'form-select'}),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: ap-southeast-1 (Singapore)',
                'required': True,
            }),
            'os_type': forms.Select(attrs={'class': 'form-select'}),
            'cpu_cores': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '128', 'required': True}),
            'ram_gb': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '1024', 'required': True}),
            'disk_gb': forms.NumberInput(attrs={'class': 'form-control', 'min': '10', 'max': '10000', 'required': True}),
            'cost_monthly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'required': True}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': 'Tên máy chủ (Server Name)',
            'ip_address': 'Địa chỉ IP',
            'provider': 'Nhà cung cấp Cloud (Cloud Provider)',
            'region': 'Khu vực máy chủ (Region / Datacenter)',
            'os_type': 'Hệ điều hành (Operating System)',
            'cpu_cores': 'Số vCPU',
            'ram_gb': 'RAM (GB)',
            'disk_gb': 'Dung lượng SSD (GB)',
            'cost_monthly': 'Chi phí ước tính ($/tháng)',
            'status': 'Trạng thái vận hành',
        }

    def clean_ip_address(self):
        ip_val = self.cleaned_data.get('ip_address', '').strip()
        try:
            ipaddress.ip_address(ip_val)
        except ValueError:
            raise forms.ValidationError('Địa chỉ IP không hợp lệ (ví dụ hợp lệ: 10.10.10.10 hoặc 192.168.100.10).')
        return ip_val

    def clean_cpu_cores(self):
        val = self.cleaned_data.get('cpu_cores')
        if val is None or val < 1 or val > 128:
            raise forms.ValidationError('Số vCPU phải nằm trong khoảng 1 đến 128.')
        return val

    def clean_ram_gb(self):
        val = self.cleaned_data.get('ram_gb')
        if val is None or val < 1 or val > 1024:
            raise forms.ValidationError('Dung lượng RAM phải nằm trong khoảng 1 đến 1024 GB.')
        return val

    def clean_disk_gb(self):
        val = self.cleaned_data.get('disk_gb')
        if val is None or val < 10 or val > 10000:
            raise forms.ValidationError('Dung lượng SSD phải nằm trong khoảng 10 đến 10000 GB.')
        return val


class StorageSnapshotForm(forms.ModelForm):
    class Meta:
        model = StorageSnapshot
        fields = ['name', 'asset', 'storage_type', 'bucket_region', 'size_mb', 'config_file', 'status', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: nginx-prod-backup-2026',
                'required': True,
                'minlength': '2',
                'maxlength': '150',
            }),
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'storage_type': forms.Select(attrs={'class': 'form-select'}),
            'bucket_region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: vn-hcm-01 (ESXi Local)',
                'required': True,
            }),
            'size_mb': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'config_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.conf,.yaml,.yml,.json,.sql,.gz,.zip,.txt,.tar',
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'maxlength': '500', 'placeholder': 'Ghi chú cấu hình hoặc bản sao lưu...'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            if user.is_staff or user.is_superuser:
                self.fields['asset'].queryset = CloudAsset.objects.all()
            else:
                self.fields['asset'].queryset = CloudAsset.objects.filter(owner=user)

    def clean_config_file(self):
        f = self.cleaned_data.get('config_file')
        if f and hasattr(f, 'name'):
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in ALLOWED_UPLOAD_EXTENSIONS:
                raise forms.ValidationError(f'Định dạng tệp "{ext}" không được phép. Chỉ chấp nhận: {", ".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}')
            if f.size > MAX_UPLOAD_SIZE_BYTES:
                raise forms.ValidationError('Kích thước tệp vượt quá giới hạn tối đa 10 MB.')
        return f

    def clean_size_mb(self):
        val = self.cleaned_data.get('size_mb')
        if val is not None and val < 0:
            raise forms.ValidationError('Dung lượng lưu trữ không thể âm.')
        return val
