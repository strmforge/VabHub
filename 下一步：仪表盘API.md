# 下一步：实现仪表盘API

## 🎯 目标

实现仪表盘API，让前端可以显示系统概览和关键指标。

## 📋 需要实现的API

### 1. 系统监控API
- **端点**: `GET /api/v1/dashboard/system-stats`
- **功能**: 返回CPU、内存、磁盘使用率
- **数据来源**: psutil库

### 2. 媒体统计API
- **端点**: `GET /api/v1/dashboard/media-stats`
- **功能**: 返回媒体库统计（电影数、电视剧数等）
- **数据来源**: 数据库查询

### 3. 下载统计API
- **端点**: `GET /api/v1/dashboard/download-stats`
- **功能**: 返回下载任务统计（活跃下载数、总速度等）
- **数据来源**: 数据库查询

### 4. 综合仪表盘API
- **端点**: `GET /api/v1/dashboard/`
- **功能**: 返回所有仪表盘数据
- **数据来源**: 整合上述所有API

## 🚀 实施步骤

### 步骤1：完善DashboardService
- [ ] 实现get_system_stats()方法
- [ ] 实现get_media_stats()方法
- [ ] 实现get_download_stats()方法
- [ ] 实现get_dashboard_data()方法

### 步骤2：完善Dashboard API
- [ ] 实现/system-stats端点
- [ ] 实现/media-stats端点
- [ ] 实现/download-stats端点
- [ ] 完善/端点

### 步骤3：测试
- [ ] 测试系统监控API
- [ ] 测试媒体统计API
- [ ] 测试下载统计API
- [ ] 测试综合API

### 步骤4：前端联调
- [ ] 前端调用API
- [ ] 数据展示
- [ ] 实时更新

## 📝 预计时间

- **步骤1**: 30分钟
- **步骤2**: 20分钟
- **步骤3**: 20分钟
- **步骤4**: 30分钟

**总计**: 约2小时

## ✅ 验收标准

- [ ] 可以获取系统资源使用情况
- [ ] 可以获取媒体统计
- [ ] 可以获取下载统计
- [ ] 前端仪表盘可以正常显示数据
- [ ] API响应时间 < 500ms

---

**准备好开始了吗？让我们实现仪表盘API！** 🚀

