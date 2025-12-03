# MoviePilot TVDB实现分析

**生成时间**: 2025-01-XX  
**目的**: 分析MoviePilot如何实现TVDB集成，特别是token管理机制

---

## 📋 一、MoviePilot的TVDB实现架构

### 1.1 核心组件

MoviePilot的TVDB实现分为三个层次：

1. **TVDB V4 API客户端** (`app/modules/thetvdb/tvdb_v4_official.py`)
   - 官方TVDB V4 API的Python封装
   - 提供认证、请求处理、URL构建等功能

2. **TVDB模块** (`app/modules/thetvdb/__init__.py`)
   - 封装TVDB客户端
   - 实现token管理和错误处理
   - 提供业务方法（搜索、获取信息等）

3. **TVDB Chain** (`app/chain/tvdb.py`)
   - 集成到MoviePilot的Chain系统
   - 提供高级业务逻辑

---

## 📋 二、Token管理机制

### 2.1 初始化流程

```python
class TheTvDbModule(_ModuleBase):
    def __init__(self):
        self._tvdb: Optional[TVDB] = None
        self._tvdb_lock = threading.Lock()  # 线程锁
    
    def _initialize_tvdb_session(self, is_retry: bool = False) -> None:
        """
        初始化TVDB会话（登录获取token）
        """
        try:
            # 从配置获取API Key和PIN
            api_key = settings.TVDB_V4_API_KEY
            pin = settings.TVDB_V4_API_PIN
            
            if not api_key:
                logger.warn("TVDB API Key未配置")
                return
            
            # 创建TVDB客户端（会自动登录获取token）
            self._tvdb = TVDB(apikey=api_key, pin=pin, 
                             proxy=settings.PROXY, timeout=15)
            
            logger.info("TVDB会话初始化成功")
        except Exception as e:
            logger.error(f"TVDB会话初始化失败: {e}")
            if not is_retry:
                # 如果是首次初始化失败，尝试重试
                self._initialize_tvdb_session(is_retry=True)
```

**关键点**:
- ✅ **延迟初始化** - 只在需要时初始化
- ✅ **线程安全** - 使用`threading.Lock()`保护
- ✅ **重试机制** - 初始化失败时自动重试

### 2.2 Token失效处理

```python
def _ensure_tvdb_session(self, is_retry: bool = False) -> None:
    """
    确保TVDB会话有效
    """
    if self._tvdb is None:
        self._initialize_tvdb_session(is_retry=is_retry)

def _handle_tvdb_call(self, method_name: str, *args, **kwargs):
    """
    包裹TVDB调用，处理token失效情况并尝试重新初始化
    """
    try:
        # 确保会话有效
        self._ensure_tvdb_session()
        
        if not self._tvdb:
            return None
        
        # 调用TVDB方法
        method = getattr(self._tvdb, method_name)
        return method(*args, **kwargs)
    
    except Exception as e:
        error_msg = str(e).lower()
        
        # 检测token失效错误
        if "unauthorized" in error_msg or "token" in error_msg:
            logger.warning("TVDB Token可能已失效，正在尝试重新登录...")
            
            # 重新初始化会话
            with self._tvdb_lock:
                self._tvdb = None
                try:
                    self._initialize_tvdb_session(is_retry=True)
                    # 重试调用
                    method = getattr(self._tvdb, method_name)
                    return method(*args, **kwargs)
                except Exception as conn_err:
                    logger.error(f"TVDB Token失效后重新登录失败: {conn_err}")
                    return None
        else:
            logger.error(f"TVDB调用失败: {e}")
            return None
```

**关键点**:
- ✅ **自动检测token失效** - 通过错误信息判断
- ✅ **自动重新登录** - token失效时自动重新初始化
- ✅ **重试机制** - 重新登录后自动重试原操作
- ✅ **线程安全** - 使用锁保护重新初始化过程

### 2.3 业务方法封装

```python
def tvdb_info(self, tvdbid: int) -> Optional[dict]:
    """
    获取TVDB剧集信息
    """
    return self._handle_tvdb_call("get_series_extended", tvdbid, short=True)

def search_tvdb(self, title: str) -> list:
    """
    搜索TVDB剧集
    """
    return self._handle_tvdb_call("search", query=title, type="series")
```

**关键点**:
- ✅ **统一错误处理** - 所有TVDB调用都通过`_handle_tvdb_call`包装
- ✅ **自动token管理** - 用户无需关心token失效问题

---

## 📋 三、TVDB V4 API客户端实现

### 3.1 认证类（Auth）

