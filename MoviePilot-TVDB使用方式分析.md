# MoviePilot TVDB 使用方式分析

**生成时间**: 2025-01-XX  
**目的**: 分析MoviePilot中TVDB的实际使用方式，解答为什么前端UI中没有TVDB设置

---

## 📋 一、TVDB在MoviePilot中的定位

### 1.1 TVDB模块类型

**模块类型**: `MediaRecognizeType.TVDB`（媒体识别模块）

**优先级**: 4（较低优先级，在TMDB、Douban等之后）

**模块文件**: `MoviePilot/MoviePilot-2/app/modules/thetvdb/__init__.py`

### 1.2 TVDB配置

**配置文件**: `MoviePilot/MoviePilot-2/app/core/config.py`

```python
# TVDB API Key（内置默认值）
TVDB_V4_API_KEY: str = "ed2aa66b-7899-4677-92a7-67bc9ce3d93a"
TVDB_V4_API_PIN: str = ""
```

**特点**:
- ✅ **内置默认值** - 用户无需配置即可使用
- ✅ **不在前端UI显示** - 因为已有默认值，不需要用户手动配置
- ✅ **可通过环境变量覆盖** - 用户仍可通过环境变量配置自己的API Key

---

## 📋 二、TVDB的实际使用场景

### 2.1 媒体识别链（MediaChain）

**文件**: `MoviePilot/MoviePilot-2/app/chain/__init__.py`

```python
def tvdb_info(self, tvdbid: int) -> Optional[dict]:
    """获取TVDB信息"""
    return self.run_module("tvdb_info", tvdbid=tvdbid)
```

**用途**: 在媒体识别过程中，作为备选数据源获取媒体信息

### 2.2 TVDB搜索链（TvdbChain）

**文件**: `MoviePilot/MoviePilot-2/app/chain/tvdb.py`

```python
class TvdbChain(ChainBase):
    def get_tvdbid_by_name(self, title: str) -> List[int]:
        """通过名称搜索TVDB ID"""
        tvdb_info_list = self.run_module("search_tvdb", title=title)
        return [int(item["tvdb_id"]) for item in tvdb_info_list]
```

**用途**: 通过剧集名称搜索TVDB ID

### 2.3 Fanart图片获取

**文件**: `MoviePilot/MoviePilot-2/app/modules/fanart/__init__.py`

```python
# 对于电视剧类型，优先使用TVDB ID获取Fanart图片
if mediainfo.type == MediaType.MOVIE:
    result = self.__request_fanart(mediainfo.type, mediainfo.tmdb_id)
else:
    if mediainfo.tvdb_id:
        result = self.__request_fanart(mediainfo.type, mediainfo.tvdb_id)
    else:
        logger.info(f"{mediainfo.title_year} 没有tvdbid，无法获取fanart图片")
        return None
```

**用途**: 
- **电影**: 使用TMDB ID获取Fanart图片
- **电视剧**: 优先使用TVDB ID获取Fanart图片（如果没有TVDB ID则无法获取）

### 2.4 NFO文件写入

**文件**: `MoviePilot/MoviePilot-2/app/modules/themoviedb/scraper.py`

```python
# TVDB
if mediainfo.tvdb_id:
    DomUtils.add_node(doc, root, "tvdbid", str(mediainfo.tvdb_id))
    uniqueid_tvdb = DomUtils.add_node(doc, root, "uniqueid", str(mediainfo.tvdb_id))
    uniqueid_tvdb.setAttribute("type", "tvdb")
```

**用途**: 在生成NFO文件时，将TVDB ID写入到NFO文件中，供媒体服务器（Plex/Jellyfin/Emby）使用

### 2.5 Servarr API集成

**文件**: `MoviePilot/MoviePilot-2/app/api/servarr.py`

```python
tvdbinfo = MediaChain().tvdb_info(tvdbid=tvdbid)
```

**用途**: 在Servarr API中提供TVDB信息查询接口

### 2.6 媒体服务器同步

**文件**: `MoviePilot/MoviePilot-2/app/modules/plex/plex.py`, `emby.py`, `jellyfin.py`

