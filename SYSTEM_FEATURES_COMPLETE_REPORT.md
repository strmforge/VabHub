# VabHub 系统功能全景报告

## 1. 项目概述

VabHub 是一个现代化的媒体自动化/媒体中心平台，提供全面的媒体管理、订阅、搜索、下载和播放功能。系统采用前后端分离架构，后端基于 FastAPI 构建，前端使用 Vue 3 + TypeScript + Vuetify 开发，支持多种媒体类型和下载器集成。

### 1.1 技术栈

| 类别 | 技术 | 版本/说明 |
|------|------|-----------|
| 后端框架 | FastAPI | 现代化 Python Web 框架 |
| 前端框架 | Vue 3 | 渐进式 JavaScript 框架 |
| 前端语言 | TypeScript | 类型安全的 JavaScript 超集 |
| UI 组件库 | Vuetify 3 | Material Design 风格组件库 |
| 状态管理 | Pinia | Vue 3 官方状态管理库 |
| 路由 | Vue Router | Vue 官方路由库 |
| ORM | SQLAlchemy | Python SQL 工具包和 ORM |
| 数据库 | PostgreSQL/SQLite | 支持多种数据库 |
| 缓存 | Redis | 高性能缓存系统 |
| 认证 | JWT | JSON Web Token 认证 |
| 容器化 | Docker | 容器化部署支持 |

## 2. 系统架构

### 2.1 整体架构

VabHub 采用模块化的前后端分离架构，主要包括以下核心组件：

- **后端服务**：提供 REST API 和 GraphQL API，处理业务逻辑、数据存储和外部服务集成
- **前端应用**：提供现代化的 Web UI，支持媒体浏览、搜索、订阅管理等功能
- **数据库**：存储用户数据、媒体信息、订阅配置等
- **缓存系统**：提高系统性能，减少数据库访问
- **外部服务集成**：支持多种下载器、媒体服务器、云存储等外部服务

### 2.2 核心模块

| 模块 | 主要功能 | 文件位置 |
|------|----------|----------|
| 认证系统 | 用户认证、JWT 管理 | `backend/app/core/auth.py` |
| 订阅系统 | 媒体订阅、自动搜索、自动下载 | `backend/app/modules/subscription/` |
| 搜索系统 | 多源搜索、结果过滤和排序 | `backend/app/modules/search/` |
| 下载系统 | 下载任务管理、下载器集成 | `backend/app/modules/download/` |
| 媒体管理 | 媒体识别、元数据管理 | `backend/app/modules/media/` |
| 高级规则 | 订阅规则、选种策略 | `backend/app/api/ruleset.py`、`backend/app/api/global_rules.py` |
| HR 安全策略 | HNR 检测、风险监控 | `backend/app/api/hnr.py`、`backend/app/modules/hnr/` |
| 通知系统 | 系统通知、用户通知 | `backend/app/models/user_notification.py` |

## 3. 高级规则功能实现

### 3.1 功能概述

高级规则是 VabHub 系统中的核心功能之一，用于控制订阅、搜索和下载过程中的选种策略。系统支持全局规则和订阅级规则，用户可以根据自己的需求配置不同的规则组合。

### 3.2 核心组件

#### 3.2.1 规则集管理 API

**文件位置**：`backend/app/api/ruleset.py`

**主要功能**：
- 提供规则集的获取和更新接口
- 支持 JSON 格式的规则配置
- 包含默认规则集配置

**核心代码**：
```python
# 默认规则集配置
rules = {
    "default": {
        "quality": "1080p",
        "resolution": "1920x1080",
        "min_seeders": 5,
        "sites": [],
        "include": [],
        "exclude": []
    }
}
```

#### 3.2.2 全局规则设置 API

**文件位置**：`backend/app/api/global_rules.py`

**主要功能**：
- 提供全局规则的获取、更新和重置接口
- 支持三档预设模式（A档-保种安全、B档-平衡模式、C档-老司机模式）
- 包含多种规则类型：HR策略、分辨率策略、源质量策略等

