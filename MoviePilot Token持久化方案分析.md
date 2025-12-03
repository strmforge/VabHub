# MoviePilot Token持久化方案分析

## 📋 MoviePilot的实现方式

### 核心设计理念

1. **使用StorageHelper + SystemConfigOper**: 
   - `StorageHelper`管理存储配置
   - `SystemConfigOper`将配置保存到系统配置表（SystemConfig）
   - 配置以JSON格式存储在数据库中

2. **access_token作为property**:
   - 每次访问时动态获取
   - 自动检查过期并刷新
   - 刷新后自动保存

3. **get_conf/set_config模式**:
   - `get_conf()`: 从配置中获取token信息
   - `set_config()`: 保存token信息到配置
   - 配置自动持久化到数据库

### 关键代码分析

#### 1. access_token Property（自动刷新机制）

```python
@property
def access_token(self) -> Optional[str]:
    """
    访问token（自动刷新）
    """
    with lock:
        tokens = self.get_conf()  # 从配置获取
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            return None
        
        expires_in = tokens.get("expires_in", 0)
        refresh_time = tokens.get("refresh_time", 0)
        
        # 检查是否过期
        if expires_in and refresh_time + expires_in < int(time.time()):
            # 自动刷新
            tokens = self.__refresh_access_token(refresh_token)
            if tokens:
                # 保存刷新后的token
                self.set_config({
                    "refresh_time": int(time.time()),
                    **tokens
                })
            else:
                return None
        
        access_token = tokens.get("access_token")
        if access_token:
            self.session.headers.update({"Authorization": f"Bearer {access_token}"})
        return access_token
```

**关键点**:
- 使用`refresh_time`和`expires_in`判断是否需要刷新
- 刷新后自动调用`set_config()`保存
- 使用锁（lock）保证线程安全

#### 2. 登录时保存Token

```python
def check_login(self) -> Optional[Tuple[dict, str]]:
    """检查登录状态"""
    if result["data"]["status"] == 2:  # 登录成功
        tokens = self.__get_access_token()
        # 保存token和刷新时间
        self.set_config({
            "refresh_time": int(time.time()),
            **tokens
        })
```

**关键点**:
- 登录成功后立即保存token
- 同时保存`refresh_time`用于后续判断

#### 3. StorageHelper实现

```python
class StorageHelper:
    def get_storage(self, storage: str) -> Optional[schemas.StorageConf]:
        """获取指定存储配置"""
        storagies = self.get_storagies()
        for s in storagies:
            if s.type == storage:
                return s
        return None
    
    def set_storage(self, storage: str, conf: dict):
        """设置存储配置"""
        storagies = self.get_storagies()
        # 更新或创建配置
        # ...
        SystemConfigOper().set(SystemConfigKey.Storages, [s.dict() for s in storagies])
```

**关键点**:
- 配置存储在系统配置表中
- 使用`SystemConfigKey.Storages`作为键
- 配置以列表形式存储，每个存储一个配置对象

## 🔄 与当前实现的对比

### 当前实现（回调方式）
- ✅ 使用回调函数保存token
- ✅ 在Service层管理token持久化
- ❌ 需要手动管理token刷新
- ❌ access_token是普通属性，不会自动刷新

### MoviePilot方式（推荐）
- ✅ access_token作为property，自动刷新
- ✅ 使用get_conf/set_config统一管理
- ✅ 自动持久化，无需回调
- ✅ 线程安全（使用锁）
- ✅ 更简洁，更符合Python习惯

## 🎯 重构建议

### 1. 实现StorageHelper（类似MoviePilot）

```python
class CloudStorageHelper:
    """云存储配置帮助类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_storage_config(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """获取存储配置"""
        storage = await self.db.get(CloudStorage, storage_id)
        if not storage:
            return None
        return {
            "access_token": storage.access_token,
            "refresh_token": storage.refresh_token,
            "expires_at": storage.expires_at.isoformat() if storage.expires_at else None,
            "refresh_time": int(storage.expires_at.timestamp()) if storage.expires_at else 0,
            "expires_in": int((storage.expires_at - datetime.utcnow()).total_seconds()) if storage.expires_at else 0,
            "user_id": storage.user_id,
            "user_name": storage.user_name
        }
    
    async def set_storage_config(self, storage_id: int, config: Dict[str, Any]):
        """保存存储配置"""
        storage = await self.db.get(CloudStorage, storage_id)
        if not storage:
            return
        
        if "access_token" in config:
            storage.access_token = config["access_token"]
        if "refresh_token" in config:
            storage.refresh_token = config["refresh_token"]
        if "expires_at" in config:
            storage.expires_at = datetime.fromisoformat(config["expires_at"])
        # ... 更新其他字段
        
        await self.db.commit()
```

### 2. 重构access_token为Property

```python
@property
async def access_token(self) -> Optional[str]:
    """访问token（自动刷新）"""
    if not self._storage_id:
        return self._access_token  # 兼容旧代码
    
    # 从数据库获取配置
    config = await self._storage_helper.get_storage_config(self._storage_id)
    if not config:
        return None
    
    refresh_token = config.get("refresh_token")
    if not refresh_token:
        return None
    
    expires_in = config.get("expires_in", 0)
    refresh_time = config.get("refresh_time", 0)
    
    # 检查是否过期
    if expires_in and refresh_time + expires_in < int(time.time()):
        # 自动刷新
        tokens = await self._refresh_access_token(refresh_token)
        if tokens:
            # 保存刷新后的token
            await self._storage_helper.set_storage_config(self._storage_id, {
                "refresh_time": int(time.time()),
                **tokens
            })
        else:
            return None
    
    access_token = config.get("access_token")
    if access_token:
        # 更新session headers
        if self.session:
            self.session.headers.update({"Authorization": f"Bearer {access_token}"})
    return access_token
```

### 3. 简化登录流程

```python
async def check_qr_status(self) -> Tuple[int, str, Dict[str, Any]]:
    """检查二维码登录状态"""
    # ... 检查状态 ...
    
    if status == 2:  # 登录成功
        tokens = await self._get_access_token()
        if tokens:
            # 直接保存到数据库
            await self._storage_helper.set_storage_config(self._storage_id, {
                "refresh_time": int(time.time()),
                **tokens
            })
            return 2, "登录成功", tokens
```

## ✅ 优势

1. **自动化**: Token自动刷新，无需手动管理
2. **简洁**: 使用property模式，代码更清晰
3. **可靠**: 经过MoviePilot多次验证
4. **统一**: 使用get_conf/set_config统一接口
5. **线程安全**: 使用锁保证并发安全

## 📝 注意事项

1. **异步处理**: 由于我们使用异步，需要适配MoviePilot的同步方式
2. **数据库模型**: 需要确保CloudStorage模型支持所有必要字段
3. **向后兼容**: 保持对旧代码的兼容性

---

**建议**: 按照MoviePilot的方式重构token持久化实现，这样可以获得经过验证的、更可靠的方案。

