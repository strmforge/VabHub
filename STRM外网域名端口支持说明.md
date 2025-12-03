# STRM外网域名端口支持说明

**更新时间**: 2025-01-XX  
**功能**: 支持外网域名带端口号，解决中国大陆家庭宽带端口限制问题

---

## 📋 一、问题背景

### 1.1 中国大陆家庭宽带限制

**端口限制**:
- ❌ **443端口（HTTPS）** - 默认关闭
- ❌ **80端口（HTTP）** - 默认关闭
- ✅ **其他端口** - 可以使用（例如：6000、8080、8443等）

**影响**:
- 无法使用标准的HTTPS（443）和HTTP（80）端口
- 必须使用自定义端口进行外网访问
- 需要在域名或配置中明确指定端口号

---

## 📋 二、解决方案

### 2.1 支持域名带端口号

**配置格式**:
```
vabhub.example.com:6000
frp.example.com:8080
ngrok.example.com:8443
```

**优势**:
- ✅ 域名和端口一起配置，更直观
- ✅ 支持从域名中自动提取端口
- ✅ 兼容不带端口的域名（使用默认端口）

### 2.2 端口提取逻辑

**优先级**:
1. **配置的端口** - 如果`external_redirect_port > 0`，直接使用
2. **域名中的端口** - 如果域名包含端口号（`domain.com:6000`），自动提取
3. **默认端口** - HTTPS使用443，HTTP使用80（但家庭宽带通常不可用）

**实现**:
```python
def _get_external_port(self) -> int:
    # 1. 如果配置了端口，直接使用
    if self.config.external_redirect_port > 0:
        return self.config.external_redirect_port
    
    # 2. 从域名中提取端口号
    if ':' in host:
        port = int(host.split(':')[-1])
        return port
    
    # 3. 使用默认端口
    return 443 if use_https else 80
```

---

## 📋 三、配置示例

### 3.1 方式1：域名中带端口号（推荐）

**配置**（使用默认端口映射，推荐）:
```json
{
  "external_redirect_host": "vabhub.example.com:8096",
  "external_redirect_port": 0,  // 从域名中提取
  "use_https": false
}
```

**生成的URL**:
```
http://vabhub.example.com:8096/api/strm/stream/115/TOKEN
```

**优势**:
- Emby客户端只需填写域名 `vabhub.example.com` 即可连接
- 地址栏下方已预制8096端口，自动使用
- 端口映射简单：内网8096 -> 外网8096

### 3.2 方式2：域名和端口分开配置

**配置**（域名和端口分开配置）:
```json
{
  "external_redirect_host": "vabhub.example.com",
  "external_redirect_port": 8096,  // 手动指定（Emby默认端口）
  "use_https": false
}
```

**生成的URL**:
```
http://vabhub.example.com:8096/api/strm/stream/115/TOKEN
```

### 3.3 方式3：使用内网穿透（frp/ngrok）

**配置**:
```json
{
  "external_redirect_host": "frp.example.com:6000",
  "external_redirect_port": 0,  // 从域名中提取
  "use_https": false
}
```

**生成的URL**:
```
http://frp.example.com:6000/api/strm/stream/115/TOKEN
```

---

## 📋 四、常见端口选择

### 4.1 推荐端口

**Emby默认端口映射（推荐）**:
- **8096** - Emby默认端口（推荐）
  - 内网端口：8096
  - 外网端口：8096（端口映射）
  - 优势：Emby客户端只需填写域名即可连接（地址栏下方已预制8096端口）

**其他常用端口**:
- 6000 - 常用frp端口
- 8080 - qBittorrent默认端口（避免使用）
- 8888 - 常用管理端口
- 9090 - 常用服务端口

**HTTPS端口**:
- 8443 - 常用HTTPS替代端口
- 9443 - 常用HTTPS替代端口

### 4.2 端口选择建议

1. **避免使用常见端口** - 减少被扫描的风险
2. **使用高位端口** - 6000-65535之间的端口
3. **与内网端口一致** - 便于记忆和配置
4. **检查端口占用** - 确保端口未被其他服务占用

---

## 📋 五、配置验证

### 5.1 域名格式验证

**支持的格式**:
- ✅ `vabhub.example.com` - 不带端口（使用默认端口）
- ✅ `vabhub.example.com:6000` - 带端口号
- ✅ `frp.example.com:8080` - 内网穿透域名
- ✅ `192.168.1.100:8096` - IP地址带端口（不推荐，但支持）

**不支持的格式**:
- ❌ `vabhub.example.com:abc` - 端口号必须是数字
- ❌ `vabhub.example.com:0` - 端口号必须在1-65535之间
- ❌ `vabhub.example.com:65536` - 端口号超出范围

### 5.2 端口范围验证

**有效端口范围**: 1-65535

**常用端口**:
- 80 - HTTP（家庭宽带通常关闭）
- 443 - HTTPS（家庭宽带通常关闭）
- 6000-65535 - 自定义端口（推荐）

---

## 📋 六、使用建议

### 6.1 推荐配置

**对于中国大陆用户（使用默认端口映射，推荐）**:
```json
{
  "external_redirect_host": "vabhub.example.com:8096",
  "external_redirect_port": 0,  // 从域名中提取
  "use_https": false,  // 家庭宽带通常关闭443端口
  "auto_adapt_network": true
}
```

**优势**:
- 端口映射简单：内网8096 -> 外网8096
- Emby客户端只需填写域名即可连接
- 地址栏下方已预制8096端口，自动使用

**对于有公网IP的用户**:
```json
{
  "external_redirect_host": "vabhub.example.com:8443",
  "external_redirect_port": 0,
  "use_https": true,  // 使用8443端口支持HTTPS
  "auto_adapt_network": true
}
```

### 6.2 配置检查清单

- [ ] 外网域名已填写（必填）
- [ ] 域名中包含端口号（推荐，例如：`domain.com:6000`）
- [ ] 端口号在有效范围内（1-65535）
- [ ] 端口未被其他服务占用
- [ ] 路由器已配置端口映射
- [ ] 防火墙已开放端口
- [ ] 自动适配已启用（推荐）

---

## 📋 七、故障排查

### 7.1 常见问题

**问题1：外网无法访问**
- 检查域名是否正确
- 检查端口是否在域名中或配置中
- 检查路由器端口映射
- 检查防火墙设置

**问题2：端口冲突**
- 检查端口是否被其他服务占用
- 更换为其他端口
- 使用`netstat -an | grep 6000`检查端口占用

**问题3：域名解析失败**
- 检查DNS设置
- 检查域名是否正确
- 检查网络连接

---

## 📋 八、总结

### 8.1 关键特性

- ✅ **支持域名带端口号** - 例如：`vabhub.example.com:6000`
- ✅ **自动提取端口** - 从域名中自动提取端口号
- ✅ **灵活配置** - 支持域名中带端口或单独配置端口
- ✅ **解决端口限制** - 完美解决家庭宽带443/80端口关闭问题

### 8.2 推荐配置

**最佳实践**:
1. 使用域名带端口号的格式（例如：`vabhub.example.com:6000`）
2. 使用自定义端口（6000-65535）
3. 启用自动适配功能
4. 配置路由器端口映射

---

**文档生成时间**: 2025-01-XX  
**适用场景**: 中国大陆家庭宽带用户，解决443/80端口关闭问题

