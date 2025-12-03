# HR-POLICY-2 – HR 案件系统 + 安全模式中心 v1 设计文档

## 一、现状巡检总结

### 1.1 现有架构分析

#### 核心组件
- **HRWatcher**: HR页面监控器，负责抓取和解析HR页面数据
- **InboxWatcher**: 站内信监控器，解析HR扣分、种子删除、站点风控通知
- **HRTorrentState**: HR状态数据模型（内存缓存）
- **LocalIntelEngine.is_move_safe**: 现有的安全检查核心逻辑
- **HRCasesRepository**: Protocol接口，便于替换实现

#### 数据流图
```
HR页面 → HRWatcher → hr_state.py → _HR_STATE_CACHE → LocalIntelEngine.is_move_safe
站内信 → InboxWatcher → hr_state.py → TorrentIndex/SiteGuard
                    ↘ HRCasesRepository (Protocol接口)
```

### 1.2 关键发现

#### ✅ 架构优势
1. **良好的分离设计**: HRWatcher和InboxWatcher职责清晰
2. **Protocol接口**: HRCasesRepository便于替换实现
3. **明确的迁移路径**: hr_state.py中有TODO注释指向DB+缓存架构
4. **完整的事件链路**: 从监控到通知的基础设施已存在

#### ⚠️ 风险点
1. **内存缓存依赖**: `_HR_STATE_CACHE`被多处直接访问
2. **状态管理分散**: HR状态更新逻辑分布在多个模块
3. **数据同步风险**: InboxWatcher直接修改hr_state，可能导致不一致

### 1.3 改造策略

采用"渐进式整合"策略：
- **保持现有功能**: HRTorrentState继续工作，不破坏现有监控
- **添加统一层**: HrCase作为facade层，提供统一接口
- **逐步迁移**: 通过feature flag控制新功能启用
- **双写同步**: 过渡期同时更新内存缓存和DB

## 二、HrCase 统一模型设计

### 2.1 数据模型

```python
@dataclass
class HrCase(BaseModel):
    """HR案件统一模型 - 整合HR状态和生命周期信息"""
    
    # 基础标识
    id: Optional[int] = None
    site_id: int
    site_key: str  # 站点标识，如 "hdhome"
    torrent_id: str
    infohash: Optional[str] = None
    
    # 状态枚举
    status: Literal["ACTIVE", "SAFE", "VIOLATED", "UNKNOWN", "NONE"] = "NONE"
    life_status: Literal["ALIVE", "DELETED"] = "ALIVE"
    
    # HR要求与进度
    requirement_ratio: Optional[float] = None
    requirement_hours: Optional[float] = None
    seeded_hours: float = 0.0
    current_ratio: Optional[float] = None
    
    # 时间线
    entered_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    penalized_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # 元数据
    last_email_notice_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None  # 原始站点数据
```

### 2.2 仓库接口设计

```python
class HrCasesRepository(Protocol):
    """HR案件统一仓库接口"""
    
    async def get_by_site_and_torrent(self, site_key: str, torrent_id: str) -> Optional[HrCase]:
        """获取指定站点的HR案件"""
        ...
    
    async def upsert_from_hr_page(self, site_key: str, torrent_id: str, 
                                 required_hours: float, seeded_hours: float, 
                                 deadline: Optional[datetime]) -> HrCase:
        """从HR页面数据更新案件"""
        ...
    
    async def mark_safe(self, site_key: str, torrent_id: str, 
                       reason: str = "hr_finished") -> HrCase:
        """标记为安全状态"""
        ...
    
    async def mark_penalized(self, site_key: str, torrent_id: str) -> HrCase:
        """标记为HR违规"""
        ...
    
    async def mark_deleted(self, site_key: str, torrent_id: str) -> HrCase:
        """标记为种子被删除"""
        ...
    
    async def list_active_for_site(self, site_key: str) -> List[HrCase]:
        """列出站点的活跃HR案件"""
        ...
    
    async def list_by_status(self, status: str, limit: int = 100) -> List[HrCase]:
        """按状态列出案件"""
        ...
```

