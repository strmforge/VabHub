# STRM端口映射最佳实践

**更新时间**: 2025-01-XX  
**适用场景**: 媒体库软件（Plex、Jellyfin、Emby）默认端口映射配置

---

## 📋 一、媒体库软件端口说明

### 1.1 支持的媒体库软件

**VabHub支持多种媒体库软件**:
- **Emby** - 默认端口：8096
- **Jellyfin** - 默认端口：8096
- **Plex** - 默认端口：32400

### 1.2 各软件默认端口

| 媒体库软件 | 默认端口 | 说明 |
|-----------|---------|------|
| **Emby** | 8096 | 客户端/web端已预制8096端口，只需填写域名 |
| **Jellyfin** | 8096 | 与Emby使用相同端口，客户端/web端已预制8096端口 |
| **Plex** | 32400 | 客户端/web端已预制32400端口，只需填写域名 |

### 1.3 端口映射场景

**默认端口映射**（推荐）:
- **Emby/Jellyfin**: 内网8096 -> 外网8096，配置：`vabhub.example.com:8096`
- **Plex**: 内网32400 -> 外网32400，配置：`vabhub.example.com:32400`

**优势**:
- ✅ 客户端只需填写域名即可连接
- ✅ 地址栏下方已预制默认端口，自动使用
- ✅ 端口映射简单，内网端口 -> 外网端口（保持一致）
- ✅ 符合用户习惯，无需额外配置

---

## 📋 二、推荐配置

### 2.1 Emby/Jellyfin默认端口映射配置（推荐）

**场景**: 使用Emby/Jellyfin默认端口，内网8096映射到外网8096

**配置**:
```json
{
  "local_redirect_host": "192.168.1.100",  // 内网IP（自动检测）
  "local_redirect_port": 8096,              // 内网端口（Emby/Jellyfin默认）
  "external_redirect_host": "vabhub.example.com:8096",  // 外网域名（带端口号）
  "external_redirect_port": 0,              // 从域名中提取
  "use_https": false,                        // HTTP（家庭宽带通常关闭443）
  "auto_adapt_network": true                 // 自动适配
}
```

**生成的URL**:
- 内网：`http://192.168.1.100:8096/api/strm/stream/115/TOKEN`
- 外网：`http://vabhub.example.com:8096/api/strm/stream/115/TOKEN`

**使用方式**:
1. 在Emby/Jellyfin客户端填写服务器地址：`vabhub.example.com`
2. 客户端自动使用8096端口连接
3. 完美匹配，无需额外配置

### 2.2 Plex默认端口映射配置（推荐）

**场景**: 使用Plex默认端口，内网32400映射到外网32400

**配置**:
```json
{
  "local_redirect_host": "192.168.1.100",  // 内网IP（自动检测）
  "local_redirect_port": 32400,            // 内网端口（Plex默认）
  "external_redirect_host": "vabhub.example.com:32400",  // 外网域名（带端口号）
  "external_redirect_port": 0,             // 从域名中提取
  "use_https": false,                      // HTTP（家庭宽带通常关闭443）
  "auto_adapt_network": true               // 自动适配
}
```

**生成的URL**:
- 内网：`http://192.168.1.100:32400/api/strm/stream/115/TOKEN`
- 外网：`http://vabhub.example.com:32400/api/strm/stream/115/TOKEN`

**使用方式**:
1. 在Plex客户端填写服务器地址：`vabhub.example.com`
2. 客户端自动使用32400端口连接
3. 完美匹配，无需额外配置

### 2.3 自定义端口映射

**场景**: 使用自定义端口（例如：6000）

**配置**:
```json
{
  "local_redirect_host": "192.168.1.100",
  "local_redirect_port": 8096,              // 内网端口（Emby默认）
  "external_redirect_host": "vabhub.example.com:6000",  // 外网域名（自定义端口）
  "external_redirect_port": 0,
  "use_https": false,
  "auto_adapt_network": true
}
```

**生成的URL**:
- 内网：`http://192.168.1.100:8096/api/strm/stream/115/TOKEN`
- 外网：`http://vabhub.example.com:6000/api/strm/stream/115/TOKEN`

**使用方式**:
1. 在Emby客户端填写服务器地址：`vabhub.example.com:6000`
2. 需要手动指定端口号
3. 适用于端口冲突或特殊需求

---

## 📋 三、端口选择建议

### 3.1 推荐端口

**媒体库默认端口（推荐）** ⭐⭐⭐⭐⭐:
- **8096** - Emby/Jellyfin默认端口
  - 优势：客户端只需填写域名，自动使用8096端口
  - 适用：Emby/Jellyfin用户，使用默认端口映射
- **32400** - Plex默认端口
  - 优势：客户端只需填写域名，自动使用32400端口
  - 适用：Plex用户，使用默认端口映射

**其他常用端口**:
- 6000 - 常用frp端口
- 8888 - 常用管理端口
- 9090 - 常用服务端口

### 3.2 避免使用的端口

**已占用端口**:
- ❌ **8080** - qBittorrent默认端口（避免冲突）
- ❌ **80** - HTTP默认端口（家庭宽带通常关闭）
- ❌ **443** - HTTPS默认端口（家庭宽带通常关闭）

