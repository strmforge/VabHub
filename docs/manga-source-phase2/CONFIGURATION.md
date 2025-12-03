# 漫画源配置指南

## 概述

本文档详细说明如何配置各种外部漫画源，包括 Komga、Suwayomi、OPDS 等服务。配置完成后，VabHub 将能够搜索、浏览和追更这些源中的漫画。

## 配置方式

### 1. Web 界面配置（推荐）

访问 VabHub 管理界面：
1. 进入「漫画中心」→「外部源管理」
2. 点击「添加漫画源」
3. 填写配置信息并测试连接
4. 启用源开始使用

### 2. 环境变量配置

在 `.env` 文件中预配置漫画源：

```bash
# Komga 源配置
MANGA_SOURCE_KOMGA_URL=http://komga:8080
MANGA_SOURCE_KOMGA_USERNAME=admin
MANGA_SOURCE_KOMGA_PASSWORD=admin123

# OPDS 源配置
MANGA_SOURCE_OPDS_URL=https://example.com/opds
MANGA_SOURCE_OPDS_USERNAME=
MANGA_SOURCE_OPDS_PASSWORD=

# Suwayomi 源配置
MANGA_SOURCE_SUWAYOMI_URL=http://suwayomi:4567
MANGA_SOURCE_SUWAYOMI_API_KEY=your_api_key_here
```

## 漫画源配置详解

### Komga 配置

Komga 是自托管的漫画服务器，支持多种漫画格式。

#### 基本配置

| 字段 | 值 | 说明 |
|------|----|----- |
| 名称 | 自定义 | 如「我的 Komga」 |
| 类型 | KOMGA | 固定值 |
| 基础URL | `http://komga:8080` | Komga 服务地址 |
| 用户名 | `admin` | Komga 管理员用户名 |
| 密码 | `admin123` | Komga 管理员密码 |

#### 常见配置示例

```yaml
# Docker Compose 环境下的 Komga
name: "家庭 Komga"
type: "KOMGA"
base_url: "http://komga:8080"
username: "admin"
password: "komga_password"
is_enabled: true
```

```yaml
# 远程 Komga 服务器
name: "远程漫画库"
type: "KOMGA"
base_url: "https://manga.example.com"
username: "myuser"
password: "secure_password"
is_enabled: true
```

#### 注意事项

- 确保 Komga 版本 ≥ 1.0.0
- URL 不要包含 `/api/v1` 后缀，VabHub 会自动添加
- 如果使用 HTTPS，确保证书有效或配置跳过验证

### OPDS 配置

OPDS 是标准的数字出版物分发协议，支持多种漫画服务。

#### 基本配置

| 字段 | 值 | 说明 |
|------|----|----- |
| 名称 | 自定义 | 如「公共 OPDS」 |
| 类型 | OPDS | 固定值 |
| 基础URL | `https://example.com/opds` | OPDS 服务地址 |
| 用户名 | 可选 | OPDS 认证用户名 |
| 密码 | 可选 | OPDS 认证密码 |

#### 常见配置示例

```yaml
# 无认证的公共 OPDS
name: "公共漫画库"
type: "OPDS"
base_url: "https://comics.example.org/opds"
username: ""
password: ""
is_enabled: true
```

```yaml
# 需要认证的 OPDS
name: "私人 OPDS"
type: "OPDS"
base_url: "https://private.example.com/opds"
username: "myuser"
password: "my_password"
is_enabled: true
```

#### 注意事项

- URL 必须指向 OPDS 目录，不是具体的漫画
- 某些 OPDS 服务可能不支持搜索功能
- 确保网络可以访问 OPDS 服务

### Suwayomi 配置

Suwayomi 是 Tachiyomi 的扩展服务，支持多种漫画网站。

#### 基本配置

| 字段 | 值 | 说明 |
|------|----|----- |
| 名称 | 自定义 | 如「Suwayomi 服务」 |
| 类型 | SUWAYOMI | 固定值 |
| 基础URL | `http://suwayomi:4567` | Suwayomi 服务地址 |
| API Key | `your_api_key` | Suwayomi API 密钥 |

#### 获取 API Key

