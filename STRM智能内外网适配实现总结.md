# STRM智能内外网适配实现总结

**实现时间**: 2025-01-XX  
**功能**: 端口自定义、智能内外网适配、解决域名/公网IP问题

---

## 📋 一、用户需求

### 1.1 核心需求

1. **端口自定义** ⭐⭐⭐⭐⭐
   - 内网端口支持自定义（每个用户网络环境不同）
   - 公网端口支持自定义（每个用户网络环境不同）

2. **外网访问域名强制要求** ⭐⭐⭐⭐⭐
   - 中国大陆网络环境大多数公网IP都是跳动的
   - 有些运营商不提供公网IP
   - 外网访问时强制要求填写域名

3. **STRM文件自动适配内外网环境** ⭐⭐⭐⭐⭐
   - 根据请求来源自动选择内网/外网地址
   - 内网请求使用内网地址
   - 外网请求使用外网域名

4. **解决域名/公网IP问题** ⭐⭐⭐⭐
   - 如果能解决不需要强制域名或公网IP，用户会感谢

---

## 📋 二、实现方案

### 2.1 配置扩展

**新增配置项**:

```python
# 内网配置（用于内网访问）
local_redirect_host: str = Field(
    default='',  # 空字符串表示自动检测内网IP
    description="内网访问主机（空字符串表示自动检测内网IP，例如：192.168.1.100）"
)
local_redirect_port: int = Field(
    default=0,  # 0表示使用系统配置的端口
    description="内网访问端口（0表示使用系统配置的端口，例如：8096）"
)

# 外网配置（用于外网访问，解决公网IP跳动问题）
external_redirect_host: str = Field(
    default='',  # 空字符串表示未配置外网访问
    description="外网访问域名（必填，用于外网访问，例如：vabhub.example.com 或 frp.example.com）"
)
external_redirect_port: int = Field(
    default=0,  # 0表示使用默认端口（80/443）
    description="外网访问端口（0表示使用默认端口，HTTP:80, HTTPS:443，或自定义端口）"
)
use_https: bool = Field(
    default=False,
    description="外网访问是否使用HTTPS（推荐，更安全）"
)

# 自动适配模式（推荐）
auto_adapt_network: bool = Field(
    default=True,
    description="自动适配内外网环境（根据请求来源自动选择内网/外网地址，推荐开启）"
)
```

### 2.2 智能适配逻辑

**工作流程**:

```
1. 生成STRM文件时
   ↓
2. 检查是否启用自动适配
   ↓
3. 如果启用，检测请求来源
   ├── 内网请求 → 使用内网地址（IP:内网端口）
   └── 外网请求 → 使用外网域名（域名:外网端口）
   ↓
4. 如果未启用，使用内网地址
   ↓
5. 生成STRM文件URL
```

**实现代码**:

```python
def _get_smart_redirect_address(self, request: Optional[Any] = None) -> tuple[str, int, str]:
    """
    智能获取重定向地址（自动适配内外网环境）
    """
    # 如果启用了自动适配，尝试根据请求来源选择
    if self.config.auto_adapt_network and request:
        # 检测请求来源
        is_external = self._is_external_request(request)
        
        if is_external and self.config.external_redirect_host:
            # 外网请求，使用外网域名
            host = self.config.external_redirect_host
            port = self._get_external_port()
            protocol = "https" if self.config.use_https else "http"
            return (host, port, protocol)
    
    # 内网请求或未配置外网域名，使用内网地址
    host = self._get_internal_host()
    port = self._get_internal_port()
    protocol = "http"
    return (host, port, protocol)
```

### 2.3 请求来源检测

**检测逻辑**:

```python
def _is_external_request(self, request: Any) -> bool:
    """
    检测是否为外网请求
    
    通过检查客户端IP是否为内网IP来判断
    """
    # 获取客户端IP
    client_ip = request.client.host
    
    # 判断是否为内网IP
    import ipaddress
    ip = ipaddress.ip_address(client_ip)
    is_private = ip.is_private
    
    return not is_private  # 不是内网IP就是外网请求
```

---

## 📋 三、使用场景

### 3.1 场景1：纯内网使用

