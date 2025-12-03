# 测试脚本使用指南

## 脚本列表

### 1. `create_test_downloads.py` - 创建真实测试任务
在实际环境中创建一些测试任务，然后使用真实的任务ID进行测试。

**使用方法**:
```bash
python VabHub/backend/scripts/create_test_downloads.py
```

**功能**:
- 检查后端服务是否运行
- 创建3个测试下载任务（使用测试磁力链接）
- 保存任务ID到 `test_task_ids.txt` 文件
- 显示创建的任务ID

**输出**:
- 成功创建的任务ID会保存到 `test_task_ids.txt`
- 这些ID可以用于其他测试脚本

**注意**:
- 需要下载器服务正在运行
- 需要下载器配置正确
- 测试磁力链接可能无效，建议使用真实的磁力链接

---

### 2. `check_backend_logs.py` - 检查后端日志
查看后端日志以了解具体的错误原因。

**使用方法**:
```bash
# 检查错误日志（默认最近50行，过去24小时）
python VabHub/backend/scripts/check_backend_logs.py

# 检查所有日志
python VabHub/backend/scripts/check_backend_logs.py --type all

# 显示更多行
python VabHub/backend/scripts/check_backend_logs.py --lines 100

# 检查过去48小时的日志
python VabHub/backend/scripts/check_backend_logs.py --hours 48

# 搜索关键词
python VabHub/backend/scripts/check_backend_logs.py --search "下载失败"
```

**功能**:
- 显示最近的错误日志
- 支持搜索关键词
- 支持时间范围过滤
- 显示日志文件信息

**参数**:
- `--type`: 日志类型（error/all），默认error
- `--lines`: 显示行数，默认50
- `--hours`: 时间范围（小时），默认24
- `--search`: 搜索关键词

---

### 3. `verify_downloader_connection.py` - 验证下载器连接
确保下载器服务正在运行且配置正确。

**使用方法**:
```bash
python VabHub/backend/scripts/verify_downloader_connection.py
```

**功能**:
- 检查后端服务是否运行
- 检查下载器配置（qBittorrent和Transmission）
- 获取下载器实例列表
- 测试每个下载器连接
- 获取下载器统计信息

**输出**:
- 显示每个下载器的连接状态
- 显示下载器统计信息（总任务数、下载中、已完成等）
- 提供问题排查建议

---

### 4. `test_download_features.py` - 测试下载功能
测试批量操作、队列管理、速度限制等功能。

**使用方法**:
```bash
python VabHub/backend/scripts/test_download_features.py
```

**功能**:
- 测试批量操作（批量暂停、恢复、删除）
- 测试队列管理（上移、下移、置顶）
- 测试速度限制（全局和单个任务）

**注意**:
- 会自动从 `test_task_ids.txt` 加载真实任务ID
- 如果没有真实任务ID，会使用测试ID（可能不存在）
- 建议先运行 `create_test_downloads.py` 创建真实任务

---

### 5. `setup_test_environment.py` - 配置测试环境
配置测试用的下载器实例、API密钥等。

**使用方法**:
```bash
python VabHub/backend/scripts/setup_test_environment.py
```

**功能**:
- 配置qBittorrent和Transmission设置
- 配置TMDB API密钥
- 测试下载器连接

---

### 6. `create_indexes.py` - 创建数据库索引
创建数据库索引以优化查询性能。

**使用方法**:
```bash
python VabHub/backend/scripts/create_indexes.py
```

**功能**:
- 为下载任务表创建索引
- 为订阅表创建索引
- 为媒体文件表创建索引
- 为其他表创建索引

---

## 推荐测试流程

### 第一次使用

1. **启动后端服务**
   ```bash
   cd VabHub/backend
   python main.py
   ```

2. **配置测试环境**
   ```bash
   python VabHub/backend/scripts/setup_test_environment.py
   ```

3. **验证下载器连接**
   ```bash
   python VabHub/backend/scripts/verify_downloader_connection.py
   ```

4. **创建真实测试任务**
   ```bash
   python VabHub/backend/scripts/create_test_downloads.py
   ```

5. **运行功能测试**
   ```bash
   python VabHub/backend/scripts/test_download_features.py
   ```

6. **检查日志（如果有错误）**
   ```bash
   python VabHub/backend/scripts/check_backend_logs.py
   ```

### 日常测试

1. **验证下载器连接**
   ```bash
   python VabHub/backend/scripts/verify_downloader_connection.py
   ```

2. **运行功能测试**
   ```bash
   python VabHub/backend/scripts/test_download_features.py
   ```

3. **检查日志（如果有问题）**
   ```bash
   python VabHub/backend/scripts/check_backend_logs.py --search "错误关键词"
   ```

---

## 故障排查

### 问题1: 无法连接到后端服务

**症状**: `无法连接到后端服务`

**解决方案**:
1. 检查后端服务是否正在运行
2. 检查端口是否正确（默认8001）
3. 检查防火墙设置

### 问题2: 下载器连接失败

**症状**: `下载器连接测试失败`

**解决方案**:
1. 运行 `verify_downloader_connection.py` 检查配置
2. 检查下载器服务是否正在运行
3. 检查下载器配置（主机、端口、用户名、密码）
4. 检查网络连接

### 问题3: 任务创建失败

**症状**: `创建任务失败`

**解决方案**:
1. 检查下载器连接是否正常
2. 检查磁力链接是否有效
3. 检查下载器是否有足够的存储空间
4. 查看后端日志了解详细错误

### 问题4: 测试任务不存在

**症状**: `任务不存在或无法操作`

**解决方案**:
1. 运行 `create_test_downloads.py` 创建真实任务
2. 检查 `test_task_ids.txt` 文件是否存在
3. 使用真实的任务ID进行测试

---

## 文件说明

- `test_task_ids.txt`: 保存创建的真实测试任务ID
- `vabhub_*.log`: 所有日志文件
- `error_*.log`: 错误日志文件

---

## 注意事项

1. **测试磁力链接**: `create_test_downloads.py` 中使用的磁力链接是示例，可能无效。建议使用真实的磁力链接。

2. **任务清理**: 测试完成后，可以删除创建的测试任务。

3. **日志文件**: 日志文件会占用磁盘空间，定期清理旧日志。

4. **并发测试**: 避免同时运行多个测试脚本，可能导致资源竞争。

