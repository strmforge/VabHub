# 常用PT站点配置文件库说明

**创建时间**: 2025-01-XX  
**目的**: 提供常用PT站点类型的配置文件，支持站点自动识别和解析

---

## 📋 一、已创建的配置文件

### 1. NexusPHP通用配置

**文件**: `resources/site-profiles/nexusphp.yml`

**适用站点**: 所有基于NexusPHP框架的PT站点

**特点**:
- 通用配置，不限制域名
- 通过meta generator或标题识别
- 支持标准的NexusPHP页面结构

**识别规则**:
- meta generator包含"NexusPHP"
- 标题包含"NexusPHP"
- 存在`table.torrents`选择器

**解析规则**:
- 列表: `table.torrents > tbody > tr`
- 详情: 标准详情页结构
- 用户信息: 标准用户信息结构

---

### 2. Gazelle通用配置

**文件**: `resources/site-profiles/gazelle.yml`

**适用站点**: 所有基于Gazelle框架的PT站点

**特点**:
- 通用配置，不限制域名
- 通过meta generator或标题识别
- 支持Gazelle特有的页面结构

**识别规则**:
- meta generator包含"Gazelle"
- 标题包含"Gazelle"
- 存在`div.torrent_table`或`table.torrent_table`选择器

**解析规则**:
- 列表: `table.torrent_table > tbody > tr`
- 详情: Gazelle详情页结构
- 用户信息: Gazelle用户信息结构

---

### 3. Unit3D通用配置

**文件**: `resources/site-profiles/unit3d.yml`

**适用站点**: 所有基于Unit3D框架的PT站点

**特点**:
- 通用配置，不限制域名
- 通过meta generator或标题识别
- 支持Unit3D的现代化页面结构

**识别规则**:
- meta generator包含"Unit3D"
- 标题包含"Unit3D"
- 存在`div.torrent-list`或`table.torrents-table`选择器

**解析规则**:
- 列表: `table.torrents-table > tbody > tr`
- 详情: Unit3D详情页结构
- 用户信息: Unit3D用户信息结构

---

### 4. 模板文件

**文件**: `resources/site-profiles/_template.yml`

**用途**: 作为创建新配置文件的模板

---

## 📋 二、如何添加新站点配置文件

### 2.1 创建配置文件

1. **复制模板文件**
   ```bash
   cp resources/site-profiles/_template.yml resources/site-profiles/{site_id}.yml
   ```

2. **编辑配置文件**
   - 修改`meta`信息（id, name, family, domains）
   - 配置`verify`规则（站点验证）
   - 配置`parse`规则（内容解析）

3. **更新catalog.json**
   ```json
   {
     "profiles": {
       "{site_id}.yml": "1.0.0"
     }
   }
   ```

### 2.2 配置文件结构

```yaml
meta:
  id: site_id          # 唯一ID
  name: 站点名称
  family: nexusphp     # 站点类型
  version: 1.0.0
  domains:            # 域名列表（可选，为空表示通用配置）
    - "https://example.com"

verify:                # 验证规则
  any:                 # 任意一个规则通过
    - meta_generator_equals: "NexusPHP"
    - title_contains: "NexusPHP"

parse:                 # 解析规则
  list:                # 列表解析
    row: "选择器"
    fields:
      字段名:
        selector: "CSS选择器"
        text: true/false
        transform: "size/int/float/date"
```

---

## 📋 三、支持的验证规则

### 3.1 基本规则

- `meta_generator_equals`: 检查meta generator标签
- `title_contains`: 检查标题包含
- `url_contains`: 检查URL包含
- `selector_exists`: 检查CSS选择器是否存在
- `text_contains`: 检查文本包含
- `regex_match`: 正则表达式匹配

### 3.2 逻辑组合

- `any`: 任意一个规则通过即可
- `all`: 所有规则都必须通过

---

## 📋 四、支持的解析规则

### 4.1 解析类型

- `list`: 列表解析（种子列表等）
- `detail`: 详情解析（种子详情等）
- `user`: 用户信息解析

### 4.2 字段配置

- `selector`: CSS选择器
- `text`: 是否提取文本（true/false）
- `attr`: 提取属性（如"href"）
- `transform`: 数据转换（size/int/float/date）

---

## 📋 五、使用示例

### 5.1 识别站点

```python
from app.modules.site_profile.service import SiteProfileService

profile_service = SiteProfileService()
profile = await profile_service.identify_site(site)

if profile:
    family = profile.get("meta", {}).get("family")
    print(f"站点类型: {family}")
```

### 5.2 解析站点内容

```python
# 解析种子列表
result = await profile_service.parse_site_content(
    site,
    parse_type="list",
    page_url="https://example.com/browse.php"
)

# 解析用户信息
user_info = await profile_service.parse_site_content(
    site,
    parse_type="user"
)
```

---

## 📋 六、常见PT站点类型

### 6.1 已支持

- ✅ **NexusPHP**: 最流行的PT站点框架
- ✅ **Gazelle**: 另一个流行的PT站点框架
- ✅ **Unit3D**: 现代化的PT站点框架

### 6.2 可扩展

- **DiscuzX**: 基于Discuz!的PT站点
- **IPTorrents**: IPTorrents专用配置
- **TorrentLeech**: TorrentLeech专用配置
- **FileList**: FileList专用配置
- **其他**: 可根据需要添加

---

## 📋 七、测试建议

### 7.1 配置文件测试

1. **语法检查**: 确保YAML格式正确
2. **字段完整性**: 检查必需字段是否存在
3. **选择器验证**: 验证CSS选择器是否正确

### 7.2 实际站点测试

1. **识别测试**: 使用真实站点URL测试识别
2. **解析测试**: 测试列表、详情、用户信息解析
3. **数据转换**: 验证数据转换是否正确

---

## 📋 八、维护建议

### 8.1 版本管理

- 使用`catalog.json`管理配置文件版本
- 更新配置文件时更新版本号

### 8.2 贡献指南

1. 创建新配置文件时，参考现有配置文件
2. 测试配置文件在实际站点上的表现
3. 更新文档说明配置文件的适用场景

---

**文档生成时间**: 2025-01-XX  
**配置文件数量**: 3个通用配置 + 1个模板

