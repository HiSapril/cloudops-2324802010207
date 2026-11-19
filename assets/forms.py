from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import CloudAsset

class RegisterForm(forms.Form):
    username = forms.CharField(
        label='Tên đăng nhập',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập tên đăng nhập',
            'autocomplete': 'username'
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
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu (tối thiểu 8 ký tự)',
            'autocomplete': 'new-password'
        })
    )
    confirm_password = forms.CharField(
        label='Xác nhận mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập lại mật khẩu',
            'autocomplete': 'new-password'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Tên đăng nhập này đã được sử dụng. Vui lòng chọn tên khác!')
        return username

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
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu',
            'autocomplete': 'current-password'
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
                'placeholder': 'Ví dụ: prod-api-cluster-01, staging-db-master'
            }),
            'ip_address': forms.TextInput(attrs={
                'class': 'form-control font-monospace',
                'placeholder': 'Ví dụ: 54.254.12.34 hoặc 10.0.1.20'
            }),
            'provider': forms.Select(attrs={
                'class': 'form-select'
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: ap-southeast-1 (Singapore), us-east-1 (N. Virginia)'
            }),
            'os_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cpu_cores': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1', 'max': '128'
            }),
            'ram_gb': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1', 'max': '1024'
            }),
            'disk_gb': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10', 'max': '10000'
            }),
            'cost_monthly': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01', 'min': '0'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
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
