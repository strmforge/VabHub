# acq-guardian 功能整合完成报告

## 📋 整合概述

成功整合了acq-guardian项目的核心功能到VabHub的HNR检测系统中，提升了检测准确性和可维护性。

## ✅ 已完成的功能

### 1. YAML签名包系统 ⭐⭐⭐

#### 功能说明
- **热更新支持**: 无需重启服务即可更新签名
- **版本控制**: 签名包支持版本化管理
- **易于维护**: YAML格式易于编辑和版本控制

#### 实现文件
- `backend/app/modules/hnr/signatures/loader.py` - 签名包加载器
- `backend/app/modules/hnr/signatures/pack.yaml` - 示例签名包文件

#### 核心功能
```python
class SignaturePackLoader:
    """签名包加载器 - 支持YAML文件热更新"""
    
    def load(self, pack_path: Optional[str] = None) -> bool:
        """加载YAML签名包"""
    
    def reload(self) -> bool:
        """重新加载签名包（热更新）"""
    
    def get_signatures(self) -> List[Signature]:
        """获取所有签名"""
    
    def get_site_selectors(self, site_id: str) -> List[str]:
        """获取站点CSS选择器"""
```

#### 签名包结构
```yaml
version: 1
signatures:
  - id: hnr_basic
    name: "基本HNR检测"
    category: "HNR_BASIC"
    patterns:
      text: ["H&R", "H-R", "H R"]
      regex: ["(?ix)\\bH(?:\\s*&\\s*|[/／＆])?R\\b"]
    confidence: 0.9
    penalties:
      base: -50
      per_level: -10

site_overrides:
  # 站点特定规则
```

---

### 2. 站点选择器（CSS选择器） ⭐⭐⭐

#### 功能说明
- **站点特定检测**: 不同站点可以使用不同的检测规则
- **CSS选择器支持**: 可以从HTML中提取特定标签
- **更准确的检测**: 避免误报

#### 实现方式
- 在签名包中配置站点选择器
- 检测时优先使用站点选择器
- 支持从HTML中提取标签文本

#### 使用示例
```yaml
site_overrides:
  site_a:
    selectors:
      - ".badge:contains('H&R')"
      - ".label:contains('H5')"
```

---

### 3. 改进误报避免 ⭐⭐

#### 功能说明
- **H.264/HDR10误报避免**: 专门的正则表达式避免误报
- **更准确的检测**: 减少误判

#### 实现方式
```python
# 避免H.264/HDR10误报的正则表达式
RE_HNR_LEVEL = re.compile(r"""(?ix)
    (?<!H\.?26[45])  # avoid H.264/H.265
    (?<!HDR)         # avoid HDR / HDR10
    \bH\s*[-/:：]?\s*(?P<level>[1-9]|10)\b
""")
```

#### 优势
- 避免将视频编码格式（H.264/H.265）误判为HNR规则
- 避免将HDR10误判为H10规则
- 提高检测准确率

---

### 4. 改进启发式检测 ⭐⭐

#### 功能说明
- **关键词共现检测**: 检测"考核/命中/保种"与"小时/天/做种/时长"的共现
- **未知标签检测**: 检测新的HNR相关标签
- **更细致的检测逻辑**: 多层次的检测策略

#### 实现方式
```python
def _heuristic_detection(self, text: str, badges_html: str = "") -> Optional[Dict[str, Any]]:
    """启发式检测 - 改进的检测逻辑"""
    # 1. 检测关键词共现
    if cooccur(text, {"考核", "命中", "保种"}, {"小时", "天", "做种", "时长"}):
        score += 0.4
    
    # 2. 检测H-<num>形状
    if RE_HNR_LEVEL.search(badges_html):
        score += 0.3
    
    # 3. 检测未知标签片段
    # ...
```

---

### 5. 热更新API ⭐⭐

#### 功能说明
- **热更新支持**: 无需重启服务即可更新签名
- **API接口**: 提供RESTful API接口

#### API端点
```python
# 重新加载签名包
POST /api/v1/hnr/signatures/reload

# 获取所有签名
GET /api/v1/hnr/signatures
```

#### 使用示例
```bash
# 重新加载签名包
curl -X POST http://localhost:8000/api/v1/hnr/signatures/reload

# 获取所有签名
curl http://localhost:8000/api/v1/hnr/signatures
```

---

## 📁 创建的文件

### 核心文件
1. **`backend/app/modules/hnr/signatures/loader.py`**
   - 签名包加载器
   - 支持YAML文件加载和热更新
   - 提供签名查询和站点选择器支持

2. **`backend/app/modules/hnr/signatures/pack.yaml`**
   - 示例签名包文件
   - 包含基础HNR检测规则
   - 支持站点特定规则配置