**核心代码**：
```python
# A档（保种安全）预设
a_safe_profile = {
    "hr_policy": HRPolicy.STRICT_SKIP.value,
    "resolution_policy": ResolutionPolicy.MAX_TIER.value,
    "resolution_tier": ResolutionTier.MID_1080P.value,
    "source_quality_policy": SourceQualityPolicy.NO_TRASH.value,
    "hdr_policy": HdrPolicy.SDR_ONLY.value,
    "codec_policy": CodecPolicy.ANY.value,
    "subtitle_policy": SubtitlePolicy.ANY.value,
    "audio_lang_policy": AudioLangPolicy.ANY.value,
    "extra_feature_policy": ExtraFeaturePolicy.FORBID_3D.value
}
```

#### 3.2.3 订阅规则引擎

**文件位置**：`backend/app/modules/subscription/rule_engine.py`

**主要功能**：
- 根据订阅规则过滤和排序搜索结果
- 支持多种规则类型：质量、分辨率、做种数、包含/排除关键词等
- 实现智能选种算法，根据规则计算结果分数

#### 3.2.4 订阅服务

**文件位置**：`backend/app/modules/subscription/service.py`

**主要功能**：
- 处理订阅的创建、更新、删除和搜索
- 应用高级规则进行搜索结果过滤
- 支持规则组合并和安全策略应用

**核心代码**：
```python
async def _filter_search_results(self, results: List[dict], subscription: Subscription) -> List[dict]:
    """根据订阅规则过滤搜索结果（使用规则引擎 + 安全策略 + 规则组）"""
    # 1. 应用安全策略过滤
    results = self._apply_security_filters(results, subscription)
    
    # 2. 解析规则组并合并过滤规则
    merged_include = subscription.include or ""
    merged_exclude = subscription.exclude or ""
    
    # 3. 构建订阅规则字典
    subscription_dict = {
        "quality": subscription.quality,
        "resolution": subscription.resolution,
        "effect": subscription.effect,
        "min_seeders": subscription.min_seeders,
        "include": merged_include,
        "exclude": merged_exclude,
        "media_type": subscription.media_type,
        "season": subscription.season,
        "start_episode": subscription.start_episode,
        "total_episode": subscription.total_episode
    }
    
    # 4. 使用规则引擎过滤和排序
    filtered = self.rule_engine.filter_and_sort_results(
        results,
        subscription_dict,
        sort_by="score"
    )
    
    return filtered
```

### 3.3 规则类型

VabHub 支持多种规则类型，用于控制订阅和下载过程：

| 规则类型 | 描述 | 示例值 |
|----------|------|--------|
| 质量规则 | 控制媒体质量 | 1080p, 4K |
| 分辨率规则 | 控制媒体分辨率 | 1920x1080, 3840x2160 |
| 做种数规则 | 控制最小做种数 | 5, 10 |
| 包含规则 | 包含关键词 | HDR, Dolby Atmos |
| 排除规则 | 排除关键词 | CAM, TS |
| 站点规则 | 限制搜索站点 | [1, 2, 3] |
| HR 策略 | 控制 HR 资源处理 | strict_skip, safe_skip, ignore |
| 源质量策略 | 控制源质量 | no_trash, any |
| HDR 策略 | 控制 HDR 内容 | sdr_only, any, hdr_preferred |
| 编码策略 | 控制视频编码 | any, h264_only, h265_only |

### 3.4 规则应用流程

1. **订阅创建/更新**：用户配置订阅规则，包括基础规则和进阶规则
2. **搜索执行**：系统根据订阅配置执行搜索
3. **结果过滤**：
   - 应用安全策略过滤（HR、H3/H5、免费种限制）
   - 合并规则组规则
   - 使用规则引擎过滤和排序结果
4. **智能选种**：根据规则计算结果分数，选择最佳结果
5. **下载执行**：创建下载任务，执行下载

## 4. HR 安全策略功能实现

