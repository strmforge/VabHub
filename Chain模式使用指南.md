# Chain 模式使用指南

## 📋 概述

Chain 模式为 VabHub 提供了统一的处理链接口，简化了不同模块的调用和管理。本文档介绍如何使用 Chain 模式。

## 🚀 快速开始

### 1. 基本使用

#### 使用 ChainManager（推荐）

```python
from app.chain.manager import get_chain_manager

# 获取Chain管理器
chain_manager = get_chain_manager()

# 使用StorageChain
storage_chain = chain_manager.storage
storages = await storage_chain.list_storages()

# 使用SubscribeChain
subscribe_chain = chain_manager.subscribe
subscriptions = await subscribe_chain.list_subscriptions()

# 使用DownloadChain
download_chain = chain_manager.download
downloads = await download_chain.list_downloads()
```

#### 使用便捷函数

```python
from app.chain import get_storage_chain, get_subscribe_chain, get_download_chain

# 直接获取Chain实例
storage_chain = get_storage_chain()
subscribe_chain = get_subscribe_chain()
download_chain = get_download_chain()
```

#### 直接实例化

```python
from app.chain.storage import StorageChain
from app.chain.subscribe import SubscribeChain
from app.chain.download import DownloadChain

# 直接创建实例
storage_chain = StorageChain()
subscribe_chain = SubscribeChain()
download_chain = DownloadChain()
```

## 📚 API 使用示例

### StorageChain

#### 列出存储配置

```python
from app.chain import get_storage_chain

chain = get_storage_chain()

# 列出所有存储
storages = await chain.list_storages()

# 列出特定提供商的存储
storages = await chain.list_storages(provider="115")
```

#### 文件操作

```python
# 列出文件
files = await chain.list_files(storage_id=1, path="/", recursive=False)

# 获取存储使用情况
usage = await chain.get_storage_usage(storage_id=1)
```

#### 认证操作

```python
# 生成二维码（115网盘）
qr_content, qr_url, error = await chain.generate_qr_code(storage_id=1)

# 检查二维码状态
status, message, token_data = await chain.check_qr_status(storage_id=1)
```

### SubscribeChain

#### 订阅管理

```python
from app.chain import get_subscribe_chain

chain = get_subscribe_chain()

# 列出所有订阅
subscriptions = await chain.list_subscriptions()

# 列出电影订阅
movie_subs = await chain.list_subscriptions(media_type="movie")

# 列出活跃订阅
active_subs = await chain.list_subscriptions(status="active")

# 获取订阅详情
subscription = await chain.get_subscription(subscription_id=1)

# 创建订阅
new_subscription = await chain.create_subscription({
    "title": "Test Movie",
    "media_type": "movie",
    "tmdb_id": 12345
})

# 更新订阅
updated = await chain.update_subscription(
    subscription_id=1,
    subscription_data={"status": "paused"}
)

# 启用/禁用订阅
await chain.enable_subscription(subscription_id=1)
await chain.disable_subscription(subscription_id=1)

# 执行订阅搜索
result = await chain.execute_search(subscription_id=1)
```

### DownloadChain

#### 下载任务管理

```python
from app.chain import get_download_chain

chain = get_download_chain()

# 列出所有下载任务
downloads = await chain.list_downloads()

# 列出下载中的任务
downloading = await chain.list_downloads(status="downloading")

# 获取下载详情
download = await chain.get_download(download_id="xxx")

# 创建下载任务
new_download = await chain.create_download({
    "title": "Test Download",
    "magnet_link": "magnet:?...",
    "downloader": "qBittorrent",
    "save_path": "/downloads"
})

# 暂停/恢复/删除下载
await chain.pause_download(download_id="xxx")
await chain.resume_download(download_id="xxx")
await chain.delete_download(download_id="xxx", delete_files=False)
```

## 🔧 在 FastAPI 中使用

### 方式1：在API端点中直接使用

```python
from fastapi import APIRouter, Depends, HTTPException
from app.chain import get_storage_chain

router = APIRouter()

@router.get("/storages")
async def list_storages():
    """列出存储配置"""
    chain = get_storage_chain()
    storages = await chain.list_storages()
    return {"storages": storages}
```

### 方式2：使用依赖注入

```python
from fastapi import APIRouter, Depends
from app.chain import get_storage_chain

router = APIRouter()

def get_storage_chain_dep():
    """StorageChain依赖"""
    return get_storage_chain()

@router.get("/storages")
async def list_storages(chain = Depends(get_storage_chain_dep)):
    """列出存储配置"""
    storages = await chain.list_storages()
    return {"storages": storages}
```

