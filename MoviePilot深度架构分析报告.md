# MoviePilot 深度架构分析报告

## 📋 概述

本报告深入分析MoviePilot的核心架构、前后端关联关系，以及每个WebUI功能对应的后端实现。

---

## 🏗️ 核心架构模式

### 1. Chain（处理链）模式

MoviePilot采用**Chain（处理链）模式**作为核心架构，这是整个系统的基础设计模式。

#### 1.1 ChainBase（处理链基类）

**位置**: `app/chain/__init__.py`

**核心特性**:
- **模块调度**: 通过`run_module()`和`async_run_module()`方法统一调用模块
- **插件支持**: 支持系统模块和插件模块的混合执行
- **优先级控制**: 模块按优先级顺序执行
- **错误处理**: 统一的错误处理和日志记录
- **缓存机制**: 内置文件缓存和异步缓存支持

**关键方法**:
```python
def run_module(self, method: str, *args, **kwargs) -> Any:
    """
    运行包含该方法的所有模块，然后返回结果
    """
    # 1. 先执行插件模块
    result = self.__execute_plugin_modules(method, result, *args, **kwargs)
    
    # 2. 再执行系统模块
    return self.__execute_system_modules(method, result, *args, **kwargs)
```

#### 1.2 StorageChain（存储处理链）

**位置**: `app/chain/storage.py`

**功能**: 统一管理所有存储相关操作

**关键方法**:
- `generate_qrcode()`: 生成二维码
- `check_login()`: 检查登录状态
- `list_files()`: 列出文件
- `create_folder()`: 创建目录
- `download_file()`: 下载文件
- `upload_file()`: 上传文件
- `delete_file()`: 删除文件
- `rename_file()`: 重命名文件
- `storage_usage()`: 获取存储使用情况

**调用流程**:
```
API Endpoint -> StorageChain.run_module() -> FileManagerModule -> StorageBase实现
```

---

### 2. 模块系统（Module System）

#### 2.1 ModuleManager（模块管理器）

**位置**: `app/core/module.py`

**功能**: 动态加载和管理所有模块

**特性**:
- 自动发现和加载模块
- 模块优先级管理
- 模块方法注册和调用
- 插件模块支持

#### 2.2 FileManagerModule（文件管理模块）

**位置**: `app/modules/filemanager/__init__.py`

**功能**: 统一管理所有存储提供商

**核心逻辑**:
```python
def __get_storage_oper(self, _storage: str, _func: Optional[str] = None) -> Optional[StorageBase]:
    """
    获取存储操作对象
    """
    for storage_schema in self._storage_schemas:
        if storage_schema.schema.value == _storage:
            return storage_schema()
    return None
```

**支持的操作**:
- 文件浏览（list_files）
- 目录创建（create_folder）
- 文件删除（delete_file）
- 文件重命名（rename_file）
- 文件下载（download_file）
- 文件上传（upload_file）
- 存储使用情况（storage_usage）
- 二维码生成（generate_qrcode）
- 登录检查（check_login）

---

### 3. 存储抽象层（Storage Abstraction）

#### 3.1 StorageBase（存储基类）

**位置**: `app/modules/filemanager/storages/__init__.py`

**设计模式**: 抽象基类（ABCMeta）

**核心方法**（所有存储提供商必须实现）:
- `init_storage()`: 初始化存储
- `check()`: 检查存储是否可用
- `list()`: 浏览文件
- `create_folder()`: 创建目录
- `get_folder()`: 获取目录（不存在则创建）
- `get_item()`: 获取文件或目录
- `delete()`: 删除文件
- `rename()`: 重命名文件
- `download()`: 下载文件
- `upload()`: 上传文件
- `detail()`: 获取文件详情
- `copy()`: 复制文件
- `move()`: 移动文件
- `link()`: 硬链接文件
- `softlink()`: 软链接文件
- `usage()`: 存储使用情况

**可选方法**:
- `generate_qrcode()`: 生成二维码（115网盘等）
- `check_login()`: 检查登录状态（115网盘等）

