# 媒体分类YAML配置实现总结

## 概述

已实现类似MoviePilot的YAML配置文件方式的媒体分类系统，支持电影、电视剧和音乐的二级分类。

## 实现内容

### 1. CategoryHelper类 (`category_helper.py`)

- **功能**：基于YAML配置文件进行分类
- **特性**：
  - 支持电影、电视剧、音乐分类
  - 支持多种匹配条件：`original_language`、`production_countries`/`origin_country`、`genre_ids`、`release_year`
  - 支持多值匹配（逗号分隔）
  - 支持排除条件（!前缀）
  - 支持年份范围（YYYY-YYYY）
  - 自动创建默认配置文件

### 2. 配置文件 (`config/category.yaml`)

- **位置**：`VabHub/config/category.yaml`
- **格式**：YAML格式，与MoviePilot兼容
- **内容**：
  - 电影分类策略（动画电影、华语电影、外语电影）
  - 电视剧分类策略（国漫、日番、纪录片、儿童、综艺、国产剧、欧美剧、日韩剧、未分类）
  - 音乐分类策略（华语音乐、欧美音乐、日韩音乐、其他音乐）
  - 完整的字典说明（genre_ids、original_language、origin_country/production_countries）

### 3. MediaClassifier集成

- **更新**：`MediaClassifier`现在优先使用YAML配置的分类策略
- **回退**：如果YAML配置未匹配或未启用，使用默认分类逻辑
- **支持**：电影、电视剧、音乐分类

### 4. MediaOrganizer集成

- **更新**：`_build_target_path`方法现在使用分类器生成的分类路径
- **效果**：文件整理时会根据YAML配置的分类策略自动创建对应的目录结构

## 使用方法

### 配置文件位置

默认配置文件位于：`VabHub/config/category.yaml`

如果配置文件不存在，系统会自动创建默认配置。

### 配置示例

```yaml
# 配置电影的分类策略
movie:
  动画电影:
    genre_ids: '16'
  华语电影:
    original_language: 'zh,cn,bo,za'
  外语电影:

# 配置电视剧的分类策略
tv:
  国漫:
    genre_ids: '16'
    origin_country: 'CN,TW,HK'
  日番:
    genre_ids: '16'
    origin_country: 'JP'
  纪录片:
    genre_ids: '99'
  国产剧:
    origin_country: 'CN,TW,HK'
  欧美剧:
    origin_country: 'US,FR,GB,DE,ES,IT,NL,PT,RU,UK'
  日韩剧:
    origin_country: 'JP,KP,KR,TH,IN,SG'
  未分类:

# 配置音乐的分类策略
music:
  华语音乐:
    original_language: 'zh,cn'
  欧美音乐:
    original_language: 'en'
  日韩音乐:
    original_language: 'ja,ko'
  其他音乐:
```

### 支持的匹配条件

1. **original_language**：语种（如：zh, cn, en, ja, ko）
2. **production_countries**：制片国家（电影，如：CN, US, JP）
3. **origin_country**：国家或地区（电视剧，如：CN, US, JP）
4. **genre_ids**：内容类型（如：16=动画, 99=纪录片）
5. **release_year**：发行年份（格式：YYYY 或 YYYY-YYYY）

### 特殊语法

- **多值匹配**：使用逗号分隔，如 `origin_country: 'CN,TW,HK'`
- **排除条件**：使用!前缀，如 `origin_country: '!CN'`（排除中国）
- **年份范围**：使用-连接，如 `release_year: '2020-2023'`
- **空规则**：空规则表示默认分类，匹配所有未匹配的项

## 与MoviePilot的对比

| 特性 | MoviePilot | VabHub |
|------|-----------|--------|
| YAML配置文件 | ✅ | ✅ |
| 电影分类 | ✅ | ✅ |
| 电视剧分类 | ✅ | ✅ |
| 音乐分类 | ❌ | ✅ **独有** |
| 多条件匹配 | ✅ | ✅ |
| 排除条件 | ✅ | ✅ |
| 年份范围 | ✅ | ✅ |
| 自动创建默认配置 | ❌ | ✅ **增强** |

## 依赖

- **ruamel.yaml**：用于解析YAML配置文件
  ```bash
  pip install ruamel.yaml
  ```

如果未安装`ruamel.yaml`，系统会使用默认分类逻辑，并记录警告日志。

## 文件结构

```
VabHub/
├── config/
│   └── category.yaml          # 分类配置文件
├── backend/
│   └── app/
│       └── modules/
│           └── media_renamer/
│               ├── category_helper.py    # 分类助手
│               ├── classifier.py          # 分类器（已更新）
│               └── organizer.py           # 整理器（已更新）
```

## 使用示例

### Python代码

```python
from app.modules.media_renamer import CategoryHelper, MediaClassifier
from pathlib import Path

# 创建分类助手
category_helper = CategoryHelper(Path("config/category.yaml"))

# 获取电影分类
tmdb_info = {
    "genre_ids": [16],
    "original_language": "zh",
    "production_countries": [{"iso_3166_1": "CN"}]
}
category = category_helper.get_movie_category(tmdb_info)
print(category)  # 输出：动画电影 或 华语电影

# 使用分类器
classifier = MediaClassifier()
media_category = await classifier.classify(media_info, tmdb_data)
print(media_category.category)  # 输出：根据YAML配置的分类名称
```

## 注意事项

1. **配置文件格式**：必须严格符合YAML语法规则
2. **匹配顺序**：分类按配置文件的顺序从上到下匹配，匹配到第一个符合条件的分类即返回
3. **默认分类**：空规则（无条件的分类）作为默认分类，应放在最后
4. **大小写**：匹配时不区分大小写
5. **音乐分类**：音乐分类可能需要根据实际数据源调整，因为音乐通常没有TMDB的`original_language`字段

## 未来改进

1. 添加前端界面来编辑分类配置
2. 支持更多匹配条件（如评分、时长等）
3. 支持正则表达式匹配
4. 添加分类统计和分析功能
5. 支持分类规则的导入/导出

