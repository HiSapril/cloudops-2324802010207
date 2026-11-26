import csv
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Sum, Q
from .models import CloudAsset, StorageSnapshot
from .forms import RegisterForm, LoginForm, CloudAssetForm, StorageSnapshotForm


def _is_admin(user):
    return bool(user.is_staff or user.is_superuser)


def _scoped_queryset(model, user):
    if _is_admin(user):
        return model.objects.select_related('owner').all()
    return model.objects.select_related('owner').filter(owner=user)


def _get_object_for_user(model, obj_id, user):
    if _is_admin(user):
        return get_object_or_404(model, id=obj_id)
    return get_object_or_404(model, id=obj_id, owner=user)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data.get('email', '')
            password = form.cleaned_data['password']
            User.objects.create_user(username=username, email=email, password=password)
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
    queryset = _scoped_queryset(CloudAsset, request.user)

    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    provider_filter = request.GET.get('provider', '').strip()

    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(ip_address__icontains=search_query) |
            Q(region__icontains=search_query) |
            Q(owner__username__icontains=search_query)
        )

    if status_filter in ['running', 'stopped', 'maintenance']:
        queryset = queryset.filter(status=status_filter)

    if provider_filter in ['aws', 'gcp', 'azure', 'digitalocean', 'local_vps']:
        queryset = queryset.filter(provider=provider_filter)

    edit_id = request.GET.get('edit')
    editing_asset = _get_object_for_user(CloudAsset, edit_id, request.user) if edit_id else None

    if request.method == 'POST':
        action = request.POST.get('action', 'create')

        if action == 'delete':
            asset_id = request.POST.get('asset_id')
            asset_to_delete = _get_object_for_user(CloudAsset, asset_id, request.user)
            asset_name = asset_to_delete.name
            asset_to_delete.delete()
            messages.success(request, f'Đã giải phóng máy chủ "{asset_name}" thành công.')
            return redirect('dashboard')

        elif action == 'update':
            asset_id = request.POST.get('asset_id')
            target_asset = _get_object_for_user(CloudAsset, asset_id, request.user)
            form = CloudAssetForm(request.POST, instance=target_asset)
            if form.is_valid():
                form.save()
                messages.success(request, f'Đã cập nhật cấu hình máy chủ "{target_asset.name}" thành công.')
                return redirect('dashboard')
            else:
                editing_asset = target_asset
                messages.error(request, 'Cập nhật thất bại. Vui lòng kiểm tra lại thông số nhập.')

        else:
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
        form = CloudAssetForm(instance=editing_asset) if editing_asset else CloudAssetForm()

    # Phân trang (6 máy chủ mỗi trang)
    paginator = Paginator(queryset, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    all_scoped_assets = _scoped_queryset(CloudAsset, request.user)
    total_assets = all_scoped_assets.count()
    running_assets = all_scoped_assets.filter(status='running').count()
    stopped_assets = all_scoped_assets.filter(status='stopped').count()
    maintenance_assets = all_scoped_assets.filter(status='maintenance').count()

    total_vcpu = all_scoped_assets.aggregate(total=Sum('cpu_cores'))['total'] or 0
    total_ram = all_scoped_assets.aggregate(total=Sum('ram_gb'))['total'] or 0
    total_disk = all_scoped_assets.aggregate(total=Sum('disk_gb'))['total'] or 0
    total_cost = all_scoped_assets.aggregate(total=Sum('cost_monthly'))['total'] or 0.00

    provider_counts = {
        p: all_scoped_assets.filter(provider=p).count()
        for p in ('aws', 'gcp', 'azure', 'digitalocean', 'local_vps')
    }

    context = {
        'assets': page_obj,
        'page_obj': page_obj,
        'form': form,
        'editing_asset': editing_asset,
        'search_query': search_query,
        'status_filter': status_filter,
        'provider_filter': provider_filter,
        'is_admin': _is_admin(request.user),
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
def snapshots_view(request):
    """Quản lý đối tượng nghiệp vụ 2: Bản lưu trữ cấu hình & Snapshot (CRUD + Upload + Tìm kiếm + Phân trang)."""
    queryset = _scoped_queryset(StorageSnapshot, request.user).select_related('asset')

    search_query = request.GET.get('q', '').strip()
    type_filter = request.GET.get('storage_type', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(bucket_region__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(owner__username__icontains=search_query)
        )

    if type_filter in ['config', 'db_backup', 'vm_snapshot', 'log_archive']:
        queryset = queryset.filter(storage_type=type_filter)

    if status_filter in ['available', 'archived', 'restoring']:
        queryset = queryset.filter(status=status_filter)

    edit_id = request.GET.get('edit')
    editing_snapshot = _get_object_for_user(StorageSnapshot, edit_id, request.user) if edit_id else None

    if request.method == 'POST':
        action = request.POST.get('action', 'create')

        if action == 'update':
            snap_id = request.POST.get('snapshot_id')
            target_snap = _get_object_for_user(StorageSnapshot, snap_id, request.user)
            form = StorageSnapshotForm(request.POST, request.FILES, instance=target_snap, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, f'Đã cập nhật bản lưu trữ "{target_snap.name}" thành công.')
                return redirect('snapshots')
            else:
                editing_snapshot = target_snap
                messages.error(request, 'Cập nhật thất bại. Vui lòng kiểm tra lại dữ liệu hoặc tệp đính kèm.')
        else:
            form = StorageSnapshotForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                new_snap = form.save(commit=False)
                new_snap.owner = request.user
                new_snap.save()
                messages.success(request, f'Đã tạo bản lưu trữ "{new_snap.name}" thành công.')
                return redirect('snapshots')
            else:
                messages.error(request, 'Tạo bản lưu trữ thất bại. Vui lòng kiểm tra lại thông tin.')
    else:
        form = StorageSnapshotForm(instance=editing_snapshot, user=request.user) if editing_snapshot else StorageSnapshotForm(user=request.user)

    paginator = Paginator(queryset, 6)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    all_scoped = _scoped_queryset(StorageSnapshot, request.user)
    context = {
        'snapshots': page_obj,
        'page_obj': page_obj,
        'form': form,
        'editing_snapshot': editing_snapshot,
        'search_query': search_query,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'is_admin': _is_admin(request.user),
        'total_count': all_scoped.count(),
        'total_size_mb': all_scoped.aggregate(total=Sum('size_mb'))['total'] or 0.00,
    }
    return render(request, 'snapshots.html', context)


@login_required
@require_POST
def delete_snapshot_view(request, snapshot_id):
    snap = _get_object_for_user(StorageSnapshot, snapshot_id, request.user)
    snap_name = snap.name
    snap.delete()
    messages.success(request, f'Đã xóa bản lưu trữ "{snap_name}" thành công.')
    return redirect('snapshots')


@login_required
def admin_overview_view(request):
    """Trang quản trị dành riêng cho vai trò Admin (is_staff / is_superuser)."""
    if not _is_admin(request.user):
        messages.error(request, 'Bạn không có quyền truy cập trang Quản trị (yêu cầu vai trò Admin).')
        return redirect('dashboard')

    if request.method == 'POST':
        target_user_id = request.POST.get('user_id')
        target_user = get_object_or_404(User, id=target_user_id)
        if target_user == request.user:
            messages.warning(request, 'Không thể tự hạ quyền của chính mình.')
        else:
            target_user.is_staff = not target_user.is_staff
            target_user.save()
            role_label = 'Admin' if target_user.is_staff else 'User'
            messages.success(request, f'Đã chuyển vai trò của "{target_user.username}" thành {role_label}.')
        return redirect('admin_overview')

    users = User.objects.all().order_by('-is_staff', 'username')
    user_rows = [
        {
            'user': u,
            'asset_count': CloudAsset.objects.filter(owner=u).count(),
            'snapshot_count': StorageSnapshot.objects.filter(owner=u).count(),
        }
        for u in users
    ]
    return render(request, 'admin_overview.html', {
        'user_rows': user_rows,
        'total_assets': CloudAsset.objects.count(),
        'total_snapshots': StorageSnapshot.objects.count(),
        'is_admin': True,
    })


@login_required
@require_POST
def toggle_power_view(request, asset_id):
    asset = _get_object_for_user(CloudAsset, asset_id, request.user)
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
    asset = _get_object_for_user(CloudAsset, asset_id, request.user)
    asset_name = asset.name
    asset.delete()
    messages.success(request, f'Đã giải phóng máy chủ "{asset_name}" khỏi hạ tầng.')
    return redirect('dashboard')


@login_required
def export_csv_view(request):
    """Xuất danh sách máy chủ Cloud ra file CSV UTF-8 mở được trên Microsoft Excel."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="cloud_assets_inventory.csv"'
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Chủ Sở Hữu', 'Tên Máy Chủ', 'Địa Chỉ IP', 'Nhà Cung Cấp',
        'Vùng (Region)', 'Hệ Điều Hành', 'vCPU', 'RAM (GB)',
        'Ổ Cứng SSD (GB)', 'Chi Phí ($/tháng)', 'Trạng Thái', 'Ngày Khởi Tạo'
    ])

    assets = _scoped_queryset(CloudAsset, request.user).order_by('-created_at')
    for a in assets:
        writer.writerow([
            a.id,
            a.owner.username,
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
