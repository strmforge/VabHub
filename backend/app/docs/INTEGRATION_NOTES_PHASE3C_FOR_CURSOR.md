# 集成指引 · Local Intel Phase 3C（给 Cursor 看）

目标：把 HR 状态 + 站内信事件 → LocalIntelAction 统一动作流，供上层使用。

## 1. 放置路径建议

建议解压到：

- backend/app/core/intel_local/actions.py
- backend/app/core/intel_local/hr_policy.py
- backend/app/core/intel_local/inbox_policy.py
- backend/app/core/intel_local/engine.py
- backend/app/docs/LOCAL_INTEL_PHASE3C_NOTES.md
- backend/app/README_LOCAL_INTEL_PHASE3C.md

如工程结构不同，请保持 import 前缀与现有 intel_local 一致。

## 2. 修正 import 路径

engine.py 中：

```python
from .watchers import HRWatcher, InboxWatcher
```

需要根据当前项目真实位置修正，例如：

```python
from .hr_watcher import HRWatcher
from .inbox_watcher import InboxWatcher
```

同理，hr_policy/inbox_policy 内若有 models/events 导入路径不一致，请以实际工程为准微调。

## 3. 要求的 Watcher API 约定

为配合 LocalIntelEngine，需要：

- HRWatcher:
  - 方法：`async def refresh_site(self, site: str, profile: IntelSiteProfile) -> None`
  - 内部负责：抓取 HR 页面 → 解析 → 更新 HRCasesRepository
- InboxWatcher:
  - 方法：`async def refresh_site(self, site: str, profile: IntelSiteProfile) -> list[InboxEvent]`
  - 内部负责：抓取站内信 → 解析 → 更新 InboxCursorRepository → 返回本次新产生的 InboxEvent 列表

如果现有实现不同，请增加包装方法保持上述签名。

## 4. 在应用启动阶段构造 LocalIntelEngine

伪代码：

```python
from app.core.intel_local.engine import LocalIntelEngine, LocalIntelEngineConfig
from app.core.intel_local.repo import (
    SqlAlchemyHRCasesRepository,
    SqlAlchemySiteGuardRepository,
    SqlAlchemyInboxCursorRepository,
)
from app.core.intel_local.hr_watcher import HRWatcher
from app.core.intel_local.inbox_watcher import InboxWatcher

def build_local_intel_engine() -> LocalIntelEngine:
    # 根据项目实际情况注入 Session / Engine
    hr_repo = SqlAlchemyHRCasesRepository(...)
    site_guard_repo = SqlAlchemySiteGuardRepository(...)
    inbox_cursor_repo = SqlAlchemyInboxCursorRepository(...)

    hr_watcher = HRWatcher(hr_repo=hr_repo, site_guard_repo=site_guard_repo, ...)
    inbox_watcher = InboxWatcher(inbox_cursor_repo=inbox_cursor_repo, site_guard_repo=site_guard_repo, ...)

    return LocalIntelEngine(
        hr_repo=hr_repo,
        site_guard_repo=site_guard_repo,
        inbox_cursor_repo=inbox_cursor_repo,
        hr_watcher=hr_watcher,
        inbox_watcher=inbox_watcher,
        config=LocalIntelEngineConfig(),
    )
```

建议挂载到 FastAPI 的 `app.state.local_intel_engine` 或一个全局 service 容器中。

## 5. 暴露一个管理入口用于调试

可以先提供一个管理 API：

```python
@router.post("/admin/local-intel/refresh/{site_id}")
async def admin_refresh_local_intel(site_id: str):
    engine = get_local_intel_engine()
    profile = get_intel_site_profile(site_id)
    actions = await engine.refresh_site(site_id, profile)
    return {"site": site_id, "actions": [a.__dict__ for a in actions]}
```

用于：

- 验证 HR / 站内信解析是否正确；
- 检查 LocalIntelAction 的结构是否符合预期。

## 6. 接入上层业务（可分两步）

1. **先只可视化，不自动动作**
   - 把 LocalIntelAction 持久化到一张 `intel_actions` 表 或 直接写日志；
   - 前端增加一个「智能提醒中心」，展示：
     - HR_MARK_RISK / HR_MARK_SAFE
     - TORRENT_DELETED_REMOTE / TORRENT_HR_PENALTY
     - SITE_THROTTLED 等。
2. **再逐步自动化**
   - HR_MARK_RISK → 在重命名/移动时阻止删除源文件；
   - TORRENT_DELETED_REMOTE → 标记订阅为「需换源」；
   - SITE_THROTTLED → 调整该站点抓取频率（结合 SiteGuard 参数）。

## 7. 配置调优

- hr_policy.HRPolicyConfig / inbox_policy.InboxPolicyConfig 可挂到配置文件：
  - 用户可设置“提前多少小时预警 HR”；
  - 是否把删种视为 error 等。
- actions.merge_actions 目前只对 HR_RECORD_PROGRESS 做简单去重，如有需要可在后续扩展。

---

总体思路：

- Phase 3C 只新增「统一动作层」，尽量不碰你已跑通的解析/仓库逻辑；
- 让 `LocalIntelEngine.refresh_site` 成为唯一入口，方便上层调用和后续重构。
