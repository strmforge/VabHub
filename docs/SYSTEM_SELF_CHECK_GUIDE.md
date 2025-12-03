# VabHub 系统自检指南

> 本文件整理了 VabHub 的健康检查和故障排查命令。  
> 详细命令清单参考 `docs/SYSTEM_HEALTH_P5_SELF_CHECK_COMMANDS.md`。

---

## 1. 快速检查（5 分钟）

### 1.1 一键检查脚本

```bash
#!/bin/bash
echo "=== VabHub 快速健康检查 ==="

# 后端服务
curl -sf http://localhost:8092/api/health >/dev/null && echo "后端服务: ✅" || echo "后端服务: ❌"

# 前端服务
curl -sf http://localhost:5173 >/dev/null && echo "前端服务: ✅" || echo "前端服务: ❌"

# 数据库
cd backend && python -c "
import asyncio, sys
sys.path.append('.')
from app.core.database import engine
async def test():
    try:
        async with engine.connect() as conn:
            print('数据库连接: ✅')
    except Exception as e:
        print(f'数据库连接: ❌ {e}')
asyncio.run(test())
" 2>/dev/null

echo "=== 检查完成 ==="
```

### 1.2 单项快速检查

```bash
# 后端健康
curl http://localhost:8092/api/health

# 系统健康详情
curl http://localhost:8092/api/system_health

# AI 总控状态
curl http://localhost:8092/api/ai/orchestrator/status

# 配置验证
cd backend && python -c "
from app.core.config import settings
print(f'SECRET_KEY: {\"已设置\" if settings.SECRET_KEY != \"change-this-to-a-random-secret-key-in-production\" else \"需要修改\"}')"
```

---

## 2. 深度检查（15 分钟）

### 2.1 后端模块检查

```bash
cd backend && python -c "
import sys
sys.path.append('.')

modules = [
    ('配置模块', 'app.core.config'),
    ('数据库', 'app.core.database'),
    ('通知服务', 'app.services.notification_service'),
    ('Telegram Bot', 'app.modules.bots.telegram_bot_client'),
    ('Runner 心跳', 'app.services.runner_heartbeat'),
    ('AI Orchestrator', 'app.core.ai_orchestrator.service'),
]

print('=== 模块导入检查 ===')
for name, module in modules:
    try:
        __import__(module)
        print(f'{name}: ✅')
    except Exception as e:
        print(f'{name}: ❌ {str(e)[:50]}')
"
```

### 2.2 数据库表检查

```bash
cd backend && python -c "
import asyncio, sys
sys.path.append('.')
from app.core.database import async_session_factory
from sqlalchemy import text

async def check():
    async with async_session_factory() as session:
        tables = ['users', 'notifications', 'subscriptions', 'media']
        for table in tables:
            try:
                result = await session.execute(text(f'SELECT COUNT(*) FROM {table}'))
                count = result.scalar()
                print(f'表 {table}: ✅ ({count} 条)')
            except:
                print(f'表 {table}: ❌ 不存在')

asyncio.run(check())
"
```

### 2.3 前端构建检查

```bash
cd frontend && pnpm run build
# 或 npm run build
```

### 2.4 Telegram Bot 检查

```bash
cd backend && python -c "
import sys
sys.path.append('.')
from app.core.config import settings

print('=== Telegram Bot 配置 ===')
print(f'Token: {\"已配置\" if settings.TELEGRAM_BOT_TOKEN else \"未配置\"} ')
print(f'启用: {settings.TELEGRAM_BOT_ENABLED}')
print(f'代理: {settings.TELEGRAM_BOT_PROXY or \"无\"}')
"
```

---

## 3. AI 专项检查

### 3.1 AI Orchestrator 状态

```bash
# API 检查
curl http://localhost:8092/api/ai/orchestrator/status

# 详细配置检查
cd backend && python -c "
import sys
sys.path.append('.')
from app.core.config import settings

print('=== AI Orchestrator 配置 ===')
print(f'启用: {settings.AI_ORCH_ENABLED}')
print(f'LLM Endpoint: {settings.AI_ORCH_LLM_ENDPOINT or \"未配置\"}')
print(f'LLM Model: {settings.AI_ORCH_LLM_MODEL or \"未配置\"}')
print(f'API Key: {\"已配置\" if settings.AI_ORCH_LLM_API_KEY else \"未配置\"}')
print(f'超时: {settings.AI_ORCH_LLM_TIMEOUT}s')
"
```