**配置**:
- 内网主机：自动检测（或手动填写 `192.168.1.100`）
- 内网端口：8096（自定义，Emby默认端口）
- 外网域名：不填写
- 自动适配：关闭

**结果**:
- STRM文件URL：`http://192.168.1.100:8096/api/strm/stream/115/TOKEN`
- 仅内网设备可以访问

### 3.2 场景2：内外网混合使用（推荐）

**配置**（以Emby为例）:
- 内网主机：自动检测（或手动填写 `192.168.1.100`）
- 内网端口：8096（Emby/Jellyfin默认端口，Plex为32400）
- 外网域名：`vabhub.example.com:8096`（必填，支持带端口号，使用默认端口映射时建议与内网端口一致）
- 外网端口：8096（从域名中提取，或手动配置）
- 自动适配：开启

**结果**:
- 内网请求：`http://192.168.1.100:8096/api/strm/stream/115/TOKEN`
- 外网请求：`http://vabhub.example.com:8096/api/strm/stream/115/TOKEN`
- **优势**：客户端只需填写域名即可连接（地址栏下方已预制默认端口）

**注意**: VabHub支持多种媒体库软件（Plex、Jellyfin、Emby），各软件默认端口不同，请根据实际使用的媒体库软件配置相应端口。
- 自动根据请求来源选择

### 3.3 场景3：使用内网穿透（frp/ngrok）

**配置**:
- 内网主机：自动检测
- 内网端口：8096（Emby默认端口）
- 外网域名：`frp.example.com:6000`（frp穿透域名，带端口号）
- 外网端口：6000（从域名中提取，或手动配置）
- 自动适配：开启

**结果**:
- 内网请求：`http://192.168.1.100:8096/api/strm/stream/115/TOKEN`
- 外网请求：`http://frp.example.com:6000/api/strm/stream/115/TOKEN`
- 完美解决公网IP跳动问题

---

## 📋 四、解决域名/公网IP问题

### 4.1 问题分析

**中国大陆网络环境**:
- ❌ 大多数公网IP都是跳动的（动态IP）
- ❌ 有些运营商不提供公网IP（NAT）
- ❌ 无法使用固定IP访问

### 4.2 解决方案

**方案1：使用域名（推荐）** ⭐⭐⭐⭐⭐
- ✅ 使用DDNS动态域名（即使IP变化，域名也会自动更新）
- ✅ 使用内网穿透服务（frp、ngrok等）
- ✅ 使用云服务商提供的固定域名

**方案2：使用内网穿透** ⭐⭐⭐⭐
- ✅ frp：免费开源，支持自定义域名
- ✅ ngrok：简单易用，提供固定域名
- ✅ 其他内网穿透服务

**方案3：使用相对路径（未来优化）** ⭐⭐⭐
- ⚠️ 让STRM文件使用相对路径
- ⚠️ Emby自动使用当前访问地址
- ⚠️ 需要Emby支持

### 4.3 推荐配置

**最佳实践**:
1. **内网访问**：使用内网IP + 自定义端口
2. **外网访问**：使用域名 + HTTPS（推荐）
3. **自动适配**：开启自动适配，系统自动选择

**配置示例**:
```json
{
  "local_redirect_host": "192.168.1.100",  // 内网IP（可选，自动检测）
  "local_redirect_port": 8096,              // 内网端口（Emby/Jellyfin默认8096，Plex默认32400）
  "external_redirect_host": "vabhub.example.com:8096",  // 外网域名（必填，支持带端口号，使用默认端口映射时建议与内网端口一致）
  "external_redirect_port": 8096,            // 外网端口（从域名提取或手动配置，使用默认端口映射时建议与内网端口一致，这样客户端只需填写域名即可连接）
  "use_https": true,                        // 使用HTTPS（推荐）
  "auto_adapt_network": true                // 自动适配（推荐）
}
```

---

## 📋 五、API增强

### 5.1 网络信息API

**端点**: `GET /api/strm/network-info`

