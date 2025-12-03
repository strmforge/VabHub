# API密钥加密存储实现总结

**生成时间**: 2025-01-XX  
**目的**: 总结API密钥加密存储的实现，防止API密钥被滥用

---

## 📋 一、已完成的工作

### 1.1 扩展CloudKeyManager ✅

**文件**: `VabHub/backend/app/core/cloud_key_manager.py`

**新增方法**:
- ✅ `set_api_key(api_name, api_key, api_pin=None)` - 设置API密钥（加密存储）
- ✅ `get_api_key(api_name)` - 获取API密钥（自动解密）
- ✅ `has_api_key(api_name)` - 检查是否有指定API的密钥
- ✅ `delete_api_key(api_name)` - 删除指定API的密钥

**特点**:
- ✅ 使用Fernet加密（与115网盘密钥相同的加密方式）
- ✅ 存储在 `~/.vabhub/cloud_keys.encrypted`
- ✅ 使用主密钥文件 `~/.vabhub/.master_key` 进行加密/解密

### 1.2 创建APIKeyManager ✅

**文件**: `VabHub/backend/app/core/api_key_manager.py`

**实现内容**:
- ✅ `APIKeyManager` 类 - 统一管理所有API密钥
- ✅ `get_tmdb_api_key()` - 获取TMDB API Key（优先从加密存储读取）
- ✅ `set_tmdb_api_key()` - 设置TMDB API Key（加密存储）
- ✅ `get_tvdb_api_key()` / `get_tvdb_api_pin()` - 获取TVDB API Key和PIN
- ✅ `set_tvdb_api_key()` - 设置TVDB API Key和PIN（加密存储）
- ✅ `get_fanart_api_key()` - 获取Fanart API Key
- ✅ `set_fanart_api_key()` - 设置Fanart API Key（加密存储）
- ✅ `initialize_default_keys()` - 初始化默认API密钥（首次启动时自动保存）

**特点**:
- ✅ 优先从加密存储读取，如果没有则使用环境变量/默认值
- ✅ 自动初始化默认密钥（TVDB、Fanart使用MoviePilot默认值）
- ✅ 统一的API密钥管理接口

### 1.3 更新配置类 ✅

**文件**: `VabHub/backend/app/core/config.py`

**更新内容**:
- ✅ `TMDB_API_KEY` - 改为property，优先从加密存储读取
- ✅ `TVDB_V4_API_KEY` - 改为property，优先从加密存储读取
- ✅ `TVDB_V4_API_PIN` - 改为property，优先从加密存储读取
- ✅ `FANART_API_KEY` - 改为property，优先从加密存储读取

**特点**:
- ✅ 向后兼容：如果没有加密存储，则使用环境变量/默认值
- ✅ 自动缓存：使用私有变量缓存，避免重复读取
- ✅ 异常处理：如果加密存储读取失败，自动降级到环境变量

### 1.4 更新系统设置API ✅

**文件**: `VabHub/backend/app/api/system_settings.py`

**更新内容**:
- ✅ 在 `update_system_env` 中特殊处理API密钥
- ✅ `TMDB_API_KEY` - 保存到加密存储
- ✅ `TVDB_V4_API_KEY` / `TVDB_V4_API_PIN` - 保存到加密存储
- ✅ `FANART_API_KEY` - 保存到加密存储

**特点**:
- ✅ 自动识别API密钥字段
- ✅ 保存到加密存储（而不是数据库）
- ✅ 数据库只保存标记（is_encrypted=True），不保存实际密钥值

### 1.5 应用启动时初始化 ✅

**文件**: `VabHub/backend/main.py`

**更新内容**:
- ✅ 在 `lifespan` 函数中添加API密钥管理器初始化
- ✅ 自动调用 `initialize_default_keys()` 初始化默认密钥

**特点**:
- ✅ 首次启动时自动保存默认密钥（TVDB、Fanart）
- ✅ 如果已存在，则跳过初始化
- ✅ 异常处理：初始化失败不影响应用启动

---

## 📋 二、加密存储机制

### 2.1 加密方式

- **算法**: Fernet（对称加密，基于AES 128位CBC模式）
- **密钥管理**: 使用主密钥文件 `~/.vabhub/.master_key`
- **存储位置**: `~/.vabhub/cloud_keys.encrypted`
- **文件权限**: 仅所有者可读写（0o600）

### 2.2 密钥读取优先级

1. **加密存储**（最高优先级）
   - 从 `~/.vabhub/cloud_keys.encrypted` 读取
   - 使用主密钥解密

2. **环境变量**（次优先级）
   - `TMDB_API_KEY`
   - `TVDB_V4_API_KEY` / `TVDB_V4_API_PIN`
   - `FANART_API_KEY`