---

## 📋 四、路由器端口映射配置

### 4.1 默认端口映射（推荐）

**Emby/Jellyfin路由器配置**:
- 内网IP：`192.168.1.100`（VabHub服务器）
- 内网端口：`8096`
- 外网端口：`8096`（与内网端口一致）
- 协议：TCP

**Plex路由器配置**:
- 内网IP：`192.168.1.100`（VabHub服务器）
- 内网端口：`32400`
- 外网端口：`32400`（与内网端口一致）
- 协议：TCP

**优势**:
- 配置简单，内网端口 -> 外网端口（保持一致）
- 客户端只需填写域名
- 符合用户习惯

### 4.2 自定义端口映射

**路由器配置**:
- 内网IP：`192.168.1.100`
- 内网端口：`8096`
- 外网端口：`6000`（自定义）
- 协议：TCP

**注意**:
- Emby客户端需要填写：`domain.com:6000`
- 需要手动指定端口号

---

## 📋 五、媒体库客户端配置

### 5.1 Emby/Jellyfin客户端配置（使用默认端口映射）

**配置步骤**:
1. 打开Emby/Jellyfin客户端
2. 填写服务器地址：`vabhub.example.com`
3. 地址栏下方显示：`:8096`（已预制）
4. 点击连接，自动使用8096端口

**优势**:
- ✅ 只需填写域名
- ✅ 无需手动指定端口
- ✅ 符合用户习惯

### 5.2 Plex客户端配置（使用默认端口映射）

**配置步骤**:
1. 打开Plex客户端
2. 填写服务器地址：`vabhub.example.com`
3. 地址栏下方显示：`:32400`（已预制）
4. 点击连接，自动使用32400端口

**优势**:
- ✅ 只需填写域名
- ✅ 无需手动指定端口
- ✅ 符合用户习惯

### 5.3 使用自定义端口

**配置步骤**:
1. 打开媒体库客户端
2. 填写服务器地址：`vabhub.example.com:6000`
3. 手动指定端口号
4. 点击连接

**注意**:
- 需要手动输入端口号
- 不如默认端口方便

---

## 📋 六、配置示例

### 6.1 最佳实践配置

**Emby/Jellyfin推荐配置**（使用默认端口）:
```json
{
  "local_redirect_host": "",                 // 自动检测
  "local_redirect_port": 8096,              // Emby/Jellyfin默认端口
  "external_redirect_host": "vabhub.example.com:8096",  // 外网域名（带端口号）
  "external_redirect_port": 0,               // 从域名中提取
  "use_https": false,                        // HTTP
  "auto_adapt_network": true                 // 自动适配
}
```

**Plex推荐配置**（使用默认端口）:
```json
{
  "local_redirect_host": "",                 // 自动检测
  "local_redirect_port": 32400,             // Plex默认端口
  "external_redirect_host": "vabhub.example.com:32400",  // 外网域名（带端口号）
  "external_redirect_port": 0,               // 从域名中提取
  "use_https": false,                        // HTTP
  "auto_adapt_network": true                 // 自动适配
}
```

**路由器端口映射**:
- **Emby/Jellyfin**: 内网 `192.168.1.100:8096` -> 外网 `公网IP:8096` 或 `域名:8096`
- **Plex**: 内网 `192.168.1.100:32400` -> 外网 `公网IP:32400` 或 `域名:32400`

**客户端配置**:
- **Emby/Jellyfin**: 服务器地址 `vabhub.example.com`，自动使用8096端口
- **Plex**: 服务器地址 `vabhub.example.com`，自动使用32400端口

### 6.2 内网穿透配置

**使用frp/ngrok**:
```json
{
  "local_redirect_host": "",
  "local_redirect_port": 8096,
  "external_redirect_host": "frp.example.com:6000",  // frp穿透域名
  "external_redirect_port": 0,
  "use_https": false,
  "auto_adapt_network": true
}
```

**Emby客户端**:
- 服务器地址：`frp.example.com:6000`
- 需要手动指定端口

---

## 📋 七、总结

### 7.1 推荐方案

**使用媒体库默认端口映射** ⭐⭐⭐⭐⭐:

**Emby/Jellyfin**:
- 内网端口：8096
- 外网端口：8096
- 外网域名：`domain.com:8096`
- 优势：客户端只需填写域名，自动使用8096端口

**Plex**:
- 内网端口：32400
- 外网端口：32400
- 外网域名：`domain.com:32400`
- 优势：客户端只需填写域名，自动使用32400端口

### 7.2 关键要点

1. **VabHub支持多种媒体库软件** - Plex、Jellyfin、Emby
2. **各软件默认端口不同** - Emby/Jellyfin: 8096, Plex: 32400
3. **客户端已预制默认端口** - 只需填写域名即可连接
4. **默认端口映射最简单** - 内网端口 -> 外网端口（保持一致）
5. **域名带端口号** - 解决家庭宽带端口限制问题

---

**文档生成时间**: 2025-01-XX  
**推荐配置**: 
- **Emby/Jellyfin**: 使用默认端口8096，内网8096映射到外网8096
- **Plex**: 使用默认端口32400，内网32400映射到外网32400

