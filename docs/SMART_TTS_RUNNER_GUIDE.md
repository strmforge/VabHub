# VabHub TTS Runner 使用指南

## 简介

本文档介绍 VabHub TTS 任务 Runner 和存储清理 Runner 的 CLI 使用说明。

这两个 CLI 工具用于：
- **TTS Job Runner**：批量执行队列中的 TTS 任务
- **TTS Storage Cleanup Runner**：根据策略自动清理 TTS 输出目录

这些工具可以在本地开发环境、生产服务器或通过 systemd timer 定时执行。

## 前置要求

- 需要在与 API 服务相同的虚拟环境 / Docker 容器里运行
- 会使用 `SMART_TTS_*` 配置（例如输出目录、限流设置、自动清理策略）
- 需要访问相同的数据库和文件系统

## 命令说明

### TTS Job Runner

**命令：**
```bash
python -m app.cli.run_tts_jobs [参数]
```

**参数：**
- `--max-jobs N`：单次执行最多处理的 Job 数量（默认：从配置 `SMART_TTS_JOB_RUNNER_MAX_JOBS_PER_RUN` 读取，通常为 5）
- `--no-stop-when-empty`：当没有 queued Job 时不立即退出（默认：无任务时立即退出）

**示例：**
```bash
# 处理最多 5 个 Job
python -m app.cli.run_tts_jobs --max-jobs=5

# 处理最多 10 个 Job
python -m app.cli.run_tts_jobs --max-jobs=10
```

**输出示例：**
```
============================================================
VabHub TTS Job Runner
============================================================
配置：最多处理 5 个 Job
停止策略：无任务时立即退出

2025-01-XX 10:00:00 | INFO     | 开始批量执行 TTS Job，最多处理 5 个
2025-01-XX 10:00:01 | INFO     | 执行 TTS Job 123 (ebook_id=456, status=queued)
2025-01-XX 10:00:15 | INFO     | Job 123 执行成功
...

============================================================
执行结果汇总
============================================================
尝试处理的 Job 数：3
实际执行的 Job 数：3
成功完成的 Job 数：2
部分完成的 Job 数：1（可继续执行）
失败的 Job 数：0
最后处理的 Job ID：125
============================================================
```

### TTS Storage Cleanup Runner

**命令：**
```bash
python -m app.cli.run_tts_storage_cleanup [参数]
```

**参数：**
- `--mode {auto|manual}`：运行模式
  - `auto`（默认）：遵循配置 `SMART_TTS_STORAGE_AUTO_*` 的策略，会检查间隔、警告级别等
  - `manual`：强制执行一次清理，忽略间隔和警告级别检查
- `--dry-run`：预览模式，只计算将要删除的文件和释放空间，不实际删除

**示例：**
```bash
# 自动模式，预览（不实际删除）
python -m app.cli.run_tts_storage_cleanup --mode=auto --dry-run

# 自动模式，实际执行
python -m app.cli.run_tts_storage_cleanup --mode=auto

# 手动模式，强制执行（忽略间隔和警告级别）
python -m app.cli.run_tts_storage_cleanup --mode=manual
```

**输出示例：**
```
============================================================
VabHub TTS Storage Cleanup Runner
============================================================
运行模式：auto
Dry Run：是（仅预览）

2025-01-XX 10:00:00 | INFO     | 开始执行定时自动清理
...

============================================================
执行结果
============================================================
状态：success
删除文件数：42
释放空间：125.50 MB
（预览模式，未实际删除）
开始时间：2025-01-XX 10:00:00
结束时间：2025-01-XX 10:00:05
============================================================
```

## 注意事项

1. **环境一致性**：CLI 工具必须与 API 服务使用相同的：
   - Python 虚拟环境
   - 数据库连接配置
   - 文件系统访问权限
   - TTS 相关配置

2. **配置检查**：
   - TTS Job Runner 需要 `SMART_TTS_ENABLED=True` 和 `SMART_TTS_JOB_RUNNER_ENABLED=True`
   - Storage Cleanup Runner 在 `auto` 模式下需要 `SMART_TTS_STORAGE_AUTO_ENABLED=True`

3. **退出码**：
   - `0`：执行成功
   - `1`：执行失败或发生错误

4. **日志输出**：所有日志输出到标准输出（stdout），适合重定向到日志文件

## systemd 部署示例（宿主机安装场景）

### TTS Job Runner Service

**文件：`/etc/systemd/system/vabhub-tts-jobs.service`**

```ini
[Unit]
Description=VabHub TTS Job Runner
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/vabhub/backend
ExecStart=/opt/vabhub/.venv/bin/python -m app.cli.run_tts_jobs --max-jobs=5
User=vabhub
Group=vabhub
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**文件：`/etc/systemd/system/vabhub-tts-jobs.timer`**

```ini
[Unit]
Description=Run VabHub TTS jobs periodically

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
```

**安装和启用：**
```bash
# 安装 service 和 timer
sudo systemctl daemon-reload
sudo systemctl enable vabhub-tts-jobs.timer
sudo systemctl start vabhub-tts-jobs.timer