### 2.3 数据迁移策略

#### Phase 1: 双写期（P1-P2）
- 保持 `_HR_STATE_CACHE` 继续工作
- 新增 `HrCasesRepository` 实现，同时写入DB和内存缓存
- 现有功能通过内存缓存继续工作

#### Phase 2: 读取迁移（P3-P4）
- 逐步将读取逻辑迁移到 `HrCasesRepository`
- 保持双写，确保数据一致性

#### Phase 3: 完全迁移（P5-P6）
- 移除内存缓存依赖
- 完全基于DB+新缓存架构

## 三、SafetyPolicyEngine 安全策略引擎

### 3.1 核心类型定义

```python
@dataclass
class SafetyContext(BaseModel):
    """安全策略评估上下文"""
    
    # 操作信息
    action: Literal["download", "delete", "move", "upload_cleanup", "generate_strm"]
    site_key: Optional[str] = None
    torrent_id: Optional[str] = None
    infohash: Optional[str] = None
    
    # 文件路径信息
    path_from: Optional[str] = None
    path_to: Optional[str] = None
    changes_seeding_path: bool = False
    
    # 触发来源
    trigger: Literal["system_runner", "user_web", "user_telegram", "mobile_upload"]
    
    # 关联信息
    subscription_id: Optional[int] = None
    hr_case: Optional[HrCase] = None

@dataclass
class SafetyDecision(BaseModel):
    """安全策略决策结果"""
    
    decision: Literal["ALLOW", "DENY", "REQUIRE_CONFIRM"]
    reason_code: str
    message: str
    suggested_alternative: Optional[str] = None
    hr_status_snapshot: Optional[Dict[str, Any]] = None
```

### 3.2 安全配置模型

```python
@dataclass
class GlobalSafetySettings(BaseModel):
    """全局安全设置"""
    
    mode: Literal["SAFE", "BALANCED", "AGGRESSIVE"] = "BALANCED"
    min_keep_hours: float = 24.0
    min_ratio_for_delete: float = 0.8
    prefer_copy_on_move_for_hr: bool = True
    enable_hr_protection: bool = True

@dataclass
class SiteSafetySettings(BaseModel):
    """站点级安全设置"""
    
    site_key: str
    hr_sensitivity: Literal["normal", "sensitive", "highly_sensitive"] = "normal"
    min_keep_ratio: Optional[float] = None
    min_keep_time_hours: Optional[float] = None

@dataclass
class SubscriptionSafetySettings(BaseModel):
    """订阅级安全设置"""
    
    allow_hr: bool = False
    allow_h3h5: bool = False
    strict_free_only: bool = False
```

### 3.3 策略引擎核心逻辑

