# MoviePilot系统设置对比分析

**分析时间**: 2025-01-XX  
**目的**: 对比MoviePilot的系统设置功能，为VabHub实现提供参考

---

## 📋 一、基础设置 (Basic Settings)

### 1.1 MoviePilot实现

**文件**: `MoviePilot-Frontend-2/src/views/setting/AccountSettingSystem.vue`

**配置项**:

1. **访问域名 (APP_DOMAIN)**
   - 类型: 文本输入
   - 说明: 用于发送通知时，添加快捷跳转地址
   - 示例: `http://localhost:3000`

2. **识别数据源 (RECOGNIZE_SOURCE)**
   - 类型: 下拉选择
   - 选项: `TheMovieDb`, `豆瓣`
   - 说明: 设置默认媒体信息识别数据源
   - 默认值: `themoviedb`

3. **API令牌 (API_TOKEN)**
   - 类型: 文本输入（密码类型）
   - 说明: 设置外部请求MoviePilot API时使用的token值
   - 验证: 长度至少16个字符
   - 功能: 支持复制和随机生成

4. **验证码识别服务器 (OCR_HOST)**
   - 类型: 文本输入
   - 说明: 用于站点签到、更新站点Cookie等识别验证码
   - 示例: `http://192.168.51.105:9899`

5. **背景壁纸 (WALLPAPER)**
   - 类型: 下拉选择
   - 选项: `TMDB电影海报`, `Bing`, `媒体服务器`, `自定义`, `无`
   - 说明: 选择登录页面背景来源

6. **自定义壁纸API (CUSTOMIZE_WALLPAPER_API_URL)**
   - 类型: 文本输入（条件显示，当WALLPAPER为"自定义"时）
   - 说明: 自定义壁纸API地址

7. **媒体服务器同步间隔 (MEDIASERVER_SYNC_INTERVAL)**
   - 类型: 数字输入
   - 单位: 小时
   - 说明: 媒体服务器同步间隔时间
   - 验证: 最小值为1

8. **Github Token (GITHUB_TOKEN)**
   - 类型: 文本输入
   - 说明: 用于访问Github API（可选）

9. **AI Agent配置** (可选)
   - **AI Agent启用 (AI_AGENT_ENABLE)**: 开关
   - **LLM提供商 (LLM_PROVIDER)**: 下拉选择（OpenAI, Google, DeepSeek）
   - **LLM模型 (LLM_MODEL)**: 文本输入
   - **LLM API Key (LLM_API_KEY)**: 密码输入
   - **LLM Base URL (LLM_BASE_URL)**: 文本输入

### 1.2 VabHub现状

**当前状态**: ⚠️ 部分实现

**已有功能**:
- ✅ 系统设置基础架构
- ⚠️ 缺少部分配置项

**需要实现**:
- ⚠️ 访问域名配置
- ⚠️ 识别数据源配置
- ⚠️ API令牌配置（可能需要增强）
- ⚠️ 验证码识别服务器配置
- ⚠️ 背景壁纸配置
- ⚠️ 媒体服务器同步间隔配置
- ⚠️ AI Agent配置（可选）

---

## 📋 二、高级设置 (Advanced Settings)

### 2.1 MoviePilot实现

**文件**: `MoviePilot-Frontend-2/src/views/setting/AccountSettingSystem.vue`

**标签页结构**:
- **系统** (System)
- **媒体** (Media)
- **网络** (Network)
- **日志** (Log)
- **实验室** (Laboratory)

#### 2.1.1 系统标签 (System Tab)

**配置项**:

1. **用户辅助认证 (AUXILIARY_AUTH_ENABLE)**
   - 类型: 开关
   - 说明: 允许外部服务进行登录认证以及自动创建用户
   - 默认值: `false`

2. **分享订阅数据 (SUBSCRIBE_STATISTIC_SHARE)**
   - 类型: 开关
   - 说明: 分享订阅统计数据到热门订阅，供其他MPer参考
   - 默认值: `true`

3. **分享工作流数据 (WORKFLOW_STATISTIC_SHARE)**
   - 类型: 开关
   - 说明: 分享工作流统计数据到热门工作流，供其他MPer参考
   - 默认值: `true`

4. **自动更新MoviePilot (MOVIEPILOT_AUTO_UPDATE)**
   - 类型: 开关
   - 说明: 重启时自动更新MoviePilot到最新发行版本
   - 默认值: `false`（可设置为`release`或`dev`）