# 查看状态
sudo systemctl status vabhub-tts-jobs.timer
sudo systemctl list-timers vabhub-tts-jobs.timer

# 手动触发一次（测试）
sudo systemctl start vabhub-tts-jobs.service
```

**说明：**
- `OnCalendar=*:0/5`：每 5 分钟执行一次
- 可根据实际需求调整频率（例如 `hourly`、`daily`、`*:0/10` 每 10 分钟）

### TTS Storage Cleanup Service

**文件：`/etc/systemd/system/vabhub-tts-storage.service`**

```ini
[Unit]
Description=VabHub TTS Storage Cleanup
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/vabhub/backend
ExecStart=/opt/vabhub/.venv/bin/python -m app.cli.run_tts_storage_cleanup --mode=auto
User=vabhub
Group=vabhub
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**文件：`/etc/systemd/system/vabhub-tts-storage.timer`**

```ini
[Unit]
Description=Run VabHub TTS storage cleanup daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

**安装和启用：**
```bash
# 安装 service 和 timer
sudo systemctl daemon-reload
sudo systemctl enable vabhub-tts-storage.timer
sudo systemctl start vabhub-tts-storage.timer

# 查看状态
sudo systemctl status vabhub-tts-storage.timer
sudo systemctl list-timers vabhub-tts-storage.timer

# 手动触发一次（测试，预览模式）
sudo systemctl start vabhub-tts-storage.service
```

**说明：**
- `OnCalendar=daily`：每天执行一次（默认在 00:00）
- 可改为 `OnCalendar=*-*-* 02:00:00` 指定每天凌晨 2 点执行

### 推荐的运行频率

- **TTS Job Runner**：
  - 开发环境：每 5-10 分钟
  - 生产环境：每 5 分钟（如果任务量大）或每 10-15 分钟（任务量小）
  
- **TTS Storage Cleanup**：
  - 开发环境：每天一次或每周一次
  - 生产环境：每天一次（在低峰时段，如凌晨 2-3 点）

## Docker 场景

如果项目使用 Docker 部署，可以通过以下方式运行：

### 单次执行

```bash
# TTS Job Runner
docker exec <container_name> python -m app.cli.run_tts_jobs --max-jobs=5

# TTS Storage Cleanup（预览）
docker exec <container_name> python -m app.cli.run_tts_storage_cleanup --mode=auto --dry-run
```

### Docker Compose 定时任务

在 `docker-compose.yml` 中可以添加定时任务容器（使用 cron 或类似工具）：

```yaml
services:
  vabhub-tts-jobs:
    image: vabhub-backend:latest
    command: >
      sh -c "
        while true; do
          python -m app.cli.run_tts_jobs --max-jobs=5
          sleep 300
        done
      "
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - db
```

### Kubernetes CronJob

如果使用 Kubernetes，可以创建 CronJob：

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: vabhub-tts-jobs
spec:
  schedule: "*/5 * * * *"  # 每 5 分钟
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: runner
            image: vabhub-backend:latest
            command:
            - python
            - -m
            - app.cli.run_tts_jobs
            - --max-jobs=5
          restartPolicy: OnFailure
```

## 故障排查

### 常见问题

1. **ImportError 或 ModuleNotFoundError**
   - 确保在正确的虚拟环境中运行
   - 确保工作目录正确（应在 backend 目录或项目根目录）

2. **数据库连接失败**
   - 检查 `DATABASE_URL` 环境变量或配置文件
   - 确保数据库服务正在运行

3. **权限错误**
   - 确保运行用户有权限访问 TTS 输出目录
   - 检查文件系统权限

4. **配置未生效**
   - 检查环境变量是否正确设置
   - 确认配置文件路径和内容

### 查看日志

**systemd 日志：**
```bash
# 查看 service 执行日志
sudo journalctl -u vabhub-tts-jobs.service -n 50

# 查看 timer 状态
sudo journalctl -u vabhub-tts-jobs.timer -n 50

# 实时跟踪日志
sudo journalctl -u vabhub-tts-jobs.service -f
```

**Docker 日志：**
```bash
docker logs <container_name> --tail 50 -f
```

## 总结

TTS Runner CLI 工具提供了灵活的方式来执行 TTS 任务和存储清理，可以：
- 在开发环境中手动测试
- 通过 systemd timer 定时自动执行
- 在 Docker/Kubernetes 环境中作为定时任务运行

所有操作都会记录到数据库（TTSJob 状态、TTSStorageCleanupLog），可以通过 Web UI 查看执行历史。

