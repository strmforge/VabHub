# SUBS-RULES-1 订阅规则中心设计文档

## 一、项目概述

### 1.1 目标
将现有散落的「订阅高级规则 + RSS规则 + 默认订阅配置」整合成可视化的「规则中心」，对齐MoviePilot的三页规则模式：
1. 默认电影订阅配置
2. 默认剧集订阅配置  
3. 过滤规则组 / 优先级规则组

### 1.2 现状分析
经过代码巡检，确认现有基础设施：

#### 已有模型和服务
- **订阅模型**: `backend/app/models/subscription.py` - 包含完整的订阅字段
- **订阅服务**: `backend/app/modules/subscription/service.py` - 调用RuleEngine进行规则匹配
- **订阅规则引擎**: `backend/app/modules/subscription/rule_engine.py` - 支持filter_groups但无配置源
- **RSS规则引擎**: `backend/app/modules/rss/rule_engine.py` - 兼容filter_groups逻辑
- **全局规则**: `backend/app/modules/global_rules/*` - 已有完整的全局规则系统

#### 前端现状
- **设置页面**: `frontend/src/pages/Settings.vue` - 已有全局规则入口
- **订阅弹窗**: `frontend/src/components/subscription/SubscriptionDialog.vue` - filterGroupOptions为空数组
- **RSS弹窗**: `frontend/src/components/rss/RSSSubscriptionDialog.vue` - 类似结构

#### 关键发现
1. `Subscription.filter_groups` 字段已存在，类型为JSON，当前存储格式为`List[Dict]`
2. `RuleEngine._check_filter_groups()` 已完整实现，期望规则组格式为：
   ```python
   [
       {
           "name": "发布组优先级",
           "priority": 1,
           "rules": [
               {"type": "include", "pattern": "CHD", "logic": "or"},
               {"type": "include", "pattern": "WiKi", "logic": "or"}
           ]
       }
   ]
   ```
3. 前端SubscriptionDialog中filterGroupOptions明确标注"优先级规则组（暂时不实现）"

## 二、数据模型设计

### 2.1 FilterRuleGroup模型
**文件**: `backend/app/models/filter_rule_group.py`

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from datetime import datetime
from app.core.database import Base

class FilterRuleGroup(Base):
    """过滤规则组模型"""
    __tablename__ = "filter_rule_groups"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null表示系统级规则组
    name = Column(String(255), nullable=False)  # 规则组名称
    description = Column(Text, nullable=True)  # 描述
    
    # 配置字段
    media_types = Column(JSON, nullable=False, default=["movie", "tv"])  # 适用媒体类型
    priority = Column(Integer, default=100)  # 优先级（数字越小越先应用）
    rules = Column(JSON, nullable=False)  # 规则配置
    enabled = Column(Boolean, default=True)  # 是否启用
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # 索引
    __table_args__ = (
        Index('idx_filter_rule_group_user', 'user_id'),
        Index('idx_filter_rule_group_media_type', 'media_types'),
        Index('idx_filter_rule_group_priority', 'priority'),
    )
```

### 2.2 默认订阅配置存储
**使用现有SystemSetting模型**，不单独建表：

```python
# 配置键格式
SUBS_DEFAULT_MOVIE = "subscription.default.movie"
SUBS_DEFAULT_TV = "subscription.default.tv"
SUBS_DEFAULT_SHORT_DRAMA = "subscription.default.short_drama"  # 预留
SUBS_DEFAULT_ANIME = "subscription.default.anime"  # 预留
SUBS_DEFAULT_MUSIC = "subscription.default.music"  # 预留

# 配置值格式
{
    "quality": "",
    "resolution": "",
    "effect": "",
    "min_seeders": 5,
    "auto_download": true,
    "best_version": false,
    "include": "",
    "exclude": "",
    "filter_group_ids": [1, 2],  # 规则组ID列表
    "allow_hr": false,
    "allow_h3h5": false,
    "strict_free_only": false,
    "sites": [1, 2, 3],
    "downloader": "",
    "save_path": ""
}
```

### 2.3 Subscription.filter_groups字段改造
**存储格式变更**：从`List[Dict]`改为`List[int]`（规则组ID列表）

```python
# 旧格式（向后兼容）
filter_groups = [
    {
        "name": "发布组优先级",
        "priority": 1,
        "rules": [...]
    }
]

