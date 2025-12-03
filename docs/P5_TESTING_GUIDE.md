# Manga Local Read Phase 1 集成测试指南

## 📋 测试概述

本测试指南用于验证 Manga Local Read Phase 1 的完整功能实现，确保所有API端点、文件存储、图片服务和前端集成正常工作。

## 🎯 测试目标

### 核心功能验证
1. **下载功能** - 单章节和批量下载正常工作
2. **图片服务** - 图片URL正确生成和加载
3. **阅读流程** - 完整的下载→阅读→进度流程
4. **向后兼容** - 旧格式数据正常处理

### 边界条件测试
1. **错误处理** - 各种异常情况的响应
2. **权限控制** - 身份验证正确执行
3. **文件格式** - 支持的图片格式正常处理

## 🔧 环境准备

### 配置检查
```bash
# 检查环境配置
echo $COMIC_LIBRARY_ROOT  # 应该指向 ./data/library/comics 或类似路径
ls -la ./data/library/comics/  # 确认目录存在且有写权限
```

### 数据库准备
```sql
-- 检查必要的表和数据
SELECT COUNT(*) FROM manga_series_local;
SELECT COUNT(*) FROM manga_chapter_local;
SELECT COUNT(*) FROM manga_reading_progress;
```

## 📝 API端点测试

### 1. 系列列表测试
```bash
# 获取本地漫画系列列表
curl -X GET "http://localhost:8001/api/manga/local/series" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# 预期响应
{
  "success": true,
  "data": {
    "items": [...],
    "total": 0,
    "page": 1,
    "page_size": 20
  }
}
```

### 2. 系列详情测试
```bash
# 获取系列详情（需要实际的series_id）
curl -X GET "http://localhost:8001/api/manga/local/series/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# 预期响应
{
  "success": true,
  "data": {
    "series": {...},
    "chapters": [...]
  }
}
```

### 3. 章节页面列表测试
```bash
# 获取章节页面列表（需要实际的chapter_id）
curl -X GET "http://localhost:8001/api/manga/local/chapters/1/pages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# 预期响应（如果章节已下载）
{
  "success": true,
  "data": [
    {
      "index": 1,
      "image_url": "/media/library/comics/series-slug/chapter/001.jpg"
    },
    ...
  ]
}

# 预期响应（如果章节未下载）
{
  "success": false,
  "error_message": "章节尚未下载完成"
}
```

### 4. 图片流测试
```bash
# 直接访问图片（需要实际的chapter_id和page_index）
curl -X GET "http://localhost:8001/api/manga/local/chapters/1/pages/1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 预期：返回图片文件流，正确的Content-Type
```

### 5. 单章节下载测试
```bash
# 下载单个章节
curl -X POST "http://localhost:8001/api/manga/local/chapters/1/download" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# 预期响应
{
  "success": true,
  "data": {
    "chapter_id": 1,
    "status": "READY",
    "page_count": 20,
    "file_path": "series-slug/chapter-001-title"
  },
  "message": "章节下载完成"
}
```

### 6. 批量下载测试
```bash
# 批量下载系列章节
curl -X POST "http://localhost:8001/api/manga/local/series/1/download" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "LATEST_N",
    "latest_n": 5
  }'

# 预期响应
{
  "success": true,
  "data": {
    "series_id": 1,
    "success_count": 5,
    "limit": 5
  },
  "message": "成功下载 5 个章节"
}
```

## 🌐 前端集成测试

### Web阅读器测试
1. **访问阅读器页面**
   ```
   http://localhost:3000/manga/local/reader/1/1
   ```

2. **功能验证**
   - [ ] 页面正常加载，显示章节选择器
   - [ ] 章节状态正确显示（READY/PENDING/FAILED）
   - [ ] 下载按钮正常工作
   - [ ] 图片正确显示
   - [ ] 翻页功能正常
   - [ ] 章节切换正常
   - [ ] 阅读进度自动保存

### 错误状态测试
1. **章节未下载状态**
   - 显示下载提示界面
   - 下载按钮正常工作
   - 下载完成后状态更新

2. **网络错误处理**
   - API调用失败时显示错误信息
   - 加载状态正确显示

