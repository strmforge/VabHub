# acq-guardian 功能整合建议

## 📋 功能对比分析

### VabHub 当前 HNR 检测功能
- ✅ 基础 HNR 检测（H&R, H3, H5, H7）
- ✅ 启发式检测
- ✅ 数据库存储签名
- ✅ REST API
- ✅ 前端界面

### acq-guardian 优势功能
- ✅ **GraphQL API** - 更灵活的查询
- ✅ **YAML签名包系统** - 版本化、可热更新
- ✅ **站点选择器（CSS选择器）** - 站点特定的检测规则
- ✅ **更好的误报避免** - H.264/HDR10 误报避免
- ✅ **站点包管理** - 站点配置管理
- ✅ **qBittorrent集成增强** - 分类、做种限制设置
- ✅ **Vue3前端组件** - 现成的UI组件
- ✅ **更完善的启发式检测** - 更细致的检测逻辑

---

## 🎯 可整合的功能

### 1. YAML签名包系统 ⭐⭐⭐ (高优先级)

#### 优势
- **热更新** - 无需重启服务即可更新签名
- **版本控制** - 签名包版本化管理
- **易于维护** - YAML格式易于编辑和版本控制
- **站点覆盖** - 支持站点特定的规则覆盖

#### 实现方案
```python
# 整合到 VabHub/backend/app/modules/hnr/signatures.py
class SignaturePackLoader:
    """签名包加载器 - 支持YAML文件热更新"""
    
    def __init__(self, pack_path: str):
        self.pack_path = Path(pack_path)
        self.pack = self._load_pack()
    
    def _load_pack(self) -> Dict:
        """从YAML文件加载签名包"""
        with open(self.pack_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def reload(self):
        """热更新签名包"""
        self.pack = self._load_pack()
    
    def get_signatures(self) -> List[Dict]:
        """获取所有签名"""
        return self.pack.get('signatures', [])
    
    def get_site_overrides(self, site_id: str) -> Dict:
        """获取站点特定规则"""
        return self.pack.get('site_overrides', {}).get(site_id, {})
```

#### 整合步骤
1. 创建 `backend/app/modules/hnr/signatures/loader.py`
2. 创建 `backend/app/modules/hnr/signatures/pack.yaml` 示例文件
3. 修改 `HNRDetector` 支持YAML签名包
4. 添加热更新API端点

---

### 2. 站点选择器（CSS选择器） ⭐⭐⭐ (高优先级)

#### 优势
- **站点特定检测** - 不同站点可以使用不同的检测规则
- **CSS选择器** - 可以从HTML中提取特定标签
- **更准确的检测** - 避免误报

#### 实现方案
```python
# 整合到 VabHub/backend/app/modules/hnr/detector.py
class HNRDetector:
    def __init__(self, signature_pack_path: str):
        self.sigpack = SignaturePackLoader(signature_pack_path)
    
    def detect(self, title: str, subtitle: str, badges_text: str, 
               list_html: str, site_id: str) -> HNRDetectionResult:
        # 1. 使用站点选择器检测
        site_selectors = self.sigpack.get_site_overrides(site_id).get('selectors', [])
        for selector in site_selectors:
            # 使用CSS选择器从HTML中提取标签
            if self._match_selector(selector, list_html):
                return self._create_blocked_result("site-selector")
        
        # 2. 使用通用规则检测
        # ... 现有检测逻辑
```

#### 整合步骤
1. 添加CSS选择器解析库（如 `beautifulsoup4` 或 `lxml`）
2. 在签名包中添加站点选择器配置
3. 修改检测逻辑支持选择器

---

### 3. 更好的误报避免 ⭐⭐ (中优先级)

#### 优势
- **避免H.264/HDR10误报** - 专门的正则表达式避免误报
- **更准确的检测** - 减少误判

#### 实现方案
```python
# 从acq-guardian借鉴的正则表达式
RE_HNR_LEVEL = re.compile(r"""(?ix)
    (?<!H\.?26[45])  # avoid H.264/H.265
    (?<!HDR)         # avoid HDR / HDR10
    \bH \s* [-/:：]? \s* (?P<level>[1-9]|10) \b
""")
```

