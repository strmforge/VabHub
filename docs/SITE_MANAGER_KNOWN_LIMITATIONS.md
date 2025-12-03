# SITE-MANAGER-1 已知限制和待办事项

## 概述

SITE-MANAGER-1 v1.0.0 提供了完整的站点管理基础设施，但部分集成功能需要进一步实现才能投入生产使用。

---

## 🔗 集成钩子限制

### 当前状态
集成钩子系统已实现事件驱动架构，但具体的集成实现仍为占位符代码：

#### CookieCloud 集成
**状态**: 🟡 需要实现  
**当前行为**: 仅记录日志，不执行实际同步
**需要实现**:
```python
async def cookiecloud_sync_hook(site: SiteDetail, **kwargs):
    # TODO: 实际的CookieCloud API调用
    # 1. 验证CookieCloud配置
    # 2. 执行Cookie同步
    # 3. 根据同步结果更新SiteStats.health_status
    
    # 当前实现：
    await asyncio.sleep(0.1)  # 模拟网络请求
    logger.info(f"CookieCloud同步完成: {site.name}")
```

**实现要求**:
- [ ] 集成 `app/modules/cookiecloud/service.py`
- [ ] 实现错误处理和重试机制
- [ ] 添加同步状态跟踪
- [ ] 实现健康状态自动更新

#### Local Intel 集成
**状态**: 🟡 需要实现  
**当前行为**: 仅记录日志，不执行实际同步
**需要实现**:
```python
async def sync_site_health_to_local_intel(site_id: int, health_status: HealthStatus, **kwargs):
    # TODO: 实际的Local Intel API调用
    # 1. 查找对应的SiteGuardProfile
    # 2. 更新健康状态字段
    # 3. 处理字符串站点名称到Site.id的映射
    
    # 当前实现：
    logger.info(f"同步健康状态到Local Intel: 站点ID {site_id} -> {health_status.value}")
```

**实现要求**:
- [ ] 创建SiteGuardProfile表的site_id字段迁移
- [ ] 实现字符串站点名称到Site.id的映射逻辑
- [ ] 集成 `app/modules/local_intel/service.py`
- [ ] 添加批量同步支持

#### External Indexer 集成
**状态**: ✅ 已实现基础功能  
**当前行为**: 提供健康站点列表过滤
**需要完善**:
- [ ] 添加访问配置的详细参数传递
- [ ] 实现缓存机制提高性能
- [ ] 添加站点权重排序逻辑

---

## 🗄️ 数据库限制

### 事务完整性
**风险**: 多表操作可能导致数据不一致  
**影响**: 站点创建/更新时，如果部分操作失败，可能产生孤立记录

**当前保护措施**:
```python
try:
    # 创建站点
    site = Site(**site_data)
    db.add(site)
    await db.flush()  # 获取ID
    
    # 创建关联记录
    config = SiteAccessConfig(site_id=site.id)
    stats = SiteStats(site_id=site.id)
    db.add(config)
    db.add(stats)
    
    await db.commit()
except Exception as e:
    await db.rollback()
    logger.error(f"创建站点失败: {e}")
    raise
```

**需要改进**:
- [ ] 添加数据库约束防止孤立记录
- [ ] 实现定期数据一致性检查
- [ ] 添加事务超时机制

### 性能限制
**当前限制**:
- 大量站点时列表查询可能较慢
- 健康检查没有并发限制
- 缺少查询结果缓存

**优化建议**:
- [ ] 实现分页查询优化
- [ ] 添加Redis缓存层
- [ ] 实现健康检查队列系统

---

## 🚀 API 限制

### 认证和授权
**当前状态**: 基础Bearer Token认证  
**缺失功能**:
- [ ] 细粒度权限控制（RBAC）
- [ ] API访问频率限制
- [ ] 审计日志记录

### 错误处理
**当前限制**:
- 错误信息可能暴露内部实现
- 缺少详细的错误分类
- 没有错误恢复建议

**改进计划**:
- [ ] 实现生产环境友好的错误消息
- [ ] 添加错误代码到恢复建议的映射
- [ ] 实现错误监控和告警

---

