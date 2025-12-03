# docs 维护指北（给 AI / IDE / 人类文档作者）

> 本文件是给**所有会修改 VabHub 文档的角色**看的（包括 ChatGPT、Windsurf、SWE-1.5、以及人类维护者）。  
> 目的是：让"系统总览 / AI 总览 / 深度分析 / 前端路由图"等文档长期保持一致、可靠，不再各写各的。

---

## 0. 先说结论：写任务书前，必须先看哪些文档？

无论你是 AI 还是人类，只要要为 VabHub 写「任务书 / Phase 说明 / 大改动设计」，请按顺序阅读：

1. `docs/VABHUB_SYSTEM_OVERVIEW.md`  
   - 全局系统总览（模块地图、完成度、最近里程碑、给新 AI/IDE 的使用说明）。
2. `docs/INDEX.md`  
   - 文档索引，了解完整文档结构。
3. 如果任务跟 **未来 AI 总控 / Orchestrator / AI 助手** 有关系，再看：  
   - `docs/FUTURE_AI_OVERVIEW.md` 
4. 如果任务需要深入某个模块（例如 Local Intel / 站点管理 / 漫画中心 / 音乐推荐等），按需查：  
   - `docs/TRUE_FILE_BY_FILE_DEEP_ANALYSIS.md` 对应章节
5. 如果任务涉及前端路由 / 页面结构：  
   - 查看或生成：`docs/FRONTEND_MAP.md`（如存在）

> 简单记忆：  
> **先看 SYSTEM_OVERVIEW → 再看 INDEX → 最后按需查其他文档。**

---

## 1. 文档分层结构（谁才是"单一事实来源"？）

### 1.1 系统总览：VABHUB_SYSTEM_OVERVIEW.md（SSoT #1）

- 定位：全项目的**单一事实来源**（Single Source of Truth）。
- 内容：
  - 项目定位 & 目标用户；
  - 核心模块地图（状态：`[DONE]/[WIP]/[PLANNED]/[LEGACY]`）；
  - 工作流 & RSSHub & 订阅体系整体位置；
  - 未来 AI 总控在整个系统中的"那一格"；
  - 最近里程碑（按时间排序）；
  - 给"新窗口 AI / IDE"的阅读顺序建议。
- 约定：
  - **任何涉及系统结构 / 模块状态的任务完成后，必须更新这里。**
  - 这是所有任务书引用系统现状时的底线来源。

### 1.2 未来 AI 总览：FUTURE_AI_OVERVIEW.md（SSoT #2）

- 定位：**未来 AI 总控 / AI Orchestrator 子系统的专用总览**。
- 内容：
  - 外部大模型 Endpoint + 本地 AI 器官 + Orchestrator 编排层 架构；
  - 5 种模式：`GENERIC / SUBS_ADVISOR / DIAGNOSE / CLEANUP_ADVISOR / READING_ASSISTANT`；
  - 每个模式对应的：
    - 后端文件（schema/service/api）
    - 前端页面（如 `/ai-lab`、`/ai-subs-assistant` 等）
  - 安全边界：站点 AI 适配通道专用、不做云端 PT 目录聚合、读写分层、危险操作双保险。
- 约定：
  - 任何**新增 / 调整 Orchestrator 模式 / AI 助手页面**的任务，必须同步更新这里；
  - 不允许在别的文档里单独定义一套"平行 AI 架构"。

### 1.3 前端路由图：FRONTEND_MAP.md

- 定位：前端页面 / 路由 / 导航结构的清单。
- 内容：
  - 每个主要页面的路由路径、组件名、所属模块；
  - 左侧导航结构、隐藏入口说明；
  - AI 相关页面集中标注。
- 约定：
  - 只要任务改动了前端路由 / 导航结构，就要更新这里；
  - 用于给新 IDE / 设计任务快速理解"页面在哪里"。

### 1.4 文档索引：INDEX.md

- 定位：文档导航的总入口
- 内容：
  - 按受众（普通用户、高级用户、开发者）分类的文档链接；
  - 核心概念和部署指南的快速链接；
  - 常见问题和联系方式。
- 约定：
  - 所有新用户和开发者都应从这里开始；
  - 文档结构变更时必须更新。

### 1.5 按受众分类的文档

#### 1.5.1 用户文档（docs/user/）
- 定位：给普通用户看的简化文档
- 核心文件：
  - GETTING_STARTED.md - 快速上手
  - DEPLOY_WITH_DOCKER.md - Docker 部署指南
  - README.md - 用户入门指南
- 约定：
  - 保持简洁明了，避免过多技术细节；
  - 重点突出安装和基本使用；
  - 与 CONFIG_OVERVIEW.md 保持一致。

