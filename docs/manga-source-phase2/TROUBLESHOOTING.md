# 故障排除指南

## 概述

本文档帮助您解决使用 Manga Source 功能时遇到的常见问题。问题按用户可见的症状分类，便于快速定位解决方案。

## 🔍 搜索相关问题

### 聚合搜索返回空结果

**症状**：开启聚合搜索后，所有源都没有返回任何结果。

**可能原因**：
1. 漫画源未正确配置或未启用
2. 网络连接问题
3. 搜索关键词过于具体
4. 源服务不可用

**解决步骤**：

1. **检查源状态**
   ```bash
   # 检查数据库中的源配置
   SELECT name, type, is_enabled FROM manga_sources;
   ```

2. **测试单个源**
   - 关闭聚合搜索
   - 逐个测试每个源的搜索功能
   - 找出有问题的源

3. **检查网络连接**
   ```bash
   # 测试源服务连通性
   curl -I http://komga:8080/api/v1/series
   curl -I https://example.com/opds
   ```

4. **调整搜索策略**
   - 使用更通用的关键词
   - 尝试不同语言
   - 检查拼写

### 单个源搜索失败

**症状**：特定源无法搜索，但其他源正常。

**可能原因**：
1. 源配置错误
2. 认证失败
3. API 版本不兼容
4. 源服务维护中

**解决步骤**：

1. **验证配置**
   - 检查 URL 格式（不要包含 API 路径）
   - 验证用户名和密码
   - 确认 API Key 有效

2. **测试 API 连接**
   ```bash
   # Komga 测试
   curl -u "admin:password" http://komga:8080/api/v1/series?search=测试
   
   # OPDS 测试
   curl -u "user:pass" https://example.com/opds/search?q=test
   
   # Suwayomi 测试
   curl -H "Authorization: Bearer API_KEY" http://suwayomi:4567/api/v1/manga/search?q=test
   ```

3. **检查源服务状态**
   - 访问源的 Web 界面
   - 查看源服务的日志
   - 确认服务版本兼容性

### 搜索结果不准确

**症状**：搜索结果与预期不符，或缺少相关结果。

**解决方法**：
1. 尝试不同的搜索关键词
2. 使用漫画的别名搜索
3. 检查源的搜索功能限制
4. 考虑使用源过滤功能

## ⭐ 追更相关问题

### "追这部"按钮无响应

**症状**：点击「追这部」按钮后没有任何反应。

**可能原因**：
1. 未登录或权限不足
2. 漫画已在追更列表中
3. 数据库连接问题
4. 前端 JavaScript 错误

**解决步骤**：

1. **检查登录状态**
   - 确认已正确登录
   - 检查用户权限

2. **检查是否已追更**
   ```bash
   # 查看当前用户的追更记录
   SELECT s.title, s.source_id, s.remote_series_id 
   FROM user_manga_follow f 
   JOIN manga_series_local s ON f.series_id = s.id 
   WHERE f.user_id = YOUR_USER_ID;
   ```

3. **检查浏览器控制台**
   - 打开开发者工具
   - 查看 Console 中的错误信息
   - 检查 Network 中的 API 请求

4. **检查后端日志**
   ```bash
   # 查看应用日志
   docker logs vabhub_container | grep "follow"
   ```

### 远程章节不更新

**症状**：追更后长时间没有收到更新通知，但原站有新章节。

**可能原因**：
1. 追更同步任务未运行
2. 源服务 API 变化
3. 网络连接问题
4. 同步频率设置过低

**解决步骤**：

1. **检查同步任务状态**
   ```bash
   # 检查 Runner 任务
   SELECT name, last_run_at, status FROM task_runners;
   ```

2. **手动触发同步**
   ```bash
   # 手动运行追更同步
   python -m app.runners.manga_follow_sync
   ```

3. **检查 chapter 映射**
   ```bash
   # 查看远程章节 ID
   SELECT last_remote_chapter_id, unread_chapter_count 
   FROM user_manga_follow 
   WHERE user_id = YOUR_USER_ID;
   ```