5. **全局图片缓存 (GLOBAL_IMAGE_CACHE)**
   - 类型: 开关
   - 说明: 将媒体图片缓存到本地，提升图片加载速度
   - 默认值: `false`

6. **上报插件安装数据 (PLUGIN_STATISTIC_SHARE)**
   - 类型: 开关
   - 说明: 上报插件安装数据给服务器，用于统计展示插件安装情况
   - 默认值: `true`

7. **大内存模式 (BIG_MEMORY_MODE)**
   - 类型: 开关
   - 说明: 使用更大的内存缓存数据，提升系统性能
   - 默认值: `false`

8. **数据库WAL模式 (DB_WAL_ENABLE)** (仅SQLite)
   - 类型: 开关
   - 说明: 启用SQLite WAL模式
   - 默认值: `true`

9. **自动更新站点资源 (AUTO_UPDATE_RESOURCE)**
   - 类型: 开关
   - 说明: 重启时自动检测和更新站点资源包
   - 默认值: `true`

#### 2.1.2 媒体标签 (Media Tab)

**配置项**:

1. **TMDB API域名 (TMDB_API_DOMAIN)**
   - 类型: 下拉选择
   - 选项: `api.themoviedb.org`, `api.tmdb.org`
   - 说明: TMDB API域名

2. **TMDB图片域名 (TMDB_IMAGE_DOMAIN)**
   - 类型: 下拉选择
   - 选项: `image.tmdb.org`
   - 说明: TMDB图片域名

3. **TMDB元数据语言 (TMDB_LOCALE)**
   - 类型: 下拉选择
   - 选项: `简体中文`, `繁体中文`, `English`
   - 说明: TMDB元数据语言

4. **元数据缓存过期时间 (META_CACHE_EXPIRE)**
   - 类型: 数字输入
   - 单位: 小时
   - 说明: 元数据缓存过期时间，0为自动
   - 默认值: `0`

5. **刮削跟随TMDB (SCRAP_FOLLOW_TMDB)**
   - 类型: 开关
   - 说明: 刮削时跟随TMDB设置
   - 默认值: `true`

6. **刮削原始图片 (TMDB_SCRAP_ORIGINAL_IMAGE)**
   - 类型: 开关
   - 说明: 使用TMDB原始语种图片
   - 默认值: `false`

7. **Fanart启用 (FANART_ENABLE)**
   - 类型: 开关
   - 说明: 启用Fanart图片源
   - 默认值: `false`

8. **Fanart语言 (FANART_LANG)**
   - 类型: 多选下拉
   - 选项: `zh`, `en`, `ja`, `ko`, `de`, `fr`, `es`, `it`, `pt`, `ru`
   - 说明: Fanart语言设置（多选，逗号分隔）

9. **刮削开关设置** (展开面板)
   - **电影**: NFO, 海报, 背景图, Logo, 光盘图, 横幅图, 缩略图
   - **电视剧**: NFO, 海报, 背景图, 横幅图, Logo, 缩略图
   - **季**: NFO, 海报, 横幅图, 缩略图
   - **集**: NFO, 缩略图

#### 2.1.3 网络标签 (Network Tab)

**配置项**:

1. **代理服务器 (PROXY_HOST)**
   - 类型: 文本输入
   - 说明: 网络代理服务器地址
   - 示例: `http://127.0.0.1:7890`

2. **Github代理 (GITHUB_PROXY)**
   - 类型: 下拉选择（可输入）
   - 说明: Github加速代理
   - 可清空

3. **PIP代理 (PIP_PROXY)**
   - 类型: 下拉选择（可输入）
   - 说明: PIP镜像站
   - 预设选项: 清华大学、中国科技大学、北京大学、阿里云、腾讯云、网易云、豆瓣等
   - 可清空

4. **DOH启用 (DOH_ENABLE)**
   - 类型: 开关
   - 说明: 启用DNS over HTTPS
   - 默认值: `false`

5. **DOH解析器 (DOH_RESOLVERS)** (条件显示)
   - 类型: 多行文本
   - 说明: DOH解析服务器列表（逗号分隔）
   - 默认值: `1.0.0.1,1.1.1.1,9.9.9.9,149.112.112.112`

6. **DOH域名 (DOH_DOMAINS)** (条件显示)
   - 类型: 多行文本
   - 说明: 使用DOH解析的域名列表（逗号分隔）
   - 默认值: `api.themoviedb.org,api.tmdb.org,webservice.fanart.tv,api.github.com,github.com,raw.githubusercontent.com,codeload.github.com,api.telegram.org`