### 4.1 功能概述

HR（Hit & Run）安全策略是 VabHub 系统的重要安全功能，用于检测和防范 HR 风险，保护用户的 PT 账号安全。系统通过 HNR（Hit & Run Risk）检测引擎，分析资源的 HR 风险，并提供多种策略来处理高风险资源。

### 4.2 核心组件

#### 4.2.1 HNR API

**文件位置**：`backend/app/api/hnr.py`

**主要功能**：
- 提供 HNR 检测接口
- 支持 HNR 监控任务管理
- 提供 HNR 风险统计

**核心代码**：
```python
@router.post("/detect", response_model=BaseResponse)
async def detect_hnr(
    request: HNRDetectionRequest,
    db = Depends(get_db)
):
    """执行HNR检测"""
    try:
        service = HNRService(db)
        detection = await service.detect_hnr(
            title=request.title,
            subtitle=request.subtitle,
            badges_text=request.badges_text,
            list_html=request.list_html,
            site_id=request.site_id,
            site_name=request.site_name,
            download_task_id=request.download_task_id
        )
        
        return success_response(
            data={
                "id": detection.id,
                "verdict": detection.verdict,
                "confidence": detection.confidence,
                "matched_rules": detection.matched_rules,
                "category": detection.category,
                "message": detection.message,
                "detected_at": detection.detected_at.isoformat() if detection.detected_at else None
            },
            message="检测完成"
        )
    except Exception as e:
        logger.error(f"执行HNR检测失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"执行HNR检测时发生错误: {str(e)}"
            ).model_dump()
        )
```

#### 4.2.2 HNR 服务

**文件位置**：`backend/app/modules/hnr/service.py`

**主要功能**：
- 实现 HNR 检测逻辑
- 管理 HNR 监控任务
- 提供风险统计和报告

#### 4.2.3 HNR 检测器

**文件位置**：`backend/app/modules/hnr/detector.py`

**主要功能**：
- 实现 HNR 检测算法
- 支持签名包加载和更新
- 提供多维度风险评估

#### 4.2.4 安全策略应用

**文件位置**：`backend/app/modules/subscription/service.py`

**主要功能**：
- 在订阅搜索中应用 HR 安全策略
- 支持多种 HR 处理策略：严格跳过、安全跳过、忽略
- 实现 Local Intel 感知，检查 HR 风险记录

**核心代码**：
```python
def _apply_security_filters(self, results: List[dict], subscription: Subscription) -> List[dict]:
    """应用安全策略过滤"""
    # 向后兼容：获取安全策略字段，默认为安全值
    allow_hr = getattr(subscription, 'allow_hr', False)
    allow_h3h5 = getattr(subscription, 'allow_h3h5', False)
    strict_free_only = getattr(subscription, 'strict_free_only', False)
    
    filtered = []
    
    for result in results:
        # HR/H&R 过滤
        if not allow_hr and result.get('is_hr', False):
            continue
        
        # H3/H5 过滤
        if not allow_h3h5 and result.get('is_hr', False):
            continue
        
        # 严格只下free过滤
        if strict_free_only and not (result.get('is_free', False) or result.get('is_half_free', False)):
            continue
        
        filtered.append(result)
    
    return filtered
```

### 4.3 HNR 检测机制

1. **资源分析**：系统分析资源标题、副标题、标签和站点信息
2. **签名匹配**：使用预定义的 HNR 签名包进行匹配
3. **风险评估**：根据匹配结果计算风险分数和置信度
4. **策略应用**：根据用户配置的 HR 策略处理结果
5. **监控跟踪**：对下载的资源进行持续监控，跟踪做种情况
6. **风险告警**：当资源存在 HR 风险时，发送告警通知

### 4.4 HR 策略类型

| 策略类型 | 描述 |
|----------|------|
| STRICT_SKIP | 严格跳过所有 HR 资源 |
| SAFE_SKIP | 跳过高风险 HR 资源，允许低风险 HR 资源 |
| IGNORE | 忽略 HR 风险，允许所有资源 |

