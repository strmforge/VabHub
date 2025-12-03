# P5 系统健康自检命令清单

## 概述
本文档提供了完整的 VabHub 系统健康检查命令清单，用于快速诊断系统状态和问题排查。

## 🚀 快速检查（5分钟内完成）

### 基础服务状态
```bash
# 检查后端服务
curl -f http://localhost:8092/api/health || echo "后端服务异常"

# 检查前端服务
curl -f http://localhost:5173 || echo "前端服务异常"

# 检查数据库连接
cd backend && python -c "
import asyncio
import sys
sys.path.append('.')
from app.core.database import engine
async def test():
    try:
        async with engine.connect() as conn:
            print('数据库连接正常')
    except Exception as e:
        print(f'数据库连接失败: {e}')
asyncio.run(test())
"
```

### 配置检查
```bash
# 检查关键配置
cd backend && python -c "
import sys
sys.path.append('.')
from app.core.config import settings
print('=== 关键配置检查 ===')
print(f'DATABASE_URL: {settings.DATABASE_URL[:20]}...')
print(f'TELEGRAM_BOT_ENABLED: {settings.TELEGRAM_BOT_ENABLED}')
print(f'SECRET_KEY: {\"已设置\" if settings.SECRET_KEY != \"change-this-to-a-random-secret-key-in-production\" else \"需要修改\"}')
"
```

## 🔍 详细检查（15分钟内完成）

### 1. 后端服务检查

#### API 健康检查
```bash
# 基础健康检查
curl http://localhost:8092/api/health

# 系统健康检查
curl http://localhost:8092/api/system_health

# 智能健康检查
curl http://localhost:8092/api/smart_health
```

#### 模块导入检查
```bash
cd backend && python -c "
import sys
sys.path.append('.')

modules_to_check = [
    ('通知服务', 'app.services.notification_service'),
    ('Telegram Bot', 'app.modules.bots.telegram_bot_client'),
    ('Runner 心跳', 'app.services.runner_heartbeat'),
    ('数据库', 'app.core.database'),
    ('配置', 'app.core.config'),
]

print('=== 模块导入检查 ===')
for name, module in modules_to_check:
    try:
        __import__(module)
        print(f'{name}: ✅ 正常')
    except Exception as e:
        print(f'{name}: ❌ {e}')
"
```

#### 数据库检查
```bash
cd backend && python -c "
import asyncio
import sys
sys.path.append('.')
from app.core.database import async_session_factory
from sqlalchemy import text

async def check_db():
    try:
        async with async_session_factory() as session:
            # 检查连接
            result = await session.execute(text('SELECT 1'))
            print('数据库连接: ✅ 正常')
            
            # 检查关键表
            tables = ['users', 'notifications', 'subscriptions']
            for table in tables:
                try:
                    result = await session.execute(text(f'SELECT COUNT(*) FROM {table}'))
                    count = result.scalar()
                    print(f'表 {table}: ✅ 存在 ({count} 条记录)')
                except Exception:
                    print(f'表 {table}: ❌ 不存在或无法访问')
                    
    except Exception as e:
        print(f'数据库检查失败: {e}')

asyncio.run(check_db())
"
```

### 2. 前端服务检查

#### 构建检查
```bash
cd frontend && npm run build
echo "前端构建: $(if [ $? -eq 0 ]; then echo '✅ 成功'; else echo '❌ 失败'; fi)"
```

#### 类型检查
```bash
cd frontend && npx vue-tsc --noEmit
echo "TypeScript 检查: $(if [ $? -eq 0 ]; then echo '✅ 通过'; else echo '❌ 存在错误'; fi)"
```

#### 依赖检查
```bash
cd frontend && npm audit --audit-level high
echo "依赖安全检查: $(if [ $? -eq 0 ]; then echo '✅ 无高危漏洞'; else echo '⚠️ 存在高危漏洞'; fi)"
```

### 3. Telegram Bot 检查

#### 配置检查
```bash
cd backend && python -c "
import sys
sys.path.append('.')
from app.core.config import settings

print('=== Telegram Bot 配置 ===')
print(f'Token: {\"已配置\" if settings.TELEGRAM_BOT_TOKEN else \"未配置\"}')
print(f'启用状态: {settings.TELEGRAM_BOT_ENABLED}')
print(f'代理: {\"已配置\" if settings.TELEGRAM_BOT_PROXY else \"未配置\"}')
print(f'白名单: {settings.TELEGRAM_BOT_ALLOWED_USERS or \"未设置\"}')
"
```

#### Bot 连接测试
```bash
cd backend && python -c "
import asyncio
import sys
sys.path.append('.')
try:
    from app.modules.bots.telegram_bot_client import get_telegram_bot_client
    client = get_telegram_bot_client()
    if client:
        print('Bot 客户端: ✅ 初始化成功')
    else:
        print('Bot 客户端: ❌ 初始化失败')
except Exception as e:
    print(f'Bot 客户端测试失败: {e}')
"
```

### 4. Runner 系统检查

#### Runner 列表
```bash
cd backend && python -c "
import os
import sys
sys.path.append('.')

runners_dir = 'app/runners'
if os.path.exists(runners_dir):
    runners = [f for f in os.listdir(runners_dir) if f.endswith('.py') and f != '__init__.py']
    print('=== 可用 Runner 列表 ===')
    for runner in sorted(runners):
        print(f'  - {runner}')
else:
    print('Runner 目录不存在')
"
```

#### 心跳服务检查
```bash
cd backend && python -c "
import sys
sys.path.append('.')
try:
    from app.services.runner_heartbeat import runner_context
    print('Runner 心跳服务: ✅ 可用')
except Exception as e:
    print(f'Runner 心跳服务: ❌ {e}')
"
```