#### 1.5.2 高级用户/运维文档（docs/admin/）
- 定位：给高级用户和运维人员的详细配置文档
- 核心文件：
  - CONFIG_OVERVIEW.md - 完整配置指南
  - SITE_INTEL_OVERVIEW.md - 站点智能功能
  - SUBS_RULES_OVERVIEW.md - 订阅规则配置
  - READING_STACK_OVERVIEW.md - 阅读栈功能
  - BACKUP_AND_RESTORE.md - 备份与恢复
  - KNOWN_LIMITATIONS.md - 已知限制
- 约定：
  - 提供详细的配置说明和最佳实践；
  - 包含常见问题的解决方案；
  - 定期更新，反映最新配置选项。

#### 1.5.3 开发者文档（docs/dev/）
- 定位：给开发者和项目维护者的技术文档
- 内容：
  - Phase 任务书
  - 实现笔记
  - 实验记录
  - 插件开发指南
  - API 文档
  - 汇总性质的 LEGACY 实施笔记
- 约定：
  - 包含技术实现细节；
  - 提供开发环境搭建和调试指南；
  - 记录架构决策和设计思路；
  - 从 REPO-DOCS-PUBLIC-1 开始，大量“阶段总结 / 测试报告 / 完成说明”类文档不再随公共仓库发布，只保留少量总览文档和指南文档；开发过程中产生的细碎总结应保存在本地或 gitignore 的路径中。

### 1.5.4 根目录文档规则

- **禁止在仓库根目录新增任何 Markdown 文档**
- **根目录允许保留的 Markdown 文件**：
  - README.md
  - CHANGELOG.md
- **所有新的说明 / 总结 / 任务书类文档**：
  - 要么进入 docs/ 对应子目录（user/admin/dev/internal）
  - 要么只放在本地 local-notes/，不加入 Git
- **约束说明**：自 REPO-DOCS-ROOT-MD-TRIM-1 任务完成起，严格执行此规则，防止根目录再次堆积开发文档。

### 1.5.5 脚本文件规范

- **禁止在仓库根目录新增任何脚本文件**（.bat, .ps1, .py 等）
- **所有脚本必须放入 scripts/ 及其子目录**：
  - `scripts/windows/`：Windows 开发/调试脚本
  - `scripts/python/`：Python 测试/辅助脚本
  - `scripts/tools/`：仓库维护/运维工具脚本
- **文档优先推荐 Docker 部署**：
  - 能通过 Docker 部署完成的场景，文档优先描述 Docker 流程
  - 不再指导用户执行根目录脚本
- **约束说明**：自 REPO-SCRIPTS-ORGANIZE-1 任务完成起，严格执行此规则，防止根目录再次堆积脚本文件。

#### 1.5.6 内部文档（docs/internal/）
- 定位：仅供项目维护者使用的内部文档
- 内容：
  - 项目计划
  - 会议记录
  - 临时笔记
  - 实验结果
- 约定：
  - 不对外暴露；
  - 包含内部决策和未公开的信息。

### 1.6 系统健康与检查

#### 1.6.1 自检指南：SYSTEM_SELF_CHECK_GUIDE.md
- 定位：系统健康检查和故障排查的**命令清单**。
- 内容：
  - 5 分钟基础检查 / 15 分钟深度检查命令；
  - AI 专项检查；
  - 常见问题排查路径。
- 约定：
  - 健康检查命令或排查流程有调整时更新；
  - 引用 `SYSTEM_HEALTH_P5_SELF_CHECK_COMMANDS.md` 中的详细命令。

#### 1.6.2 预发布检查笔记：PRE_RELEASE_CHECK_NOTES.md
- 定位：记录真实环境检查过程和结果
- 内容：
  - 版本统一检查；
  - 仓库清理检查；
  - Docker 部署验证；
  - 文档更新检查；
  - 安全检查。
- 约定：
  - 每次预发布前执行检查并更新；
  - 记录实际环境中的检查结果和遇到的问题；
  - 包含具体的命令和输出示例。

#### 1.6.3 已知限制：KNOWN_LIMITATIONS.md
- 定位：对用户期望管理的总入口
- 内容：
  - 功能层面限制；
  - 性能与规模限制；
  - 部署与环境限制；
  - Docker 首跑场景下的已知限制；
  - AI 与外部服务限制。
- 约定：
  - 如实记录当前版本的已知问题和限制；
  - 为用户提供清晰的预期管理；
  - 定期更新，反映最新状态。

---

## 2. 常见改动场景 → 必须更新哪些文档？

> 下面是最常见的几类任务，方便 AI / IDE 快速判断需要改哪几份 docs。

