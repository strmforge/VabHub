# 本地智能大脑 · Phase 3C 说明（策略引擎 & 动作流）

## 已有能力（Phase 1–3B 回顾）

- 有 HR 状态模型：`HRTorrentState` / `HRStatus` / `TorrentLife`；
- 有本地仓库：`HRCasesRepository` / `SiteGuardRepository` / `InboxCursorRepository`（Phase 3A）；
- 有 Watcher：`HRWatcher` / `InboxWatcher`，能：
  - 调用 HTTP 客户端（Phase 3B）；
  - 解析 HR 页面 / 站内信页面；
  - 产出内部 `HRRow` / `InboxMessage` / `InboxEvent`。

## Phase 3C 要解决的问题

之前的数据流大致是：

> 站点 HTML → 解析 → HRRow / InboxEvent → （局部更新状态）

但还缺少：

- 「到底应该干什么」的统一判断：
  - 这个 HR 是否已经安全？
  - 这个 HR 是否已经踩雷？
  - 某个站点是否应该减速 / 暂停扫描？
  - 某种站内信（删除 / HR 扣分）是否需要通知用户？
- 一个统一的动作表达：供上层「订阅规则引擎 / UI / 通知系统」使用。

## Phase 3C 的核心思路

1. 定义统一动作：`LocalIntelAction` / `LocalIntelActionType`
2. 从 HR 仓库推理动作（hr_policy）：
   - 例：`HR_ACTIVE` → 「继续观察」
   - 例：`HR_OK` → 「可解除本地 HR 标记」
   - 例：`HR_RISK` → 「发出警告、禁止移动源文件」
3. 从站内信事件推理动作（inbox_policy）：
   - 例：`InboxEventType.HR_PENALTY` → 「记录一次事故 + 提醒用户」
   - 例：`InboxEventType.TORRENT_DELETED` → 「标记本地任务为“远端已删种”」
4. 用 `LocalIntelEngine` 把上述动作合并，并暴露统一入口：
   - `await engine.refresh_site(site_id)`
   - 返回 `List[LocalIntelAction]` 供上层消费。

## 可配置 / 可扩展

Phase 3C 的策略实现大部分是「默认温和策略」，保守不乱动你的数据。
你可以后续：

- 在 hr_policy/inbox_policy 里增加自己的规则；
- 或者在 UI 中给一些高级用户「策略开关」。