```python
class SafetyPolicyEngine:
    """安全策略引擎"""
    
    def __init__(self, 
                 hr_repo: HrCasesRepository,
                 safety_settings_service: SafetySettingsService):
        self._hr_repo = hr_repo
        self._settings_service = safety_settings_service
    
    async def evaluate(self, ctx: SafetyContext) -> SafetyDecision:
        """评估安全策略"""
        
        # 1. 获取相关配置
        global_settings = await self._settings_service.get_global()
        site_settings = await self._settings_service.get_site(ctx.site_key) if ctx.site_key else None
        sub_settings = await self._settings_service.get_subscription(ctx.subscription_id) if ctx.subscription_id else None
        
        # 2. 获取HR状态
        hr_case = ctx.hr_case
        if ctx.site_key and ctx.torrent_id and not hr_case:
            hr_case = await self._hr_repo.get_by_site_and_torrent(ctx.site_key, ctx.torrent_id)
        
        # 3. 按操作类型评估
        if ctx.action == "download":
            return await self._evaluate_download(ctx, hr_case, global_settings, site_settings, sub_settings)
        elif ctx.action == "delete":
            return await self._evaluate_delete(ctx, hr_case, global_settings, site_settings, sub_settings)
        elif ctx.action == "move":
            return await self._evaluate_move(ctx, hr_case, global_settings, site_settings, sub_settings)
        elif ctx.action == "upload_cleanup":
            return await self._evaluate_upload_cleanup(ctx, hr_case, global_settings, site_settings, sub_settings)
        else:
            return SafetyDecision(decision="ALLOW", reason_code="unknown_action", message="未知操作类型")
    
    async def _evaluate_download(self, ctx: SafetyContext, hr_case: Optional[HrCase],
                                global_settings: GlobalSafetySettings,
                                site_settings: Optional[SiteSafetySettings],
                                sub_settings: Optional[SubscriptionSafetySettings]) -> SafetyDecision:
        """评估下载操作"""
        
        # HR保护检查
        if global_settings.enable_hr_protection and hr_case and hr_case.status == "ACTIVE":
            return SafetyDecision(
                decision="DENY",
                reason_code="hr_active_download",
                message="该种子正处于HR期，禁止下载",
                hr_status_snapshot={"status": hr_case.status, "deadline": hr_case.deadline}
            )
        
        # 订阅设置检查
        if sub_settings and not sub_settings.allow_hr:
            if hr_case and hr_case.status in ["ACTIVE", "VIOLATED"]:
                return SafetyDecision(
                    decision="REQUIRE_CONFIRM",
                    reason_code="subscription_no_hr",
                    message="订阅设置不允许HR种子，是否确认下载？"
                )
        
        # 站点敏感度检查
        if site_settings and site_settings.hr_sensitivity == "highly_sensitive":
            if hr_case and hr_case.status != "NONE":
                return SafetyDecision(
                    decision="REQUIRE_CONFIRM",
                    reason_code="site_highly_sensitive",
                    message="站点为高敏感站点，建议谨慎下载HR种子"
                )
        
        return SafetyDecision(decision="ALLOW", reason_code="safe", message="允许下载")
    
    async def _evaluate_delete(self, ctx: SafetyContext, hr_case: Optional[HrCase],
                              global_settings: GlobalSafetySettings,
                              site_settings: Optional[SiteSafetySettings],
                              sub_settings: Optional[SubscriptionSafetySettings]) -> SafetyDecision:
        """评估删除操作"""
        
        # HR期内禁止删除
        if hr_case and hr_case.status == "ACTIVE":
            return SafetyDecision(
                decision="DENY",
                reason_code="hr_active_delete",
                message="该种子正处于HR期，禁止删除源文件",
                hr_status_snapshot={"status": hr_case.status, "seeded_hours": hr_case.seeded_hours}
            )
        
        # 非HR种子的最低保种要求检查
        if not hr_case or hr_case.status in ["NONE", "SAFE"]:
            min_ratio = site_settings.min_keep_ratio if site_settings else global_settings.min_ratio_for_delete
            if hr_case and hr_case.current_ratio and hr_case.current_ratio < min_ratio:
                return SafetyDecision(
                    decision="REQUIRE_CONFIRM",
                    reason_code="ratio_too_low",
                    message=f"当前分享率{hr_case.current_ratio:.2f}低于最低要求{min_ratio:.2f}，是否确认删除？"
                )
        
        return SafetyDecision(decision="ALLOW", reason_code="safe", message="允许删除")
    
    async def _evaluate_move(self, ctx: SafetyContext, hr_case: Optional[HrCase],
                            global_settings: GlobalSafetySettings,
                            site_settings: Optional[SiteSafetySettings],
                            sub_settings: Optional[SubscriptionSafetySettings]) -> SafetyDecision:
        """评估移动操作"""
        
        # HR期内影响做种路径的移动需要特别处理
        if hr_case and hr_case.status == "ACTIVE" and ctx.changes_seeding_path:
            if global_settings.prefer_copy_on_move_for_hr:
                return SafetyDecision(
                    decision="REQUIRE_CONFIRM",
                    reason_code="hr_move_suggest_copy",
                    message="HR期内移动会影响做种，建议使用复制而非移动",
                    suggested_alternative="复制文件到目标位置"
                )
            else:
                return SafetyDecision(
                    decision="DENY",
                    reason_code="hr_move_deny",
                    message="HR期内禁止移动影响做种路径的文件",
                    hr_status_snapshot={"status": hr_case.status, "deadline": hr_case.deadline}
                )
        
        # HR安全的种子按常规规则处理
        if hr_case and hr_case.status == "SAFE":
            return SafetyDecision(decision="ALLOW", reason_code="hr_safe", message="HR已完成，允许移动")
        
        return SafetyDecision(decision="ALLOW", reason_code="safe", message="允许移动")
    
    async def _evaluate_upload_cleanup(self, ctx: SafetyContext, hr_case: Optional[HrCase],
                                      global_settings: GlobalSafetySettings,
                                      site_settings: Optional[SiteSafetySettings],
                                      sub_settings: Optional[SubscriptionSafetySettings]) -> SafetyDecision:
        """评估自动清理操作"""
        
        # 自动清理遇到HR种子时更保守
        if hr_case and hr_case.status == "ACTIVE":
            return SafetyDecision(
                decision="DENY",
                reason_code="hr_active_cleanup",
                message="自动清理检测到HR期种子，已跳过删除",
                hr_status_snapshot={"status": hr_case.status, "torrent_id": hr_case.torrent_id}
            )
        
        return SafetyDecision(decision="ALLOW", reason_code="safe", message="允许清理")
```

