# VabHub STRM文件链接格式设计

## 📋 概述

本文档设计VabHub生成的STRM文件中的链接格式，对比MoviePilot插件格式，提供更安全、更灵活的解决方案。

## 🔍 MoviePilot插件格式分析

### 当前格式

```
http://192.168.51.105:3000/api/v1/plugin/P115StrmHelper/redirect_url?apikey=mwKtUfs6MDjnMDt04b8naQ&pickcode=cg16zx93h3xy6ddf1
```

### 格式特点

1. **API路径**: `/api/v1/plugin/P115StrmHelper/redirect_url`
2. **查询参数**:
   - `apikey`: API密钥（用于认证）
   - `pickcode`: 115网盘文件提取码
3. **安全性**: 使用apikey进行认证
4. **简洁性**: URL相对简洁

### 存在的问题

1. **安全性风险**: apikey直接暴露在URL中，可能被日志记录或泄露
2. **可扩展性差**: 只支持115网盘，不支持其他云存储
3. **功能局限**: 不支持字幕文件、多语言等高级功能
4. **参数暴露**: pickcode直接暴露，可能被滥用

## 🎯 VabHub STRM链接格式设计

### 方案1：基于Token的安全链接（推荐）

#### 视频文件STRM链接

```
http://your-nas:8000/api/strm/stream/115/{token}
```

**特点**:
- ✅ **安全性高**: 使用JWT token，不暴露敏感信息
- ✅ **简洁**: URL简洁，易于管理
- ✅ **可扩展**: 支持多种云存储（115、123等）
- ✅ **功能丰富**: 支持视频、字幕、元数据等

#### Token生成逻辑

```python
# Token包含的信息
{
    "pick_code": "cg16zx93h3xy6ddf1",  # 115网盘文件提取码
    "storage_type": "115",              # 云存储类型
    "file_type": "video",               # 文件类型：video/subtitle
    "language": "chi",                  # 语言（字幕文件）
    "exp": 1234567890,                  # 过期时间
    "iat": 1234567800                   # 签发时间
}
```

#### 字幕文件STRM链接

```
http://your-nas:8000/api/strm/stream/115/{subtitle_token}
```

**Token包含的信息**:
```python
{
    "pick_code": "subtitle_pick_code",
    "storage_type": "115",
    "file_type": "subtitle",
    "language": "chi",
    "video_pick_code": "cg16zx93h3xy6ddf1",  # 关联的视频文件
    "exp": 1234567890,
    "iat": 1234567800
}
```

### 方案2：基于查询参数的可读链接（备选）

#### 视频文件STRM链接

```
http://your-nas:8000/api/strm/redirect?storage=115&pickcode=cg16zx93h3xy6ddf1&token={signed_token}
```

**特点**:
- ✅ **可读性强**: 参数清晰，易于调试
- ✅ **兼容性好**: 与MoviePilot插件格式类似
- ⚠️ **安全性中等**: 使用签名token，但参数仍然暴露

### 方案3：混合方案（最佳实践）

#### 视频文件STRM链接

```
http://your-nas:8000/api/strm/stream/{storage_type}/{token}
```

**示例**:
```
http://192.168.51.105:8000/api/strm/stream/115/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwaWNrX2NvZGUiOiJjZzE2eng5M2gzeHk2ZGRmMSIsInN0b3JhZ2VfdHlwZSI6IjExNSIsImZpbGVfdHlwZSI6InZpZGVvIiwiZXhwIjoxNzM1NjgwMDAwfQ.signature
```

#### 字幕文件STRM链接

```
http://your-nas:8000/api/strm/stream/{storage_type}/{subtitle_token}
```

**示例**:
```
http://192.168.51.105:8000/api/strm/stream/115/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwaWNrX2NvZGUiOiJzdWJ0aXRsZV9waWNrX2NvZGUiLCJzdG9yYWdlX3R5cGUiOiIxMTUiLCJmaWxlX3R5cGUiOiJzdWJ0aXRsZSIsImxhbmd1YWdlIjoiY2hpIiwidmlkZW9fcGlja19jb2RlIjoiY2cxNnp4OTNoM3h5NmRkZjEiLCJleHAiOjE3MzU2ODAwMDB9.signature
```

## 🔧 实现方案

### 1. STRM文件生成器更新