#### 3.2 存储提供商实现

**支持的存储类型**:
1. **U115Pan** (115网盘) - `app/modules/filemanager/storages/u115.py`
2. **Rclone** (RClone) - `app/modules/filemanager/storages/rclone.py`
3. **AliPan** (阿里云盘) - `app/modules/filemanager/storages/alipan.py`
4. **Alist** (Alist) - `app/modules/filemanager/storages/alist.py`
5. **SMB** (SMB) - `app/modules/filemanager/storages/smb.py`
6. **LocalStorage** (本地存储) - `app/modules/filemanager/storages/local.py`

---

## 🔌 115网盘深度实现分析

### 1. U115Pan类

**位置**: `app/modules/filemanager/storages/u115.py`

#### 1.1 认证流程

**PKCE规范实现**:
```python
def generate_qrcode(self) -> Tuple[dict, str]:
    """
    实现PKCE规范的设备授权二维码生成
    """
    # 1. 生成PKCE参数
    code_verifier = secrets.token_urlsafe(96)[:128]
    code_challenge = base64.b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).decode("utf-8")
    
    # 2. 请求设备码
    resp = self.session.post(
        "https://passportapi.115.com/open/authDeviceCode",
        data={
            "client_id": settings.U115_APP_ID,
            "code_challenge": code_challenge,
            "code_challenge_method": "sha256"
        }
    )
    
    # 3. 持久化验证参数
    self._auth_state = {
        "code_verifier": code_verifier,
        "uid": result["data"]["uid"],
        "time": result["data"]["time"],
        "sign": result["data"]["sign"]
    }
    
    # 4. 返回二维码内容
    return {
        "codeContent": result['data']['qrcode']
    }, ""
```

**登录状态检查**:
```python
def check_login(self) -> Optional[Tuple[dict, str]]:
    """
    改进的带PKCE校验的登录状态检查
    """
    # 1. 检查二维码状态
    resp = self.session.get(
        "https://qrcodeapi.115.com/get/status/",
        params={
            "uid": self._auth_state["uid"],
            "time": self._auth_state["time"],
            "sign": self._auth_state["sign"]
        }
    )
    
    # 2. 如果登录成功（status == 2），获取token
    if result["data"]["status"] == 2:
        tokens = self.__get_access_token()
        self.set_config({
            "refresh_time": int(time.time()),
            **tokens
        })
    
    return {"status": result["data"]["status"], "tip": result["data"]["msg"]}, ""
```

**Token刷新**:
```python
def __refresh_access_token(self, refresh_token: str) -> Optional[dict]:
    """
    刷新access_token
    """
    resp = self.session.post(
        "https://passportapi.115.com/open/refreshToken",
        data={
            "refresh_token": refresh_token
        }
    )
    return result.get("data")
```

#### 1.2 文件上传流程

**完整的秒传、断点续传、二次认证实现**:

1. **Step 1: 初始化上传**
   - 计算文件SHA1和PREID
   - 调用`/open/upload/init`接口
   - 获取OSS上传凭证和回调信息

2. **Step 2: 处理二次认证**（如果需要）
   - 如果返回码为700或701，需要进行二次认证
   - 计算指定区间的SHA1值
   - 重新调用初始化接口

3. **Step 3: 秒传检查**
   - 如果`status == 2`，说明文件已存在，秒传成功
   - 直接返回文件信息

4. **Step 4: 获取上传凭证**
   - 调用`/open/upload/get_token`接口
   - 获取OSS的AccessKeyId、AccessKeySecret、SecurityToken

5. **Step 5: 断点续传检查**
   - 调用`/open/upload/resume`接口
   - 检查是否有未完成的上传任务

6. **Step 6: 对象存储上传**
   - 使用OSS2库进行分片上传
   - 每个分片10MB
   - 实时更新进度
   - 完成后调用回调接口

#### 1.3 文件下载流程

1. **获取下载链接**: 调用`/open/ufile/downurl`接口
2. **流式下载**: 使用requests的stream功能
3. **进度更新**: 实时更新下载进度
4. **错误处理**: 网络错误时删除部分下载的文件

