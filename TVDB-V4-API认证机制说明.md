# TVDB V4 API 认证机制说明

**生成时间**: 2025-01-XX  
**目的**: 解释TVDB V4 API认证的复杂性和实现要点

---

## 📋 一、为什么TVDB集成最复杂？

### 1.1 三种API的认证方式对比

#### **TMDB API** - 最简单 ⭐
```python
# 直接使用API Key，无需额外认证
url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}"
response = requests.get(url)  # 直接使用，无需token
```

**特点**:
- ✅ 只需API Key
- ✅ 无需登录
- ✅ 无需token管理
- ✅ 无需token刷新

#### **Fanart API** - 简单 ⭐⭐
```python
# 直接使用API Key，无需额外认证
url = f"https://webservice.fanart.tv/v3/movies/{tmdb_id}?api_key={api_key}"
response = requests.get(url)  # 直接使用，无需token
```

**特点**:
- ✅ 只需API Key
- ✅ 无需登录
- ✅ 无需token管理
- ✅ 无需token刷新

#### **TVDB V4 API** - 复杂 ⭐⭐⭐⭐⭐
```python
# 第一步：登录获取token
login_url = "https://api4.thetvdb.com/v4/login"
login_data = {"apikey": api_key, "pin": pin}  # 需要PIN（可选但推荐）
response = requests.post(login_url, json=login_data)
token = response.json()["data"]["token"]  # 获取token

# 第二步：使用token进行后续请求
headers = {"Authorization": f"Bearer {token}"}
url = f"https://api4.thetvdb.com/v4/series/{series_id}"
response = requests.get(url, headers=headers)  # 必须使用token
```

**特点**:
- ❌ 需要两步认证（先登录，再使用token）
- ❌ 需要管理token生命周期
- ❌ 需要处理token过期和刷新
- ❌ 需要可选的PIN（增强安全性）
- ❌ 每个请求都需要携带token

---

## 📋 二、TVDB V4 API认证流程详解

### 2.1 认证步骤

#### **步骤1：登录获取Token**
```python
POST https://api4.thetvdb.com/v4/login
Content-Type: application/json

{
    "apikey": "your-api-key",
    "pin": "your-pin"  # 可选，但推荐使用
}

# 响应
{
    "status": "success",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # JWT Token
    }
}
```

#### **步骤2：使用Token进行API请求**
```python
GET https://api4.thetvdb.com/v4/series/{id}
Authorization: Bearer {token}

# 响应
{
    "status": "success",
    "data": {
        "id": 12345,
        "name": "Series Name",
        ...
    }
}
```

#### **步骤3：Token过期处理**
```python
# 如果token过期，会返回401错误
{
    "status": "failure",
    "message": "Unauthorized"
}

# 需要重新登录获取新token
```

### 2.2 Token生命周期管理

**Token特点**:
- Token是JWT格式
- Token有过期时间（通常30天）
- Token过期后需要重新登录
- 没有refresh token机制（必须重新登录）

**需要实现的功能**:
1. ✅ Token缓存（避免频繁登录）
2. ✅ Token过期检测
3. ✅ 自动重新登录
4. ✅ Token刷新机制（虽然TVDB没有refresh token，但可以提前刷新）

---

## 📋 三、实现复杂度对比

### 3.1 代码复杂度

| API | 认证代码行数 | Token管理 | 错误处理 | 总复杂度 |
|-----|------------|----------|---------|---------|
| **TMDB** | ~5行 | 无 | 简单 | ⭐ 低 |
| **Fanart** | ~5行 | 无 | 简单 | ⭐ 低 |
| **TVDB** | ~100行 | 需要 | 复杂 | ⭐⭐⭐⭐⭐ 高 |

### 3.2 需要实现的功能

#### **TMDB/Fanart** - 简单实现
```python
class TMDBClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def get_movie(self, movie_id: int):
        url = f"{BASE_URL}/movie/{movie_id}?api_key={self.api_key}"
        return await self._request(url)
```

#### **TVDB** - 复杂实现
```python
class TVDBClient:
    def __init__(self, api_key: str, pin: str = ""):
        self.api_key = api_key
        self.pin = pin
        self.token = None
        self.token_expires_at = None
    
    async def _login(self):
        """登录获取token"""
        url = "https://api4.thetvdb.com/v4/login"
        data = {"apikey": self.api_key}
        if self.pin:
            data["pin"] = self.pin
        
        response = await self._request(url, method="POST", json=data)
        self.token = response["data"]["token"]
        # 解析JWT获取过期时间
        self.token_expires_at = self._parse_token_expiry(self.token)
    
    async def _ensure_token(self):
        """确保token有效"""
        if not self.token or self._is_token_expired():
            await self._login()
    
    def _is_token_expired(self) -> bool:
        """检查token是否过期"""
        if not self.token_expires_at:
            return True
        return datetime.utcnow() >= self.token_expires_at
    
    async def get_series(self, series_id: int):
        """获取剧集信息"""
        await self._ensure_token()  # 确保token有效
        url = f"https://api4.thetvdb.com/v4/series/{series_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        return await self._request(url, headers=headers)
```