## 📁 文件系统验证

### 路径结构检查
```bash
# 检查新格式路径结构
ls -la ./data/library/comics/
# 预期：series-slug/chapter-number - title/ 格式

# 检查旧格式路径结构（如果存在）
ls -la ./data/library/comics/
# 预期：series_1/chapter_1/ 格式

# 验证图片文件
ls -la ./data/library/comics/series-slug/chapter-001-title/
# 预期：001.jpg, 002.jpg, ... 按顺序排列
```

### 图片URL验证
```bash
# 测试生成的图片URL
curl -I "http://localhost:8001/media/library/comics/series-slug/chapter-001-title/001.jpg"
# 预期：200 OK，正确的Content-Type

# 测试旧格式URL（如果存在）
curl -I "http://localhost:8001/media/library/comics/series_1/chapter_1/001.jpg"
# 预期：200 OK
```

## 🔍 向后兼容性测试

### 旧格式数据测试
```sql
-- 查找旧格式数据
SELECT id, file_path FROM manga_chapter_local 
WHERE file_path LIKE 'data/%' OR file_path LIKE '%series_%';

-- 验证API能正确处理旧格式
```

### 路径检测测试
```bash
# 测试_get_page_url函数的路径检测逻辑
# 旧格式：data/library/comics/series_1/chapter_1
# 新格式：series-slug/chapter-001-title
```

## ⚠️ 错误场景测试

### 权限测试
```bash
# 未授权访问
curl -X GET "http://localhost:8001/api/manga/local/series"
# 预期：401 Unauthorized

# 无效token
curl -X GET "http://localhost:8001/api/manga/local/series" \
  -H "Authorization: Bearer INVALID_TOKEN"
# 预期：401 Unauthorized
```

### 数据不存在测试
```bash
# 不存在的系列
curl -X GET "http://localhost:8001/api/manga/local/series/99999"
# 预期：404 Not Found

# 不存在的章节
curl -X GET "http://localhost:8001/api/manga/local/chapters/99999/pages"
# 预期：404 Not Found
```

### 文件系统错误测试
```bash
# 删除章节文件后访问
rm -rf ./data/library/comics/series-slug/chapter-001-title/
curl -X GET "http://localhost:8001/api/manga/local/chapters/1/pages"
# 预期：404 Not Found 或适当的错误信息
```

## 📊 性能测试

### 下载性能
```bash
# 测试大章节下载时间
time curl -X POST "http://localhost:8001/api/manga/local/chapters/1/download" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 预期：< 2分钟（中等大小章节）
```

### 图片加载性能
```bash
# 测试图片加载时间
time curl -I "http://localhost:8001/media/library/comics/series-slug/chapter/001.jpg"

# 预期：< 3秒首次加载，< 500ms翻页响应
```

## ✅ 测试清单

### 基础功能
- [ ] API端点正常响应
- [ ] 下载功能正常工作
- [ ] 图片正确显示
- [ ] 阅读进度正常保存
- [ ] 错误处理正确

### 兼容性
- [ ] 新格式路径正常工作
- [ ] 旧格式数据向后兼容
- [ ] 前端API调用正常

### 性能
- [ ] 下载速度符合预期
- [ ] 图片加载速度符合预期
- [ ] 翻页响应速度符合预期

### 安全性
- [ ] 身份验证正常工作
- [ ] 权限控制正确执行
- [ ] 错误信息不泄露敏感信息

## 🚨 常见问题排查

### 图片404错误
1. 检查`MANGA_ROOT`配置是否正确
2. 验证文件路径是否匹配媒体服务配置
3. 确认图片文件实际存在

### 下载失败
1. 检查网络连接和远程源配置
2. 验证存储目录权限
3. 查看后端日志详细错误信息

### 前端显示异常
1. 检查API响应格式是否正确
2. 验证前端类型定义匹配
3. 确认身份验证token有效

## 📞 问题反馈

测试过程中如发现问题，请记录以下信息：
1. 具体操作步骤
2. 预期结果 vs 实际结果
3. 错误信息和日志
4. 环境配置信息
5. 数据状态（相关表记录）

---

**测试完成后，请更新测试结果并确认是否可以进入生产发布阶段。**
