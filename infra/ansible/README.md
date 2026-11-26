# Infrastructure as Code (Ansible) - CloudOps Console (MSSV: 2324802010207)

Thư mục này chứa mã cấu hình tự động hóa hạ tầng bằng **Ansible** cho 2 VPS:
- `web-2324802010207` (`10.10.10.10` / `10.10.20.10`)
- `db-2324802010207` (`10.10.20.20`)

## Cách chạy:
1. Cập nhật IP Tailscale của 2 VPS vào `inventory.ini`.
2. Kiểm tra kết nối:
   ```bash
   ansible all -i inventory.ini -m ping
   ```
3. Chạy playbook:
   ```bash
   ansible-playbook -i inventory.ini playbook.yml
   ```