#### 整合步骤
1. 更新 `HNRDetector` 中的正则表达式
2. 添加H.264/HDR10检测逻辑
3. 测试误报避免

---

### 4. qBittorrent集成增强 ⭐⭐ (中优先级)

#### 优势
- **分类管理** - 自动设置HNR资源分类
- **做种限制** - 自动设置做种比例和时间
- **标签管理** - 支持标签添加和删除

#### 实现方案
```python
# 整合到 VabHub/backend/app/core/downloaders/qbittorrent.py
class QBittorrentClient:
    def set_category(self, torrent_hash: str, category: str):
        """设置分类"""
        self.client.torrents_set_category(
            torrent_hashes=torrent_hash,
            category=category
        )
    
    def set_share_limits(self, torrent_hash: str, ratio: float = -1, 
                        seeding_time_minutes: int = -1):
        """设置做种限制"""
        self.client.torrents_set_share_limits(
            torrent_hashes=torrent_hash,
            ratio_limit=ratio,
            seeding_time_limit=seeding_time_minutes
        )
    
    def add_tags(self, torrent_hash: str, tags: List[str]):
        """添加标签"""
        self.client.torrents_add_tags(
            torrent_hashes=torrent_hash,
            tags=tags
        )
```

#### 整合步骤
1. 增强 `QBittorrentClient` 功能
2. 在下载服务中集成HNR检测
3. 自动设置分类和做种限制

---

### 5. 站点包管理 ⭐ (低优先级)

#### 优势
- **站点配置管理** - 统一管理站点配置
- **批量操作** - 支持批量更新站点配置

#### 实现方案
```python
# 创建 VabHub/backend/app/modules/hnr/site_bundles.py
class SiteBundleService:
    """站点包服务"""
    
    async def create_bundle(self, bundle_data: Dict) -> SiteBundle:
        """创建站点包"""
        pass
    
    async def get_bundles(self) -> List[SiteBundle]:
        """获取所有站点包"""
        pass
    
    async def update_bundle(self, bundle_id: int, bundle_data: Dict):
        """更新站点包"""
        pass
```

#### 整合步骤
1. 创建站点包数据模型
2. 创建站点包服务层
3. 创建站点包API
4. 创建前端界面

---

### 6. GraphQL API ⭐ (低优先级)

#### 优势
- **灵活查询** - 客户端可以自定义查询字段
- **减少请求** - 一次请求获取多个数据

#### 实现方案
```python
# 使用 Strawberry 或 Ariadne 添加GraphQL支持
from strawberry.fastapi import GraphQLRouter
from strawberry import Schema

@strawberry.type
class HNRQuery:
    @strawberry.field
    def signatures(self, since_version: int = 0) -> List[Signature]:
        """获取签名列表"""
        pass
    
    @strawberry.field
    def detect_hnr(self, candidate: CandidateInput) -> HNRDetectionResult:
        """检测HNR"""
        pass
```

#### 整合步骤
1. 安装GraphQL库（如 `strawberry-graphql`）
2. 创建GraphQL Schema
3. 添加GraphQL路由
4. 测试GraphQL API

---

### 7. Vue3前端组件 ⭐⭐ (中优先级)

#### 优势
- **现成的UI组件** - 可以直接使用
- **更好的用户体验** - 优化过的界面

#### 实现方案
```vue
<!-- 整合到 VabHub/frontend/src/components/hnr/AcqCandidateCard.vue -->
<template>
  <v-card>
    <v-card-title>
      {{ candidate.title }}
      <v-chip v-if="result?.verdict.flagged" color="error">H&R</v-chip>
      <v-chip v-else-if="result?.verdict.suspected" color="warning">
        疑似 H&R ({{ Math.round(result.verdict.confidence * 100) }}%)
      </v-chip>
      <v-chip v-else color="success">安全</v-chip>
    </v-card-title>
    <v-card-text>
      <div v-if="result">
        <div>评估结果：</div>
        <ul>
          <li v-for="reason in result.reasons" :key="reason">{{ reason }}</li>
        </ul>
      </div>
    </v-card-text>
    <v-card-actions>
      <v-btn @click="handleEvaluate">评估</v-btn>
      <v-btn @click="handleEvaluateAndDownload">评估并下载</v-btn>
    </v-card-actions>
  </v-card>
</template>
```