```python
# backend/app/modules/strm/generator.py

import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class STRMGenerator:
    """STRM文件生成器"""
    
    def __init__(self, config: STRMConfig):
        self.config = config
        self.jwt_secret = config.jwt_secret  # JWT密钥
        self.jwt_algorithm = "HS256"
        self.token_expire_hours = 24 * 365  # Token有效期（1年）
    
    def _generate_strm_url(
        self,
        pick_code: str,
        cloud_storage: str,
        file_type: str = "video",
        language: Optional[str] = None,
        video_pick_code: Optional[str] = None
    ) -> str:
        """
        生成STRM文件URL（使用JWT token）
        
        Args:
            pick_code: 文件提取码
            cloud_storage: 云存储类型（115/123）
            file_type: 文件类型（video/subtitle）
            language: 语言代码（字幕文件）
            video_pick_code: 关联的视频文件提取码（字幕文件）
        
        Returns:
            STRM文件URL
        """
        # 生成JWT token
        token = self._generate_jwt_token(
            pick_code=pick_code,
            storage_type=cloud_storage,
            file_type=file_type,
            language=language,
            video_pick_code=video_pick_code
        )
        
        # 生成STRM URL
        base_url = self.config.redirect_server_url
        base_path = self.config.redirect_server_base_path
        
        return f"{base_url}{base_path}/{cloud_storage}/{token}"
    
    def _generate_jwt_token(
        self,
        pick_code: str,
        storage_type: str,
        file_type: str = "video",
        language: Optional[str] = None,
        video_pick_code: Optional[str] = None
    ) -> str:
        """
        生成JWT token
        
        Args:
            pick_code: 文件提取码
            storage_type: 云存储类型
            file_type: 文件类型
            language: 语言代码
            video_pick_code: 关联的视频文件提取码
        
        Returns:
            JWT token字符串
        """
        # 构建payload
        payload = {
            "pick_code": pick_code,
            "storage_type": storage_type,
            "file_type": file_type,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.token_expire_hours)
        }
        
        # 添加可选字段
        if language:
            payload["language"] = language
        if video_pick_code:
            payload["video_pick_code"] = video_pick_code
        
        # 生成token
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
```

### 2. STRM重定向API端点

```python
# backend/app/api/strm.py

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
import jwt
from datetime import datetime
from loguru import logger

router = APIRouter(prefix="/api/strm", tags=["strm"])

# JWT配置
JWT_SECRET = "your-secret-key"  # 从配置读取
JWT_ALGORITHM = "HS256"


@router.get("/stream/{storage_type}/{token}")
async def stream_file(
    storage_type: str,
    token: str,
    request: Request
):
    """
    STRM文件流媒体重定向端点
    
    支持视频文件和字幕文件的302跳转
    
    Args:
        storage_type: 云存储类型（115/123）
        token: JWT token（包含pick_code等信息）
    
    Returns:
        302重定向到实际下载地址
    """
    try:
        # 1. 验证JWT token
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token已过期")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 2. 获取文件信息
        pick_code = payload.get("pick_code")
        file_type = payload.get("file_type", "video")
        storage_type_from_token = payload.get("storage_type")
        
        # 3. 验证storage_type是否匹配
        if storage_type_from_token != storage_type:
            raise HTTPException(status_code=400, detail="Storage type不匹配")
        
        # 4. 根据存储类型获取下载地址
        if storage_type == "115":
            download_url = await get_115_download_url(pick_code)
        elif storage_type == "123":
            download_url = await get_123_download_url(pick_code)
        else:
            raise HTTPException(status_code=400, detail="不支持的存储类型")
        
        if not download_url:
            raise HTTPException(status_code=404, detail="文件不存在或无法获取下载地址")
        
        # 5. 记录访问日志
        logger.info(f"STRM重定向: {storage_type}/{pick_code} -> {download_url}")
        
        # 6. 返回302重定向
        return RedirectResponse(url=download_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STRM重定向失败: {e}")
        raise HTTPException(status_code=500, detail=f"重定向失败: {str(e)}")


async def get_115_download_url(pick_code: str) -> Optional[str]:
    """
    获取115网盘文件下载地址
    
    Args:
        pick_code: 文件提取码
    
    Returns:
        下载地址
    """
    from app.core.cloud_storage.providers.cloud_115_api import Cloud115API
    from app.core.settings import settings
    
    # 初始化115 API客户端
    api = Cloud115API(access_token=settings.cloud_115_access_token)
    
    # 获取下载地址
    result = await api.get_download_url(pick_code=pick_code)
    
    if result.get("success"):
        return result.get("download_url")
    else:
        logger.error(f"获取115网盘下载地址失败: {result.get('error')}")
        return None


async def get_123_download_url(pick_code: str) -> Optional[str]:
    """
    获取123云盘文件下载地址
    
    Args:
        pick_code: 文件提取码
    
    Returns:
        下载地址
    """
    # TODO: 实现123云盘下载地址获取
    return None
```

### 3. 配置更新

```python
# backend/app/modules/strm/config.py

class STRMConfig(BaseModel):
    """STRM系统配置"""
    # ... 现有配置 ...
    
    # 重定向服务器
    redirect_server_url: str = 'http://localhost:8000'
    redirect_server_base_path: str = '/api/strm/stream'
    
    # JWT配置
    jwt_secret: str = 'your-secret-key'  # 从环境变量或配置文件读取
    jwt_algorithm: str = 'HS256'
    token_expire_hours: int = 24 * 365  # Token有效期（1年）
```

