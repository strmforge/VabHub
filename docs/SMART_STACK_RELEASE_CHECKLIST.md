# 智能子系统发布检查清单

本文档用于在发布 VabHub 第一个 Release 前，检查智能子系统的配置和功能是否正常。

## 模块概览

智能子系统包含三个核心模块：

1. **Local Intel（本地智能）**
   - HR 保护（自动将 MOVE 转为 COPY）
   - 站点防风控（访问频率监控）
   - 站内信监控
   - 智能事件时间线

2. **External Indexer（外部索引桥接）**
   - 集成外部 PT 索引引擎
   - 搜索结果补充
   - 多站点聚合搜索

3. **AI Site Adapter（站点 AI 适配）**
   - 自动生成站点适配配置
   - Cloudflare Pages LLM 服务集成
   - 站点配置缓存和频率限制

## 发布前检查项

### 1. 数据库迁移

确保已执行以下数据库迁移脚本：

- [ ] `backend/scripts/migrate_ai_site_adapter_schema.py` - AI 站点适配表结构
- [ ] Local Intel 相关表（如果项目中有独立的迁移脚本）

**检查命令**：
```bash
cd VabHub/backend
python -c "from app.models.ai_site_adapter import AISiteAdapter; print('AI 适配表结构正常')"
```

### 2. 外部服务配置

#### External Indexer

- [ ] 如果启用 `EXTERNAL_INDEXER_ENABLED=true`，需配置：
  - [ ] `EXTERNAL_INDEXER_MODULE` 指向正确的外部索引模块路径
  - [ ] 外部索引服务可访问且正常运行

#### AI Site Adapter

- [ ] 如果启用 `AI_ADAPTER_ENABLED=true`，需配置：
  - [ ] `AI_ADAPTER_ENDPOINT` 指向有效的 Cloudflare Pages 适配器端点
  - [ ] 或使用官方默认端点：`https://vabhub-cf-adapter.pages.dev/api/site-adapter`
  - [ ] 确保端点可访问（网络可达）

### 3. 环境变量配置

检查以下环境变量是否按预期设置（参考 `docs/SMART_MODES_OVERVIEW.md`）：

**纯本地模式**：
```bash
INTEL_ENABLED=true
EXTERNAL_INDEXER_ENABLED=false
AI_ADAPTER_ENABLED=false
```

**增强模式**：
```bash
INTEL_ENABLED=true
EXTERNAL_INDEXER_ENABLED=true
EXTERNAL_INDEXER_MIN_RESULTS=10
AI_ADAPTER_ENABLED=true
AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES=120
```

**实验模式**：
```bash
INTEL_ENABLED=true
EXTERNAL_INDEXER_ENABLED=true
AI_ADAPTER_ENABLED=true
```

### 4. 功能验证

#### 健康检查 API

访问健康检查接口，确认所有模块状态正常：

```bash
curl http://localhost:8092/api/smart/health
```

**预期返回示例**（增强模式）：
```json
{
  "ok": true,
  "features": {
    "local_intel": {
      "enabled": true,
      "db_ready": true
    },
    "external_indexer": {
      "enabled": true,
      "module_loaded": true,
      "runtime_ok": true
    },
    "ai_site_adapter": {
      "enabled": true,
      "endpoint_configured": true
    }
  }
}
```

**如果 `ok: false`**，检查对应模块的配置和日志。

#### 单元测试

运行智能子系统相关测试：

```bash
cd VabHub/backend
pytest tests/site_ai_adapter/ tests/ext_indexer/ -q
```

**预期结果**：所有测试通过（或跳过因项目代码问题导致的测试）

#### 功能测试

- [ ] **Local Intel**：
  - [ ] HR 保护功能：执行 MOVE 操作，检查是否自动转为 COPY
  - [ ] 站点访问频率监控：检查日志中是否有频率限制记录