## 5. 核心功能模块

### 5.1 认证系统

- **功能**：用户认证、JWT 管理、权限控制
- **实现**：基于 FastAPI 安全模块，使用 JWT 进行身份验证
- **文件位置**：`backend/app/core/auth.py`

### 5.2 订阅系统

- **功能**：媒体订阅、自动搜索、自动下载
- **支持的媒体类型**：电影、电视剧、短剧、音乐、动漫
- **核心流程**：订阅创建 → 定时搜索 → 结果过滤 → 智能选种 → 自动下载
- **文件位置**：`backend/app/modules/subscription/`

### 5.3 搜索系统

- **功能**：多源搜索、结果过滤和排序
- **支持的搜索源**：多种 PT 站点、媒体数据库（TMDB、TVDB）
- **搜索优化**：支持索引搜索，提高搜索速度
- **文件位置**：`backend/app/modules/search/`

### 5.4 下载系统

- **功能**：下载任务管理、下载器集成
- **支持的下载器**：qBittorrent、Transmission
- **核心功能**：任务创建、状态监控、速度限制、分类管理
- **文件位置**：`backend/app/modules/download/`

### 5.5 媒体管理

- **功能**：媒体识别、元数据管理、媒体库管理
- **支持的媒体类型**：电影、电视剧、音乐、电子书、有声书、漫画
- **元数据来源**：TMDB、TVDB、FanArt
- **文件位置**：`backend/app/modules/media/`

### 5.6 阅读中心

- **功能**：统一阅读平台，支持小说、有声书、漫画
- **核心功能**：阅读进度跟踪、书架管理、阅读设置
- **文件位置**：`backend/app/modules/reading/`

### 5.7 通知系统

- **功能**：系统通知、用户通知、多渠道推送
- **支持的通知渠道**：Web 通知、Telegram Bot
- **通知类型**：订阅命中、下载完成、HR 风险告警等
- **文件位置**：`backend/app/models/user_notification.py`

### 5.8 插件系统

- **功能**：支持插件扩展，增强系统功能
- **插件类型**：站点插件、下载器插件、媒体处理插件
- **插件市场**：支持远程插件安装和更新
- **文件位置**：`backend/app/api/plugins.py`

## 6. 数据模型

### 6.1 核心数据模型

| 模型 | 主要功能 | 文件位置 |
|------|----------|----------|
| User | 用户信息 | `backend/app/models/user.py` |
| Subscription | 订阅配置 | `backend/app/models/subscription.py` |
| DownloadTask | 下载任务 | `backend/app/models/download.py` |
| Media | 媒体信息 | `backend/app/models/media.py` |
| MediaFile | 媒体文件 | `backend/app/models/media.py` |
| HNRDetection | HNR 检测记录 | `backend/app/models/hnr.py` |
| HNRTask | HNR 监控任务 | `backend/app/models/hnr.py` |
| UserNotification | 用户通知 | `backend/app/models/user_notification.py` |
| Plugin | 插件信息 | `backend/app/models/plugin.py` |

### 6.2 模型关系

- **User** → **Subscription**：一对多，一个用户可以有多个订阅
- **Subscription** → **DownloadTask**：一对多，一个订阅可以创建多个下载任务
- **Media** → **MediaFile**：一对多，一个媒体可以有多个文件
- **DownloadTask** → **HNRDetection**：一对一，一个下载任务对应一个 HNR 检测记录
- **DownloadTask** → **HNRTask**：一对一，一个下载任务对应一个 HNR 监控任务

## 7. 前端架构

### 7.1 核心组件