4. **验证源 API**
   - 手动调用源的章节列表 API
   - 检查章节 ID 格式是否变化
   - 确认 API 认证有效

### 追更记录丢失

**症状**：之前追更的漫画在列表中消失。

**可能原因**：
1. 数据库问题
2. 用户数据清理
3. 漫画被删除
4. 权限变更

**解决步骤**：

1. **检查数据库**
   ```bash
   # 查看所有追更记录
   SELECT COUNT(*) FROM user_manga_follow WHERE user_id = YOUR_USER_ID;
   
   # 查看最近删除的记录
   SELECT * FROM user_manga_follow_audit 
   WHERE user_id = YOUR_USER_ID 
   ORDER BY changed_at DESC LIMIT 10;
   ```

2. **检查漫画状态**
   ```bash
   # 查看漫画是否被删除
   SELECT * FROM manga_series_local 
   WHERE id IN (SELECT series_id FROM user_manga_follow WHERE user_id = YOUR_USER_ID);
   ```

## 🔔 通知相关问题

### 收不到更新通知

**症状**：漫画有更新但没有收到 Telegram 通知。

**可能原因**：
1. Telegram Bot 未配置
2. 通知被禁用
3. 网络问题
4. Bot Token 过期

**解决步骤**：

1. **检查 Telegram 配置**
   ```bash
   # 检查环境变量
   echo $TELEGRAM_BOT_TOKEN
   echo $TELEGRAM_CHAT_ID
   ```

2. **测试 Bot 连接**
   ```bash
   # 测试 Telegram Bot
   curl "https://api.telegram.org/botYOUR_TOKEN/getMe"
   ```

3. **检查通知设置**
   - 进入设置 → 通知设置
   - 确认漫画更新通知已启用
   - 检查用户通知偏好

4. **查看通知日志**
   ```bash
   # 查看通知发送日志
   docker logs vabhub_container | grep "notification"
   ```

### 通知内容错误

**症状**：收到的通知信息不正确或不完整。

**可能原因**：
1. 漫画信息缺失
2. 字符编码问题
3. 模板错误

**解决步骤**：

1. **检查漫画信息**
   ```bash
   # 查看漫画基本信息
   SELECT title, cover_url, description 
   FROM manga_series_local 
   WHERE id = SERIES_ID;
   ```

2. **检查通知模板**
   - 确认通知模板文件完整
   - 检查多语言支持
   - 验证字符编码

### 通知按钮不工作

**症状**：通知中的「在原站打开」按钮无法正常跳转。

**解决方法**：
1. 检查外部 URL 构建功能
2. 验证源配置中的基础 URL
3. 确认远程系列 ID 正确

## 🔗 源连接问题

### 源连接超时

**症状**：测试连接时显示超时错误。

**可能原因**：
1. 网络延迟
2. 源服务负载高
3. 防火墙阻拦
4. DNS 解析问题

**解决步骤**：

1. **检查网络连通性**
   ```bash
   # 测试基础连接
   ping komga.example.com
   telnet komga.example.com 8080
   ```

2. **调整超时设置**
   ```yaml
   # 在源配置中添加
   extra_config: |
     {
       "timeout": 30,
       "retries": 3
     }
   ```

3. **检查防火墙设置**
   - 确认端口开放
   - 检查防火墙日志
   - 验证 Docker 网络配置

### HTTPS 证书问题

**症状**：HTTPS 源连接失败，提示证书错误。

**解决方法**：

1. **跳过证书验证（仅测试环境）**
   ```yaml
   extra_config: |
     {
       "verify_ssl": false
     }
   ```

2. **配置自定义证书**
   ```yaml
   extra_config: |
     {
       "verify_ssl": true,
       "ssl_cert_path": "/path/to/ca.pem"
     }
   ```

3. **更新证书**
   - 联系源管理员更新证书
   - 使用有效的自签名证书

## 🗄️ 数据库问题

### 迁移失败

**症状**：数据库迁移时出现错误。

**解决步骤**：

