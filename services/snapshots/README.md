# VabHub Snapshots

静态快照服务，提供离线/低带宽环境支持。

## 文件说明

- `alias-latest.json` / `alias-latest.json.gz` - 别名快照
- `index-latest.json` / `index-latest.json.json.gz` - 索引快照
- `rules.json` - 规则包

## 部署

### Cloudflare Pages部署

1. 创建GitHub仓库
2. 上传快照文件
3. 在Cloudflare Pages中连接仓库
4. 设置自定义域名：`snap.hbnetwork.top`
5. 配置长期缓存

### Cloudflare R2部署

1. 创建R2存储桶
2. 上传快照文件
3. 配置公共访问
4. 绑定自定义域名
5. 配置缓存规则

## 更新机制

快照文件应定期更新：
- 每小时生成一次快照
- 使用CI/CD自动推送
- 版本管理（可选）

## 客户端使用

客户端启动时：
1. 优先加载快照文件
2. 检查版本
3. 根据在线状态增量更新

