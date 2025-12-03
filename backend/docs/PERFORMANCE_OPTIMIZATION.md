# 性能优化指南

本文档描述了VabHub系统的性能优化策略和实施建议。

## 数据库优化

### 1. 索引优化

#### 下载任务表索引
```sql
-- 为下载任务表添加索引
CREATE INDEX IF NOT EXISTS idx_download_tasks_status ON download_tasks(status);
CREATE INDEX IF NOT EXISTS idx_download_tasks_created_at ON download_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_download_tasks_downloader_hash ON download_tasks(downloader_hash);
```

#### 订阅表索引
```sql
-- 为订阅表添加索引
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_media_type ON subscriptions(media_type);
CREATE INDEX IF NOT EXISTS idx_subscriptions_created_at ON subscriptions(created_at);
```

#### 媒体文件表索引
```sql
-- 为媒体文件表添加索引
CREATE INDEX IF NOT EXISTS idx_media_files_tmdb_id ON media_files(tmdb_id);
CREATE INDEX IF NOT EXISTS idx_media_files_media_type ON media_files(media_type);
CREATE INDEX IF NOT EXISTS idx_media_files_file_path ON media_files(file_path);
```

### 2. 查询优化

#### 使用分页
- 所有列表查询都应该使用分页
- 默认每页20条，最大100条
- 避免一次性加载大量数据

#### 使用连接池
- SQLAlchemy默认使用连接池
- 建议配置连接池大小：
  ```python
  engine = create_async_engine(
      DATABASE_URL,
      pool_size=10,
      max_overflow=20,
      pool_pre_ping=True
  )
  ```

#### 避免N+1查询
- 使用`joinedload`或`selectinload`预加载关联数据
- 批量查询替代循环查询

### 3. 缓存策略

#### Redis缓存
- 使用Redis缓存频繁访问的数据
- 缓存键命名规范：`{module}:{resource}:{id}`
- 设置合理的TTL（Time To Live）

#### 缓存示例
```python
# 缓存下载列表（30秒）
cache_key = f"downloads:list:{status}:{page}"
await cache.set(cache_key, data, ttl=30)

# 缓存媒体详情（1小时）
cache_key = f"media:detail:{tmdb_id}"
await cache.set(cache_key, data, ttl=3600)
```

## API优化

### 1. 响应时间监控

- 使用`PerformanceMonitoringMiddleware`监控API响应时间
- 识别慢端点（>1秒）
- 定期分析性能数据

### 2. 异步处理

- 所有I/O操作使用异步
- 长时间运行的任务使用后台任务
- 使用WebSocket推送实时更新

### 3. 批量操作

- 批量操作比单个操作更高效
- 使用事务确保数据一致性
- 按下载器分组批量操作

## 前端优化

### 1. 数据加载

- 使用分页加载，避免一次性加载大量数据
- 使用虚拟滚动显示长列表
- 实现数据懒加载

### 2. 请求优化

- 使用请求去抖（debounce）避免频繁请求
- 合并多个请求为单个请求
- 使用WebSocket替代轮询

### 3. 缓存策略

- 缓存API响应数据
- 使用本地存储缓存用户偏好
- 实现智能缓存失效策略

## 监控和诊断

### 1. 性能监控

- 使用`/api/performance/metrics`端点获取性能指标
- 定期运行`analyze_slow_queries.py`分析慢查询
- 监控API响应时间、错误率、吞吐量

### 2. 日志分析

- 使用结构化日志（JSON格式）
- 记录关键操作的执行时间
- 分析日志识别性能瓶颈

### 3. 数据库分析

- 定期分析慢查询日志
- 检查索引使用情况
- 优化查询计划

## 优化建议

### 高优先级

1. **添加数据库索引**
   - 为常用查询字段添加索引
   - 定期检查索引使用情况

2. **实现缓存层**
   - 缓存频繁访问的数据
   - 设置合理的缓存TTL

3. **优化查询**
   - 使用分页避免大量数据加载
   - 使用预加载避免N+1查询

### 中优先级

1. **异步处理**
   - 长时间运行的任务使用后台任务
   - 使用消息队列处理批量操作

2. **前端优化**
   - 实现虚拟滚动
   - 使用请求去抖

3. **监控和诊断**
   - 定期分析性能数据
   - 识别和优化慢查询

### 低优先级

1. **数据库分区**
   - 对于大表考虑分区
   - 归档历史数据

2. **CDN加速**
   - 静态资源使用CDN
   - 图片使用CDN加速

3. **负载均衡**
   - 多实例部署
   - 使用负载均衡器

## 性能基准

### 目标响应时间

- API响应时间：< 200ms（P95）
- 数据库查询：< 100ms（P95）
- 页面加载时间：< 2s

### 目标吞吐量

- API请求：> 1000 req/s
- 数据库查询：> 5000 qps
- WebSocket连接：> 100 并发

## 工具和脚本

### 性能分析脚本

1. `analyze_slow_queries.py` - 分析慢查询
2. `test_new_endpoints.py` - 测试端点性能
3. `setup_test_environment.py` - 配置测试环境

### 监控工具

1. `/api/performance/metrics` - 性能指标API
2. 日志系统 - 结构化日志
3. 数据库慢查询日志

## 持续优化

1. **定期审查**
   - 每周审查性能指标
   - 每月分析慢查询
   - 每季度优化数据库

2. **性能测试**
   - 定期运行性能测试
   - 压力测试识别瓶颈
   - A/B测试优化策略

3. **文档更新**
   - 记录优化经验
   - 更新性能基准
   - 分享最佳实践