1. **检查迁移状态**
   ```bash
   # 查看迁移记录
   SELECT * FROM migration_history ORDER BY executed_at DESC;
   ```

2. **手动执行迁移**
   ```bash
   # 手动运行特定迁移
   python -m app.core.migrations.run manga_remote_follow
   ```

3. **回滚迁移**
   ```bash
   # 如果迁移失败，回滚到上一个状态
   python -m app.core.migrations.rollback manga_remote_follow
   ```

### 数据不一致

**症状**：追更数据与实际状态不符。

**解决步骤**：

1. **检查数据完整性**
   ```bash
   # 检查孤立的追更记录
   SELECT f.* FROM user_manga_follow f 
   LEFT JOIN manga_series_local s ON f.series_id = s.id 
   WHERE s.id IS NULL;
   ```

2. **修复数据**
   ```sql
   -- 删除孤立记录
   DELETE FROM user_manga_follow 
   WHERE series_id NOT IN (SELECT id FROM manga_series_local);
   ```

3. **重建索引**
   ```bash
   # 重建数据库索引
   python -m app.db.maintenance rebuild_indexes
   ```

## 🐳 Docker 环境问题

### 容器间网络不通

**症状**：VabHub 无法访问其他容器中的漫画源。

**解决步骤**：

1. **检查网络配置**
   ```bash
   # 查看网络列表
   docker network ls
   
   # 查看网络详情
   docker network inspect vabhub_default
   ```

2. **确保在同一网络**
   ```yaml
   # docker-compose.yml
   services:
     vabhub:
       networks:
         - manga-network
     komga:
       networks:
         - manga-network
   ```

3. **测试容器间连接**
   ```bash
   # 从 VabHub 容器测试
   docker exec vabhub_container ping komga
   docker exec vabhub_container curl http://komga:8080
   ```

### 权限问题

**症状**：容器无法访问文件或数据库。

**解决方法**：
1. 检查文件权限设置
2. 确认用户 ID 映射
3. 验证卷挂载配置

## 🔧 调试工具

### 启用调试模式

```bash
# 设置环境变量
export DEBUG=true
export LOG_LEVEL=DEBUG

# 或在 .env 文件中
DEBUG=true
LOG_LEVEL=DEBUG
```

### 查看详细日志

```bash
# 查看应用日志
docker logs -f vabhub_container

# 查看特定模块日志
docker logs vabhub_container | grep "manga_source"
docker logs vabhub_container | grep "follow_sync"
```

### API 调试

```bash
# 测试聚合搜索 API
curl -v "http://localhost:8000/api/manga/remote/aggregated-search?q=test"

# 测试源列表 API
curl -v "http://localhost:8000/api/manga/remote/sources"

# 测试追更 API
curl -v -X POST "http://localhost:8000/api/manga/remote/follow" \
  -H "Content-Type: application/json" \
  -d '{"source_id": 1, "remote_series_id": "test"}'
```

## 📞 获取帮助

如果以上方法都无法解决您的问题：

1. **收集信息**：
   - 错误消息截图
   - 系统日志
   - 配置信息（隐藏敏感数据）

2. **提交 Issue**：
   - 访问项目 GitHub 页面
   - 详细描述问题现象
   - 提供复现步骤

3. **社区支持**：
   - 加入用户群组
   - 查看已有讨论
   - 寻求技术支持

## 📋 常用检查清单

### 新用户设置检查

- [ ] 已正确配置至少一个漫画源
- [ ] 源测试连接成功
- [ ] 已启用通知功能
- [ ] 搜索功能正常
- [ ] 追更功能可用

### 故障排查检查

- [ ] 检查网络连接
- [ ] 验证源服务状态
- [ ] 查看应用日志
- [ ] 测试 API 连接
- [ ] 确认权限设置

### 性能优化检查

- [ ] 源数量合理（不超过 10 个）
- [ ] 定期清理无用追更
- [ ] 监控数据库大小
- [ ] 检查同步频率设置

更多技术支持请参考项目文档或联系开发团队。