### 3.2 AI 页面功能验证

通过浏览器访问以下页面，确认正常加载：

| 页面 | URL | 验证点 |
|------|-----|--------|
| AI 实验室 | `/ai-lab` | 状态卡片显示、工具列表加载 |
| AI 订阅助手 | `/ai-subs-assistant` | 输入框可用、示例可点击 |
| AI 故障医生 | `/ai-log-doctor` | 预设场景可选择 |
| AI 整理顾问 | `/ai-cleanup-advisor` | 清理选项可配置 |
| AI 阅读助手 | `/ai-reading-assistant` | 阅读计划可生成 |

### 3.3 推荐系统检查

```bash
cd backend && python -c "
import sys
sys.path.append('.')
from app.core.config import settings

print('=== 推荐系统配置 ===')
print(f'深度学习启用: {settings.DEEP_LEARNING_ENABLED}')
print(f'GPU 启用: {settings.DEEP_LEARNING_GPU_ENABLED}')
print(f'模型类型: {settings.DEEP_LEARNING_MODEL_TYPE}')
print(f'模型路径: {settings.DEEP_LEARNING_MODEL_PATH}')
"
```

---

## 4. 常见问题排查

### 4.1 后端无法启动

**症状**：`curl http://localhost:8092/api/health` 无响应

**排查步骤**：
1. 检查端口占用：`netstat -tulpn | grep 8092`
2. 检查日志：`tail -100 logs/vabhub.log`
3. 检查数据库连接：`echo $DATABASE_URL`
4. 手动启动查看错误：`cd backend && python -m app.main`

### 4.2 AI 页面报错

**症状**：AI 页面加载失败或显示错误

**排查步骤**：
1. 检查 AI 总控状态：
   ```bash
   curl http://localhost:8092/api/ai/orchestrator/status
   ```
2. 确认 LLM 配置（未配置时使用 Dummy 模式）：
   ```bash
   echo $AI_ORCH_LLM_ENDPOINT
   echo $AI_ORCH_LLM_MODEL
   ```
3. 测试 LLM 连通性（如已配置外部 LLM）

### 4.3 Telegram Bot 无响应

**症状**：Bot 不回复消息

**排查步骤**：
1. 确认 Bot 启用：`echo $TELEGRAM_BOT_ENABLED`
2. 确认 Token 配置：`echo $TELEGRAM_BOT_TOKEN | head -c 10`
3. 检查代理设置（国内环境需要）：`echo $TELEGRAM_BOT_PROXY`
4. 查看 Bot 日志中的错误信息

### 4.4 下载器连接失败

**症状**：下载任务无法添加

**排查步骤**：
1. 在 Web UI 设置页检查下载器配置
2. 确认下载器服务运行中
3. 测试下载器 API：
   ```bash
   # qBittorrent
   curl http://localhost:8080/api/v2/app/version
   ```

### 4.5 数据库迁移问题

**症状**：启动时报表不存在

**排查步骤**：
1. 检查数据库文件存在：`ls -la vabhub.db`
2. 运行迁移：`cd backend && alembic upgrade head`
3. 检查迁移状态：`alembic current`

---

## 5. 检查清单模板

### 日常检查（每日）

- [ ] 后端服务响应正常
- [ ] 前端页面可访问
- [ ] 数据库连接正常
- [ ] 日志无严重错误
- [ ] 磁盘空间充足（`df -h`）

### 深度检查（每周）

- [ ] 所有模块导入正常
- [ ] 数据库表结构完整
- [ ] 前端构建成功
- [ ] Telegram Bot 响应正常
- [ ] AI 页面功能正常

### 部署前检查

- [ ] `SECRET_KEY` / `JWT_SECRET_KEY` 已修改
- [ ] `TMDB_API_KEY` 已配置
- [ ] 数据库迁移已完成
- [ ] 前端构建成功
- [ ] 服务端口未冲突

---

## 6. 相关文档

- **配置总览**：`docs/CONFIG_OVERVIEW.md`
- **健康检查命令详情**：`docs/SYSTEM_HEALTH_P5_SELF_CHECK_COMMANDS.md`
- **系统健康总结**：`docs/SYSTEM_HEALTH_P6_FINAL_SUMMARY.md`

---

*最后更新：2025-12-02 CONFIG-SELF-CHECK-1*