```python
class Auth:
    """
    TVDB认证类
    """
    def __init__(self, url: str, apikey: str, pin: str = "", proxy: dict = None, timeout: int = 15):
        login_info = {"apikey": apikey}
        if pin != "":
            login_info["pin"] = pin
        
        # 发送登录请求
        req_utils = RequestUtils(proxies=proxy, timeout=timeout)
        response = req_utils.post_res(
            url=url,
            data=json.dumps(login_info, indent=2),
            headers={"Content-Type": "application/json"}
        )
        
        if response and response.status_code == 200:
            result = response.json()
            self.token = result["data"]["token"]  # 保存token
        else:
            raise Exception(f"TVDB认证失败: {response.status_code}")
    
    def get_token(self):
        return self.token
```

**关键点**:
- ✅ **同步登录** - 在初始化时立即登录
- ✅ **支持PIN** - 可选但推荐使用PIN增强安全性
- ✅ **错误处理** - 登录失败时抛出异常

### 3.2 请求处理类（Request）

```python
class Request:
    """
    请求处理类
    """
    def __init__(self, auth_token: str, proxy: dict = None, timeout: int = 15):
        self.auth_token = auth_token
        self.proxy = proxy
        self.timeout = timeout
    
    @cached(maxsize=settings.CONF.tmdb, ttl=settings.CONF.meta, skip_none=True)
    def make_request(self, url: str, if_modified_since: bool = None):
        """
        发送请求（带缓存）
        """
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        if if_modified_since:
            headers["If-Modified-Since"] = str(if_modified_since)
        
        req_utils = RequestUtils(proxies=self.proxy, timeout=self.timeout)
        response = req_utils.get_res(url=url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            data = result.get("data", None)
            if data is not None and result.get("status", "failure") != "failure":
                return data
            raise ValueError(f"获取失败: {result.get('message', '未知错误')}")
        else:
            raise ValueError(f"HTTP {response.status_code}")
```

**关键点**:
- ✅ **缓存支持** - 使用`@cached`装饰器缓存响应
- ✅ **Token自动携带** - 每个请求自动添加Authorization头
- ✅ **错误处理** - 统一处理HTTP错误

### 3.3 TVDB主类

```python
class TVDB:
    """
    TVDB API主类
    """
    def __init__(self, apikey: str, pin: str = "", proxy: dict = None, timeout: int = 15):
        self.url = Url()  # URL构建器
        login_url = self.url.construct("login")
        
        # 初始化时立即登录获取token
        self.auth = Auth(login_url, apikey, pin, proxy, timeout)
        auth_token = self.auth.get_token()
        
        # 创建请求处理器（使用token）
        self.request = Request(auth_token, proxy, timeout)
    
    def get_series(self, id: int, meta: str = None, if_modified_since: bool = None) -> dict:
        """获取剧集信息"""
        url = self.url.construct("series", id, meta=meta)
        return self.request.make_request(url, if_modified_since)
    
    def get_series_extended(self, id: int, meta=None, short=False, if_modified_since=None) -> dict:
        """获取剧集扩展信息"""
        url = self.url.construct("series", id, "extended", meta=meta, short=short)
        return self.request.make_request(url, if_modified_since)
    
    def search(self, query: str, **kwargs) -> list:
        """搜索"""
        url = self.url.construct("search", query=query, **kwargs)
        return self.request.make_request(url)
```

**关键点**:
- ✅ **初始化时登录** - 创建TVDB实例时立即登录获取token
- ✅ **Token持久化** - token保存在`self.auth.token`中
- ✅ **方法封装** - 每个API端点都有对应的方法

---

## 📋 四、MoviePilot的简化策略

### 4.1 不主动管理Token过期

**MoviePilot的策略**:
- ❌ **不解析JWT token获取过期时间**
- ❌ **不主动刷新token**
- ✅ **被动处理** - 只在API调用失败时（401错误）才重新登录

**优点**:
- 实现简单
- 不需要解析JWT
- 不需要管理过期时间

**缺点**:
- 每次token失效都会导致一次失败的API调用
- 用户体验稍差（有延迟）

### 4.2 错误驱动的Token刷新

```python
def _handle_tvdb_call(self, method_name: str, *args, **kwargs):
    try:
        # 正常调用
        method = getattr(self._tvdb, method_name)
        return method(*args, **kwargs)
    except Exception as e:
        # 检测到token失效
        if "unauthorized" in str(e).lower():
            # 重新初始化（重新登录）
            self._tvdb = None
            self._initialize_tvdb_session(is_retry=True)
            # 重试
            method = getattr(self._tvdb, method_name)
            return method(*args, **kwargs)
```

**关键点**:
- ✅ **错误驱动** - 通过API错误判断token失效
- ✅ **自动重试** - 重新登录后自动重试
- ✅ **简单可靠** - 不需要复杂的token生命周期管理

### 4.3 线程安全保护