- [ ] **External Indexer**（如果启用）：
  - [ ] 搜索功能：执行搜索，检查是否有外部结果补充
  - [ ] 结果去重：检查重复资源是否正确去重

- [ ] **AI Site Adapter**（如果启用）：
  - [ ] 自动分析：新增或修改站点，检查是否有 AI 生成的配置
  - [ ] 频率限制：检查是否遵守 `AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES` 限制

### 5. 前端界面检查

- [ ] **开发者模式隐藏**：
  - [ ] 默认情况下（`VITE_DEV_MODE` 未设置），Local Intel / External Indexer 菜单项不显示
  - [ ] 站点编辑对话框中，AI 适配设置区域不显示
  - [ ] 站点卡片上，AI 状态图标和调试按钮不显示

- [ ] **开发者模式显示**（可选测试）：
  - [ ] 设置 `VITE_DEV_MODE=true` 后，相关 UI 正常显示
  - [ ] Local Intel 和 External Indexer 页面顶部显示开发者提示

### 6. 日志检查

检查后端日志，确认：

- [ ] 无严重错误（ERROR 级别）
- [ ] 智能子系统相关警告（WARNING）已记录但不影响功能
- [ ] 配置加载正常（无配置缺失警告）

### 7. 性能检查

- [ ] 启动时间：后端启动时间正常（无长时间阻塞）
- [ ] 响应时间：健康检查 API 响应时间 < 100ms
- [ ] 内存占用：智能子系统相关模块内存占用正常

## 快速验证脚本

创建一个简单的验证脚本 `backend/scripts/verify_smart_stack.py`：

```python
#!/usr/bin/env python3
"""快速验证智能子系统配置"""
import asyncio
import httpx
from app.core.config import settings

async def main():
    print("=== 智能子系统配置检查 ===\n")
    
    # 检查配置
    print("1. 配置检查：")
    print(f"   Local Intel: {'✅ 启用' if settings.INTEL_ENABLED else '❌ 禁用'}")
    print(f"   External Indexer: {'✅ 启用' if settings.EXTERNAL_INDEXER_ENABLED else '❌ 禁用'}")
    print(f"   AI Site Adapter: {'✅ 启用' if settings.AI_ADAPTER_ENABLED else '❌ 禁用'}")
    
    # 检查健康状态
    print("\n2. 健康检查：")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8092/api/smart/health", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                print(f"   状态: {'✅ 正常' if data.get('ok') else '⚠️ 异常'}")
                print(f"   详情: {data}")
            else:
                print(f"   ⚠️ HTTP {resp.status_code}")
    except Exception as e:
        print(f"   ❌ 无法连接: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 发布后验证

发布后，建议用户：

1. 访问 `/api/smart/health` 检查状态
2. 根据 `docs/SMART_MODES_OVERVIEW.md` 选择合适的运行模式
3. 如有问题，查看后端日志中的智能子系统相关错误

## 常见问题

### Q: 健康检查返回 `ok: false`

**可能原因**：
- External Indexer 模块路径配置错误
- AI Site Adapter 端点不可访问
- 数据库连接问题

**解决方法**：
1. 检查环境变量配置
2. 查看后端日志中的详细错误信息
3. 参考 `docs/SMART_MODES_OVERVIEW.md` 调整配置

### Q: 测试失败

**可能原因**：
- 项目代码中缺少某些依赖（如 `SqlAlchemyTorrentIndexRepository`）
- 测试环境配置不完整

**解决方法**：
1. 检查测试输出中的具体错误信息
2. 确认测试环境已正确配置
3. 某些测试可能因项目代码问题被跳过，这是正常的

### Q: 前端看不到智能相关 UI

**可能原因**：
- `VITE_DEV_MODE` 未设置为 `true`
- 这是预期行为（普通用户界面默认隐藏）

**解决方法**：
- 如需查看调试界面，设置 `VITE_DEV_MODE=true` 并重启前端
- 普通用户无需看到这些界面，功能在后台正常运行
