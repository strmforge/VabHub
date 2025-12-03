# VabHub文件操作模式实现总结

## 📋 实现概述

参考MoviePilot的文件操作模式，实现VabHub的文件操作机制，支持四种模式：
1. **下载器监控** - 定时扫描下载器中的任务（只处理打了标签的任务）
2. **目录监控** - 文件系统实时监控
3. **手动整理** - 用户手动触发
4. **不整理** - 仅作为下载目录

## ✅ 已完成

### 1. 配置和模型

#### 1.1 标签配置
**文件**: `VabHub/backend/app/core/config.py`

```python
# 下载器标签配置（用于标识VabHub添加的下载任务）
TORRENT_TAG: str = os.getenv("TORRENT_TAG", "VABHUB")  # 默认标签为VABHUB
```

#### 1.2 目录配置模型
**文件**: `VabHub/backend/app/schemas/directory.py`

- `DirectoryConfig` 模型
- 支持 `monitor_type`（downloader/directory/null）
- 支持 `transfer_type`（copy/move/link/softlink）
- 支持媒体类型和类别过滤
- 支持优先级排序

### 2. 下载器客户端更新

#### 2.1 qBittorrent客户端
**文件**: `VabHub/backend/app/core/downloaders/qbittorrent.py`

**新增功能**:
- `add_torrent()` - 支持 `tags` 参数
- `set_torrent_tags()` - 设置种子标签
- `remove_torrent_tags()` - 移除种子标签
- `get_torrents()` - 支持 `tags` 参数过滤
- `get_completed_torrents()` - 支持标签过滤
- `get_downloading_torrents()` - 支持标签过滤

#### 2.2 统一接口更新
**文件**: `VabHub/backend/app/core/downloaders/__init__.py`

**新增功能**:
- `add_torrent()` - 支持 `tags` 参数
- `get_torrents()` - 支持 `tags` 参数过滤
- `get_completed_torrents()` - 支持标签过滤
- `get_downloading_torrents()` - 支持标签过滤

**注意**: Transmission标签功能待实现（标记为TODO）

## 🚧 待实现

### 3. 下载服务更新
**文件**: `VabHub/backend/app/modules/download/service.py`

**需要更新**:
- `create_download()` - 添加任务时自动打标签

### 4. 下载器监控服务
**文件**: `VabHub/backend/app/modules/file_operation/downloader_monitor.py`（新建）

**功能**:
- 定时任务（每5分钟）扫描下载器
- 只查询打了 `TORRENT_TAG` 标签的任务
- 检查任务是否在下载器监控目录中
- 查询下载历史记录（获取媒体信息）
- 调用文件整理服务

### 5. 目录监控服务
**文件**: `VabHub/backend/app/modules/file_operation/directory_monitor.py`（新建）

**功能**:
- 使用文件系统监控（watchdog）实时监测目录变化
- 检测到新增或修改的文件时，自动触发整理
- 支持本地和远程目录监控

### 6. 文件整理服务
**文件**: `VabHub/backend/app/modules/file_operation/transfer_service.py`（新建）

**功能**:
- 整合 `TransferHandler`
- 支持根据 `transfer_type` 执行不同的整理方式
- 支持媒体识别和重命名
- 支持覆盖模式

### 7. 目录配置API
**文件**: `VabHub/backend/app/api/directory.py`（新建）

**端点**:
- `GET /api/v1/directories` - 获取所有目录配置
- `POST /api/v1/directories` - 创建目录配置
- `PUT /api/v1/directories/{id}` - 更新目录配置
- `DELETE /api/v1/directories/{id}` - 删除目录配置

### 8. 目录配置数据库模型
**文件**: `VabHub/backend/app/models/directory.py`（新建）

**模型**:
- `Directory` - 目录配置表

## 📊 工作流程

### 下载器监控流程

```
定时任务（每5分钟）
  ↓
获取下载器监控目录配置
  ↓
查询下载器中的已完成任务（只查询打了VABHUB标签的任务）
  ↓
检查任务是否在下载器监控目录中
  ↓
查询下载历史记录（获取媒体信息）
  ↓
调用文件整理服务（根据transfer_type执行整理）
  ↓
标记任务为已整理
```

### 目录监控流程

```
文件系统监控（watchdog）
  ↓
检测到新增或修改的文件
  ↓
检查文件是否在目录监控配置的路径中
  ↓
调用文件整理服务（根据transfer_type执行整理）
```

### 手动整理流程

```
用户在WebUI中选择文件或目录
  ↓
调用手动整理API
  ↓
调用文件整理服务（根据transfer_type执行整理）
```

## 🎯 下一步

1. ✅ 完成下载服务更新（添加任务时打标签）
2. ✅ 实现下载器监控服务
3. ✅ 实现目录监控服务
4. ✅ 实现文件整理服务
5. ✅ 创建目录配置数据库模型和API
6. ✅ 集成到定时任务系统
7. ✅ 前端界面开发

## 📝 注意事项

1. **标签机制**：
   - 所有VabHub添加的下载任务都会自动打上 `TORRENT_TAG` 标签
   - 查询下载任务时只返回打了标签的任务
   - WebUI也只显示打了标签的任务

2. **Transmission支持**：
   - Transmission标签功能需要单独实现
   - 目前标记为TODO，优先支持qBittorrent

3. **目录配置存储**：
   - 可以使用数据库存储（推荐）
   - 也可以使用配置文件存储

4. **文件整理方式**：
   - `copy`: 复制（最安全，但占用空间）
   - `move`: 移动（节省空间，但删除源文件）
   - `link`: 硬链接（节省空间，但需要同盘）
   - `softlink`: 软链接（节省空间，但依赖源文件）