### 5. 通知系统检查

#### 通知服务检查
```bash
cd backend && python -c "
import sys
sys.path.append('.')
try:
    from app.services.notification_service import NotificationService
    print('通知服务: ✅ 可用')
except Exception as e:
    print(f'通知服务: ❌ {e}')
"
```

#### 通知渠道检查
```bash
cd backend && python -c "
import sys
sys.path.append('.')
try:
    from app.modules.notification.channels.telegram import TelegramChannel
    config = {'bot_token': None, 'chat_id': None}
    channel = TelegramChannel(config)
    valid, msg = channel.validate_config()
    print(f'Telegram 通知渠道: {\"✅\" if valid else \"⚠️\"} {msg or \"正常\"}')
except Exception as e:
    print(f'Telegram 通知渠道: ❌ {e}')
"
```

## 🔧 问题诊断命令

### 常见问题排查

#### 1. 数据库连接问题
```bash
# 检查数据库文件权限
ls -la ./vabhub.db 2>/dev/null || echo "SQLite 文件不存在"

# 检查 PostgreSQL 连接
cd backend && python -c "
import asyncio
import sys
sys.path.append('.')
from app.core.config import settings
from sqlalchemy import create_engine
try:
    engine = create_engine(settings.DATABASE_URL.replace('sqlite+aiosqlite://', 'sqlite://'))
    with engine.connect() as conn:
        print('数据库连接正常')
except Exception as e:
    print(f'数据库连接失败: {e}')
"
```

#### 2. 端口冲突检查
```bash
# 检查端口占用
netstat -tulpn | grep :8092 || echo "8092 端口未被占用"
netstat -tulpn | grep :5173 || echo "5173 端口未被占用"
```

#### 3. 权限问题检查
```bash
# 检查数据目录权限
ls -la ./data/
ls -la ./tmp/

# 检查日志目录权限
ls -la ./logs/
```

#### 4. 依赖问题检查
```bash
# 后端依赖检查
cd backend && pip list | grep -E "(fastapi|sqlalchemy|loguru)"

# 前端依赖检查
cd frontend && npm list --depth=0 | grep -E "(vue|vite|vuetify)"
```

## 📊 性能检查

### 系统资源检查
```bash
# CPU 和内存使用
top -bn1 | head -5

# 磁盘空间
df -h | grep -E "(/$|/data|/tmp)"

# 内存详情
free -h
```

### 应用性能检查
```bash
# 后端启动时间检查
cd backend && python -c "
import time
import sys
sys.path.append('.')
start = time.time()
from app.core.config import settings
from app.core.database import engine
end = time.time()
print(f'后端模块加载时间: {end - start:.2f}秒')
"
```

## 🚨 应急恢复命令

### 快速重启服务
```bash
# 重启后端服务
pkill -f "python.*app.main" || true
cd backend && python -m app.main &

# 重启前端服务
cd frontend && npm run dev &
```

### 清理缓存
```bash
# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 清理前端缓存
cd frontend && rm -rf node_modules/.cache dist/ || true
```

### 重置数据库（谨慎使用）
```bash
# 仅开发环境：重置 SQLite 数据库
# cd backend && rm -f ./vabhub.db && python -c "
# import asyncio
# import sys
# sys.path.append('.')
# from app.core.database import engine
# from app.models import Base
# async def init():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
# asyncio.run(init())
# "
```

## 📋 检查清单模板

### 日常检查（每日）
- [ ] 后端服务响应正常
- [ ] 前端页面可访问
- [ ] 数据库连接正常
- [ ] 关键日志无错误
- [ ] 磁盘空间充足

### 深度检查（每周）
- [ ] 所有模块导入正常
- [ ] 数据库表结构完整
- [ ] 依赖包无安全漏洞
- [ ] 系统资源使用正常
- [ ] 备份文件可恢复

### 部署前检查
- [ ] 代码构建成功
- [ ] 所有测试通过
- [ ] 配置文件正确
- [ ] 数据库迁移完成
- [ ] 监控告警配置

## 📞 故障报告模板

当发现问题时，请按以下格式报告：

```
**问题描述：**
简要描述遇到的问题

**检查结果：**
- 后端状态: ✅/❌
- 前端状态: ✅/❌  
- 数据库: ✅/❌
- 其他组件: ✅/❌

**错误信息：**
粘贴相关错误日志

**环境信息：**
- 操作系统:
- Python 版本:
- Node.js 版本:
- 部署方式:

**复现步骤：**
1. 步骤一
2. 步骤二
3. 步骤三
```

## 🔄 自动化脚本

创建快速检查脚本 `quick_health_check.sh`：

```bash
#!/bin/bash
echo "=== VabHub 快速健康检查 ==="

# 检查后端
if curl -f http://localhost:8092/api/health >/dev/null 2>&1; then
    echo "后端服务: ✅"
else
    echo "后端服务: ❌"
fi

# 检查前端
if curl -f http://localhost:5173 >/dev/null 2>&1; then
    echo "前端服务: ✅"
else
    echo "前端服务: ❌"
fi

# 检查配置
cd backend && python -c "
from app.core.config import settings
print(f'Telegram Bot: {\"✅\" if settings.TELEGRAM_BOT_ENABLED else \"⚠️\"}')
" 2>/dev/null || echo "配置检查: ❌"

echo "=== 检查完成 ==="
```

使用方法：
```bash
chmod +x quick_health_check.sh
./quick_health_check.sh
```

---

**注意：** 
- 所有命令都应在项目根目录下执行
- 生产环境执行前请确认影响范围
- 建议在维护窗口期间执行深度检查
- 定期更新此清单以保持同步
