# CLOUDOPS CONSOLE - ENTERPRISE MULTI-CLOUD MANAGEMENT PLATFORM

> **Nền tảng:** Django 6.x (Python 3.12+)  
> **Cơ sở dữ liệu:** MySQL 8.0+ (Production) / SQLite3 (Local Dev Fallback)  
> **Máy chủ triển khai thực tế:** Ubuntu Server 24.04 LTS  
> - **Hostname:** `vps-2324802010207`  
> - **IP tĩnh:** `192.168.100.10`  
> - **User hệ thống:** `sv2324802010207`  
> - **Thư mục ứng dụng:** `/home/sv2324802010207/cloud_manager`  
> **Kiến trúc:** Nginx Reverse Proxy & Static Cache &bull; Gunicorn WSGI Daemon &bull; MySQL Internal Loopback &bull; UFW Security Firewall

---

## 1. Giới Thiệu Hệ Thống

**CloudOps Console** là nền tảng quản trị và điều phối hạ tầng đám mây đa nhà cung cấp (Multi-Cloud: AWS, Google Cloud, Microsoft Azure, DigitalOcean, On-Premise). Hệ thống cung cấp bảng điều khiển trung tâm giúp kỹ sư DevOps, Cloud Architect và quản trị viên hệ thống giám sát tài nguyên tính toán (Compute / vCPU), bộ nhớ (RAM), lưu trữ (SSD) và dự toán chi phí vận hành hàng tháng theo thời gian thực.

### Các Tính Năng Trọng Tâm:
- **Quản Trị Vòng Đời Máy Chủ Toàn Diện (Full Lifecycle CRUD):**
  - Khởi tạo (Deploy), xem chi tiết (Inspect), cập nhật cấu hình phần cứng (Resize/Update), và giải phóng máy chủ (Terminate/Delete).
  - Tác vụ nguồn nhanh một chạm (**One-click Quick Power Toggle**): Bật / Tắt máy chủ tức thì (`Running` &harr; `Stopped`).
- **Thống Kê Đa Chiều & Trực Quan Hóa (Visual Analytics):**
  - Thẻ chỉ số tổng hợp: Tổng số máy chủ, tổng công suất CPU (vCPU), tổng dung lượng RAM (GB), tổng bộ nhớ SSD và tổng chi phí dự toán hàng tháng ($).
  - Tích hợp biểu đồ tương tác thời gian thực (**Chart.js**): Biểu đồ Doughnut phân bố tình trạng máy chủ và Biểu đồ cột phân bố tài nguyên giữa các nhà cung cấp Cloud.
- **Tìm Kiếm & Bộ Lọc Đa Tiêu Chí (Multi-Filter & Instant Search):**
  - Tìm kiếm linh hoạt theo Tên máy chủ, Địa chỉ IP Public/Private, Khu vực Datacenter (Region).
  - Lọc nhanh theo Trạng thái vận hành (`Running`, `Stopped`, `Maintenance`) và Nhà cung cấp Cloud.
- **Trích Xuất Dữ Liệu Kiểm Kê (Data Export):**
  - Xuất toàn bộ danh mục tài nguyên ra định dạng `.csv` hỗ trợ UTF-8 BOM, tương thích hoàn hảo với Microsoft Excel và các công cụ BI.
- **Bảo Mật & Phân Quyền Đa Người Dùng (Multi-Tenant Security):**
  - Xác thực an toàn với cơ chế băm mật khẩu PBKDF2 của Django.
  - Phân tách dữ liệu: Mỗi tài khoản chỉ quản lý tài nguyên thuộc quyền sở hữu của chính mình.
  - Chức năng đổi mật khẩu quản trị và quản lý tài khoản trực tiếp trên Console.

---

## 2. Kiến Trúc Triển Khai Thực Tế Trên VPS

Mô hình triển khai chuẩn Doanh nghiệp nhiều lớp (Multi-tier Enterprise Architecture) trên máy chủ `vps-2324802010207`:

```
[ Client / Web Browser / Admin Workstation (192.168.100.x) ]
                            │
                            ├────────────────────────────────┐
                            │ (Port 80 HTTP)                 │ (Port 22 SSH nội bộ)
                            ▼                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Ubuntu Server 24.04 LTS (Hostname: vps-2324802010207)                 │
│  IP Tĩnh: 192.168.100.10 &bull; User: sv2324802010207                  │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ UFW Firewall Rules:                                              │  │
│  │ - SSH: Allow from 192.168.100.0/24 to any port 22                │  │
│  │ - Web: Allow 80/tcp                                              │  │
│  │ - Default: Deny all other incoming traffic                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                          │                                             │
│                          ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Nginx (Reverse Proxy & Static Files Cache)                       │  │
│  │ - Phục vụ tệp tĩnh: /home/sv2324802010207/cloud_manager/        │  │
│  │                     staticfiles/                                 │  │
│  │ - Chuyển tiếp Request động sang Gunicorn Socket                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                          │ Unix Domain Socket                          │
│                          │ (/run/gunicorn.sock)                        │
│                          ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Gunicorn WSGI Server (Systemd Service)                           │  │
│  │ - User: sv2324802010207 | Group: www-data                        │  │
│  │ - WorkingDir: /home/sv2324802010207/cloud_manager                │  │
│  │ - Chạy ứng dụng Django trong môi trường ảo venv                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                          │ TCP 127.0.0.1:3306                          │
│                          ▼ (Loopback Only)                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ MySQL Server 8.0+                                                │  │
│  │ - Database: cloud_asset_db (Charset: utf8mb4)                    │  │
│  │ - User: app_user (Chỉ kết nối từ 127.0.0.1)                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Cấu Trúc Thư Mục Dự Án

```
cloud_manager/
├── assets/                     # Core App quản trị tài nguyên Cloud
│   ├── migrations/             # Lịch sử lược đồ Database
│   ├── admin.py                # Giao diện Django Admin
│   ├── apps.py                 # Khai báo cấu hình App
│   ├── forms.py                # Forms: Login, Register, CloudAsset
│   ├── models.py               # Data Models: CloudAsset (Provider, Specs, Region...)
│   ├── tests.py                # Bộ Test Suites tự động
│   ├── urls.py                 # Định tuyến route nội bộ của App
│   └── views.py                # Xử lý Logic CRUD, Thống kê, Export CSV, Power Toggle
├── config/                     # Thiết lập toàn cục của dự án
│   ├── settings.py             # Cấu hình dotenv, database fallback, static, templates
│   ├── urls.py                 # URL Resolver cấp dự án
│   └── wsgi.py                 # WSGI Gateway cho Gunicorn
├── templates/                  # Giao diện điều khiển (Bootstrap 5 & Chart.js)
│   ├── base.html               # Layout chuẩn Enterprise Console
│   ├── dashboard.html          # Dashboard chính (Metrics, Charts, CRUD, Power Control)
│   ├── login.html              # Trang đăng nhập
│   ├── profile.html            # Trang quản lý bảo mật và đổi mật khẩu
│   └── register.html           # Trang đăng ký người dùng mới
├── .env.example                # Bản mẫu khai báo biến môi trường chuẩn
├── .gitignore                  # Danh sách loại trừ commit Git
├── manage.py                   # Django CLI tool
├── requirements.txt            # Thư viện phụ thuộc
└── README.md                   # Tài liệu kỹ thuật triển khai dự án
```

---

## 4. Hướng Dẫn Chạy Thử Nghiệm Tại Máy Cục Bộ (Local Development)

Hệ thống tích hợp sẵn **cơ chế Fallback CSDL thông minh**:
- Khi biến `DB_NAME` chưa được khai báo trong `.env`, ứng dụng sẽ tự động chuyển sang sử dụng `sqlite3` giúp lập trình viên kiểm thử nhanh gọn.

### 1. Kích hoạt môi trường ảo:
- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Linux / macOS:**
  ```bash
  source venv/bin/activate
  ```

### 2. Cài đặt các gói phụ thuộc:
```bash
pip install -r requirements.txt
```

### 3. Áp dụng lược đồ CSDL:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Chạy kiểm thử tự động (Unit Tests):
```bash
python manage.py test
```

### 5. Khởi chạy máy chủ phát triển:
```bash
python manage.py runserver 127.0.0.1:8000
```
Truy cập vào bảng điều khiển: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 5. Hướng Dẫn Triển Khai Thực Tế Trên VPS (`vps-2324802010207`)

### Bước 1: Chuẩn bị hệ điều hành và gói hệ thống
Đăng nhập SSH vào máy chủ VPS bằng tài khoản `sv2324802010207`:
```bash
ssh sv2324802010207@192.168.100.10
```
Cập nhật hệ điều hành và cài đặt các gói phụ thuộc:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv python3-dev \
    default-libmysqlclient-dev build-essential pkg-config \
    mysql-server nginx git ufw
```

