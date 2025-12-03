# 115网盘Token持久化实现说明

## 📋 概述

实现了115网盘访问令牌（access_token）和刷新令牌（refresh_token）的持久化存储功能，将token保存到数据库中，确保应用重启后无需重新登录。

## 🎯 实现目标

1. **自动保存**: 登录成功后自动保存token到数据库
2. **自动加载**: 初始化Provider时自动从数据库加载token
3. **自动更新**: Token刷新后自动更新到数据库
4. **持久化**: Token存储在数据库中，应用重启后仍然有效

## 🔧 实现方案

### 1. Provider层（Cloud115Provider）

#### 添加属性
- `_storage_id`: 存储配置ID（用于标识要保存的存储配置）
- `_token_save_callback`: Token保存回调函数（由Service层提供）

#### 修改方法

**`initialize`方法**:
- 从credentials中获取`storage_id`和`token_save_callback`
- 从credentials中加载已保存的token（如果存在）

**`check_qr_status`方法**:
- 登录成功后调用`_save_tokens_to_db()`保存token

**`refresh_token`方法**:
- Token刷新成功后调用`_save_tokens_to_db()`更新token

**新增方法**:
```python
async def _save_tokens_to_db(self):
    """保存token到数据库（通过回调函数）"""
    if self._token_save_callback and self._storage_id:
        await self._token_save_callback(
            storage_id=self._storage_id,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            expires_at=self.expires_at,
            user_id=self.user_id,
            user_name=self.user_name
        )
```

### 2. Service层（CloudStorageService）

#### 修改方法

**`initialize_provider`方法**:
- 从数据库加载已保存的token（如果存在）
- 设置`storage_id`和`token_save_callback`到credentials中

**新增方法**:
```python
async def _save_storage_tokens(
    self,
    storage_id: int,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None
):
    """保存云存储token到数据库（内部方法，供provider回调使用）"""
    # 更新CloudStorage模型的token字段
    # 保存到数据库
```

**`check_qr_status`方法**:
- 移除了重复的token保存逻辑（因为provider已经通过回调保存）

### 3. 数据模型（CloudStorage）

数据库模型已包含以下字段：
- `access_token`: 访问令牌（Text类型）
- `refresh_token`: 刷新令牌（Text类型）
- `expires_at`: 过期时间（DateTime类型）
- `user_id`: 用户ID（String类型）
- `user_name`: 用户名（String类型）

## 📊 工作流程

### 登录流程
1. 用户扫描二维码登录
2. `check_qr_status`检测到登录成功
3. Provider获取access_token和refresh_token
4. Provider调用`_save_tokens_to_db()`
5. Service层的`_save_storage_tokens`方法保存token到数据库
6. Token持久化完成

### 初始化流程
1. 调用`initialize_provider(storage_id)`
2. 从数据库加载CloudStorage配置
3. 如果存在已保存的token，将其添加到credentials中
4. 设置`storage_id`和`token_save_callback`
5. 初始化Provider，Provider从credentials中加载token
6. Token自动恢复

### 刷新流程
1. Provider检测到token即将过期
2. 调用`refresh_token()`刷新token
3. 刷新成功后调用`_save_tokens_to_db()`
4. Service层更新数据库中的token
5. Token更新完成

## 🧪 测试

### 测试脚本
创建了`backend/scripts/test_115_token_persist.py`测试脚本，用于验证：
1. Token从数据库加载
2. Token保存到数据库
3. Token刷新和更新

### 运行测试
```bash
python backend/scripts/test_115_token_persist.py
```

## ✅ 优势

1. **自动化**: Token保存和加载完全自动化，无需手动操作
2. **持久化**: Token存储在数据库中，应用重启后仍然有效
3. **可靠性**: 使用回调机制，确保token及时保存
4. **可扩展**: 回调机制可以轻松扩展到其他云存储提供商

## 📝 注意事项

1. **Token加密**: 当前token以明文存储在数据库中，建议在生产环境中加密存储
2. **Token过期**: Token过期后需要重新登录，系统会自动处理
3. **多存储配置**: 每个存储配置都有独立的token，互不影响

## 🔄 后续优化建议

1. **Token加密**: 使用Fernet加密存储token
2. **自动刷新**: 在token即将过期时自动刷新
3. **Token验证**: 定期验证token有效性
4. **日志记录**: 记录token保存和加载的详细日志

## 📚 相关文件

- `backend/app/core/cloud_storage/providers/cloud_115.py`: Provider实现
- `backend/app/modules/cloud_storage/service.py`: Service层实现
- `backend/app/models/cloud_storage.py`: 数据模型
- `backend/scripts/test_115_token_persist.py`: 测试脚本

---

**状态**: ✅ 已完成  
**最后更新**: 2025-01-XX