3. **默认值**（最低优先级）
   - TVDB: `ed2aa66b-7899-4677-92a7-67bc9ce3d93a`
   - Fanart: `d2d31f9ecabea050fc7d68aa3146015f`
   - TMDB: 空字符串（需要用户自己申请）

### 2.3 密钥保存流程

1. **用户在前端输入API密钥**
2. **前端发送到后端API** (`/api/system/env`)
3. **后端识别为API密钥字段**
4. **保存到加密存储**（使用CloudKeyManager）
5. **数据库只保存标记**（is_encrypted=True，value为空）

---

## 📋 三、支持的API密钥

### 3.1 TMDB API Key

- **用途**: 媒体搜索和识别
- **获取方式**: 用户需要自己申请（https://www.themoviedb.org/settings/api）
- **加密存储**: ✅ 是
- **默认值**: 无（需要用户配置）

### 3.2 TVDB API Key & PIN

- **用途**: 电视剧元数据和图片获取
- **获取方式**: 使用MoviePilot默认值（用户可覆盖）
- **加密存储**: ✅ 是
- **默认值**: 
  - Key: `ed2aa66b-7899-4677-92a7-67bc9ce3d93a`
  - PIN: 空字符串

### 3.3 Fanart API Key

- **用途**: 媒体图片获取（海报、背景图等）
- **获取方式**: 使用MoviePilot默认值（用户可覆盖）
- **加密存储**: ✅ 是
- **默认值**: `d2d31f9ecabea050fc7d68aa3146015f`

---

## 📋 四、安全性

### 4.1 加密存储

- ✅ **Fernet加密**: 使用业界标准的对称加密算法
- ✅ **主密钥保护**: 主密钥文件权限为0o600（仅所有者可读写）
- ✅ **加密文件保护**: 加密文件权限为0o600（仅所有者可读写）

### 4.2 数据库存储

- ✅ **不存储实际密钥**: 数据库只保存标记（is_encrypted=True）
- ✅ **标记字段**: 用于标识该字段已加密存储
- ✅ **向后兼容**: 如果加密存储读取失败，自动降级到环境变量

### 4.3 防止滥用

- ✅ **加密存储**: 密钥以加密形式存储，即使文件泄露也无法直接读取
- ✅ **主密钥保护**: 主密钥文件独立存储，权限严格控制
- ✅ **环境变量支持**: 支持通过环境变量配置（生产环境推荐）

---

## 📋 五、使用方式

### 5.1 前端配置

用户在前端系统设置页面输入API密钥，系统自动：
1. 保存到加密存储
2. 数据库只保存标记

### 5.2 后端使用

```python
from app.core.config import settings

# 直接使用settings，自动从加密存储读取
tmdb_key = settings.TMDB_API_KEY
tvdb_key = settings.TVDB_V4_API_KEY
fanart_key = settings.FANART_API_KEY
```

### 5.3 手动管理

```python
from app.core.api_key_manager import get_api_key_manager

api_key_manager = get_api_key_manager()

# 设置API密钥
api_key_manager.set_tmdb_api_key("your-tmdb-key")
api_key_manager.set_tvdb_api_key("your-tvdb-key", "your-pin")
api_key_manager.set_fanart_api_key("your-fanart-key")

# 获取API密钥
tmdb_key = api_key_manager.get_tmdb_api_key()
tvdb_key = api_key_manager.get_tvdb_api_key()
fanart_key = api_key_manager.get_fanart_api_key()
```

---

## 📋 六、迁移说明

### 6.1 首次启动

- ✅ 自动初始化默认密钥（TVDB、Fanart）
- ✅ 如果环境变量中有密钥，优先使用环境变量
- ✅ 用户在前端配置后，自动保存到加密存储

### 6.2 从环境变量迁移

如果之前使用环境变量配置API密钥：
1. 首次启动时，系统会自动从环境变量读取
2. 用户在前端配置后，会自动保存到加密存储
3. 之后优先使用加密存储的密钥

### 6.3 从数据库迁移

如果之前数据库中有API密钥：
1. 系统会自动识别并迁移到加密存储
2. 数据库中的密钥会被清空（只保留标记）

---

## 📋 七、总结

### 7.1 实现完成

- ✅ **加密存储**: 所有API密钥使用Fernet加密存储
- ✅ **统一管理**: 使用APIKeyManager统一管理所有API密钥
- ✅ **自动初始化**: 首次启动时自动初始化默认密钥
- ✅ **向后兼容**: 支持环境变量和默认值降级
- ✅ **安全性**: 主密钥和加密文件权限严格控制

### 7.2 优势

1. **防止滥用**: 密钥加密存储，即使文件泄露也无法直接读取
2. **统一管理**: 所有API密钥使用相同的加密机制
3. **易于使用**: 前端配置后自动加密存储，无需手动操作
4. **向后兼容**: 支持环境变量配置，不影响现有部署

---

**文档生成时间**: 2025-01-XX  
**文档版本**: 1.0