# 新格式
filter_groups = [1, 3, 5]  # 规则组ID列表
```

## 三、服务层设计

### 3.1 FilterRuleGroupService
**文件**: `backend/app/modules/filter_rule_group/service.py`

```python
class FilterRuleGroupService:
    """过滤规则组服务"""
    
    async def list_groups(
        self, 
        user_id: Optional[int] = None, 
        media_type: Optional[str] = None
    ) -> List[FilterRuleGroup]:
        """获取规则组列表"""
        
    async def get_group(self, group_id: int) -> Optional[FilterRuleGroup]:
        """获取单个规则组"""
        
    async def create_group(self, user_id: int, data: dict) -> FilterRuleGroup:
        """创建规则组"""
        
    async def update_group(self, group_id: int, data: dict) -> FilterRuleGroup:
        """更新规则组"""
        
    async def delete_group(self, group_id: int) -> bool:
        """删除规则组"""
        
    async def resolve_groups_for_subscription(
        self, 
        user_id: int, 
        group_ids: List[int], 
        media_type: str
    ) -> List[dict]:
        """
        为订阅解析规则组，返回RuleEngine可用结构
        
        Returns:
            [
                {
                    "name": group.name,
                    "priority": group.priority,
                    "rules": group.rules["rules"],
                },
                ...
            ]
        """
```

### 3.2 DefaultSubscriptionConfigService
**文件**: `backend/app/modules/subscription/defaults.py`

```python
from pydantic import BaseModel
from typing import List, Optional

class DefaultSubscriptionConfig(BaseModel):
    """默认订阅配置模型"""
    quality: str = ""
    resolution: str = ""
    effect: str = ""
    min_seeders: int = 5
    auto_download: bool = True
    best_version: bool = False
    include: str = ""
    exclude: str = ""
    filter_group_ids: List[int] = []
    allow_hr: bool = False
    allow_h3h5: bool = False
    strict_free_only: bool = False
    sites: List[int] = []
    downloader: str = ""
    save_path: str = ""

class DefaultSubscriptionConfigService:
    """默认订阅配置服务"""
    
    async def get_default_config(self, media_type: str) -> DefaultSubscriptionConfig:
        """获取默认配置，无记录时返回内置默认值"""
        
    async def save_default_config(self, media_type: str, data: dict) -> DefaultSubscriptionConfig:
        """保存默认配置到SystemSetting"""
```

### 3.3 订阅服务改造
**文件**: `backend/app/modules/subscription/service.py`

```python
class SubscriptionService:
    # 在现有方法中添加：
    
    async def create_subscription(self, user_id: int, data: dict) -> Subscription:
        """创建订阅时应用默认配置"""
        # 如果前端没传基础字段，使用DefaultSubscriptionConfigService提供默认值
        
    async def run_subscription(self, subscription_id: int):
        """运行订阅时解析规则组"""
        # 在调用RuleEngine之前：
        # 1. 根据subscription.filter_groups（ID列表）
        # 2. 调用FilterRuleGroupService.resolve_groups_for_subscription
        # 3. 将返回的规则组结构塞入subscription_dict["filter_groups"]
        # 4. 传给RuleEngine进行匹配
```

### 3.4 RSS服务改造
**文件**: `backend/app/modules/rss/service.py`

```python
class RSSService:
    # 在RSS匹配逻辑中：
    # 1. 解析RSS订阅配置中的filter_group_ids
    # 2. 通过FilterRuleGroupService解析成规则组结构
    # 3. 传给rss.rule_engine的filter_groups参数
```

## 四、API层设计

### 4.1 过滤规则组API
**文件**: `backend/app/api/filter_rule_groups.py`

```python
from fastapi import APIRouter, Depends, Query
from app.core.schemas import BaseResponse

router = APIRouter(prefix="/filter-rule-groups", tags=["filter-rule-groups"])

@router.get("", response_model=BaseResponse[List[FilterRuleGroupResponse]])
async def list_filter_rule_groups(
    media_type: Optional[str] = Query(None, description="媒体类型过滤"),
    current_user: User = Depends(get_current_user)
):
    """获取规则组列表"""