1. 访问 Suwayomi Web 界面
2. 进入「Settings」→「Security」
3. 生成或查看 API Key
4. 复制 API Key 到配置中

#### 配置示例

```yaml
# 本地 Suwayomi
name: "本地 Suwayomi"
type: "SUWAYOMI"
base_url: "http://localhost:4567"
api_key: "abcd1234efgh5678"
is_enabled: true
```

```yaml
# Docker 环境下的 Suwayomi
name: "Docker Suwayomi"
type: "SUWAYOMI"
base_url: "http://suwayomi:4567"
api_key: "your_docker_api_key"
is_enabled: true
```

#### 注意事项

- API Key 是必需的，不能为空
- 确保 Suwayomi 版本支持 API v1
- 某些源可能需要额外的配置

### Generic HTTP 配置

用于支持自定义 HTTP API 的漫画源。

#### 基本配置

| 字段 | 值 | 说明 |
|------|----|----- |
| 名称 | 自定义 | 如「自定义源」 |
| 类型 | GENERIC_HTTP | 固定值 |
| 基础URL | `https://api.example.com` | API 基础地址 |
| 额外配置 | JSON | 自定义 API 配置 |

#### 额外配置示例

```json
{
  "endpoints": {
    "search": "/search",
    "series": "/series/{id}",
    "chapters": "/series/{id}/chapters"
  },
  "headers": {
    "Authorization": "Bearer your_token",
    "User-Agent": "VabHub/1.0"
  },
  "response_format": "standard"
}
```

## 测试连接

配置完成后，务必测试连接：

1. 在配置界面点击「测试连接」
2. 检查返回的状态和可用库列表
3. 如果失败，检查：
   - 网络连接
   - 认证信息
   - API 版本兼容性
   - URL 格式

## 常见配置错误

### Komga

```bash
# ❌ 错误：包含 API 路径
base_url: "http://komga:8080/api/v1"

# ✅ 正确：只需要基础地址
base_url: "http://komga:8080"
```

### OPDS

```bash
# ❌ 错误：指向具体漫画
base_url: "https://example.com/opds/comic/123"

# ✅ 正确：指向 OPDS 目录
base_url: "https://example.com/opds"
```

### Suwayomi

```bash
# ❌ 错误：缺少 API Key
api_key: ""

# ✅ 正确：包含有效的 API Key
api_key: "abcd1234efgh5678"
```

## 网络配置

### Docker 环境

确保漫画源在 Docker 网络中可访问：

```yaml
# docker-compose.yml
services:
  vabhub:
    # ... 其他配置
    networks:
      - manga-network
      
  komga:
    image: gotson/komga
    networks:
      - manga-network
      
networks:
  manga-network:
    driver: bridge
```

### 反向代理

如果使用反向代理，确保正确配置：

```nginx
# Nginx 配置示例
location /komga/ {
    proxy_pass http://komga:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 安全配置

### HTTPS 配置

```yaml
# 使用 HTTPS 的源
name: "安全漫画源"
type: "KOMGA"
base_url: "https://secure-manga.example.com"
# 可选：配置证书验证
extra_config: |
  {
    "verify_ssl": true,
    "ssl_cert_path": "/path/to/cert.pem"
  }
```

### 认证配置

```yaml
# 使用 API Token 认证
name: "Token 认证源"
type: "OPDS"
base_url: "https://api.example.com/opds"
extra_config: |
  {
    "auth_type": "bearer",
    "token": "your_bearer_token_here"
  }
```

## 批量导入

可以通过 SQL 直接批量导入漫画源：

```sql
INSERT INTO manga_sources (name, type, base_url, username, password, is_enabled, created_at, updated_at) VALUES
('我的 Komga', 'KOMGA', 'http://komga:8080', 'admin', 'password123', true, NOW(), NOW()),
('公共 OPDS', 'OPDS', 'https://comics.example.org/opds', '', '', true, NOW(), NOW()),
('Suwayomi 服务', 'SUWAYOMI', 'http://suwayomi:4567', '', 'api_key_here', true, NOW(), NOW());
```

## 故障排除

如果配置遇到问题，请参考 [故障排除指南](./TROUBLESHOOTING.md) 中的详细解决方案。