## 🌐 前端限制

### 浏览器兼容性
**当前支持**: Chrome 90+, Firefox 88+, Safari 14+  
**需要测试**:
- [ ] Internet Explorer 11 兼容性
- [ ] 移动端浏览器适配
- [ ] 低性能设备优化

### 用户体验
**待改进**:
- [ ] 添加加载状态指示器
- [ ] 实现离线模式支持
- [ ] 优化大数据量列表渲染

---

## 📊 监控和运维限制

### 日志系统
**当前状态**: 基础文件日志  
**需要实现**:
- [ ] 结构化日志格式（JSON）
- [ ] 日志聚合和分析系统
- [ ] 敏感信息脱敏

### 监控指标
**缺失指标**:
- [ ] API响应时间分布
- [ ] 数据库连接池状态
- [ ] 内存和CPU使用率
- [ ] 业务指标（站点健康率等）

---

## 🔄 版本升级限制

### 数据库迁移
**风险**: 大型数据库迁移可能导致停机  
**缓解措施**:
- [ ] 实现零停机迁移策略
- [ ] 添加迁移回滚机制
- [ ] 提供迁移进度监控

### API兼容性
**当前策略**: 语义化版本控制  
**需要文档**:
- [ ] API变更日志模板
- [ ] 废弃功能通知机制
- [ ] 客户端迁移指南

---

## 📋 生产部署前必做事项

### 高优先级（必须完成）
1. **实现CookieCloud实际集成**
   - 评估工作量：2-3人天
   - 负责模块：CookieCloud团队
   - 依赖：CookieCloud API文档

2. **实现Local Intel实际集成**
   - 评估工作量：3-5人天
   - 负责模块：Local Intel团队
   - 依赖：SiteGuardProfile表结构确认

3. **添加数据库约束**
   ```sql
   -- 防止孤立记录
   ALTER TABLE site_stats ADD CONSTRAINT fk_site_stats_site 
     FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE;
   
   ALTER TABLE site_access_configs ADD CONSTRAINT fk_site_access_configs_site 
     FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE;
   ```

### 中优先级（建议完成）
4. **实现API访问频率限制**
5. **添加Redis缓存层**
6. **完善错误处理和监控**

### 低优先级（后续迭代）
7. **实现细粒度权限控制**
8. **优化前端性能**
9. **添加更多监控指标**

---

## 🎯 里程碑计划

### v1.0.1（补丁版本，2周内）
- [ ] 修复数据库约束问题
- [ ] 完善错误处理
- [ ] 添加基础监控

### v1.1.0（功能版本，1个月内）
- [ ] 实现CookieCloud完整集成
- [ ] 实现Local Intel完整集成
- [ ] 添加API访问限制

### v1.2.0（优化版本，2个月内）
- [ ] 性能优化和缓存
- [ ] 完善监控和告警
- [ ] 移动端适配

---

## 📞 技术债务跟踪

### GitHub Issues 需要创建
1. `#123` - Implement CookieCloud integration in Site Manager
2. `#124` - Implement Local Intel integration in Site Manager  
3. `#125` - Add database constraints for data integrity
4. `#126` - Implement API rate limiting
5. `#127` - Add Redis caching for site queries

### 代码审查要点
- [ ] 集成钩子的实际实现逻辑
- [ ] 数据库事务的完整性
- [ ] 错误处理的用户友好性
- [ ] 性能瓶颈的识别和优化

---

## ⚠️ 风险评估

### 高风险项
1. **数据一致性**: 多表操作失败可能导致数据不一致
2. **集成依赖**: CookieCloud和Local Intel集成未完成
3. **性能瓶颈**: 大量站点时查询性能问题

### 缓解策略
1. **数据一致性**: 添加数据库约束和定期检查
2. **集成依赖**: 明确标记为TODO，分配责任人
3. **性能瓶颈**: 实现分页和缓存机制

---

**总结**: SITE-MANAGER-1 基础架构完整且稳定，可以部署到生产环境进行测试，但需要完成上述高优先级项目才能正式投入生产使用。建议采用分阶段发布策略，先部署基础功能，再逐步完善集成功能。
