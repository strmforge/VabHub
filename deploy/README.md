# VabHub 部署配置示例

本目录包含 VabHub 的各种部署配置示例文件。

## 文件说明

| 文件名 | 说明 |
|--------|------|
| `docker-compose.example.vabfeiniu.yml` | 绿联飞牛 NAS 简化部署示例 |

## 使用说明

### 绿联飞牛 NAS 部署

1. 复制配置文件：
   ```bash
   cp deploy/docker-compose.example.vabfeiniu.yml docker-compose.yml
   cp .env.docker.example .env.docker
   ```

2. 编辑 `.env.docker`，设置必要的环境变量：
   ```bash
   DB_PASSWORD=your_secure_password
   TMDB_API_KEY=your_tmdb_api_key  # 可选，但推荐配置
   ```

3. 根据实际 NAS 路径修改 `docker-compose.yml` 中的挂载目录：
   - `/vol1/1000/...` 需要改为您的实际路径

4. 启动服务：
   ```bash
   docker compose up -d
   ```

5. 访问 `http://<NAS-IP>:52180`

## 当前版本

**VabHub 0.0.2 (Testing)**

0.0.2 是针对"完全新装 NAS + 空库"场景的体验优化版本，主要改进：
- UI 基线升级
- 导航结构梳理
- 空态页面不报错
- 日志中心可用

详见 `docs/CHANGELOG.md`