7. **安全图片域名 (SECURITY_IMAGE_DOMAINS)** (展开面板)
   - 类型: 标签列表（可添加/删除）
   - 说明: 允许加载图片的安全域名列表

#### 2.1.4 日志标签 (Log Tab)

**配置项**:

1. **调试模式 (DEBUG)**
   - 类型: 开关
   - 说明: 启用调试模式
   - 默认值: `false`

2. **日志级别 (LOG_LEVEL)** (条件显示，当DEBUG为false时)
   - 类型: 下拉选择
   - 选项: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
   - 说明: 日志级别
   - 默认值: `INFO`

3. **日志文件最大大小 (LOG_MAX_FILE_SIZE)**
   - 类型: 数字输入
   - 单位: MB
   - 说明: 单个日志文件最大大小
   - 默认值: `5`
   - 验证: 最小值为1

4. **日志备份数量 (LOG_BACKUP_COUNT)**
   - 类型: 数字输入
   - 说明: 日志文件备份数量
   - 默认值: `3`
   - 验证: 最小值为1

5. **日志文件格式 (LOG_FILE_FORMAT)**
   - 类型: 文本输入
   - 说明: 日志文件格式
   - 默认值: `【%(levelname)s】%(asctime)s - %(message)s`

#### 2.1.5 实验室标签 (Laboratory Tab)

**配置项**:

1. **插件自动重载 (PLUGIN_AUTO_RELOAD)**
   - 类型: 开关
   - 说明: 启用插件自动重载
   - 默认值: `false`

2. **编码检测性能模式 (ENCODING_DETECTION_PERFORMANCE_MODE)**
   - 类型: 开关
   - 说明: 启用编码检测性能模式
   - 默认值: `true`

### 2.2 VabHub现状

**当前状态**: ⚠️ 部分实现

**已有功能**:
- ✅ 系统设置基础架构
- ✅ 部分高级设置项（如代理、日志等）
- ⚠️ 缺少完整的标签页结构
- ⚠️ 缺少部分配置项

**需要实现**:
- ⚠️ 完整的标签页结构（系统、媒体、网络、日志、实验室）
- ⚠️ 系统标签的所有配置项
- ⚠️ 媒体标签的所有配置项（包括刮削开关设置）
- ⚠️ 网络标签的DOH配置
- ⚠️ 日志标签的完整配置
- ⚠️ 实验室标签的配置

---

## 📋 三、后端API实现

### 3.1 MoviePilot后端

**文件**: `MoviePilot-2/app/api/endpoints/system.py`

**主要端点**:
- `GET /system/env` - 获取系统环境变量（配置）
- `POST /system/env` - 保存系统环境变量（配置）
- `GET /system/setting/Downloaders` - 获取下载器设置
- `POST /system/setting/Downloaders` - 保存下载器设置
- `GET /system/setting/MediaServers` - 获取媒体服务器设置
- `POST /system/setting/MediaServers` - 保存媒体服务器设置
- `GET /system/setting/ScrapingSwitchs` - 获取刮削开关设置
- `POST /system/setting/ScrapingSwitchs` - 保存刮削开关设置

**配置管理**:
- 使用环境变量（`.env`文件）存储配置
- 使用`pydantic`的`BaseSettings`管理配置
- 配置验证和自动生成（如API_TOKEN）

### 3.2 VabHub现状

**当前状态**: ⚠️ 部分实现

**已有功能**:
- ✅ 系统设置API基础架构
- ⚠️ 缺少部分配置项的支持

**需要实现**:
- ⚠️ 完整的配置项支持
- ⚠️ 配置验证和自动生成
- ⚠️ 刮削开关设置API

---

## 📋 四、实现建议

### 4.1 优先级

**高优先级**:
1. ✅ 基础设置的核心配置项（访问域名、识别数据源、API令牌、验证码识别服务器）
2. ✅ 高级设置的系统标签（用户辅助认证、分享数据、自动更新等）
3. ✅ 高级设置的媒体标签（TMDB配置、刮削开关）

**中优先级**:
4. ⚠️ 高级设置的网络标签（DOH配置）
5. ⚠️ 高级设置的日志标签
6. ⚠️ 高级设置的实验室标签

**低优先级**:
7. ⚠️ AI Agent配置（可选）
8. ⚠️ 背景壁纸配置（可选）

### 4.2 实现步骤