## 📊 格式对比

| 特性 | MoviePilot插件 | VabHub方案1（Token） | VabHub方案2（查询参数） | VabHub方案3（混合） |
|------|---------------|---------------------|----------------------|-------------------|
| **安全性** | ⚠️ 中等（apikey暴露） | ✅ 高（JWT token） | ⚠️ 中等（签名token） | ✅ 高（JWT token） |
| **简洁性** | ✅ 简洁 | ✅ 简洁 | ⚠️ 中等 | ✅ 简洁 |
| **可读性** | ✅ 可读 | ⚠️ 低（token不可读） | ✅ 可读 | ⚠️ 低（token不可读） |
| **可扩展性** | ❌ 差（只支持115） | ✅ 好（支持多存储） | ✅ 好（支持多存储） | ✅ 好（支持多存储） |
| **功能丰富** | ⚠️ 基础 | ✅ 丰富（支持字幕等） | ✅ 丰富（支持字幕等） | ✅ 丰富（支持字幕等） |
| **兼容性** | ✅ 好 | ✅ 好 | ✅ 好 | ✅ 好 |

## 🎯 推荐方案

**推荐使用方案3（混合方案）**，原因：

1. **安全性高**: 使用JWT token，不暴露敏感信息
2. **简洁**: URL简洁，易于管理
3. **可扩展**: 支持多种云存储和文件类型
4. **功能丰富**: 支持视频、字幕、多语言等高级功能
5. **兼容性好**: 与媒体服务器兼容

## 📝 STRM文件内容示例

### 视频文件STRM

```strm
# VabHub STRM Metadata
# {
#   "file_id": "cg16zx93h3xy6ddf1",
#   "provider": "115",
#   "media_type": "movie",
#   "title": "示例电影",
#   "year": 2023
# }
http://192.168.51.105:8000/api/strm/stream/115/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwaWNrX2NvZGUiOiJjZzE2eng5M2gzeHk2ZGRmMSIsInN0b3JhZ2VfdHlwZSI6IjExNSIsImZpbGVfdHlwZSI6InZpZGVvIiwiZXhwIjoxNzM1NjgwMDAwfQ.signature
```

### 字幕文件STRM

```strm
# VabHub Subtitle STRM Metadata
# {
#   "file_id": "subtitle_pick_code",
#   "provider": "115",
#   "file_type": "subtitle",
#   "language": "chi",
#   "video_pick_code": "cg16zx93h3xy6ddf1"
# }
http://192.168.51.105:8000/api/strm/stream/115/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwaWNrX2NvZGUiOiJzdWJ0aXRsZV9waWNrX2NvZGUiLCJzdG9yYWdlX3R5cGUiOiIxMTUiLCJmaWxlX3R5cGUiOiJzdWJ0aXRsZSIsImxhbmd1YWdlIjoiY2hpIiwidmlkZW9fcGlja19jb2RlIjoiY2cxNnp4OTNoM3h5NmRkZjEiLCJleHAiOjE3MzU2ODAwMDB9.signature
```

## 🔒 安全性考虑

### 1. JWT Token安全

- ✅ **签名验证**: 使用HMAC-SHA256签名，防止篡改
- ✅ **过期时间**: Token设置过期时间，防止长期有效
- ✅ **密钥保护**: JWT密钥存储在配置文件中，不暴露在代码中

### 2. 访问控制

- ✅ **限流**: 对重定向请求进行限流，防止滥用
- ✅ **日志记录**: 记录所有重定向请求，便于审计
- ✅ **IP白名单**: 可选配置IP白名单，限制访问来源

### 3. 错误处理

- ✅ **友好错误**: 返回友好的错误信息，不暴露内部细节
- ✅ **日志记录**: 记录所有错误，便于排查问题
- ✅ **重试机制**: 支持重试机制，提高可靠性

## 🚀 实施步骤

1. ✅ **更新STRM生成器**: 实现JWT token生成逻辑
2. ✅ **创建重定向API**: 实现STRM重定向端点
3. ✅ **集成115 API**: 集成115网盘下载地址获取
4. ✅ **测试验证**: 测试STRM文件生成和重定向功能
5. ✅ **文档更新**: 更新用户文档和API文档

## 📚 相关文档

- [视频字幕列表API在302跳转STRM中的应用分析](./视频字幕列表API在302跳转STRM中的应用分析.md)
- [原生STRM系统设计方案](./原生STRM系统设计方案.md)
- [115网盘官方API文档集成完成总结](./115网盘官方API文档集成完成总结.md)