---

### Bước 2: Thiết lập Cơ sở dữ liệu MySQL nội bộ
```bash
sudo systemctl enable --now mysql
sudo mysql
```

Thực thi trong MySQL Console:
```sql
CREATE DATABASE cloud_asset_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'StrongProductionPassword@2026';
GRANT ALL PRIVILEGES ON cloud_asset_db.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

### Bước 3: Đưa mã nguồn vào thư mục `/home/sv2324802010207/cloud_manager`
Tạo thư mục ứng dụng và phân quyền:
```bash
mkdir -p /home/sv2324802010207/cloud_manager
cd /home/sv2324802010207/cloud_manager

# Clone mã nguồn từ GitHub hoặc copy source code vào đây
# git clone <URL_REPO_GITHUB> .
```

Khởi tạo môi trường ảo Python và cài đặt thư viện:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Bước 4: Thiết lập file môi trường `.env` Production
Tạo file `.env` từ file mẫu:
```bash
cp .env.example .env
nano .env
```
Nội dung file `.env`:
```ini
SECRET_KEY=prod-cloudops-secret-key-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=192.168.100.10,localhost,127.0.0.1

DB_NAME=cloud_asset_db
DB_USER=app_user
DB_PASSWORD=StrongProductionPassword@2026
DB_HOST=127.0.0.1
DB_PORT=3306
```

---

### Bước 5: Chạy Migration và Thu gom tệp tĩnh (Static Files)
Trong môi trường ảo `venv`:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
```

---

### Bước 6: Cấu hình Gunicorn Systemd Service

Tạo socket:
```bash
sudo nano /etc/systemd/system/gunicorn.socket
```
```ini
[Unit]
Description=Gunicorn socket for CloudOps Console

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

Tạo service cho user `sv2324802010207`:
```bash
sudo nano /etc/systemd/system/gunicorn.service
```
```ini
[Unit]
Description=Gunicorn daemon for CloudOps Console
Requires=gunicorn.socket
After=network.target

[Service]
User=sv2324802010207
Group=www-data
WorkingDirectory=/home/sv2324802010207/cloud_manager
ExecStart=/home/sv2324802010207/cloud_manager/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Cấp quyền cho group `www-data` truy cập vào thư mục home và static:
```bash
chmod 755 /home/sv2324802010207
```

Khởi động và kích hoạt Gunicorn:
```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl status gunicorn.socket
```

---

### Bước 7: Cấu hình Nginx Reverse Proxy

Tạo file cấu hình site:
```bash
sudo nano /etc/nginx/sites-available/cloudops
```
```nginx
server {
    listen 80;
    server_name 192.168.100.10 localhost;

    client_max_body_size 25M;

    # Phục vụ tệp tĩnh trực tiếp từ thư mục của user sv2324802010207
    location /static/ {
        alias /home/sv2324802010207/cloud_manager/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }

    # Chuyển tiếp request động sang socket Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Kích hoạt site và khởi động lại Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/cloudops /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Bước 8: Thiết lập Tường lửa UFW (Bảo Mật Tối Đa)

Chỉ cho phép quản trị SSH từ dải mạng nội bộ và mở cổng HTTP:
```bash
# Chỉ cho phép kết nối SSH từ dải mạng nội bộ 192.168.100.0/24
sudo ufw allow from 192.168.100.0/24 to any port 22

# Cho phép truy cập cổng Web HTTP
sudo ufw allow 80/tcp

# Bật tường lửa UFW
sudo ufw enable
sudo ufw status verbose
```

---

## 6. Bảo Trì & Giám Sát Sau Triển Khai

- **Kiểm tra trạng thái dịch vụ:**
  ```bash
  sudo systemctl status gunicorn.socket
  sudo systemctl status gunicorn.service
  sudo systemctl status nginx
  ```
- **Xem nhật ký trực tiếp:**
  ```bash
  sudo journalctl -u gunicorn -f
  sudo tail -f /var/log/nginx/error.log
  ```
- **Quy trình cập nhật mã nguồn (CI/CD / Manual):**
  ```bash
  cd /home/sv2324802010207/cloud_manager
  git pull
  source venv/bin/activate
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py collectstatic --noinput
  sudo systemctl restart gunicorn
  ```
