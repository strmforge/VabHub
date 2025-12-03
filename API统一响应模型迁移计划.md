# API统一响应模型迁移计划

## 📋 概述

将现有API迁移到统一响应模型（`BaseResponse`、`PaginatedResponse`、`ErrorResponse`），提升API一致性和前端开发体验。

## 🎯 目标

1. **统一响应格式**：所有API使用统一的响应格式
2. **提升一致性**：前端可以统一处理响应
3. **改善错误处理**：统一的错误响应格式
4. **向后兼容**：保持现有功能不变

## 📊 统一响应模型

### BaseResponse
```python
class BaseResponse(BaseModel):
    success: bool = True
    message: str = "success"
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
```

### PaginatedResponse
```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

### ErrorResponse
```python
class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
```

## 📝 迁移规则

### 1. 单个对象响应
**迁移前**：
```python
@router.get("/{id}", response_model=SubscriptionResponse)
async def get_subscription(id: int):
    return subscription
```

**迁移后**：
```python
@router.get("/{id}", response_model=BaseResponse)
async def get_subscription(id: int):
    return BaseResponse(
        success=True,
        message="获取成功",
        data=subscription
    )
```

### 2. 列表响应
**迁移前**：
```python
@router.get("/", response_model=List[SubscriptionResponse])
async def list_subscriptions():
    return subscriptions
```

**迁移后**：
```python
@router.get("/", response_model=BaseResponse)
async def list_subscriptions():
    return BaseResponse(
        success=True,
        message="获取成功",
        data=subscriptions
    )
```

### 3. 分页响应
**迁移前**：
```python
@router.get("/", response_model=List[SubscriptionResponse])
async def list_subscriptions(page: int = 1, page_size: int = 20):
    return subscriptions
```

**迁移后**：
```python
@router.get("/", response_model=PaginatedResponse[SubscriptionResponse])
async def list_subscriptions(page: int = 1, page_size: int = 20):
    return PaginatedResponse.create(
        items=subscriptions,
        total=total,
        page=page,
        page_size=page_size
    )
```

### 4. 错误响应
**迁移前**：
```python
if not subscription:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="订阅不存在"
    )
```

**迁移后**：
```python
if not subscription:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=NotFoundResponse(
            error_code="NOT_FOUND",
            error_message="订阅不存在"
        ).model_dump_json()
    )
```

## 📋 迁移清单

### 优先级1：核心模块（高优先级）⭐⭐⭐

#### 1. 订阅管理API (`subscription.py`)
- [ ] `GET /subscriptions/` - 列表（支持分页）
- [ ] `GET /subscriptions/{id}` - 详情
- [ ] `POST /subscriptions/` - 创建
- [ ] `PUT /subscriptions/{id}` - 更新
- [ ] `DELETE /subscriptions/{id}` - 删除
- [ ] `POST /subscriptions/{id}/enable` - 启用
- [ ] `POST /subscriptions/{id}/disable` - 禁用
- [ ] `POST /subscriptions/{id}/search` - 执行搜索

#### 2. 下载管理API (`download.py`)
- [ ] `GET /downloads/` - 列表
- [ ] `GET /downloads/{id}` - 详情
- [ ] `POST /downloads/` - 创建
- [ ] `POST /downloads/{id}/pause` - 暂停
- [ ] `POST /downloads/{id}/resume` - 恢复
- [ ] `DELETE /downloads/{id}` - 删除

#### 3. 搜索系统API (`search.py`)
- [ ] `POST /search/` - 搜索
- [ ] `GET /search/history` - 搜索历史
- [ ] `GET /search/suggestions` - 搜索建议

### 优先级2：其他模块（中优先级）⭐⭐

#### 4. 站点管理API (`site.py`)
- [ ] 所有端点

#### 5. 工作流API (`workflow.py`)
- [ ] 所有端点

#### 6. 通知API (`notification.py`)
- [ ] 所有端点

#### 7. 音乐API (`music.py`)
- [ ] 所有端点

#### 8. 其他API
- [ ] 仪表盘API (`dashboard.py`)
- [ ] 日历API (`calendar.py`)
- [ ] 设置API (`settings.py`)
- [ ] HNR检测API (`hnr.py`)
- [ ] 推荐API (`recommendation.py`)
- [ ] 媒体识别API (`media_identification.py`)
- [ ] 云存储API (`cloud_storage.py`)

## 🚀 迁移步骤

### 步骤1：创建辅助函数（可选）
创建辅助函数简化迁移：
```python
def success_response(data: Any, message: str = "success") -> BaseResponse:
    """创建成功响应"""
    return BaseResponse(success=True, message=message, data=data)

def error_response(error_code: str, error_message: str, details: Optional[Dict] = None) -> ErrorResponse:
    """创建错误响应"""
    return ErrorResponse(
        success=False,
        error_code=error_code,
        error_message=error_message,
        details=details
    )
```

### 步骤2：逐个模块迁移
1. 选择一个模块（如subscription.py）
2. 更新所有端点使用统一响应模型
3. 更新错误处理
4. 测试验证
5. 更新文档

### 步骤3：测试验证
1. 单元测试
2. 集成测试
3. 前端联调测试

## 📝 注意事项

### 1. 保持向后兼容
- 考虑前端是否已经依赖现有格式
- 可能需要同时支持新旧格式（通过版本控制）

### 2. 错误处理
- 使用统一的错误响应格式
- 保持HTTP状态码不变
- 错误信息要清晰明确

### 3. 分页处理
- 统一使用`PaginatedResponse`
- 统一分页参数（page, page_size）
- 计算总页数

### 4. 测试
- 每个迁移的端点都要测试
- 确保响应格式正确
- 确保错误处理正确

## ✅ 迁移检查清单

对于每个API端点，检查：
- [ ] 响应模型已更新为`BaseResponse`或`PaginatedResponse`
- [ ] 成功响应使用`BaseResponse`
- [ ] 错误响应使用`ErrorResponse`或特定错误响应类
- [ ] 分页响应使用`PaginatedResponse`
- [ ] 错误处理已更新
- [ ] 测试已更新
- [ ] 文档已更新

---

**状态**: 📋 计划制定完成  
**开始时间**: 2025-01-XX  
**预计完成时间**: 1-2周

