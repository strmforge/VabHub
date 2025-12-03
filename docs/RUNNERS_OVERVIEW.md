# VabHub Runner 配置指南

> LAUNCH-1 L6 实现

## 概述

VabHub 使用多个 Runner 执行后台任务，如 TTS 生成、漫画同步、音乐下载等。
建议通过 systemd timer 或 cron 定时运行这些 Runner。

## Runner 列表

### TTS 相关

#### TTS Worker
- **命令**: `python -m app.runners.tts_worker`
- **运行方式**: 定时执行
- **建议周期**: 每 5 分钟
- **说明**: 处理 TTS 生成队列中的任务

#### TTS Cleanup
- **命令**: `python -m app.runners.tts_cleanup`
- **运行方式**: 定时执行
- **建议周期**: 每天 1 次
- **说明**: 清理过期的 TTS 音频文件

### 漫画相关

#### 漫画追更同步
- **命令**: `python -m app.runners.manga_follow_sync`
- **运行方式**: 定时执行
- **建议周期**: 每 15-30 分钟
- **说明**: 检查追更漫画是否有新章节

#### 漫画远程同步
- **命令**: `python -m app.runners.manga_remote_sync`
- **运行方式**: 定时执行
- **建议周期**: 每 1 小时
- **说明**: 从远程漫画源同步元数据

### 音乐相关

#### 音乐榜单同步
- **命令**: `python -m app.runners.music_chart_sync`
- **运行方式**: 定时执行
- **建议周期**: 每 6 小时
- **说明**: 同步各音乐平台的榜单数据

#### 音乐订阅同步
- **命令**: `python -m app.runners.music_subscription_sync`
- **运行方式**: 定时执行
- **建议周期**: 每 1 小时
- **说明**: 检查音乐订阅并触发下载

#### 音乐下载调度
- **命令**: `python -m app.runners.music_download_dispatcher`
- **运行方式**: 定时执行
- **建议周期**: 每 5 分钟
- **说明**: 调度音乐下载任务

#### 音乐下载状态同步
- **命令**: `python -m app.runners.music_download_status_sync`
- **运行方式**: 定时执行
- **建议周期**: 每 5 分钟
- **说明**: 同步下载器状态，更新下载任务进度

## systemd Timer 配置示例

### 创建 Service 文件

`/etc/systemd/system/vabhub-tts-worker.service`:

```ini
[Unit]
Description=VabHub TTS Worker
After=network.target

[Service]
Type=oneshot
User=vabhub
WorkingDirectory=/opt/vabhub
ExecStart=/opt/vabhub/venv/bin/python -m app.runners.tts_worker
Environment=PYTHONPATH=/opt/vabhub

[Install]
WantedBy=multi-user.target
```

### 创建 Timer 文件

`/etc/systemd/system/vabhub-tts-worker.timer`:

```ini
[Unit]
Description=VabHub TTS Worker Timer

[Timer]
OnCalendar=*:0/5
Persistent=true
RandomizedDelaySec=30

[Install]
WantedBy=timers.target
```

### 启用 Timer

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启用并启动 timer
sudo systemctl enable vabhub-tts-worker.timer
sudo systemctl start vabhub-tts-worker.timer

# 查看 timer 状态
sudo systemctl list-timers | grep vabhub
```

## Docker Compose 配置示例

如果使用 Docker，可以通过 Ofelia 或类似的 cron 调度器：

```yaml
services:
  vabhub:
    image: vabhub/vabhub:latest
    # ...

  scheduler:
    image: mcuadros/ofelia:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    labels:
      ofelia.job-exec.tts-worker.schedule: "@every 5m"
      ofelia.job-exec.tts-worker.container: "vabhub"
      ofelia.job-exec.tts-worker.command: "python -m app.runners.tts_worker"
      
      ofelia.job-exec.manga-sync.schedule: "@every 30m"
      ofelia.job-exec.manga-sync.container: "vabhub"
      ofelia.job-exec.manga-sync.command: "python -m app.runners.manga_follow_sync"
      
      ofelia.job-exec.music-chart.schedule: "@every 6h"
      ofelia.job-exec.music-chart.container: "vabhub"
      ofelia.job-exec.music-chart.command: "python -m app.runners.music_chart_sync"
```

## 推荐配置汇总

| Runner | 周期 | 优先级 |
|--------|------|--------|
| tts_worker | 5 分钟 | 高 |
| tts_cleanup | 每天 | 低 |
| manga_follow_sync | 15-30 分钟 | 中 |
| manga_remote_sync | 1 小时 | 低 |
| music_chart_sync | 6 小时 | 低 |
| music_subscription_sync | 1 小时 | 中 |
| music_download_dispatcher | 5 分钟 | 高 |
| music_download_status_sync | 5 分钟 | 高 |

## 监控建议

1. 在 AdminDashboard 中查看 Runner 状态
2. 检查日志文件 `/var/log/vabhub/runners/`
3. 设置告警：如果 Runner 长时间未执行

## 相关文档

- [安装指南](./INSTALL_GUIDE.md)
- [备份与恢复](./BACKUP_AND_RESTORE.md)