```python
self._tvdb_lock = threading.Lock()  # 线程锁

# 在重新初始化时使用锁
with self._tvdb_lock:
    self._tvdb = None
    self._initialize_tvdb_session(is_retry=True)
```

**关键点**:
- ✅ **防止并发问题** - 多个线程同时重新初始化时避免冲突
- ✅ **保证一致性** - 确保只有一个线程能重新初始化

---

## 📋 五、与VabHub实现的对比

### 5.1 复杂度对比

| 方面 | MoviePilot | 我之前建议的完整实现 |
|------|-----------|-------------------|
| **Token过期检测** | 被动（错误驱动） | 主动（解析JWT） |
| **Token刷新** | 错误时重新登录 | 提前刷新 |
| **代码复杂度** | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐⭐ 高 |
| **实现难度** | 简单 | 复杂 |
| **可靠性** | 高 | 高 |

### 5.2 MoviePilot的优势

1. **实现简单**
   - 不需要解析JWT token
   - 不需要管理过期时间
   - 代码量少（~100行）

2. **可靠性高**
   - 错误驱动的方式更可靠
   - 不依赖JWT解析（JWT格式可能变化）

3. **维护成本低**
   - 逻辑简单，易于维护
   - 不需要复杂的token生命周期管理

### 5.3 MoviePilot的缺点

1. **性能稍差**
   - 每次token失效都会导致一次失败的API调用
   - 有轻微延迟

2. **用户体验**
   - 第一次调用可能失败（如果token已过期）

---

## 📋 六、VabHub实现建议

### 6.1 采用MoviePilot的简化策略

**推荐实现**（参考MoviePilot）:

```python
class TVDBClient:
    def __init__(self, api_key: str, pin: str = ""):
        self.api_key = api_key
        self.pin = pin
        self._tvdb = None
        self._lock = asyncio.Lock()  # 异步锁
    
    async def _initialize_session(self):
        """初始化TVDB会话（登录获取token）"""
        from app.modules.tvdb.tvdb_v4_official import TVDB
        self._tvdb = TVDB(apikey=self.api_key, pin=self.pin)
    
    async def _ensure_session(self):
        """确保会话有效"""
        if self._tvdb is None:
            await self._initialize_session()
    
    async def _handle_call(self, method_name: str, *args, **kwargs):
        """包裹TVDB调用，处理token失效"""
        try:
            await self._ensure_session()
            method = getattr(self._tvdb, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            error_msg = str(e).lower()
            if "unauthorized" in error_msg or "token" in error_msg:
                logger.warning("TVDB Token失效，重新登录...")
                async with self._lock:
                    self._tvdb = None
                    await self._initialize_session()
                    method = getattr(self._tvdb, method_name)
                    return method(*args, **kwargs)
            raise
    
    async def get_series(self, series_id: int):
        """获取剧集信息"""
        return await self._handle_call("get_series_extended", series_id, short=True)
    
    async def search(self, query: str):
        """搜索剧集"""
        return await self._handle_call("search", query=query, type="series")
```

**关键点**:
- ✅ **参考MoviePilot** - 使用相同的简化策略
- ✅ **异步支持** - 使用`asyncio.Lock()`而不是`threading.Lock()`
- ✅ **错误驱动** - 通过错误判断token失效
- ✅ **自动重试** - 重新登录后自动重试

### 6.2 实现复杂度

**采用MoviePilot策略后**:
- **代码量**: ~150行（包括TVDB V4 API客户端）
- **实现难度**: ⭐⭐⭐ 中等（比完整实现简单很多）
- **预计工作量**: 1-2天（而不是2-3天）

---

## 📋 七、总结

### 7.1 MoviePilot的实现特点

1. **简化策略** - 不主动管理token过期，被动处理
2. **错误驱动** - 通过API错误判断token失效
3. **自动重试** - 重新登录后自动重试
4. **线程安全** - 使用锁保护并发访问

### 7.2 为什么MoviePilot的实现更简单？

1. **不需要解析JWT** - 不关心token过期时间
2. **不需要主动刷新** - 只在失败时重新登录
3. **错误处理简单** - 统一通过异常处理

### 7.3 VabHub实现建议

**采用MoviePilot的简化策略**:
- ✅ 实现简单（~150行代码）
- ✅ 可靠性高（错误驱动）
- ✅ 维护成本低（逻辑简单）
- ✅ 预计工作量：1-2天（而不是2-3天）

**实施步骤**:
1. 复制TVDB V4 API客户端（`tvdb_v4_official.py`）
2. 实现TVDB模块（参考MoviePilot的`__init__.py`）
3. 集成到媒体识别服务

---

**文档生成时间**: 2025-01-XX  
**文档版本**: 1.0