---

## 📋 四、TVDB认证的特殊要求

### 4.1 PIN（个人识别码）

**PIN的作用**:
- 增强安全性
- 防止API Key泄露后的滥用
- 可选但推荐使用

**获取方式**:
- 在TVDB开发者平台设置
- 可以随时更改

### 4.2 Token缓存策略

**推荐策略**:
```python
# 1. 缓存token到内存（应用生命周期内）
self.token = None
self.token_expires_at = None

# 2. 缓存token到Redis（跨进程共享）
await redis.set("tvdb_token", token, ex=token_ttl)

# 3. 提前刷新（在过期前1天刷新）
if (token_expires_at - datetime.utcnow()).days < 1:
    await self._login()
```

### 4.3 错误处理

**需要处理的错误**:
1. **401 Unauthorized** - Token过期或无效
   - 处理：重新登录
2. **429 Too Many Requests** - 请求频率限制
   - 处理：实现重试机制和速率限制
3. **500 Internal Server Error** - 服务器错误
   - 处理：重试机制

---

## 📋 五、实现建议

### 5.1 简化实现方案

**方案1：简单实现（适合小规模使用）**
```python
class TVDBClient:
    def __init__(self, api_key: str, pin: str = ""):
        self.api_key = api_key
        self.pin = pin
        self.token = None
    
    async def _get_token(self):
        """获取token（带缓存）"""
        if self.token:
            return self.token
        
        # 登录获取token
        url = "https://api4.thetvdb.com/v4/login"
        data = {"apikey": self.api_key}
        if self.pin:
            data["pin"] = self.pin
        
        response = await httpx.post(url, json=data)
        self.token = response.json()["data"]["token"]
        return self.token
    
    async def request(self, endpoint: str):
        """发送请求（自动处理token）"""
        token = await self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://api4.thetvdb.com/v4/{endpoint}"
        
        try:
            response = await httpx.get(url, headers=headers)
            if response.status_code == 401:
                # Token过期，重新登录
                self.token = None
                token = await self._get_token()
                headers = {"Authorization": f"Bearer {token}"}
                response = await httpx.get(url, headers=headers)
            return response.json()
        except Exception as e:
            logger.error(f"TVDB请求失败: {e}")
            raise
```

**方案2：完整实现（适合生产环境）**
- Token过期时间解析和缓存
- 自动刷新机制
- 重试和错误处理
- 速率限制
- 连接池管理

### 5.2 与TMDB/Fanart的集成

**建议的集成方式**:
```python
class MediaMetadataService:
    def __init__(self):
        self.tmdb_client = TMDBClient(api_key=TMDB_API_KEY)  # 简单
        self.fanart_client = FanartClient(api_key=FANART_API_KEY)  # 简单
        self.tvdb_client = TVDBClient(api_key=TVDB_API_KEY, pin=TVDB_PIN)  # 复杂
    
    async def get_tv_metadata(self, tvdb_id: int):
        """获取电视剧元数据"""
        # 优先使用TMDB（简单）
        tmdb_data = await self.tmdb_client.get_tv(tvdb_id)
        
        # 补充TVDB数据（复杂，但数据更完整）
        try:
            tvdb_data = await self.tvdb_client.get_series(tvdb_id)
            # 合并数据
            return self._merge_metadata(tmdb_data, tvdb_data)
        except Exception as e:
            logger.warning(f"TVDB数据获取失败，仅使用TMDB数据: {e}")
            return tmdb_data
```

---

## 📋 六、总结

### 6.1 复杂度对比

| 方面 | TMDB | Fanart | TVDB |
|------|------|--------|------|
| **认证步骤** | 1步（直接使用） | 1步（直接使用） | 2步（登录+使用） |
| **Token管理** | 不需要 | 不需要 | 需要 |
| **Token刷新** | 不需要 | 不需要 | 需要 |
| **错误处理** | 简单 | 简单 | 复杂 |
| **代码量** | ~50行 | ~50行 | ~200行 |
| **实现难度** | ⭐ 低 | ⭐ 低 | ⭐⭐⭐⭐⭐ 高 |

### 6.2 为什么TVDB最复杂？

1. **两步认证流程** - 需要先登录获取token，再使用token
2. **Token生命周期管理** - 需要处理token过期、刷新、缓存
3. **错误处理复杂** - 需要处理401错误并自动重新登录
4. **可选PIN** - 增加了配置复杂度
5. **没有refresh token** - 必须重新登录，不能简单刷新

### 6.3 实施建议

**如果TVDB不是必需功能**:
- 可以暂时跳过，优先实现Fanart和多通知渠道
- TVDB主要用于补充TMDB缺失的电视剧信息
- 对于大多数用户，TMDB数据已经足够

**如果TVDB是必需功能**:
- 建议使用简单实现方案（方案1）
- 后续可以根据需要升级到完整实现（方案2）
- 预计工作量：2-3天（包括测试）

---

**文档生成时间**: 2025-01-XX  
**文档版本**: 1.0