## 四、P0-P6 分阶段实施计划

### P0 – 现状巡检 & HR 案件系统设计落盘 ✅

**目标**: 完成代码巡检，形成统一HrCase设计

**完成内容**:
- ✅ 梳理了HRWatcher、InboxWatcher、LocalIntelEngine的完整数据流
- ✅ 识别了`_HR_STATE_CACHE`的直接访问点和风险
- ✅ 设计了HrCase统一模型和渐进式迁移策略
- ✅ 制定了SafetyPolicyEngine的核心架构

**关键发现**:
- 现有架构已为整合做好准备，有明确的迁移路径
- 需要特别注意内存缓存的同步问题
- InboxWatcher直接修改状态，需要统一接口

### P1 – HrCase 统一模型 & 仓库重整

**目标**: 实现统一HrCase接口，保证后续SafetyPolicyEngine只通过统一Repo访问

**工作内容**:
1. **模型实现**
   - 创建 `backend/app/modules/hr_case/models.py`
   - 实现HrCase Pydantic模型和SQLAlchemy ORM
   - 创建数据库迁移脚本

2. **仓库实现**
   - 实现 `SqlAlchemyHrCasesRepository`
   - 添加双写支持：同时更新DB和`_HR_STATE_CACHE`
   - 实现缓存一致性检查

3. **向后兼容层**
   - 修改 `hr_state.py` 中的函数，通过HrCasesRepository操作
   - 保持现有API不变，内部实现逐步迁移

**验收标准**:
- HRWatcher/InboxWatcher通过新仓库正常工作
- 现有HR功能不退化
- 可以列出某站的所有HrCase

### P2 – SafetyPolicyEngine v1 实现（仅后端）

**目标**: 实现SafetyPolicyEngine核心逻辑，通过单元测试验证

**工作内容**:
1. **类型定义**
   - 创建 `backend/app/modules/safety/models.py`
   - 实现SafetyContext、SafetyDecision等核心类型

2. **配置集成**
   - 扩展SETTINGS-RULES-1配置模型
   - 实现SafetySettingsService

3. **引擎实现**
   - 创建 `backend/app/modules/safety/engine.py`
   - 实现核心评估逻辑
   - 添加feature flag控制

4. **单元测试**
   - 创建 `backend/tests/safety/test_policy_engine_basic.py`
   - 覆盖关键决策场景

**验收标准**:
- 测试全绿
- 能在REPL中对典型上下文给出合理决策

### P3 – 后端接入：下载 / 删除 / 移动 / 自动整理

**目标**: 把所有"会影响种子/文件命运"的操作都挂到SafetyPolicyEngine下

**工作内容**:
1. **下载前检查**
   - 修改订阅/搜索添加Torrent流程
   - 集成SafetyPolicyEngine评估
   - 实现二次确认机制

