from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import CloudAsset

class CloudAssetAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'devops_admin'
        self.password = 'SecurePassword123@'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_register_user(self):
        # Đăng ký tài khoản mới thành công
        response = self.client.post(reverse('register'), {
            'username': 'cloud_engineer',
            'email': 'engineer@cloudops.io',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='cloud_engineer').exists())

        # Kiểm tra trùng username
        response_dup = self.client.post(reverse('register'), {
            'username': 'cloud_engineer',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        self.assertEqual(response_dup.status_code, 200)
        self.assertContains(response_dup, 'đã được sử dụng')

    def test_login_and_logout(self):
        login_success = self.client.login(username=self.username, password=self.password)
        self.assertTrue(login_success)

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CloudOps')

        logout_response = self.client.get(reverse('logout'))
        self.assertEqual(logout_response.status_code, 302)

    def test_crud_and_power_toggle(self):
        self.client.login(username=self.username, password=self.password)

        # 1. Khởi tạo máy chủ (Create)
        response_create = self.client.post(reverse('dashboard'), {
            'action': 'create',
            'name': 'prod-k8s-master',
            'ip_address': '54.254.10.20',
            'provider': 'aws',
            'region': 'ap-southeast-1 (Singapore)',
            'os_type': 'ubuntu',
            'cpu_cores': 4,
            'ram_gb': 16,
            'disk_gb': 100,
            'cost_monthly': 85.00,
            'status': 'running'
        })
        self.assertEqual(response_create.status_code, 302)
        asset = CloudAsset.objects.filter(name='prod-k8s-master', owner=self.user).first()
        self.assertIsNotNone(asset)
        self.assertEqual(asset.ip_address, '54.254.10.20')
        self.assertEqual(asset.provider, 'aws')

        # 2. Xem danh sách (Read)
        response_read = self.client.get(reverse('dashboard'))
        self.assertEqual(response_read.status_code, 200)
        self.assertContains(response_read, 'prod-k8s-master')
        self.assertContains(response_read, '54.254.10.20')

        # 3. Cập nhật cấu hình (Update)
        response_update = self.client.post(reverse('dashboard'), {
            'action': 'update',
            'asset_id': asset.id,
            'name': 'prod-k8s-master-scaled',
            'ip_address': '54.254.10.20',
            'provider': 'aws',
            'region': 'ap-southeast-1 (Singapore)',
            'os_type': 'ubuntu',
            'cpu_cores': 8,
            'ram_gb': 32,
            'disk_gb': 200,
            'cost_monthly': 160.00,
            'status': 'running'
        })
        self.assertEqual(response_update.status_code, 302)
        asset.refresh_from_db()
        self.assertEqual(asset.name, 'prod-k8s-master-scaled')
        self.assertEqual(asset.cpu_cores, 8)
        self.assertEqual(asset.ram_gb, 32)

        # 4. Thao tác nguồn nhanh (Toggle Power: Running -> Stopped)
        response_power = self.client.post(reverse('toggle_power', args=[asset.id]))
        self.assertEqual(response_power.status_code, 302)
        asset.refresh_from_db()
        self.assertEqual(asset.status, 'stopped')

        # 5. Xuất danh sách CSV (Export CSV)
        response_csv = self.client.get(reverse('export_csv'))
        self.assertEqual(response_csv.status_code, 200)
        self.assertEqual(response_csv['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('prod-k8s-master-scaled', response_csv.content.decode('utf-8'))

        # 6. Giải phóng máy chủ (Delete)
        response_delete = self.client.post(reverse('delete_asset', args=[asset.id]))
        self.assertEqual(response_delete.status_code, 302)
        self.assertFalse(CloudAsset.objects.filter(id=asset.id).exists())