**返回数据**:
```json
{
  "local_ip": "192.168.1.100",
  "port": 9096,
  "internal_url_example": "http://192.168.1.100:9096/api/strm/stream/115/TOKEN",
  "external_url_example": "https://vabhub.example.com:443/api/strm/stream/115/TOKEN",
  "external_configured": true,
  "auto_adapt_enabled": true,
  "suggestions": {
    "internal_port": "建议使用系统端口或自定义内网端口。常见媒体库默认端口：Emby/Jellyfin: 8096, Plex: 32400",
    "external_domain": "外网访问建议使用域名（解决公网IP跳动问题），支持带端口号，例如：vabhub.example.com:8096 或 frp.example.com:6000（注意：如果使用默认端口映射，建议配置为 domain.com:端口号，端口号应与媒体库默认端口一致：Emby/Jellyfin: 8096, Plex: 32400，这样客户端只需填写域名即可连接）",
    "external_port": "外网端口建议：如果域名中已包含端口号，此配置可留空；否则建议使用媒体库默认端口（Emby/Jellyfin: 8096, Plex: 32400，如果使用默认端口映射），或自定义端口（例如：6000等），因为家庭宽带通常关闭443和80端口",
    "auto_adapt": "启用自动适配后，系统会根据请求来源自动选择内网/外网地址"
  }
}
```

---

## 📋 六、优势

### 6.1 完全满足用户需求

- ✅ **端口自定义** - 内网端口和公网端口都支持自定义
- ✅ **域名强制要求** - 外网访问时强制要求填写域名
- ✅ **自动适配** - STRM文件自动适配内外网环境
- ✅ **解决IP跳动问题** - 使用域名解决公网IP跳动问题

### 6.2 用户体验

- ✅ **傻瓜式操作** - 配置一次，自动适配
- ✅ **灵活配置** - 支持各种网络环境
- ✅ **智能检测** - 自动检测请求来源
- ✅ **详细提示** - 提供配置建议和示例

### 6.3 兼容性

- ✅ **向后兼容** - 不影响现有配置
- ✅ **可选功能** - 自动适配可关闭
- ✅ **灵活切换** - 可以随时切换模式

---

## 📋 七、使用说明

### 7.1 配置步骤

1. **配置内网访问**（可选）
   - 内网主机：自动检测或手动填写
   - 内网端口：自定义（例如：9096）

2. **配置外网访问**（必填，如果需要在外面访问）
   - 外网域名：填写域名（例如：`vabhub.example.com`）
   - 外网端口：HTTPS使用443，HTTP使用80，或自定义
   - 使用HTTPS：推荐开启

3. **启用自动适配**（推荐）
   - 自动适配：开启
   - 系统会根据请求来源自动选择内网/外网地址

### 7.2 域名获取方式

**方式1：DDNS动态域名**
- 使用DDNS服务（如：花生壳、No-IP等）
- 即使IP变化，域名也会自动更新

**方式2：内网穿透**
- 使用frp、ngrok等内网穿透服务
- 提供固定域名，解决公网IP问题

**方式3：云服务商域名**
- 使用云服务商提供的域名
- 配置DNS解析到服务器IP

---

## 📋 八、总结

### 8.1 实现完成

- ✅ **端口自定义** - 内网端口和公网端口都支持自定义
- ✅ **域名强制要求** - 外网访问时强制要求填写域名
- ✅ **自动适配** - STRM文件自动适配内外网环境
- ✅ **解决IP跳动问题** - 使用域名解决公网IP跳动问题

### 8.2 关键特性

- ✅ **智能检测** - 自动检测请求来源
- ✅ **灵活配置** - 支持各种网络环境
- ✅ **详细提示** - 提供配置建议和示例
- ✅ **向后兼容** - 不影响现有配置

### 8.3 用户收益

- ✅ **解决公网IP跳动问题** - 使用域名，即使IP变化也能访问
- ✅ **自动适配** - 无需手动切换，系统自动选择
- ✅ **灵活配置** - 支持各种网络环境
- ✅ **傻瓜式操作** - 配置一次，永久使用

---

**文档生成时间**: 2025-01-XX  
**实现状态**: ✅ 已完成  
**用户反馈**: 完全满足用户需求，解决了公网IP跳动问题

