# API端点测试指南

## 测试准备

### 1. 启动后端服务

有两种方式启动后端服务：

#### 方式1: 使用启动脚本（推荐）
```bash
# Windows
start_backend.bat

# 或者在项目根目录执行
cd VabHub
start_backend.bat
```

#### 方式2: 手动启动
```bash
cd VabHub/backend
python main.py
```

服务启动后，访问：
- API根路径: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 2. 运行API测试脚本

在另一个终端窗口中运行测试脚本：

```bash
cd VabHub/backend
python test_api_endpoints_manual.py
```

## 测试内容

### 1. 健康检查测试
- `GET /health` - 检查服务健康状态

### 2. 媒体服务器API测试
- `GET /api/v1/media-servers/` - 获取服务器列表
- `POST /api/v1/media-servers/` - 创建媒体服务器
- `GET /api/v1/media-servers/{server_id}` - 获取服务器详情
- `PUT /api/v1/media-servers/{server_id}` - 更新服务器
- `DELETE /api/v1/media-servers/{server_id}` - 删除服务器

### 3. 调度器API测试
- `GET /api/v1/scheduler/jobs` - 获取任务列表
- `GET /api/v1/scheduler/statistics` - 获取统计信息
- `POST /api/v1/scheduler/sync` - 同步任务

## 使用Postman或curl测试

### 健康检查
```bash
curl http://localhost:8000/health
```

### 创建媒体服务器
```bash
curl -X POST http://localhost:8000/api/v1/media-servers/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试Jellyfin服务器",
    "server_type": "jellyfin",
    "url": "http://localhost:8096",
    "api_key": "test_api_key",
    "user_id": "test_user_id",
    "enabled": false
  }'
```

### 获取服务器列表
```bash
curl http://localhost:8000/api/v1/media-servers/
```

### 获取调度器统计
```bash
curl http://localhost:8000/api/v1/scheduler/statistics
```

### 同步任务
```bash
curl -X POST http://localhost:8000/api/v1/scheduler/sync
```

## 使用API文档测试

1. 访问 http://localhost:8000/docs
2. 在Swagger UI中：
   - 展开 `/api/v1/media-servers/` 端点
   - 点击 "Try it out"
   - 填写参数
   - 点击 "Execute" 执行请求
   - 查看响应结果

## 预期结果

### 健康检查
- 状态码: 200
- 响应包含: `status: "healthy"`

### 媒体服务器API
- 创建: 状态码 200/201，返回创建的服务器信息
- 列表: 状态码 200，返回服务器列表
- 详情: 状态码 200，返回服务器详细信息
- 更新: 状态码 200，返回更新后的服务器信息
- 删除: 状态码 200/204，删除成功

### 调度器API
- 任务列表: 状态码 200，返回任务列表（可能为空）
- 统计信息: 状态码 200，返回统计信息
- 同步任务: 状态码 200，返回同步结果

## 常见问题

### 1. 服务启动失败
- 检查端口8000是否被占用
- 检查数据库是否初始化
- 查看日志输出

### 2. 连接被拒绝
- 确认服务已启动
- 检查防火墙设置
- 确认端口号正确

### 3. 数据库错误
- 运行数据库初始化: `python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"`
- 检查数据库文件权限

## 下一步

测试通过后，可以：
1. 开发前端界面
2. 继续实现其他高优先级功能
3. 进行实际环境的集成测试

