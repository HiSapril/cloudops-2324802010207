# CloudOps Console — Hệ thống Quản lý Hạ tầng & Lưu trữ Đám mây

> **Sinh viên thực hiện:** Phạm Minh Đức — MSSV: `2324802010207`  
> **Tên miền công khai:** [`https://app.duc.id.vn`](https://app.duc.id.vn) | [`https://api.duc.id.vn/api/health/`](https://api.duc.id.vn/api/health/) | [`https://status.duc.id.vn/status/cloudops`](https://status.duc.id.vn/status/cloudops)

---

## 1. Kiến trúc tổng thể
Hệ thống được xây dựng trên nền tảng **VMware ESXi 8.0** với mô hình **2 vùng mạng tách biệt** và **2 VPS IP tĩnh**:

| Thành phần | Tên máy / Mạng | IP tĩnh / Dải mạng | Dịch vụ chính |
| :--- | :--- | :--- | :--- |
| **Vùng Web** | `Net-Web` (`vSwitch-Web`) | `10.10.10.0/24` | Vùng máy chủ ứng dụng |
| **Vùng Dữ liệu** | `Net-DB` (`vSwitch-DB`) | `10.10.20.0/24` | Vùng cô lập cơ sở dữ liệu |
| **VPS Web** | `web-2324802010207` | `10.10.10.10`, `10.10.20.10` | Nginx, Django + DRF (Gunicorn `127.0.0.1:8000`), Uptime Kuma (Docker `:3001`), `cloudflared`, Tailscale, GitHub Self-hosted Runner |
| **VPS DB** | `db-2324802010207` | `10.10.20.20` | MySQL 8.0 (chỉ lắng nghe `10.10.20.20:3306`), Tailscale, `backup_db.sh` (Cron 02:00) |

- **Đường vào người dùng (Internet):** `https://app.duc.id.vn`, `https://api.duc.id.vn`, `https://status.duc.id.vn` → **Cloudflare Tunnel** → Nginx trên `web-2324802010207`.
- **Đường vào quản trị:** Laptop quản trị → **Tailscale VPN** (`100.64.0.0/10`) → SSH bằng khóa (cấm `root`, tắt mật khẩu).

---

## 2. Tính năng ứng dụng Web & API
- **Xác thực & Bảo mật:** Đăng ký, đăng nhập, đổi mật khẩu; băm mật khẩu bằng **Argon2** (`Argon2PasswordHasher`); kiểm tra đầu vào cả frontend & backend; bí mật tách ra `.env`.
- **Phân quyền 2 vai trò:**
  - `Admin` (`is_staff`): Xem và quản lý toàn bộ tài nguyên hệ thống, phân quyền người dùng tại `/admin-overview/`.
  - `User`: Chỉ thao tác trên tài nguyên của chính mình.
- **2 đối tượng nghiệp vụ (CRUD + Tìm kiếm + Phân trang):**
  1. `CloudAsset` (`/`): Quản lý máy chủ ảo đa đám mây, bật/tắt nguồn, thống kê Chart.js, xuất CSV.
  2. `StorageSnapshot` (`/snapshots/`): Quản lý tệp cấu hình, bản sao lưu DB, snapshot kèm **upload tệp** (giới hạn đuôi hợp lệ & ≤ 10 MB).
- **REST API (`/api/`):** `GET /api/health/`, `POST /api/auth/token/`, `/api/assets/`, `/api/snapshots/`.

---

## 3. Cấu trúc thư mục dự án
```text
.
├── .github/workflows/deploy.yml   # CI/CD: chạy unit/API test & tự động deploy lên web-2324802010207
├── assets/                        # App chính: models, forms, views, serializers, api_views, tests
├── config/                        # Cấu hình Django, Argon2, DRF, CORS, MySQL/SQLite fallback
├── infra/
│   ├── ansible/                   # IaC: inventory.ini, playbook.yml, Nginx & Gunicorn Jinja2 templates
│   └── scripts/backup_db.sh       # Script sao lưu MySQL tự động & đồng bộ sang web-2324802010207
├── templates/                     # Giao diện Bootstrap 5 (dashboard, snapshots, admin_overview, auth)
├── .env.example                   # Mẫu biến môi trường (không chứa bí mật thật)
├── manage.py
└── requirements.txt
```

---

## 4. Hướng dẫn dựng lại hệ thống từ đầu

### Bước 1: Dựng 2 VPS & chạy Ansible (IaC)
1. Trên ESXi, tạo 2 Port Group `Net-Web`, `Net-DB` và `datastore2-2324802010207`.
2. Tạo `web-2324802010207` và `db-2324802010207` (Ubuntu Server, user `sv2324802010207`), cấu hình IP tĩnh Netplan và cài Tailscale.
3. Chạy Ansible Playbook để tự động cấu hình SSH hardening, Fail2ban, `unattended-upgrades`, UFW 2 lớp, MySQL, Nginx và Gunicorn:
   ```bash
   cd infra/ansible
   ansible-playbook -i inventory.ini playbook.yml --ask-become-pass
   ```

### Bước 2: Khởi tạo Database trên `db-2324802010207`
```sql
CREATE DATABASE cloud_asset_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'app_user'@'10.10.20.10' IDENTIFIED BY '<MAT_KHAU_MANH>';
GRANT ALL PRIVILEGES ON cloud_asset_db.* TO 'app_user'@'10.10.20.10';
FLUSH PRIVILEGES;
```

### Bước 3: Triển khai Django trên `web-2324802010207`
```bash
git clone https://github.com/HiSapril/cloudops-2324802010207.git ~/cloud_manager
cd ~/cloud_manager
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Điền SECRET_KEY, DB_HOST=10.10.20.20, DB_PASSWORD...
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
sudo systemctl enable --now gunicorn nginx
```

### Bước 4: Kiểm thử tự động (Local / CI)
```bash
python manage.py test
```
*(Chế độ local chưa khai báo `DB_NAME` trong `.env` sẽ tự động dùng SQLite3).*