### 方式3：使用ChainManager

```python
from fastapi import APIRouter
from app.chain.manager import get_chain_manager

router = APIRouter()
chain_manager = get_chain_manager()

@router.get("/storages")
async def list_storages():
    """列出存储配置"""
    storages = await chain_manager.storage.list_storages()
    return {"storages": storages}

@router.get("/subscriptions")
async def list_subscriptions():
    """列出订阅"""
    subscriptions = await chain_manager.subscribe.list_subscriptions()
    return {"subscriptions": subscriptions}
```

## 🎯 迁移现有API

### 迁移前（使用Service）

```python
from app.modules.cloud_storage.service import CloudStorageService
from app.core.database import get_db

@router.get("/storages")
async def list_storages(db = Depends(get_db)):
    """列出存储配置"""
    service = CloudStorageService(db)
    storages = await service.list_storages()
    return {"storages": storages}
```

### 迁移后（使用Chain）

```python
from app.chain import get_storage_chain

@router.get("/storages")
async def list_storages():
    """列出存储配置"""
    chain = get_storage_chain()
    storages = await chain.list_storages()
    return {"storages": storages}
```

### 优势

1. **简化代码**: 不需要手动管理数据库会话
2. **统一接口**: 所有操作通过Chain统一处理
3. **缓存支持**: Chain层自动提供缓存
4. **错误处理**: Chain层统一处理错误

## 🔄 缓存管理

### 清除缓存

```python
from app.chain.manager import get_chain_manager

chain_manager = get_chain_manager()

# 清除所有Chain的缓存
chain_manager.clear_cache()

# 清除特定Chain的缓存
chain_manager.clear_cache("storage")
chain_manager.clear_cache("subscribe")
chain_manager.clear_cache("download")
```

### 手动清除特定缓存

```python
# StorageChain
storage_chain = get_storage_chain()
await storage_chain.clear_file_cache(storage_id=1, path="/")

# SubscribeChain
subscribe_chain = get_subscribe_chain()
await subscribe_chain._clear_subscription_cache(subscription_id=1)

# DownloadChain
download_chain = get_download_chain()
await download_chain._clear_download_cache(download_id="xxx")
```

## ⚠️ 注意事项

### 1. 会话管理

Chain 模式自动管理数据库会话，每个操作使用独立的会话。不需要手动管理会话生命周期。

### 2. 缓存策略

- **StorageChain**: 文件列表5分钟、使用情况1分钟
- **SubscribeChain**: 订阅列表1分钟、订阅详情1分钟
- **DownloadChain**: 下载列表30秒、下载详情30秒

### 3. 错误处理

Chain 模式提供统一的错误处理机制。如果操作失败，会抛出异常，需要在API层处理。

### 4. 向后兼容

现有的Service层仍然可以使用。Chain模式是对Service层的封装，不破坏现有功能。

## 📊 性能优化

### 1. 使用缓存

Chain 模式自动提供缓存，减少数据库查询和外部API调用。

### 2. 批量操作

对于批量操作，建议直接使用Service层，因为Chain模式每次操作都创建新的会话。

### 3. 异步操作

所有Chain操作都是异步的，可以在并发场景下使用。

## 🧪 测试

### 运行测试脚本

```bash
# 测试所有Chain
python backend/scripts/test_all_chains.py

# 测试单个Chain
python backend/scripts/test_storage_chain.py
python backend/scripts/test_subscribe_chain.py
python backend/scripts/test_download_chain.py
```

## 📝 最佳实践

### 1. 使用ChainManager

推荐使用 `get_chain_manager()` 获取Chain管理器，然后通过管理器访问各个Chain。

### 2. 错误处理

在API层统一处理错误，提供友好的错误消息。

### 3. 缓存策略

根据数据变化频率调整缓存时间。对于频繁变化的数据（如下载状态），使用较短的缓存时间。

### 4. 日志记录

Chain模式自动记录日志，可以在API层添加额外的日志记录。

## 🎉 总结

Chain 模式为 VabHub 提供了：

1. **统一的接口**: 所有操作通过Chain统一处理
2. **简化的代码**: 不需要手动管理数据库会话
3. **自动缓存**: Chain层自动提供缓存机制
4. **错误处理**: Chain层统一处理错误
5. **易于扩展**: 添加新的操作只需在Chain中添加方法

使用Chain模式可以让代码更简洁、更易维护，同时提供更好的性能和用户体验。

---

**版本**: 1.0  
**更新日期**: 2025-01-XX

