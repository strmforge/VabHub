# Plugin Hub 使用指南

## 概述

**Plugin Hub** 是 VabHub 的官方插件索引中心，托管在 [vabhub-plugins](https://github.com/strmforge/vabhub-plugins) 仓库。通过 Plugin Hub，您可以：

- 浏览官方和社区插件
- 查看插件功能说明和安装状态
- 获取插件安装指南
- 检查本地插件是否有更新

## 配置

### 环境变量

在 `.env` 文件中可以配置以下选项：

```bash
# Plugin Hub 索引 JSON 地址
# 默认为官方仓库
APP_PLUGIN_HUB_URL=https://raw.githubusercontent.com/strmforge/vabhub-plugins/main/plugins.json

# 插件索引缓存时间（秒），默认 30 分钟
APP_PLUGIN_HUB_CACHE_TTL=1800
```

### 使用自定义插件仓库

如果您想使用自己的插件索引，只需：

1. Fork 官方 `vabhub-plugins` 仓库或创建新仓库
2. 按照 `plugins.json` 格式添加您的插件信息
3. 修改 `APP_PLUGIN_HUB_URL` 指向您的 `plugins.json` raw 地址

```bash
# 示例：使用自己的仓库
APP_PLUGIN_HUB_URL=https://raw.githubusercontent.com/your-org/your-plugins/main/plugins.json
```

## 在 Web UI 中使用

### 访问 Plugin Hub

1. 以管理员身份登录 VabHub
2. 进入「开发者」→「插件开发中心」页面
3. 点击「Plugin Hub」选项卡

### 功能说明

#### 插件列表

Plugin Hub Tab 显示远程索引中的所有插件，每个插件卡片包含：

- **名称和描述**：插件的基本信息
- **标签**：如 `official`、`example` 等
- **功能图标**：
  - 🔍 搜索扩展
  - 🤖 Bot 命令
  - 📊 UI 面板
  - ⚙️ Workflow
- **安装状态**：
  - 🟢 已安装
  - 🟠 可更新（有新版本）
  - ⚪ 未安装

#### 刷新索引

点击右上角的「刷新」按钮可强制从远程重新获取插件列表。

系统会缓存索引数据（默认 30 分钟），以减少对远程服务器的请求。

#### 安装指南

点击插件卡片上的「安装指南」按钮，会弹出详细的安装说明，包括：

1. 进入 VabHub 根目录
2. 创建 `plugins` 目录
3. 使用 `git clone` 克隆插件仓库
4. 重启 VabHub 或执行「重新扫描插件」

## 安装插件

### 手动安装步骤

```bash
# 1. 进入 VabHub 根目录
cd /path/to/vabhub

# 2. 确保 plugins 目录存在
mkdir -p plugins

# 3. 克隆插件仓库
git clone https://github.com/xxx/plugin-name plugins/plugin-name

# 4. 重启 VabHub 或在 Web UI 执行「重新扫描插件」
```

### 更新插件

```bash
cd plugins/plugin-name
git pull origin main
```

然后在 Web UI 中执行「重新扫描插件」。

## 与本地插件的关系

- Plugin Hub 只是一个**索引目录**，本身不包含插件代码
- 实际的插件代码存储在各自的 Git 仓库中
- 安装后的插件存放在本地的 `plugins/` 目录
- Plugin Hub 会自动对比本地已安装插件的版本，标记可更新的插件

## plugins.json 格式

```json
{
  "hub_name": "VabHub Official Plugin Hub",
  "hub_version": 1,
  "plugins": [
    {
      "id": "plugin-id",
      "name": "插件名称",
      "description": "插件描述",
      "author": "作者",
      "tags": ["tag1", "tag2"],
      "homepage": "https://...",
      "repo": "https://github.com/...",
      "download_url": "https://...",
      "version": "1.0.0",
      "min_core_version": "0.9.0",
      "supports": {
        "search": true,
        "bot_commands": false,
        "ui_panels": true,
        "workflows": false
      },
      "panels": ["home_dashboard"],
      "enabled_by_default": false
    }
  ]
}
```

## API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/dev/plugin_hub` | 获取插件索引（含本地状态） |
| GET | `/api/dev/plugin_hub/{id}` | 获取单个插件详情 |
| GET | `/api/dev/plugin_hub/{id}/readme` | 获取插件 README |
| GET | `/api/dev/plugin_hub/{id}/install_guide` | 获取安装指南 |

所有端点需要管理员权限。

## 一键安装 / 更新 / 卸载（PLUGIN-HUB-2）

从 PLUGIN-HUB-2 版本开始，支持在 Web UI 中直接进行插件的安装、更新和卸载操作。

### 前置条件

1. **服务器已安装 Git**：确保 `git` 命令在 PATH 中可用
2. **配置正确**：确保以下环境变量已配置

```bash
# 插件目录
APP_PLUGINS_DIR=plugins

# 允许的 Git 主机（安全限制）
APP_PLUGIN_GIT_ALLOWED_HOSTS=github.com,gitee.com

# 默认分支（可选）
APP_PLUGIN_GIT_DEFAULT_BRANCH=main
```

### Git 主机白名单

为了安全起见，系统只允许从配置的主机列表克隆代码。默认允许：
- `github.com`
- `gitee.com`

如需添加其他主机，修改 `APP_PLUGIN_GIT_ALLOWED_HOSTS` 配置（逗号分隔）。

### 使用方法

1. 登录 VabHub Web UI（需要管理员权限）
2. 进入「开发者」→「插件开发中心」→「Plugin Hub」Tab
3. 根据插件状态选择操作：

| 状态 | 可用操作 |
|------|----------|
| 未安装 | **安装**：点击后弹出确认对话框，确认后自动 `git clone` |
| 已安装（无更新） | **卸载**：删除插件目录和数据库记录 |
| 已安装（有更新） | **更新**：执行 `git pull` 拉取最新代码<br>**卸载**：删除插件 |

### 操作流程

#### 安装插件

1. 在「Plugin Hub」Tab 找到目标插件
2. 点击「安装」按钮
3. 在确认对话框中查看仓库地址
4. 点击「确认安装」
5. 等待安装完成，插件会自动注册到系统

#### 更新插件

1. 找到标记为「可更新」的插件
2. 点击「更新」按钮
3. 确认后系统会执行 `git pull`
4. 插件版本信息会自动更新

#### 卸载插件

1. 点击已安装插件的「卸载」按钮
2. 阅读警告信息（目录将被删除）
3. 确认卸载
4. 插件目录和数据库记录都会被删除

### API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/dev/plugin_hub/{id}/install` | 一键安装插件 |
| POST | `/api/dev/plugin_hub/{id}/update` | 一键更新插件 |
| POST | `/api/dev/plugin_hub/{id}/uninstall` | 卸载插件 |

### 插件来源追踪

系统会为每个插件记录来源信息：

| 字段 | 说明 |
|------|------|
| `source` | 来源类型：`local`（手动）/ `plugin_hub`（一键安装） |
| `hub_id` | 对应 Plugin Hub 中的插件 ID |
| `repo_url` | Git 仓库地址 |
| `installed_ref` | 当前安装的 commit hash |
| `auto_update_enabled` | 是否允许一键更新 |

## 官方插件 vs 社区插件（PLUGIN-HUB-3）

Plugin Hub 中的插件分为两类：

### 官方插件（channel=official）

- 仓库存放在 `strmforge` 等官方组织
- 由 VabHub 官方维护
- 版本兼容性和基础安全性在合理范围内经过检查
- 若发现严重问题，官方会在 Plugin Hub 中下架或标记有风险

### 社区插件（channel=community）

- 由第三方开发者维护
- 代码托管在第三方仓库
- **官方不参与开发与维护，仅提供展示与安装能力**
- 使用社区插件需自行承担风险

### 频道自动判定

系统会根据以下规则自动判定插件频道：

1. 如果 `plugins.json` 中显式指定了 `channel` 字段，直接使用
2. 否则根据 `repo_url` 中的组织名判断：
   - 组织在 `APP_PLUGIN_OFFICIAL_ORGS` 列表中 → `official`
   - 否则 → `community`

### 社区插件配置开关

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `APP_PLUGIN_COMMUNITY_VISIBLE` | `true` | 是否在 Plugin Hub 中展示社区插件 |
| `APP_PLUGIN_COMMUNITY_INSTALL_ENABLED` | `true` | 是否允许一键安装/更新社区插件 |
| `APP_PLUGIN_OFFICIAL_ORGS` | `strmforge` | 官方组织列表（逗号分隔） |

**推荐策略：**

- **生产环境 / 给他人使用**：建议关闭 `APP_PLUGIN_COMMUNITY_INSTALL_ENABLED`
- **内网 / 个人测试**：可以全部打开

### 前端 UI 行为

- 默认只显示官方插件，社区插件需要手动打开「社区插件」开关
- 社区插件卡片带有橙色 `[社区]` 标签
- 安装/更新社区插件时，确认弹窗会显示额外的风险提示
- 如果 `APP_PLUGIN_COMMUNITY_INSTALL_ENABLED=false`：
  - 社区插件的「安装/更新」按钮会被禁用
  - 用户只能通过「安装指南」手动部署

## 未来扩展

以下功能计划在后续版本中实现：

- **多索引源支持**：支持配置多个 Plugin Hub URL
- **插件签名验证**：增强安全性
- **自动更新检查**：定期检查并通知可用更新

## 故障排除

### 无法加载 Plugin Hub

1. 检查 `APP_PLUGIN_HUB_URL` 配置是否正确
2. 确认网络可以访问 GitHub（或您的自定义仓库）
3. 如果使用代理，检查 `PROXY_HOST` 配置
4. 查看后端日志中的 `[plugin-hub]` 相关信息

### 插件状态不正确

1. 确保本地插件的 `plugin.json` 中 `id` 字段与 Hub 中一致
2. 执行「重新扫描插件」刷新本地插件状态
3. 点击「刷新」按钮重新获取远程索引

### 安装失败：仓库地址不在白名单

错误信息：`仓库地址不在白名单中`

解决方法：
1. 检查 `APP_PLUGIN_GIT_ALLOWED_HOSTS` 配置
2. 确保插件仓库的主机在白名单中
3. 如需添加新主机，修改配置并重启服务

### 安装失败：Git 未安装

错误信息：`Git is not installed or not in PATH`

解决方法：
1. 安装 Git：`apt install git` 或 `yum install git`
2. 确保 `git` 命令在系统 PATH 中
3. 重启 VabHub 服务

### 更新失败：插件来源不正确

错误信息：`Cannot update plugin with source 'local'`

解决方法：
- 只有通过 Plugin Hub 安装的插件（`source=plugin_hub`）才能一键更新
- 手动安装的插件（`source=local`）需要通过命令行 `git pull` 更新

### 卸载失败：权限不足

解决方法：
1. 确保运行 VabHub 的用户对 `plugins/` 目录有写权限
2. 检查目录权限：`ls -la plugins/`
3. 修复权限：`chmod -R 755 plugins/`
