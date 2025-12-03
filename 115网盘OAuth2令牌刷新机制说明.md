# 115网盘OAuth2令牌刷新机制说明

## 📋 概述

基于115网盘官方API文档，本文档详细说明OAuth2令牌的获取、刷新机制和生命周期管理。

## 🔐 OAuth2令牌类型

### 1. Access Token（访问令牌）

**用途**: 访问资源接口的凭证

**生命周期**:
- **初始获取**: 7200秒（2小时）
- **刷新后**: 2592000秒（30天）

**特点**:
- 每次刷新都会生成新的access_token
- 刷新后会同时刷新有效期
- 必须在HTTP请求头中携带: `Authorization: Bearer {access_token}`

### 2. Refresh Token（刷新令牌）

**用途**: 刷新access_token的凭证

**生命周期**:
- **有效期**: 1年（固定，不延长不改变）
- **刷新后**: 返回新的refresh_token，但有效期不变

**特点**:
- 有效期固定为1年，不会因为刷新而延长
- 每次刷新都会返回新的refresh_token
- 必须妥善保存，丢失后需要重新授权

## 🔄 令牌刷新流程

### API端点

```
POST https://passportapi.115.com/open/refreshToken
```

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| refresh_token | text | 是 | 刷新令牌 |

### 请求头

```
Content-Type: application/x-www-form-urlencoded
```

### 响应数据

```json
{
    "state": 1,
    "code": 0,
    "message": "",
    "data": {
        "access_token": "新的access_token",
        "refresh_token": "新的refresh_token",
        "expires_in": 2592000
    }
}
```

### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| access_token | string | 新的access_token，同时刷新有效期 |
| refresh_token | string | 新的refresh_token，有效期不延长不改变 |
| expires_in | number | access_token有效期，单位秒（默认2592000，即30天） |

## ⚠️ 注意事项

### 1. 频控限制

**请勿频繁刷新，否则列入频控**

- 115网盘对刷新操作有频控限制
- 建议在access_token即将过期前刷新（例如：过期前1小时）
- 避免在短时间内多次刷新

### 2. Refresh Token管理

- **保存**: 必须妥善保存refresh_token，建议加密存储
- **更新**: 每次刷新后，必须使用新的refresh_token替换旧的
- **有效期**: refresh_token有效期为1年，不会因为刷新而延长
- **丢失处理**: 如果refresh_token丢失或过期，需要重新进行OAuth2授权

### 3. Access Token管理

- **自动刷新**: 建议实现自动刷新机制，在token即将过期前刷新
- **错误处理**: 如果access_token过期，应使用refresh_token刷新
- **并发控制**: 多线程/多进程环境下，需要实现令牌刷新的并发控制

## 💡 最佳实践

### 1. 令牌存储

```python
# 推荐：使用数据库存储令牌
{
    "access_token": "xxx",
    "refresh_token": "xxx",
    "expires_at": 1234567890,  # 过期时间戳
    "refresh_token_expires_at": 1234567890  # refresh_token过期时间戳（1年后）
}
```

### 2. 自动刷新机制

```python
import asyncio
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, oauth_client, token_store):
        self.oauth = oauth_client
        self.store = token_store
    
    async def get_valid_token(self):
        """获取有效的access_token，如果过期则自动刷新"""
        token_info = self.store.get_token()
        
        if not token_info:
            # 没有令牌，需要重新授权
            return None
        
        # 检查access_token是否即将过期（提前1小时刷新）
        expires_at = token_info.get("expires_at", 0)
        now = datetime.now().timestamp()
        
        if now >= expires_at - 3600:  # 提前1小时刷新
            # 刷新令牌
            new_token = await self.oauth.refresh_access_token(
                token_info["refresh_token"]
            )
            
            if new_token:
                # 更新存储
                token_info.update({
                    "access_token": new_token["access_token"],
                    "refresh_token": new_token["refresh_token"],
                    "expires_at": now + new_token["expires_in"],
                    "updated_at": now
                })
                self.store.save_token(token_info)
        
        return token_info["access_token"]
```

### 3. 错误处理

```python
async def refresh_token_with_retry(oauth_client, refresh_token, max_retries=3):
    """带重试的令牌刷新"""
    for attempt in range(max_retries):
        try:
            token_info = await oauth_client.refresh_access_token(refresh_token)
            if token_info:
                return token_info
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"刷新令牌失败，已重试{max_retries}次: {e}")
                # 需要重新授权
                return None
            await asyncio.sleep(2 ** attempt)  # 指数退避
    
    return None
```

### 4. 并发控制

```python
import asyncio
from threading import Lock

class TokenManager:
    def __init__(self):
        self._lock = Lock()
        self._refreshing = False
        self._refresh_event = asyncio.Event()
    
    async def get_valid_token(self):
        """获取有效的access_token，支持并发控制"""
        # 检查是否需要刷新
        if self._need_refresh():
            # 如果正在刷新，等待刷新完成
            if self._refreshing:
                await self._refresh_event.wait()
            else:
                # 开始刷新
                self._refreshing = True
                self._refresh_event.clear()
                try:
                    await self._do_refresh()
                finally:
                    self._refreshing = False
                    self._refresh_event.set()
        
        return self._get_current_token()
```

## 📊 令牌生命周期示例

```
时间线：
T0: 初始授权
  ├── access_token: 有效期 2小时 (7200秒)
  └── refresh_token: 有效期 1年

T1: 1.5小时后刷新 (提前刷新)
  ├── access_token: 新的token，有效期 30天 (2592000秒)
  └── refresh_token: 新的token，有效期仍为1年（从T0开始计算）

T2: 30天后刷新
  ├── access_token: 新的token，有效期 30天
  └── refresh_token: 新的token，有效期仍为1年（从T0开始计算）

T3: 1年后
  └── refresh_token过期，需要重新授权
```

## 🔗 相关文档

- [115网盘官方API文档](https://www.yuque.com/115yun/open/qur839kyx9cgxpxi)
- [OAuth2认证流程](./115网盘官方API文档集成完成总结.md)
- [API客户端使用](./115网盘官方API文档集成完成总结.md)

## ✅ 实现检查清单

- [x] OAuth2认证客户端实现
- [x] 获取访问令牌
- [x] 刷新访问令牌
- [x] 令牌生命周期管理
- [x] 错误处理
- [x] 频控注意事项
- [ ] 自动刷新机制（待实现）
- [ ] 令牌持久化存储（待实现）
- [ ] 并发控制（待实现）

## 🎯 下一步

1. 实现令牌管理器（TokenManager）
2. 集成到API客户端，实现自动刷新
3. 实现令牌持久化存储
4. 添加并发控制机制
5. 编写单元测试