#### 1.4 文件列表流程

1. **获取目录CID**: 根目录为'0'，其他目录通过fileid获取
2. **分页获取**: 每次获取1000条，使用offset分页
3. **数据转换**: 将115网盘数据格式转换为统一的FileItem格式

#### 1.5 存储使用情况

```python
def usage(self) -> Optional[schemas.StorageUsage]:
    """
    获取带有企业级配额信息的存储使用情况
    """
    resp = self._request_api(
        "GET",
        "/open/user/info",
        "data"
    )
    space = resp["rt_space_info"]
    return schemas.StorageUsage(
        total=space["all_total"]["size"],
        available=space["all_remain"]["size"]
    )
```

---

## 🔄 RClone实现分析

### 1. Rclone类

**位置**: `app/modules/filemanager/storages/rclone.py`

#### 1.1 核心特性

- **命令行调用**: 通过subprocess调用rclone命令
- **JSON解析**: 使用`rclone lsjson`命令获取文件列表
- **进度监控**: 解析rclone的进度输出
- **跨平台支持**: Windows和Linux/Mac都支持

#### 1.2 关键方法

**文件列表**:
```python
def list(self, fileitem: schemas.FileItem) -> List[schemas.FileItem]:
    """
    浏览文件
    """
    ret = subprocess.run(
        [
            'rclone', 'lsjson',
            f'MP:{fileitem.path}'
        ],
        capture_output=True,
        startupinfo=self.__get_hidden_shell()
    )
    items = json.loads(ret.stdout)
    return [self.__get_rcloneitem(item, parent=fileitem.path) for item in items]
```

**进度解析**:
```python
def __parse_rclone_progress(line: str) -> Optional[float]:
    """
    解析rclone进度输出
    """
    # 支持多种进度输出格式
    # "Transferred: 1.234M / 5.678M, 22%, 1.234MB/s, ETA 2m3s"
    if 'ETA' in line:
        percent_str = line.split('%')[0].split()[-1]
        return float(percent_str)
    # ...
```

---

## 🌐 API层架构

### 1. API端点

**位置**: `app/api/endpoints/storage.py`

#### 1.1 二维码相关

```python
@router.get("/qrcode/{name}", summary="生成二维码内容")
def qrcode(name: str, _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    生成二维码
    """
    qrcode_data, errmsg = StorageChain().generate_qrcode(name)
    return schemas.Response(success=True, data=qrcode_data, message=errmsg)

@router.get("/check/{name}", summary="二维码登录确认")
def check(name: str, ck: Optional[str] = None, t: Optional[str] = None,
          _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    二维码登录确认
    """
    data, errmsg = StorageChain().check_login(name, ck=ck, t=t)
    return schemas.Response(success=True, data=data)
```

#### 1.2 文件操作

```python
@router.post("/list", summary="所有目录和文件")
def list_files(fileitem: schemas.FileItem,
               sort: Optional[str] = 'updated_at',
               _: User = Depends(get_current_active_superuser)) -> Any:
    """
    查询当前目录下所有目录和文件
    """
    file_list = StorageChain().list_files(fileitem)
    # 排序处理
    if sort == "name":
        file_list.sort(key=lambda x: StringUtils.natural_sort_key(x.name or ""))
    else:
        file_list.sort(key=lambda x: x.modify_time or datetime.min, reverse=True)
    return file_list
```

#### 1.3 配置管理

```python
@router.post("/save/{name}", summary="保存存储配置")
def save(name: str, conf: dict, _: User = Depends(get_current_active_superuser)) -> Any:
    """
    保存存储配置
    """
    StorageChain().save_config(name, conf)
    return schemas.Response(success=True)
```

---

## 🎨 前端-后端关联分析

### 1. 存储设置页面

**前端文件**: `MoviePilot-Frontend-2/src/views/setup/StorageSettingsStep.vue`

#### 1.1 二维码登录流程

