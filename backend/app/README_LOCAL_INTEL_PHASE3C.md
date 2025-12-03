# VabHub 本地智能大脑 · Phase 3C 包（HR / 站内信策略引擎 + 统一动作流）

> 前置：已完成 Phase 1 + Phase 2 + Phase 3A + Phase 3B

本包的目标是：

- 把 **HR 状态** + **站内信事件** + **站点风控信息** 汇总成一条统一的「动作流」；
- 这些「动作」是提供给上层（重命名、移动、洗版、提醒 UI 等）的决策建议；
- 策略规则做成可扩展、可调优，而不是写死到 Watcher 里。

核心新增：

- `core/intel_local/actions.py`：统一的 LocalIntelAction/ActionType 定义；
- `core/intel_local/hr_policy.py`：基于 HR 仓库（hr_cases）评估「是否达标 / 是否危险」；
- `core/intel_local/inbox_policy.py`：把 InboxEvent → 高层动作（如“HR 扣分风险”“种子被删”）；
- `core/intel_local/engine.py`：LocalIntelEngine，协调 Watcher + Repository + Policy，输出最终动作列表；
- `INTEGRATION_NOTES_PHASE3C_FOR_CURSOR.md`：给 Cursor 的接线指引。

> 注意：本包 **不会直接改动你现有的文件**，只新增模块。
> 具体如何在 Scheduler / Service 层调用 LocalIntelEngine，请按指引由 IDE 帮你补完。
