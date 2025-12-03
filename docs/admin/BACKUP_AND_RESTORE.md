# 备份与恢复指南

> LAUNCH-1 L4-3 实现

## 概述

VabHub 提供配置导出和用户数据导出功能，方便 NAS 用户在重装/迁移时保留重要数据。

## 备份内容

### 配置导出 (`/api/backup/export/config`)

包含：
- 全局配置（敏感字段已脱敏）
- 漫画源配置
- 音乐榜单源配置

### 用户数据导出 (`/api/backup/export/user_data`)

包含：
- 用户基本信息
- 阅读进度（小说、漫画）
- 追更设置
- 收藏数据

## 使用方法

### 通过 API 导出

```bash
# 获取 Token
TOKEN=$(curl -s -X POST http://localhost:8092/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=yourpassword" | jq -r '.data.access_token')

# 导出配置
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8092/api/backup/export/config > config_backup.json

# 导出用户数据
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8092/api/backup/export/user_data > user_data_backup.json

# 导出特定用户数据
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8092/api/backup/export/user_data?user_id=1" > user_1_backup.json
```

### 定时备份（推荐）

在 NAS 上创建 cron 任务：

```bash
# /etc/cron.d/vabhub-backup
0 3 * * * root /opt/vabhub/scripts/backup.sh >> /var/log/vabhub-backup.log 2>&1
```

备份脚本示例：

```bash
#!/bin/bash
# /opt/vabhub/scripts/backup.sh

BACKUP_DIR="/data/backups/vabhub"
DATE=$(date +%Y%m%d)
TOKEN="your_api_token"

mkdir -p "$BACKUP_DIR"

# 导出配置
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8092/api/backup/export/config > "$BACKUP_DIR/config_$DATE.json"

# 导出用户数据
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8092/api/backup/export/user_data > "$BACKUP_DIR/user_data_$DATE.json"

# 备份数据库
cp /opt/vabhub/data/vabhub.db "$BACKUP_DIR/vabhub_$DATE.db"

# 保留最近 7 天的备份
find "$BACKUP_DIR" -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

## 恢复指南

### 数据库恢复

```bash
# 停止服务
docker-compose stop vabhub

# 恢复数据库
cp /data/backups/vabhub/vabhub_20241201.db /opt/vabhub/data/vabhub.db

# 重启服务
docker-compose start vabhub
```

### 配置恢复

目前配置恢复需要手动操作：

1. 查看导出的 `config_backup.json`
2. 根据内容修改 `.env` 文件
3. 重启服务

### 用户数据恢复

用户数据恢复需要通过数据库导入：

1. 查看 `user_data_backup.json` 中的数据
2. 使用数据库工具导入到对应表

> **TODO**: 未来版本将提供自动恢复 API

## 最佳实践

1. **定期备份**: 建议每天备份一次
2. **异地存储**: 将备份文件同步到其他存储设备
3. **验证备份**: 定期检查备份文件是否完整
4. **版本管理**: 保留多个版本的备份

## 相关文档

- [安装指南](./INSTALL_GUIDE.md)
- [Runner 配置指南](./RUNNERS_OVERVIEW.md)