**前端调用**:
```typescript
// 1. 生成二维码
const qrcodeData = await api.get(`/api/v1/storage/qrcode/${storageName}`)

// 2. 轮询检查登录状态
const checkLogin = async () => {
    const result = await api.get(`/api/v1/storage/check/${storageName}`)
    if (result.data.status === 2) {
        // 登录成功
        // 刷新存储列表
    }
}
```

**后端处理**:
```
前端请求 -> API Endpoint -> StorageChain.generate_qrcode() -> 
FileManagerModule.generate_qrcode() -> U115Pan.generate_qrcode() -> 
返回二维码数据 -> 前端显示二维码 -> 
前端轮询检查 -> API Endpoint -> StorageChain.check_login() -> 
FileManagerModule.check_login() -> U115Pan.check_login() -> 
返回登录状态 -> 前端处理
```

#### 1.2 文件列表展示

**前端调用**:
```typescript
const fileList = await api.post('/api/v1/storage/list', {
    storage: 'u115',
    path: '/',
    fileid: '0'
})
```

**后端处理**:
```
前端请求 -> API Endpoint -> StorageChain.list_files() -> 
FileManagerModule.list_files() -> U115Pan.list() -> 
返回文件列表 -> 前端展示
```

### 2. 存储卡片组件

**前端文件**: `MoviePilot-Frontend-2/src/components/cards/StorageCard.vue`

**功能**:
- 显示存储名称和类型
- 显示存储使用情况
- 显示登录状态
- 提供登录/登出按钮
- 提供文件管理入口

**API调用**:
- `GET /api/v1/storage/usage/{name}`: 获取存储使用情况
- `GET /api/v1/storage/qrcode/{name}`: 生成二维码
- `GET /api/v1/storage/check/{name}`: 检查登录状态

---

## 📊 数据流图

### 1. 存储操作完整流程

```
┌─────────────┐
│  前端页面   │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────┐
│  API Layer  │ (app/api/endpoints/storage.py)
└──────┬──────┘
       │ StorageChain().method()
       ▼
┌─────────────┐
│ Chain Layer │ (app/chain/storage.py)
└──────┬──────┘
       │ run_module()
       ▼
┌─────────────┐
│Module Layer │ (app/modules/filemanager/__init__.py)
└──────┬──────┘
       │ __get_storage_oper()
       ▼
┌─────────────┐
│Storage Base │ (app/modules/filemanager/storages/u115.py)
└──────┬──────┘
       │ API Call
       ▼
┌─────────────┐
│ 115 API     │ (https://proapi.115.com)
└─────────────┘
```

### 2. 模块执行流程

```
StorageChain.run_module("list_files")
    │
    ├─> __execute_plugin_modules()
    │   └─> 插件模块（如果有）
    │
    └─> __execute_system_modules()
        └─> FileManagerModule.list_files()
            └─> U115Pan.list()
                └─> _request_api()
                    └─> 115 API
```

---

## 🔐 配置管理

### 1. StorageHelper

**位置**: `app/helper/storage.py`

**功能**: 统一管理存储配置

**关键方法**:
- `get_storagies()`: 获取所有存储配置
- `get_storage()`: 获取指定存储配置
- `set_storage()`: 设置存储配置
- `add_storage()`: 添加存储配置
- `reset_storage()`: 重置存储配置

**配置存储**: 使用`SystemConfigOper`存储在数据库中

### 2. 配置结构

```python
class StorageConf:
    type: str  # 存储类型（u115, rclone等）
    name: str  # 存储名称
    config: dict  # 存储配置（token、密钥等）
```

---

## 🎯 关键设计模式

### 1. 策略模式（Strategy Pattern）

**应用**: 存储提供商的选择

```python
# 不同的存储提供商实现相同的接口
class U115Pan(StorageBase): ...
class Rclone(StorageBase): ...
class AliPan(StorageBase): ...

# 运行时动态选择
storage_oper = self.__get_storage_oper(storage_type)
result = storage_oper.list(fileitem)
```

### 2. 模板方法模式（Template Method Pattern）