| 组件 | 主要功能 | 文件位置 |
|------|----------|----------|
| App.vue | 应用根组件 | `frontend/src/App.vue` |
| DefaultLayout | 默认布局 | `frontend/src/layouts/DefaultLayout.vue` |
| HomeDashboard | 首页仪表盘 | `frontend/src/pages/HomeDashboard.vue` |
| Search | 搜索页面 | `frontend/src/pages/Search.vue` |
| Subscriptions | 订阅管理 | `frontend/src/pages/Subscriptions.vue` |
| Downloads | 下载管理 | `frontend/src/pages/Downloads.vue` |
| Settings | 系统设置 | `frontend/src/pages/Settings.vue` |
| ReadingHub | 阅读中心 | `frontend/src/pages/reading/ReadingHubPage.vue` |

### 7.2 状态管理

- **应用状态**：主题、加载状态、通知 | `frontend/src/stores/app.ts` |
- **认证状态**：用户信息、登录状态 | `frontend/src/stores/auth.ts` |
- **媒体状态**：当前播放媒体、播放进度 | `frontend/src/stores/media.ts` |

### 7.3 路由配置

- **认证守卫**：保护需要登录的页面
- **路由分组**：按功能模块分组路由
- **动态路由**：支持插件动态添加路由
- **文件位置**：`frontend/src/router/index.ts`

## 8. 部署和配置

### 8.1 环境配置

- **环境变量**：使用 `.env` 文件配置环境变量
- **配置项**：数据库连接、Redis 配置、存储路径、API 密钥等
- **文件位置**：`.env.example`

### 8.2 Docker 部署

- **Docker Compose**：支持一键部署
- **服务组件**：PostgreSQL、Redis、后端、前端
- **文件位置**：`docker-compose.yml`

### 8.3 开发环境

- **后端开发**：`cd backend && python main.py` 或 `uvicorn app.main:app --reload`
- **前端开发**：`cd frontend && npm run dev` 或 `pnpm dev`
- **测试**：`cd backend && pytest`

## 9. 系统特点和优势

### 9.1 模块化设计

- 采用模块化架构，易于扩展和维护
- 支持插件系统，允许第三方扩展功能
- 前后端分离，便于独立开发和部署

### 9.2 智能选种

- 基于高级规则的智能选种算法
- 支持多种规则类型，灵活配置
- 实现 HR 安全策略，保护用户 PT 账号

### 9.3 全面的媒体支持

- 支持多种媒体类型：电影、电视剧、音乐、电子书、有声书、漫画
- 统一的媒体管理界面
- 支持多种元数据来源

### 9.4 安全可靠

- 实现 HR 安全策略，防范 HR 风险
- 支持多种认证方式，保障系统安全
- 完善的日志系统，便于故障排查

### 9.5 现代化 UI

- 基于 Vuetify 3 的 Material Design 风格
- 响应式设计，支持多种设备
- 流畅的用户体验，丰富的交互效果

## 10. 未来发展方向

### 10.1 功能增强

- 增强 AI 推荐系统
- 支持更多媒体类型和格式
- 完善移动客户端支持
- 增强多用户支持

### 10.2 性能优化

- 优化搜索性能，支持更多搜索源
- 优化数据库查询，提高系统响应速度
- 增强缓存机制，减少外部 API 调用

### 10.3 安全性提升

- 增强 HR 检测引擎，提高检测准确率
- 实现更细粒度的权限控制
- 增强数据加密，保护用户隐私

### 10.4 生态扩展

- 完善插件市场，支持更多插件类型
- 增强与外部服务的集成
- 支持社区贡献，建立开放生态

## 11. 总结

VabHub 是一个功能全面、架构现代化的媒体自动化/媒体中心平台，提供了从媒体订阅、搜索、下载到播放的完整解决方案。系统的高级规则和 HR 安全策略功能，为用户提供了智能、安全的 PT 资源管理能力，保护用户的 PT 账号安全。

系统采用模块化设计，支持插件扩展，具有良好的可扩展性和可维护性。现代化的前端界面，提供了流畅的用户体验。全面的媒体支持，满足用户多样化的媒体需求。

未来，VabHub 将继续增强功能、优化性能、提升安全性，建立开放的生态系统，为用户提供更优质的媒体管理体验。