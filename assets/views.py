import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Sum, Q, Count
from .models import CloudAsset
from .forms import RegisterForm, LoginForm, CloudAssetForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data.get('email', '')
            password = form.cleaned_data['password']
            # Băm mật khẩu an toàn với create_user
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Đăng ký tài khoản thành công! Vui lòng đăng nhập để truy cập Cloud Console.')
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Chào mừng {user.username} đã truy cập bảng điều khiển!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Tên đăng nhập hoặc mật khẩu không chính xác.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Đã đăng xuất phiên làm việc an toàn.')
    return redirect('login')


@login_required
def dashboard_view(request):
    # Lấy tài nguyên thuộc quyền sở hữu của user
    queryset = CloudAsset.objects.filter(owner=request.user)

    # Xử lý tìm kiếm và bộ lọc
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    provider_filter = request.GET.get('provider', '').strip()

    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | 
            Q(ip_address__icontains=search_query) |
            Q(region__icontains=search_query)
        )

    if status_filter in ['running', 'stopped', 'maintenance']:
        queryset = queryset.filter(status=status_filter)

    if provider_filter in ['aws', 'gcp', 'azure', 'digitalocean', 'local_vps']:
        queryset = queryset.filter(provider=provider_filter)

    # Chỉnh sửa qua query ?edit=<id>
    edit_id = request.GET.get('edit')
    editing_asset = None
    if edit_id:
        editing_asset = get_object_or_404(CloudAsset, id=edit_id, owner=request.user)

    if request.method == 'POST':
        action = request.POST.get('action', 'create')

        if action == 'delete':
            asset_id = request.POST.get('asset_id')
            asset_to_delete = get_object_or_404(CloudAsset, id=asset_id, owner=request.user)
            asset_name = asset_to_delete.name
            asset_to_delete.delete()
            messages.success(request, f'Đã giải phóng máy chủ "{asset_name}" thành công.')
            return redirect('dashboard')

        elif action == 'update':
            asset_id = request.POST.get('asset_id')
            target_asset = get_object_or_404(CloudAsset, id=asset_id, owner=request.user)
            form = CloudAssetForm(request.POST, instance=target_asset)
            if form.is_valid():
                form.save()
                messages.success(request, f'Đã cập nhật cấu hình máy chủ "{target_asset.name}" thành công.')
                return redirect('dashboard')
            else:
                editing_asset = target_asset
                messages.error(request, 'Cập nhật thất bại. Vui lòng kiểm tra lại thông số nhập.')

        else: # create
            form = CloudAssetForm(request.POST)
            if form.is_valid():
                new_asset = form.save(commit=False)
                new_asset.owner = request.user
                new_asset.save()
                messages.success(request, f'Đã khởi tạo máy chủ "{new_asset.name}" thành công.')
                return redirect('dashboard')
            else:
                messages.error(request, 'Khởi tạo thất bại. Vui lòng kiểm tra lại thông số nhập.')
    else:
        if editing_asset:
            form = CloudAssetForm(instance=editing_asset)
        else:
            form = CloudAssetForm()

    # Thống kê toàn diện (trên toàn bộ tài sản của user, độc lập với bộ lọc hiển thị)
    all_user_assets = CloudAsset.objects.filter(owner=request.user)
    total_assets = all_user_assets.count()
    running_assets = all_user_assets.filter(status='running').count()
    stopped_assets = all_user_assets.filter(status='stopped').count()
    maintenance_assets = all_user_assets.filter(status='maintenance').count()

    total_vcpu = all_user_assets.aggregate(total=Sum('cpu_cores'))['total'] or 0
    total_ram = all_user_assets.aggregate(total=Sum('ram_gb'))['total'] or 0
    total_disk = all_user_assets.aggregate(total=Sum('disk_gb'))['total'] or 0
    total_cost = all_user_assets.aggregate(total=Sum('cost_monthly'))['total'] or 0.00

    # Phân bố theo Cloud Provider cho biểu đồ
    provider_counts = {
        'aws': all_user_assets.filter(provider='aws').count(),
        'gcp': all_user_assets.filter(provider='gcp').count(),
        'azure': all_user_assets.filter(provider='azure').count(),
        'digitalocean': all_user_assets.filter(provider='digitalocean').count(),
        'local_vps': all_user_assets.filter(provider='local_vps').count(),
    }

    context = {
        'assets': queryset,
        'form': form,
        'editing_asset': editing_asset,
        'search_query': search_query,
        'status_filter': status_filter,
        'provider_filter': provider_filter,
        'stats': {
            'total': total_assets,
            'running': running_assets,
            'stopped': stopped_assets,
            'maintenance': maintenance_assets,
            'total_vcpu': total_vcpu,
            'total_ram': total_ram,
            'total_disk': total_disk,
            'total_cost': total_cost,
        },
        'chart_data': {
            'status': [running_assets, stopped_assets, maintenance_assets],
            'providers': [
                provider_counts['aws'],
                provider_counts['gcp'],
                provider_counts['azure'],
                provider_counts['digitalocean'],
                provider_counts['local_vps'],
            ]
        }
    }
    return render(request, 'dashboard.html', context)


@login_required
@require_POST
def toggle_power_view(request, asset_id):
    asset = get_object_or_404(CloudAsset, id=asset_id, owner=request.user)
    if asset.status == 'running':
        asset.status = 'stopped'
        messages.warning(request, f'Máy chủ "{asset.name}" đã được tắt nguồn (Stopped).')
    elif asset.status == 'stopped':
        asset.status = 'running'
        messages.success(request, f'Máy chủ "{asset.name}" đã được khởi động (Running).')
    else:
        messages.info(request, f'Máy chủ "{asset.name}" đang trong trạng thái bảo trì.')
    asset.save()
    return redirect('dashboard')


@login_required
@require_POST
def delete_asset_view(request, asset_id):
    asset = get_object_or_404(CloudAsset, id=asset_id, owner=request.user)
    asset_name = asset.name
    asset.delete()
    messages.success(request, f'Đã giải phóng máy chủ "{asset_name}" khỏi hạ tầng.')
    return redirect('dashboard')


@login_required
def export_csv_view(request):
    """Xuất danh sách máy chủ Cloud ra file CSV UTF-8 mở được trên Microsoft Excel"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="cloud_assets_inventory.csv"'

    # Ghi UTF-8 BOM để Excel hiển thị tiếng Việt chuẩn
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Tên Máy Chủ', 'Địa Chỉ IP', 'Nhà Cung Cấp', 
        'Vùng (Region)', 'Hệ Điều Hành', 'vCPU', 'RAM (GB)', 
        'Ổ Cứng SSD (GB)', 'Chi Phí ($/tháng)', 'Trạng Thái', 'Ngày Khởi Tạo'
    ])

    assets = CloudAsset.objects.filter(owner=request.user).order_by('-created_at')
    for a in assets:
        writer.writerow([
            a.id,
            a.name,
            a.ip_address,
            a.get_provider_display(),
            a.region,
            a.get_os_type_display(),
            a.cpu_cores,
            a.ram_gb,
            a.disk_gb,
            f"{a.cost_monthly:.2f}",
            a.get_status_display(),
            a.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Đổi mật khẩu thành công!')
            return redirect('profile')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin mật khẩu cũ và mới.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'profile.html', {'form': form})