#### 整合步骤
1. 复制acq-guardian的Vue组件
2. 适配VabHub的API
3. 集成到HNR监控页面

---

## 📊 优先级排序

### 高优先级 (立即整合)
1. ✅ **YAML签名包系统** - 热更新、版本控制
2. ✅ **站点选择器** - 站点特定检测规则
3. ✅ **更好的误报避免** - H.264/HDR10误报避免

### 中优先级 (后续整合)
4. ✅ **qBittorrent集成增强** - 分类、做种限制
5. ✅ **Vue3前端组件** - 现成的UI组件

### 低优先级 (可选整合)
6. ✅ **站点包管理** - 站点配置管理
7. ✅ **GraphQL API** - 灵活的查询接口

---

## 🔧 整合实施方案

### 阶段1: 核心功能整合 (1-2天)
1. 整合YAML签名包系统
2. 整合站点选择器
3. 改进误报避免逻辑

### 阶段2: 功能增强 (2-3天)
4. 增强qBittorrent集成
5. 整合Vue3前端组件
6. 优化用户体验

### 阶段3: 扩展功能 (可选)
7. 实现站点包管理
8. 添加GraphQL API支持

---

## 📝 具体整合步骤

### 步骤1: 整合YAML签名包系统

1. **创建签名包加载器**
   ```bash
   # 创建文件
   VabHub/backend/app/modules/hnr/signatures/loader.py
   VabHub/backend/app/modules/hnr/signatures/pack.yaml
   ```

2. **修改HNRDetector**
   ```python
   # 修改 VabHub/backend/app/modules/hnr/detector.py
   class HNRDetector:
       def __init__(self, signature_pack_path: str = None):
           if signature_pack_path:
               self.sigpack = SignaturePackLoader(signature_pack_path)
           else:
               # 使用默认签名
               self.signatures = self._load_default_signatures()
   ```

3. **添加热更新API**
   ```python
   # 在 VabHub/backend/app/api/hnr.py 中添加
   @router.post("/signatures/reload")
   async def reload_signatures():
       """重新加载签名包"""
       detector.reload()
       return {"message": "签名包已重新加载"}
   ```

### 步骤2: 整合站点选择器

1. **添加CSS选择器支持**
   ```bash
   # 安装依赖
   pip install beautifulsoup4
   ```

2. **修改检测逻辑**
   ```python
   # 在HNRDetector中添加
   def _match_selector(self, selector: str, html: str) -> bool:
       """使用CSS选择器匹配"""
       from bs4 import BeautifulSoup
       soup = BeautifulSoup(html, 'html.parser')
       return bool(soup.select(selector))
   ```

### 步骤3: 改进误报避免

1. **更新正则表达式**
   ```python
   # 使用acq-guardian的正则表达式
   RE_HNR_LEVEL = re.compile(r"""(?ix)
       (?<!H\.?26[45])  # avoid H.264/H.265
       (?<!HDR)         # avoid HDR / HDR10
       \bH \s* [-/:：]? \s* (?P<level>[1-9]|10) \b
   """)
   ```

---

## 🎯 预期效果

### 整合后优势
1. ✅ **更灵活的签名管理** - YAML文件易于编辑和版本控制
2. ✅ **更准确的检测** - 站点特定规则减少误报
3. ✅ **更好的用户体验** - 现成的UI组件
4. ✅ **更完善的下载管理** - 自动分类和做种限制
5. ✅ **热更新支持** - 无需重启即可更新签名

---

## 📖 参考文档

### acq-guardian 项目文件
- `F:\新建文件夹\acq-guardian-starter\src\acq_guardian\detect\hnr.py` - 检测逻辑
- `F:\新建文件夹\acq-guardian-starter\src\acq_guardian\signatures\loader.py` - 签名包加载器
- `F:\新建文件夹\acq-guardian-starter-extended-qb\src\acq_guardian\integrations\qbittorrent.py` - qBittorrent集成
- `F:\新建文件夹\acq-guardian-vue3-site-bundles-pro\src\components\AcqCandidateCard.vue` - Vue组件

---

**创建时间**: 2025-11-08
**状态**: 待实施