3. **`backend/app/modules/hnr/utils/text.py`**
   - 文本处理工具
   - 文本标准化函数
   - 关键词共现检测
   - HNR级别提取

4. **`backend/app/modules/hnr/utils/__init__.py`**
   - 工具模块初始化文件

### 配置文件
5. **`backend/requirements.txt`**
   - 添加了PyYAML依赖
   - 添加了beautifulsoup4依赖（用于CSS选择器）

---

## 📝 更新的文件

### 核心文件
1. **`backend/app/modules/hnr/detector.py`**
   - 整合YAML签名包加载器
   - 支持站点选择器检测
   - 改进误报避免逻辑
   - 改进启发式检测

2. **`backend/app/modules/hnr/service.py`**
   - 使用配置中的签名包路径
   - 添加热更新方法

3. **`backend/app/api/hnr.py`**
   - 添加热更新API端点
   - 添加获取签名API端点

4. **`backend/app/core/config.py`**
   - 添加HNR签名包路径配置

---

## 🔧 技术细节

### 依赖项
- **PyYAML>=6.0**: YAML文件解析
- **pydantic>=2.0**: 数据验证
- **beautifulsoup4>=4.12.0**: HTML解析（可选，用于CSS选择器）

### 配置项
```python
# HNR检测配置
HNR_SIGNATURE_PACK_PATH: str = ""  # 留空则使用默认路径
```

### 检测流程
1. **站点选择器检测** - 优先使用站点特定规则
2. **基本HNR检测** - 使用改进的正则表达式
3. **HNR级别检测** - 检测H3/H5/H7等，避免误报
4. **签名包匹配** - 使用YAML签名包匹配
5. **启发式检测** - 检测未知标签和关键词组合

---

## 🎯 优势

### 1. 更灵活的签名管理
- YAML格式易于编辑和版本控制
- 支持热更新，无需重启服务
- 版本化管理，易于回滚

### 2. 更准确的检测
- 站点特定规则减少误报
- 改进的误报避免逻辑
- 多层次的检测策略

### 3. 更好的可维护性
- 代码结构清晰
- 易于扩展
- 完善的文档

---

## 📊 性能优化

### 1. 正则表达式预编译
- 签名包加载时预编译正则表达式
- 提高检测性能

### 2. 已知标签缓存
- 缓存已知标签集合
- 快速判断标签是否已知

### 3. 站点选择器缓存
- 缓存站点特定规则
- 减少重复查询

---

## 🚀 后续计划

### 1. 完整CSS选择器支持
- 集成BeautifulSoup4
- 支持完整的CSS选择器语法

### 2. 站点包管理
- 站点配置管理界面
- 批量导入/导出站点配置

### 3. 签名包管理
- 签名包管理界面
- 在线编辑签名包
- 签名包版本对比

### 4. 统计分析
- 检测准确率统计
- 误报率统计
- 检测趋势分析

---

## 📖 使用指南

### 1. 配置签名包路径
```python
# 在 .env 文件中配置
HNR_SIGNATURE_PACK_PATH=./app/modules/hnr/signatures/pack.yaml
```

### 2. 编辑签名包
```yaml
# 编辑 pack.yaml 文件
version: 1
signatures:
  - id: custom_rule
    name: "自定义规则"
    category: "HNR_BASIC"
    patterns:
      text: ["自定义标签"]
      regex: ["自定义正则"]
    confidence: 0.9
```

### 3. 热更新签名包
```bash
# 调用API重新加载
curl -X POST http://localhost:8000/api/v1/hnr/signatures/reload
```

---

## 🔍 测试建议

### 1. 基础功能测试
- 测试YAML签名包加载
- 测试热更新功能
- 测试站点选择器

### 2. 检测准确率测试
- 测试H.264/HDR10误报避免
- 测试H3/H5/H7检测
- 测试启发式检测

### 3. 性能测试
- 测试检测性能
- 测试签名包加载性能
- 测试热更新性能

---

## 📝 注意事项

### 1. 签名包路径
- 默认路径: `backend/app/modules/hnr/signatures/pack.yaml`
- 可以通过配置项自定义路径

### 2. 热更新限制
- 热更新不会影响正在进行的检测
- 建议在低峰期进行热更新

### 3. 站点选择器
- 当前版本使用简化实现
- 完整CSS选择器支持需要BeautifulSoup4

---

## ✅ 整合完成状态

- [x] YAML签名包系统
- [x] 站点选择器（CSS选择器）
- [x] 改进误报避免（H.264/HDR10）
- [x] 改进启发式检测
- [x] 热更新API
- [ ] 完整CSS选择器支持（待后续实现）
- [ ] 站点包管理（待后续实现）
- [ ] 签名包管理界面（待后续实现）

---

**创建时间**: 2025-11-08
**状态**: ✅ 已完成核心功能整合

