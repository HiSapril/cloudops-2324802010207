from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .models import CloudAsset, StorageSnapshot


class CloudAssetAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'devops_user'
        self.password = 'SecurePassword123@'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.admin_user = User.objects.create_user(
            username='cloud_admin', password=self.password, is_staff=True
        )

    def test_argon2_password_hashing(self):
        self.assertTrue(self.user.password.startswith('argon2$'))

    def test_register_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'cloud_engineer',
            'email': 'engineer@cloudops.io',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)
        created = User.objects.get(username='cloud_engineer')
        self.assertTrue(created.password.startswith('argon2$'))

        response_dup = self.client.post(reverse('register'), {
            'username': 'cloud_engineer',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        self.assertEqual(response_dup.status_code, 200)
        self.assertContains(response_dup, 'đã được sử dụng')

    def test_login_and_logout(self):
        self.assertTrue(self.client.login(username=self.username, password=self.password))
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2324802010207')

        logout_response = self.client.get(reverse('logout'))
        self.assertEqual(logout_response.status_code, 302)

    def test_crud_validation_and_power_toggle(self):
        self.client.login(username=self.username, password=self.password)

        # Validation: invalid IP should fail
        bad_resp = self.client.post(reverse('dashboard'), {
            'action': 'create',
            'name': 'bad-ip-server',
            'ip_address': '999.999.999.999',
            'provider': 'aws',
            'region': 'ap-southeast-1',
            'os_type': 'ubuntu',
            'cpu_cores': 2,
            'ram_gb': 4,
            'disk_gb': 20,
            'cost_monthly': 10.00,
            'status': 'running',
        })
        self.assertEqual(bad_resp.status_code, 200)
        self.assertFalse(CloudAsset.objects.filter(name='bad-ip-server').exists())

        # Create valid asset
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

        # Update
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
        self.assertEqual(asset.cpu_cores, 8)

        # Toggle Power
        self.client.post(reverse('toggle_power', args=[asset.id]))
        asset.refresh_from_db()
        self.assertEqual(asset.status, 'stopped')

        # Export CSV
        response_csv = self.client.get(reverse('export_csv'))
        self.assertEqual(response_csv.status_code, 200)
        self.assertIn('prod-k8s-master-scaled', response_csv.content.decode('utf-8'))

        # Delete
        self.client.post(reverse('delete_asset', args=[asset.id]))
        self.assertFalse(CloudAsset.objects.filter(id=asset.id).exists())

    def test_role_based_access_and_admin_overview(self):
        CloudAsset.objects.create(owner=self.user, name='user-only-vps', ip_address='10.10.10.11')
        CloudAsset.objects.create(owner=self.admin_user, name='admin-only-vps', ip_address='10.10.10.12')

        # Normal user cannot see admin_overview or admin's asset
        self.client.login(username=self.username, password=self.password)
        resp_user_dash = self.client.get(reverse('dashboard'))
        self.assertContains(resp_user_dash, 'user-only-vps')
        self.assertNotContains(resp_user_dash, 'admin-only-vps')
        resp_admin_page = self.client.get(reverse('admin_overview'))
        self.assertEqual(resp_admin_page.status_code, 302)

        # Admin sees all assets and admin_overview
        self.client.login(username='cloud_admin', password=self.password)
        resp_admin_dash = self.client.get(reverse('dashboard'))
        self.assertContains(resp_admin_dash, 'user-only-vps')
        self.assertContains(resp_admin_dash, 'admin-only-vps')
        self.assertEqual(self.client.get(reverse('admin_overview')).status_code, 200)

    def test_storage_snapshot_crud_and_upload_validation(self):
        self.client.login(username=self.username, password=self.password)

        # Disallowed file extension (.exe) must be rejected
        bad_file = SimpleUploadedFile('malware.exe', b'binarydata', content_type='application/octet-stream')
        bad_resp = self.client.post(reverse('snapshots'), {
            'action': 'create',
            'name': 'bad-upload',
            'storage_type': 'config',
            'bucket_region': 'vn-hcm-01',
            'size_mb': '1.00',
            'status': 'available',
            'config_file': bad_file,
        })
        self.assertEqual(bad_resp.status_code, 200)
        self.assertFalse(StorageSnapshot.objects.filter(name='bad-upload').exists())

        # Valid .conf upload
        good_file = SimpleUploadedFile('nginx.conf', b'server { listen 80; }', content_type='text/plain')
        good_resp = self.client.post(reverse('snapshots'), {
            'action': 'create',
            'name': 'nginx-prod-conf',
            'storage_type': 'config',
            'bucket_region': 'vn-hcm-01',
            'size_mb': '0.01',
            'status': 'available',
            'config_file': good_file,
        })
        self.assertEqual(good_resp.status_code, 302)
        snap = StorageSnapshot.objects.get(name='nginx-prod-conf')
        self.assertTrue(bool(snap.config_file))

        # Delete snapshot
        del_resp = self.client.post(reverse('delete_snapshot', args=[snap.id]))
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(StorageSnapshot.objects.filter(id=snap.id).exists())

    def test_rest_api_endpoints(self):
        api = APIClient()

        # Public health check
        health = api.get('/api/health/')
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.data['status'], 'ok')
        self.assertEqual(health.data['mssv'], '2324802010207')

        # Unauthenticated assets request rejected
        self.assertEqual(api.get('/api/assets/').status_code, 401)

        # Token auth
        token_resp = api.post('/api/auth/token/', {'username': self.username, 'password': self.password})
        self.assertEqual(token_resp.status_code, 200)
        token = token_resp.data['token']

        api.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        create_resp = api.post('/api/assets/', {
            'name': 'api-vps-01',
            'ip_address': '10.10.10.10',
            'provider': 'local_vps',
            'os_type': 'ubuntu',
            'region': 'vn-hcm-01',
            'cpu_cores': 2,
            'ram_gb': 2,
            'disk_gb': 20,
            'cost_monthly': '0.00',
            'status': 'running',
        }, format='json')
        self.assertEqual(create_resp.status_code, 201)

        list_resp = api.get('/api/assets/?search=api-vps-01')
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.data['count'], 1)
