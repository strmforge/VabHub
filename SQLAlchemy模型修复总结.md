# SQLAlchemy模型修复总结

**生成时间**: 2025-01-XX  
**问题**: SQLAlchemy保留字冲突

---

## 🐛 发现的问题

### 问题描述

多个SQLAlchemy模型使用了`metadata`作为列名，但`metadata`是SQLAlchemy的保留字，会导致以下错误：

```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

### 受影响的模型

1. **UploadTask** (`app/models/upload.py`)
   - 字段: `metadata` → 改为 `extra_metadata`

2. **STRMWorkflowTask** (`app/models/strm.py`)
   - 字段: `metadata` → 改为 `extra_metadata`

3. **SubscriptionRefreshHistory** (`app/models/subscription_refresh.py`)
   - 字段: `metadata` → 改为 `extra_metadata`

4. **OCRRecord** (`app/models/ocr_statistics.py`)
   - 字段: `metadata` → 改为 `extra_metadata`

5. **BackupRecord** (`app/models/backup.py`)
   - 字段: `metadata` → 改为 `extra_metadata`
   - 同时修复了`to_dict()`方法中的字段名

---

## ✅ 修复内容

### 1. 模型字段重命名

所有使用`metadata`作为列名的模型都已重命名为`extra_metadata`，并添加了注释说明：

```python
# 修复前
metadata = Column(JSON, nullable=True)  # 额外元数据

# 修复后
extra_metadata = Column(JSON, nullable=True)  # 额外元数据（避免使用metadata保留字）
```

### 2. 相关代码更新

- **`app/models/backup.py`**: 修复了`to_dict()`方法中的字段名
- **`app/modules/subscription/refresh_monitor.py`**: 修复了`history.metadata`的赋值

### 3. 其他修复

- **`app/modules/media_renamer/identifier.py`**: 添加了缺失的导入`MediaInfo`和`FilenameParser`
- **`app/modules/media_renamer/category_helper.py`**: 修复了`CommentedMap`在`ruamel.yaml`未安装时的类型注解问题

---

## 📋 修复文件列表

1. ✅ `VabHub/backend/app/models/upload.py`
2. ✅ `VabHub/backend/app/models/strm.py`
3. ✅ `VabHub/backend/app/models/subscription_refresh.py`
4. ✅ `VabHub/backend/app/models/ocr_statistics.py`
5. ✅ `VabHub/backend/app/models/backup.py`
6. ✅ `VabHub/backend/app/modules/subscription/refresh_monitor.py`
7. ✅ `VabHub/backend/app/modules/media_renamer/identifier.py`
8. ✅ `VabHub/backend/app/modules/media_renamer/category_helper.py`

---

## ⚠️ 注意事项

### 数据库迁移

如果数据库中已有数据，需要执行数据库迁移：

1. **创建迁移脚本**（如果需要）：
   ```sql
   ALTER TABLE upload_tasks RENAME COLUMN metadata TO extra_metadata;
   ALTER TABLE strm_workflow_tasks RENAME COLUMN metadata TO extra_metadata;
   ALTER TABLE subscription_refresh_history RENAME COLUMN metadata TO extra_metadata;
   ALTER TABLE ocr_records RENAME COLUMN metadata TO extra_metadata;
   ALTER TABLE backup_records RENAME COLUMN metadata TO extra_metadata;
   ```

2. **或者重新创建数据库**（开发环境）：
   - 删除现有数据库
   - 重新运行初始化脚本

### API响应格式

如果前端或其他服务依赖`metadata`字段名，需要更新：

- 前端代码需要将`metadata`改为`extra_metadata`
- API文档需要更新字段名

---

## ✅ 验证

修复后，测试脚本可以正常导入所有模型：

```bash
python scripts/test_fanart_nfo.py
```

---

**文档生成时间**: 2025-01-XX  
**文档版本**: 1.0