2. **删除操作保护**
   - 修改删除任务/文件API
   - 添加安全检查拦截

3. **移动/整理保护**
   - 识别所有文件移动操作
   - 检测是否影响做种路径
   - 实现安全策略

4. **自动清理保护**
   - 修改待整理目录清理逻辑
   - 防止误删HR文件

**验收标准**:
- HR ACTIVE案例无法删除/危险移动
- 正常流程不被过度打断

### P4 – 前端安全模式中心 + UI 提示

**目标**: 提供直观的安全策略设置界面和状态提示

**工作内容**:
1. **安全模式设置页**
   - 在Settings中新增安全模式Tab
   - 实现三档模式选择
   - 添加HR移动策略设置

2. **站点墙 & 详情增强**
   - 显示站点HR敏感度
   - 添加站点保种阈值展示

3. **下载详情提示**
   - 显示HR状态区域
   - 展示安全操作建议
   - 拦截决策用户提示

4. **订阅编辑优化**
   - 简化安全设置说明
   - 显示有效策略总结

**验收标准**:
- 安全模式页正常读写配置
- 关键界面显示HR状态提示

### P5 – 通知中心 & Telegram 联动

**目标**: 危险操作决策可见、可追溯，支持TG一次性放行

**工作内容**:
1. **通知集成**
   - 新增SAFETY_BLOCKED/WARNING通知类型
   - SafetyPolicyEngine决策时发送通知
   - 优化通知内容展示

2. **Telegram Bot集成**
   - 修改相关命令集成安全检查
   - 实现一次性放行机制
   - 添加inline keyboard支持

3. **安全状态查询**
   - 新增`/safety_status`命令
   - 显示近期拦截记录
   - 提供配置概览

**验收标准**:
- Web/TG拦截操作有对应通知
- 一次性放行机制正常工作

### P6 – 测试、回归与文档

**目标**: 保证新安全系统不引入问题，留好文档

**工作内容**:
1. **测试补充**
   - HrCasesRepository核心方法测试
   - SafetyPolicyEngine边界情况测试
   - 典型操作流集成测试

2. **回归检查**
   - 运行现有订阅/下载/整理测试
   - 确保关闭安全模式时不受影响

3. **文档完善**
   - 更新设计文档为最终版
   - 创建用户指南
   - 准备发布说明

**验收标准**:
- 测试通过、CI绿
- 文档完整可维护

## 五、风险控制与质量保证

### 5.1 技术风险

**数据一致性风险**
- 双写期可能出现内存缓存与DB不一致
- **缓解**: 实现原子性写入操作，定期一致性检查

**性能风险**
- 频繁的DB查询可能影响性能
- **缓解**: 实现多级缓存，异步写入优化

**兼容性风险**
- 现有功能可能被意外破坏
- **缓解**: 完整的回归测试，feature flag控制

### 5.2 实施风险

**复杂度风险**
- 涉及模块多，改造范围大
- **缓解**: 渐进式实施，每阶段独立验证

**用户接受度风险**
- 安全策略可能过于严格影响使用
- **缓解**: 提供多档位选择，用户可自定义

### 5.3 质量保证措施

1. **代码质量**: 遵循现有代码规范，完整类型注解
2. **测试覆盖**: 核心逻辑100%测试覆盖
3. **文档完整**: 设计文档、API文档、用户指南齐全
4. **监控告警**: 关键操作添加日志和监控

## 六、成功标准

### 6.1 功能标准
- ✅ HR期内危险操作100%被拦截
- ✅ HR完成后自动解除限制
- ✅ 用户可通过界面灵活配置安全策略
- ✅ 所有操作有完整审计日志

### 6.2 性能标准
- 安全检查响应时间 < 100ms
- 不影响现有下载/整理性能
- 内存使用增长 < 20%

### 6.3 可用性标准
- 界面直观，用户5分钟内理解安全模式
- 不破坏现有用户习惯
- 提供清晰的错误提示和操作建议

---

**文档版本**: v1.0  
**创建时间**: 2025-11-29  
**负责人**: Cascade  
**预计工期**: 6个阶段，约3-4周