### 2.1 改后端功能模块（非 AI）

例如：Local Intel、下载管理、站点管理、漫画中心、音乐中心等。

必须更新：

- `VABHUB_SYSTEM_OVERVIEW.md` 
  - 对应模块在 §3「核心模块地图」中的状态 / 要点；
  - 如是一个阶段性里程碑，追加到 §7「最近里程碑」。
- `TRUE_FILE_BY_FILE_DEEP_ANALYSIS.md` 
  - 若改动较大，更新对应模块的小节要点（或加 NOTE 标记该分析偏旧）。

### 2.2 改未来 AI 总控 / Orchestrator / AI 助手

例如：新增一个 AI 模式，给现有模式增加新工具，扩展 AI 订阅助手、故障医生、整理顾问、阅读助手等。

必须更新：

- `FUTURE_AI_OVERVIEW.md` 
  - §2 架构总览（如有新模式 / 新器官）；
  - §4 模式详解（新增/修改的模式）；
  - §5 已落地场景（新增页面或增强说明）。
- `VABHUB_SYSTEM_OVERVIEW.md` 
  - 在「核心模块地图」中更新 AI 总控 / 相关模块状态；
  - 在「最近里程碑」中追加本次任务。
- 对应 Notes 文件：
  - 例如 `FUTURE_AI_XYZ_NOTES.md` 增补设计细节 / 示例。

### 2.3 改前端页面 / 路由 / 导航

例如：给 AI 助手加入口，调整导航分组，重命名某个主页面。

必须更新：

- `VABHUB_SYSTEM_OVERVIEW.md` 
  - §5 「前端结构」中的页面 / 导航说明；
- `FRONTEND_MAP.md`（如存在）
  - 增删改页面路径、分组、入口位置。

### 2.4 仅修 Bug / 小范围重构

如果任务只是修内部逻辑 / 类型标注 / 小 bug，而不影响：

- 模块职责，
- 对外行为（API 形态不变），
- 模块完成度状态（仍然是 DONE/WIP），

则可以不改文档。  
**但如果任务书本身在标题中强调"阶段完成 / 功能升级"，仍然建议在里程碑中留一条简短记录。**

---

## 3. PZ. 文档更新要求（任务书尾部模板）

> 所有 VabHub 任务书，必须带一个类似下面的固定小节。  
> 可以按实际任务微调，但不要删掉"必须更新哪几份文档"的要求。

```markdown
PZ. 文档更新要求（必须执行）

1. 更新 `docs/VABHUB_SYSTEM_OVERVIEW.md`：
   - 在 **3. 核心模块地图** 中，调整本次涉及模块的状态标记，并简要补充新能力要点。
   - 在 **7. 最近里程碑** 末尾追加 1 条描述本次任务的记录（不超过 2 行）。

2. 如本任务涉及 AI Orchestrator / AI 助手：
   - 请同步更新 `docs/FUTURE_AI_OVERVIEW.md`：
     - 在相应模式小节中补充新能力或调整状态；
     - 如新增模式/页面，写明对应的后端文件和前端路由。

3. 如本任务涉及前端路由 / 页面结构改动：
   - 更新或生成 `docs/FRONTEND_MAP.md`：
     - 标明本次新增/修改的页面路径、组件名、所属分组。

4. 如本任务重构了某个模块的核心实现：
   - 在 `docs/TRUE_FILE_BY_FILE_DEEP_ANALYSIS.md` 中对应模块的小节补充一段 NOTE：
     - 简要说明本次重构对原分析的影响（例如"已更新至 2025-12-01 版本实现"）。
```

---

## 4. 写文档时的风格和约束

### 高层文档不写大段代码

在 `SYSTEM_OVERVIEW` / `FUTURE_AI_OVERVIEW` 里只放路径和一句话说明，不放大段代码片段。

### 控制长度

- `VABHUB_SYSTEM_OVERVIEW.md` 建议保持在 ~4000–6000 字符；
- `FUTURE_AI_OVERVIEW.md` 建议控制在 ~4000–7000 字符；
- 超出时优先把旧里程碑 / 历史方案移动到 `VABHUB_HISTORY.md` 或 `FUTURE_AI_HISTORY.md`。

### 状态标记统一

只用这四个：`[DONE]` / `[WIP]` / `[PLANNED]` / `[LEGACY]`；

避免自创标签（如 `[BROKEN]`、`[EXPERIMENTAL]`），可以在描述文本里说清楚。

### 命名一致

模块名、模式名、任务名以代码和 README 为准，例如：

- AI Orchestrator（不要改叫 AI Engine）；
- FUTURE-AI-ORCHESTRATOR-1（不要随意改缩写）。