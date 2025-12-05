# /dev/novel/upload-txt 开发接口说明

> ⚠️ **注意**：这是一个**开发/演示接口**，不是正式用户入口。

## 接口信息

| 项目 | 说明 |
|------|------|
| **路径** | `POST /dev/novel/upload-txt` |
| **Content-Type** | `multipart/form-data` |
| **用途** | 快速验证 TXT→EPUB 流水线 |

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | ✅ | TXT 格式的小说文件 |
| `title` | string | ❌ | 小说标题（不传则从文件名推断） |
| `author` | string | ❌ | 作者 |
| `description` | string | ❌ | 简介 |
| `generate_audiobook` | bool | ❌ | 是否生成有声书（默认 false） |

### 响应结构

```json
{
  "success": true,
  "data": {
    "ebook_path": "/path/to/generated.epub",
    "ebook_id": 123,           // 或 null
    "audiobook_created": false,
    "audiobook_files_count": 0,
    "message": "成功导入小说《xxx》到电子书库"
  }
}
```

## 行为说明

### 始终执行
1. 保存上传的 TXT 文件到 `NOVEL_UPLOAD_ROOT` 目录
2. 调用章节切分器解析章节
3. 生成 EPUB 文件（目前为占位实现）

### 条件执行
- **数据库就绪时**：尝试将电子书写入正式电子书库 → `ebook_id` 为整数
- **数据库未就绪时**：不抛 500 错误，仅返回 `ebook_id = null`

## 与正式流程对比

| 场景 | 入口 | 说明 |
|------|------|------|
| **正式链路** | 待整理目录 / Inbox → Novel Pipeline | 完整的入库流程，经过元数据补全、分类等 |
| **DEV 接口** | `/dev/novel/upload-txt` | 快速验证"章节切分 + EPUB 生成"子链路 |

正式链路流程：
```
待整理目录 → Novel Pipeline → EBook 库 → 有声书（可选） → 小说中心
```

## 手工验证步骤

### curl 示例

```bash
# 假设后端运行在 localhost:8000
curl -X POST "http://localhost:8000/dev/novel/upload-txt" \
  -F "file=@/path/to/test_novel.txt;type=text/plain" \
  -F "title=测试小说" \
  -F "author=测试作者"
```

### 预期输出

- **HTTP 状态码**: 200
- **JSON 响应关键点**:
  - `success`: `true`
  - `data.ebook_path`: 非空字符串（生成的 EPUB 路径）
  - `data.ebook_id`: 
    - 数据库就绪时为整数
    - 数据库未初始化时为 `null`

### 错误情况

| 状态码 | 原因 |
|--------|------|
| 400 | 上传的不是 TXT 文件 |
| 422 | 缺少必要的 `file` 字段 |
| 500 | 流水线执行失败（如章节切分异常） |

## 相关文件

- `backend/app/api/novel_demo.py` - 接口实现
- `backend/app/modules/novel/` - Novel Pipeline 模块
- `backend/tests/test_novel_upload_api.py` - 测试用例