**应用**: StorageBase定义模板方法，子类实现具体逻辑

### 3. 工厂模式（Factory Pattern）

**应用**: ModuleManager动态创建模块实例

### 4. 责任链模式（Chain of Responsibility Pattern）

**应用**: ChainBase的模块调用链

---

## 🔍 前后端关联总结

### 1. WebUI功能 -> 后端API映射

| WebUI功能 | 前端组件 | 后端API | Chain方法 | 模块方法 | 存储方法 |
|---------|---------|---------|-----------|----------|----------|
| 生成二维码 | StorageSettingsStep.vue | GET /api/v1/storage/qrcode/{name} | generate_qrcode() | generate_qrcode() | U115Pan.generate_qrcode() |
| 检查登录 | StorageSettingsStep.vue | GET /api/v1/storage/check/{name} | check_login() | check_login() | U115Pan.check_login() |
| 文件列表 | StorageCard.vue | POST /api/v1/storage/list | list_files() | list_files() | U115Pan.list() |
| 创建目录 | 文件管理器 | POST /api/v1/storage/mkdir | create_folder() | create_folder() | U115Pan.create_folder() |
| 删除文件 | 文件管理器 | POST /api/v1/storage/delete | delete_file() | delete_file() | U115Pan.delete() |
| 下载文件 | 文件管理器 | POST /api/v1/storage/download | download_file() | download_file() | U115Pan.download() |
| 重命名文件 | 文件管理器 | POST /api/v1/storage/rename | rename_file() | rename_file() | U115Pan.rename() |
| 存储使用情况 | StorageCard.vue | GET /api/v1/storage/usage/{name} | storage_usage() | storage_usage() | U115Pan.usage() |
| 保存配置 | StorageSettingsStep.vue | POST /api/v1/storage/save/{name} | save_config() | save_config() | StorageHelper.set_storage() |
| 重置配置 | StorageSettingsStep.vue | GET /api/v1/storage/reset/{name} | reset_config() | reset_config() | StorageHelper.reset_storage() |

### 2. 数据模型

#### 2.1 FileItem（文件项）

```python
class FileItem:
    storage: str  # 存储类型
    fileid: str  # 文件ID
    parent_fileid: str  # 父目录ID
    name: str  # 文件名
    basename: str  # 基础名称
    extension: str  # 扩展名
    type: str  # 类型（file/dir）
    path: str  # 路径
    size: int  # 大小
    modify_time: int  # 修改时间
    pickcode: str  # 提取码（115网盘）
```

#### 2.2 StorageUsage（存储使用情况）

```python
class StorageUsage:
    total: int  # 总空间
    available: int  # 可用空间
    used: int  # 已用空间（计算得出）
    percentage: float  # 使用率（计算得出）
```

---

## 🚀 优化建议

### 1. 当前VabHub实现的问题

1. **缺少Chain层**: 直接调用Service，缺少统一的处理链
2. **存储抽象不完整**: 没有统一的StorageBase基类
3. **配置管理分散**: 配置存储在数据库，但管理逻辑分散
4. **错误处理不统一**: 缺少统一的错误处理机制

### 2. 改进方案

1. **引入Chain模式**: 创建StorageChain统一管理存储操作
2. **完善存储抽象**: 创建StorageBase基类，统一接口
3. **统一配置管理**: 使用StorageHelper统一管理配置
4. **完善错误处理**: 在Chain层统一处理错误

---

## 📝 总结

MoviePilot的核心架构特点：

1. **Chain模式**: 统一的处理链，支持模块化扩展
2. **存储抽象**: 统一的存储接口，支持多种存储提供商
3. **模块系统**: 动态加载和管理模块，支持插件扩展
4. **API层**: 清晰的API端点，统一的数据模型
5. **配置管理**: 集中的配置管理，统一的存储方式

这些设计模式使得MoviePilot具有高度的可扩展性和可维护性。

---

**最后更新**: 2025-11-08  
**分析版本**: MoviePilot-2  
**分析范围**: 存储管理、115网盘、RClone、前后端关联