**步骤1: 后端配置模型**
- 扩展`app/core/config.py`，添加所有配置项
- 实现配置验证和默认值
- 实现配置的读取和保存

**步骤2: 后端API**
- 扩展`app/api/settings.py`，添加所有配置项的API
- 实现刮削开关设置的API
- 实现配置验证

**步骤3: 前端基础设置页面**
- 实现基础设置表单
- 实现配置项的输入和验证
- 实现保存功能

**步骤4: 前端高级设置对话框**
- 实现标签页结构
- 实现各标签页的配置项
- 实现展开面板（刮削开关、安全域名等）

---

## 📋 五、配置项对比表

| 配置项 | MoviePilot | VabHub | 优先级 |
|--------|-----------|--------|--------|
| **基础设置** |
| 访问域名 | ✅ | ⚠️ | 高 |
| 识别数据源 | ✅ | ⚠️ | 高 |
| API令牌 | ✅ | ⚠️ | 高 |
| 验证码识别服务器 | ✅ | ⚠️ | 高 |
| 背景壁纸 | ✅ | ❌ | 低 |
| 媒体服务器同步间隔 | ✅ | ⚠️ | 中 |
| Github Token | ✅ | ❌ | 低 |
| AI Agent | ✅ | ❌ | 低 |
| **高级设置-系统** |
| 用户辅助认证 | ✅ | ❌ | 中 |
| 分享订阅数据 | ✅ | ❌ | 低 |
| 分享工作流数据 | ✅ | ❌ | 低 |
| 自动更新 | ✅ | ⚠️ | 中 |
| 全局图片缓存 | ✅ | ⚠️ | 中 |
| 上报插件数据 | ✅ | ❌ | 低 |
| 大内存模式 | ✅ | ❌ | 中 |
| 数据库WAL模式 | ✅ | ⚠️ | 中 |
| 自动更新站点资源 | ✅ | ⚠️ | 中 |
| **高级设置-媒体** |
| TMDB API域名 | ✅ | ⚠️ | 中 |
| TMDB图片域名 | ✅ | ⚠️ | 中 |
| TMDB元数据语言 | ✅ | ⚠️ | 中 |
| 元数据缓存过期时间 | ✅ | ⚠️ | 中 |
| 刮削跟随TMDB | ✅ | ❌ | 中 |
| 刮削原始图片 | ✅ | ❌ | 低 |
| Fanart启用 | ✅ | ⚠️ | 低 |
| Fanart语言 | ✅ | ❌ | 低 |
| 刮削开关设置 | ✅ | ❌ | 中 |
| **高级设置-网络** |
| 代理服务器 | ✅ | ⚠️ | 中 |
| Github代理 | ✅ | ⚠️ | 低 |
| PIP代理 | ✅ | ❌ | 低 |
| DOH启用 | ✅ | ⚠️ | 中 |
| DOH解析器 | ✅ | ⚠️ | 中 |
| DOH域名 | ✅ | ⚠️ | 中 |
| 安全图片域名 | ✅ | ❌ | 低 |
| **高级设置-日志** |
| 调试模式 | ✅ | ⚠️ | 中 |
| 日志级别 | ✅ | ⚠️ | 中 |
| 日志文件最大大小 | ✅ | ❌ | 低 |
| 日志备份数量 | ✅ | ❌ | 低 |
| 日志文件格式 | ✅ | ❌ | 低 |
| **高级设置-实验室** |
| 插件自动重载 | ✅ | ⚠️ | 中 |
| 编码检测性能模式 | ✅ | ❌ | 低 |

**图例**:
- ✅ 已实现
- ⚠️ 部分实现
- ❌ 未实现

---

## 📋 六、总结

### 6.1 MoviePilot特点

1. **配置项丰富**: 涵盖系统、媒体、网络、日志、实验室等多个方面
2. **分类清晰**: 基础设置和高级设置分离，高级设置使用标签页组织
3. **用户体验好**: 有详细的说明和提示，支持条件显示和验证
4. **功能完整**: 包括刮削开关、安全域名等细节配置

### 6.2 VabHub改进方向

1. **完善基础设置**: 实现访问域名、识别数据源、API令牌、验证码识别服务器等核心配置
2. **实现高级设置**: 创建标签页结构，实现系统、媒体、网络、日志、实验室等配置
3. **增强配置管理**: 实现配置验证、自动生成、默认值等功能
4. **优化用户体验**: 添加详细的说明和提示，支持条件显示和验证

---

**文档版本**: 1.0  
**最后更新**: 2025-01-XX