**用途**: 从媒体服务器同步媒体信息时，读取TVDB ID并保存到本地数据库

---

## 📋 三、为什么前端UI中没有TVDB设置？

### 3.1 设计理念

**TVDB是后台自动使用的数据源**，不是用户需要手动配置的功能：

1. ✅ **内置默认API Key** - 系统已经内置了默认的TVDB API Key
2. ✅ **自动识别使用** - 在媒体识别链中自动调用，无需用户干预
3. ✅ **低优先级备选** - 作为TMDB的备选数据源，优先级较低
4. ✅ **透明使用** - 用户无需知道TVDB的存在，系统自动处理

### 3.2 与TMDB的区别

| 特性 | TMDB | TVDB |
|------|------|------|
| **用户配置** | ✅ 需要用户申请API Key | ❌ 使用内置默认值 |
| **前端UI** | ✅ 显示在系统设置中 | ❌ 不显示 |
| **主要用途** | 主要数据源（电影和电视剧） | 备选数据源（主要是电视剧） |
| **优先级** | 高（优先级1-2） | 低（优先级4） |
| **使用场景** | 媒体搜索、识别、元数据 | Fanart图片、NFO文件、Servarr |

### 3.3 实际使用流程

```
用户操作 → 媒体识别链 → TMDB（主要） → TVDB（备选） → 结果
                              ↓
                        如果没有TMDB结果
                              ↓
                        尝试TVDB搜索
                              ↓
                        获取TVDB ID
                              ↓
                        用于Fanart图片、NFO文件等
```

---

## 📋 四、TVDB在VabHub中的建议实现

### 4.1 保持MoviePilot的设计理念

**建议**: 与MoviePilot保持一致

1. ✅ **使用内置默认API Key** - 已实现 ✅
2. ✅ **不在前端UI显示** - 不需要用户配置
3. ✅ **作为媒体识别模块** - 集成到媒体识别链中
4. ✅ **低优先级备选** - 在TMDB之后使用

### 4.2 实现场景

**需要实现的功能**:

1. **媒体识别模块** - 实现`TheTvDbModule`，作为`MediaRecognizeType.TVDB`
2. **TVDB搜索** - 实现`search_tvdb`方法，通过名称搜索TVDB剧集
3. **TVDB信息获取** - 实现`tvdb_info`方法，通过TVDB ID获取详细信息
4. **Fanart集成** - 在Fanart模块中，对于电视剧类型使用TVDB ID获取图片
5. **NFO文件写入** - 在NFO文件生成时，写入TVDB ID
6. **媒体识别链集成** - 将TVDB模块集成到媒体识别链中，作为备选数据源

### 4.3 前端UI策略

**建议**: **不在前端UI中显示TVDB设置**

**原因**:
- ✅ **已有默认值** - 使用MoviePilot的默认API Key
- ✅ **后台自动使用** - 用户无需知道TVDB的存在
- ✅ **简化界面** - 减少用户困惑
- ✅ **与MoviePilot一致** - 保持相同的用户体验

**如果需要覆盖**:
- 用户可以通过环境变量`TVDB_V4_API_KEY`配置自己的API Key
- 不需要在前端UI中提供配置选项

---

## 📋 五、总结

### 5.1 MoviePilot的TVDB使用方式

- ✅ **后台自动使用** - 作为媒体识别链的一部分，自动调用
- ✅ **内置默认API Key** - 用户无需配置
- ✅ **不在前端UI显示** - 因为已有默认值，不需要用户配置
- ✅ **主要用途**:
  - Fanart图片获取（电视剧类型）
  - NFO文件写入（TVDB ID）
  - 媒体识别备选数据源
  - Servarr API集成

### 5.2 VabHub的实现建议

- ✅ **保持MoviePilot的设计理念** - 后台自动使用，不在前端UI显示
- ✅ **使用内置默认API Key** - 已实现 ✅
- ✅ **集成到媒体识别链** - 作为备选数据源
- ✅ **实现Fanart集成** - 对于电视剧使用TVDB ID获取图片
- ✅ **实现NFO文件写入** - 写入TVDB ID到NFO文件

---

**文档生成时间**: 2025-01-XX  
**文档版本**: 1.0

