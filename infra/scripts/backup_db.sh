#!/bin/bash
# Script sao lưu tự động MySQL trên db-2324802010207 và đồng bộ sang web-2324802010207 (10.10.20.10)
set -euo pipefail

BACKUP_DIR="/home/sv2324802010207/backups"
REMOTE_USER="sv2324802010207"
REMOTE_HOST="10.10.20.10"
REMOTE_DIR="/home/sv2324802010207/db_backups"
DB_NAME="cloud_asset_db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

# Sao lưu dữ liệu bằng cấu hình ~/.my.cnf (không lưu mật khẩu trong script)
mysqldump --single-transaction --routines --triggers "${DB_NAME}" | gzip > "${BACKUP_FILE}"

# Chuyển bản sao lưu sang máy khác qua mạng nội bộ vùng DB (10.10.20.0/24)
ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ${REMOTE_DIR}"
scp -o StrictHostKeyChecking=no "${BACKUP_FILE}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"

# Dọn dẹp bản sao lưu cũ hơn 7 ngày
find "${BACKUP_DIR}" -type f -name "*.sql.gz" -mtime +7 -delete

echo "[$(date)] Backup completed and synced to ${REMOTE_HOST}: ${BACKUP_FILE}"