@router.post("", response_model=BaseResponse[FilterRuleGroupResponse])
async def create_filter_rule_group(
    data: FilterRuleGroupCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """创建规则组"""

@router.put("/{group_id}", response_model=BaseResponse[FilterRuleGroupResponse])
async def update_filter_rule_group(
    group_id: int,
    data: FilterRuleGroupUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """更新规则组"""

@router.delete("/{group_id}", response_model=BaseResponse[bool])
async def delete_filter_rule_group(
    group_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除规则组"""
```

### 4.2 默认订阅配置API
**文件**: `backend/app/api/subscription_defaults.py`

```python
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/subscriptions/default-config", tags=["subscription-defaults"])

@router.get("", response_model=BaseResponse[DefaultSubscriptionConfig])
async def get_default_subscription_config(
    media_type: str = Query(..., description="媒体类型"),
    current_user: User = Depends(get_current_user)
):
    """获取默认订阅配置"""

@router.post("", response_model=BaseResponse[DefaultSubscriptionConfig])
async def save_default_subscription_config(
    media_type: str = Query(..., description="媒体类型"),
    data: DefaultSubscriptionConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """保存默认订阅配置"""
```

### 4.3 订阅API改造
**文件**: `backend/app/api/subscription.py`

```python
# 请求/响应模型调整：
class SubscriptionRequest(BaseModel):
    # ... 其他字段
    filter_groups: Optional[List[int]] = None  # 改为规则组ID列表

class SubscriptionResponse(BaseModel):
    # ... 其他字段
    filter_groups: Optional[List[int]] = None  # 规则组ID列表
    filter_group_names: Optional[List[str]] = None  # 方便前端显示的名称列表
```

## 五、前端设计

### 5.1 导航改造
**文件**: `frontend/src/pages/Settings.vue`

```typescript
// 在categories数组中添加：
{
  value: 'rules',
  title: '规则中心',
  icon: 'mdi-tune-variant',
  children: [
    { value: 'global_rules', title: '全局规则', icon: 'mdi-shield-check' },
    { value: 'subscription_defaults', title: '订阅默认配置', icon: 'mdi-cog-clock' },
    { value: 'filter_rule_groups', title: '过滤规则组', icon: 'mdi-filter-variant' }
  ]
}
```

### 5.2 订阅默认配置页
**文件**: `frontend/src/pages/SubscriptionDefaultSettings.vue`

```vue
<template>
  <v-container>
    <!-- 媒体类型Tab切换 -->
    <v-tabs v-model="activeTab">
      <v-tab value="movie">电影</v-tab>
      <v-tab value="tv">电视剧</v-tab>
    </v-tabs>
    
    <!-- 配置表单 -->
    <v-window v-model="activeTab">
      <v-window-item value="movie">
        <SubscriptionDefaultForm 
          media-type="movie"
          @save="handleSave"
        />
      </v-window-item>
      <v-window-item value="tv">
        <SubscriptionDefaultForm 
          media-type="tv"
          @save="handleSave"
        />
      </v-window-item>
    </v-window>
  </v-container>
</template>
```

### 5.3 过滤规则组中心页
**文件**: `frontend/src/pages/FilterRuleGroupCenter.vue`

```vue
<template>
  <v-container>
    <v-row>
      <!-- 左侧规则组列表 -->
      <v-col cols="12" md="8">
        <FilterRuleGroupList 
          @edit="handleEdit"
          @create="handleCreate"
        />
      </v-col>
      
      <!-- 右侧编辑表单 -->
      <v-col cols="12" md="4">
        <FilterRuleGroupForm
          v-if="editingGroup"
          :group="editingGroup"
          @save="handleSave"
          @cancel="handleCancel"
        />
      </v-col>
    </v-row>
  </v-container>
</template>
```

### 5.4 订阅弹窗改造
**文件**: `frontend/src/components/subscription/SubscriptionDialog.vue`

```typescript
// 在script setup中添加：
import { getFilterRuleGroups } from '@/api/filterRuleGroups'
import { getDefaultSubscriptionConfig, saveDefaultSubscriptionConfig } from '@/api/subscription'

// 加载默认配置
const loadDefaultConfig = async (mediaType: string) => {
  try {
    const response = await getDefaultSubscriptionConfig(mediaType)
    if (response.success && response.data) {
      // 只在创建新订阅且用户未修改时应用默认值
      if (!editingSubscription && !userModified) {
        Object.assign(form, response.data)
      }
    }
  } catch (error) {
    console.error('加载默认配置失败:', error)
  }
}

// 加载规则组选项
const loadFilterGroupOptions = async (mediaType: string) => {
  try {
    const response = await getFilterRuleGroups({ media_type: mediaType })
    if (response.success && response.data) {
      filterGroupOptions.value = response.data.map(group => ({
        title: group.name,
        value: group.id
      }))
    }
  } catch (error) {
    console.error('加载规则组失败:', error)
  }
}
```

## 六、向后兼容策略

### 6.1 数据格式兼容
**在FilterRuleGroupService.resolve_groups_for_subscription中实现**：

```python
async def resolve_groups_for_subscription(
    self, 
    user_id: int, 
    group_ids: List[int], 
    media_type: str
) -> List[dict]:
    """解析规则组，支持向后兼容"""
    
    # 处理历史数据格式
    if not group_ids:
        return []
    
    # 如果是字符串列表（老数据），记录警告并忽略
    if all(isinstance(item, str) for item in group_ids):
        logger.warning("发现字符串格式的filter_groups，建议使用规则组中心管理")
        return []
    
    # 如果是字典列表（手动配置的老数据），记录警告并忽略
    if all(isinstance(item, dict) for item in group_ids):
        logger.warning("发现字典格式的filter_groups，建议迁移到规则组中心")
        return []
    
    # 新格式：整数ID列表
    valid_ids = [item for item in group_ids if isinstance(item, int)]
    
    # 查询规则组
    groups = await self.get_enabled_groups_by_ids(valid_ids, media_type)
    
    # 转换为RuleEngine期望的格式
    return [
        {
            "name": group.name,
            "priority": group.priority,
            "rules": group.rules.get("rules", []),
        }
        for group in groups
    ]
```

### 6.2 迁移策略
1. **渐进式迁移**：新订阅使用规则组ID格式，老订阅保持兼容
2. **用户提示**：在日志和UI中提示用户迁移到规则组中心
3. **数据清理**：提供可选的数据迁移工具，将老格式转换为新格式

## 七、测试策略

### 7.1 单元测试
- FilterRuleGroupService CRUD操作测试
- DefaultSubscriptionConfigService配置管理测试
- 规则组解析逻辑测试
- 向后兼容性测试

### 7.2 集成测试
- 订阅创建时默认配置应用测试
- 订阅运行时规则组解析测试
- RSS订阅规则组匹配测试
- API端点完整流程测试

### 7.3 前端测试
- 规则组管理页面功能测试
- 订阅弹窗默认配置加载测试
- 规则组选择和回显测试

## 八、部署和监控

### 8.1 数据库迁移
```bash
# 创建FilterRuleGroup表
alembic revision --autogenerate -m "Create filter_rule_groups table"
alembic upgrade head
```

### 8.2 监控指标
- 规则组使用统计
- 默认配置应用次数
- 向后兼容警告日志
- API调用量和性能

## 九、文件改动清单

### 新建文件
```
backend/
├── app/models/filter_rule_group.py
├── app/modules/filter_rule_group/
│   ├── __init__.py
│   └── service.py
├── app/modules/subscription/defaults.py
├── app/api/filter_rule_groups.py
├── app/api/subscription_defaults.py
├── tests/filter_rule_group/
│   ├── __init__.py
│   ├── test_service_basic.py
│   └── test_integration.py
└── tests/subscription/
    ├── test_default_config_api.py
    └── test_subscription_with_rule_groups.py

frontend/
├── src/pages/SubscriptionDefaultSettings.vue
├── src/pages/FilterRuleGroupCenter.vue
├── src/api/filterRuleGroups.ts
├── src/api/subscriptionDefaults.ts
└── src/components/ruleCenter/
    ├── FilterRuleGroupList.vue
    ├── FilterRuleGroupForm.vue
    └── SubscriptionDefaultForm.vue

docs/
└── SUBS_RULES_1_DESIGN.md
```

### 修改文件
```
backend/
├── app/models/subscription.py (filter_groups字段文档更新)
├── app/modules/subscription/service.py (添加默认配置和规则组解析)
├── app/modules/rss/service.py (添加规则组支持)
├── app/api/subscription.py (请求/响应模型调整)
├── app/api/__init__.py (注册新路由)
└── alembic/versions/ (新的migration文件)

frontend/
├── src/pages/Settings.vue (添加规则中心导航)
├── src/components/subscription/SubscriptionDialog.vue (对接规则组)
├── src/components/rss/RSSSubscriptionDialog.vue (对接规则组)
└── src/types/subscription.ts (类型定义更新)
```

## 十、风险评估和缓解

### 10.1 风险识别
1. **数据迁移风险**：老订阅数据可能丢失
2. **性能风险**：规则组解析可能影响订阅性能
3. **兼容性风险**：前端类型定义变更可能导致错误

### 10.2 缓解措施
1. **渐进式迁移**：保持向后兼容，提供迁移工具
2. **性能优化**：缓存规则组数据，异步解析
3. **充分测试**：完整的单元测试和集成测试覆盖
4. **灰度发布**：先在小范围测试，再全量发布

---

**设计版本**: v1.0  
**创建日期**: 2025年11月29日  
**最后更新**: 2025年11月29日  
**负责人**: SUBS-RULES-1项目组
