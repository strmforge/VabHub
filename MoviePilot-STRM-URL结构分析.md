# MoviePilot STRM URL结构分析

**分析时间**: 2025-01-XX  
**来源**: MoviePilot p115strmhelper插件生成的STRM文件

---

## 📋 URL结构拆解

### 完整URL示例

```
http://192.168.51.105:3000/api/v1/plugin/P115StrmHelper/redirect_url?apikey=mwKtUfs6MDjnMDt04b8naQ&pickcode=cg16zx93h3xy6ddf1
```

### 结构分析

| 部分 | 内容 | 说明 |
|------|------|------|
| **协议和主机** | `http://192.168.51.105:3000` | MoviePilot本地服务器地址 |
| **API路径** | `/api/v1/plugin/P115StrmHelper` | 115网盘助手插件API路径 |
| **端点** | `/redirect_url` | 重定向URL端点 |
| **查询参数1** | `apikey=mwKtUfs6MDjnMDt04b8naQ` | API令牌（用于验证请求） |
| **查询参数2** | `pickcode=cg16zx93h3xy6ddf1` | 115网盘文件pickcode（文件唯一标识码） |

---

## 🔍 关键概念解释

### 1. `/redirect_url` 端点

**作用**: 这是一个**302重定向端点**，用于将STRM文件中的URL重定向到115网盘的实际下载地址。

**工作流程**:
1. 媒体服务器（Emby/Jellyfin/Plex）读取STRM文件
2. 向 `redirect_url` 端点发起请求（携带 `apikey` 和 `pickcode`）
3. 插件验证 `apikey` 是否有效
4. 使用 `pickcode` 调用115网盘API获取实际下载地址
5. 返回302重定向响应，指向115网盘的实际下载URL
6. 媒体服务器跟随重定向，开始播放

**优势**:
- ✅ 不直接暴露115网盘下载地址（下载地址有时效性）
- ✅ 可以动态刷新下载地址（当旧地址过期时）
- ✅ 可以添加访问控制和日志记录
- ✅ 可以添加限流和缓存机制

### 2. `pickcode` 参数

**定义**: `pickcode` 是115网盘文件的**唯一标识码**，类似于文件的"提取码"。

**特点**:
- ✅ 每个115网盘文件都有唯一的 `pickcode`
- ✅ `pickcode` 是永久性的（不会过期）
- ✅ 通过 `pickcode` 可以获取文件的下载地址
- ✅ `pickcode` 通常是一个16-20位的字符串

**获取方式**:
- 通过115网盘API获取文件列表时，每个文件都会返回 `pickcode`
- 通过115网盘官方开发者API的 `/open/ufile/files` 接口获取

**使用示例**:
```python
# 115网盘API获取下载地址
POST /open/ufile/downurl
{
    "pick_code": "cg16zx93h3xy6ddf1"
}

# 返回
{
    "data": {
        "url": {
            "url": "https://115.com/file/xxx?token=xxx"
        }
    }
}
```

### 3. `apikey` 参数

**定义**: `apikey` 是MoviePilot的**API令牌**，用于验证请求的合法性。

**作用**:
- ✅ 防止未授权访问
- ✅ 限制只有知道API密钥的用户才能获取下载地址
- ✅ 可以用于统计和日志记录

**配置位置**:
- MoviePilot系统设置 → 基础设置 → API令牌

**说明**: "设置外部请求MoviePilot API时使用的token值"

---

## 🔄 完整工作流程

### 1. STRM文件生成阶段

```
1. 扫描115网盘媒体文件
2. 获取文件的pickcode
3. 生成STRM文件，内容为：
   http://192.168.51.105:3000/api/v1/plugin/P115StrmHelper/redirect_url?apikey=xxx&pickcode=xxx
```

### 2. 媒体服务器播放阶段

```
1. 用户点击播放
2. 媒体服务器读取STRM文件
3. 向redirect_url发起GET请求
4. 插件验证apikey
5. 使用pickcode获取115下载地址
6. 返回302重定向
7. 媒体服务器跟随重定向
8. 开始播放
```

### 3. 下载地址刷新机制

```
1. 如果115下载地址过期
2. 插件可以重新调用115 API获取新地址
3. 返回新的302重定向
4. 媒体服务器继续播放
```

---

## 📊 与VabHub的对比

### MoviePilot方案

```
STRM内容: http://localhost:3000/api/v1/plugin/P115StrmHelper/redirect_url?apikey=xxx&pickcode=xxx
```

**特点**:
- ✅ 使用插件系统实现
- ✅ 需要配置API密钥
- ✅ pickcode直接暴露在URL中
- ✅ 需要本地服务器运行

### VabHub当前方案

根据之前的实现，VabHub有两种模式：

#### 1. Direct模式（直接使用115下载地址）

```
STRM内容: https://115.com/file/xxx?token=xxx
```

**特点**:
- ✅ 简单直接
- ❌ 下载地址可能过期
- ❌ 无法动态刷新

#### 2. Local Redirect模式（本地重定向）

```
STRM内容: http://192.168.1.100:8000/api/strm/stream/115/TOKEN
```

**特点**:
- ✅ 使用token验证（更安全）
- ✅ 可以动态刷新下载地址
- ✅ 支持限流和日志
- ✅ 自动检测本地IP

---

## 💡 关键发现

### 1. pickcode的重要性

`pickcode` 是115网盘文件的核心标识，**必须保存**在文件元数据中，用于：
- 获取下载地址
- 文件识别
- 文件操作（重命名、移动、删除等）

### 2. redirect_url的必要性

使用 `redirect_url` 而不是直接使用115下载地址的原因：
- ✅ 115下载地址有**时效性**（通常几小时到几天）
- ✅ 直接使用会导致播放中断
- ✅ 通过redirect可以**动态刷新**下载地址

### 3. API密钥的作用

`apikey` 用于：
- ✅ 验证请求合法性
- ✅ 防止未授权访问
- ✅ 统计和日志记录

---

## 🎯 对VabHub的启示

### 当前实现状态

VabHub已经实现了类似的机制：
- ✅ Local Redirect模式（`/api/strm/stream/{storage_type}/{token}`）
- ✅ Token验证机制
- ✅ 自动IP检测

### 可以改进的地方

1. **pickcode存储**
   - ✅ 已实现：在文件元数据中存储pickcode
   - ⚠️ 需要确保：所有115文件操作都保存pickcode

2. **redirect端点**
   - ✅ 已实现：`/api/strm/stream/115/TOKEN`
   - ⚠️ 需要验证：是否正确使用pickcode获取下载地址

3. **API密钥机制**
   - ✅ 已实现：使用token验证
   - ✅ 优势：比MoviePilot的apikey更安全（token有时效性）

---

## 📝 总结

### MoviePilot方案分析

1. **URL结构**: `http://{host}:{port}/api/v1/plugin/{plugin_name}/redirect_url?apikey={key}&pickcode={code}`
2. **redirect_url**: 302重定向端点，动态获取115下载地址
3. **pickcode**: 115网盘文件唯一标识码，永久有效
4. **apikey**: API令牌，用于验证请求

### VabHub方案对比

VabHub的实现更加**现代化和安全**：
- ✅ 使用token而不是固定的apikey
- ✅ 自动检测本地IP
- ✅ 统一的API路径结构
- ✅ 更好的安全机制

**建议**: 保持VabHub当前的实现，它已经比MoviePilot的方案更优！

---

**文档生成时间**: 2025-01-XX  
**文档版本**: 1.0

