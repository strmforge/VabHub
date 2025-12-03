# VabHub相关包详细说明

**分析时间**: 2025-01-XX  
**来源**: `F:\对标版本\新建文件夹\`

---

## 📋 一、vabhub_douban_fallback（豆瓣回退服务）

### 1.1 功能说明

**目的**: 提供豆瓣API回退功能（TMDb → Douban Fallback）

**特点**:
- ✅ 支持离线模式（使用示例数据）
- ✅ 支持生产模式（配置代理网关和Cookie）
- ✅ 提供TMDB和豆瓣提供者

### 1.2 配置

**环境变量**:
- `DOUBAN_OFFLINE=0` - 生产模式（0=生产，1=离线）
- `DOUBAN_SEARCH_URL` - 豆瓣搜索代理网关URL
- Cookie配置 - 必要的Cookie

### 1.3 运行方式

**本地运行**:
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r service/requirements.txt
uvicorn service.app:app --reload --port 9101
```

**Docker运行**:
```bash
docker build -t vabhub-douban-fallback:dev .
docker run --rm -p 9101:9101 --env-file .env.example vabhub-douban-fallback:dev
```

### 1.4 API示例

```
GET /api/scraper/test?q=搏击俱乐部&year=1999
```

---

## 📋 二、vabhub_gap_patch（功能补丁）

### 2.1 功能说明

**目的**: WebUI→后端对齐"差异补齐包"（对标MoviePilot）

**特点**:
- ✅ FastAPI后端Stub（可启动，返回占位数据/501）
- ✅ UI期望端点清单
- ✅ 自动对齐检查脚本
- ✅ capabilities.json与GitHub Actions工作流
- ✅ 前端路由建议

### 2.2 目录结构

```
vabhub_gap_patch/
├── backend-stub/                 # FastAPI端点骨架
│   ├── app.py
│   ├── models.py
│   └── requirements.txt
├── frontend/
│   └── routes.json               # 建议的页面与路由
├── tools/
│   ├── ui_expected_endpoints.txt  # UI期望端点清单
│   └── check_ui_backend_alignment.py  # 对齐检查脚本
├── capabilities.json              # 最小能力清单
└── README.md
```

### 2.3 使用方法

**运行Stub**:
```bash
cd backend-stub
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 9000
# 打开 http://127.0.0.1:9000/docs 查看 OpenAPI
```

**检查对齐**:
```bash
cd tools
python check_ui_backend_alignment.py \
  --openapi http://127.0.0.1:9000/openapi.json \
  --expected ui_expected_endpoints.txt
# 输出 JSON：缺哪些、冗余哪些
```

### 2.4 集成建议

- `backend-stub/` → 迁入 **vabhub-Core**，逐步替换Stub为真实实现
- `frontend/routes.json` → 作为 **vabhub-frontend** 的路由蓝图
- `tools/*.py` 与 `capabilities.json` → 放 **vabhub-deploy** 用于质量闸

---

## 📋 三、vabhub_jellyfin_parity（Jellyfin兼容性）

### 3.1 功能说明

**目的**: Emby/Jellyfin平权（最小实现）

**特点**:
- ✅ 统一接口管理两类媒体服务器
- ✅ 提供`/api/library/servers`列表
- ✅ 提供`/ping`和`/refresh`接口
- ✅ 可直接替换现有"仅Emby"的UI卡片

### 3.2 目录结构

```
vabhub_jellyfin_parity/
├── service/
│   ├── app.py
│   ├── client/
│   │   ├── emby.py      # Emby客户端
│   │   └── jellyfin.py  # Jellyfin客户端
│   └── requirements.txt
└── README.md
```

### 3.3 运行方式

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r service/requirements.txt
uvicorn service.app:app --reload --port 9102
```

### 3.4 API接口

- `GET /api/library/servers` - 获取服务器列表
- `GET /ping` - 健康检查
- `POST /refresh` - 刷新服务器信息

---

## 📋 四、vabhub_stream_gateway（流媒体网关）

### 4.1 功能说明

**目的**: Stream Gateway（最小实现）

**特点**:
- ✅ 让`.strm`文件指向稳定URL（本网关）
- ✅ 网关内部获取115/123的短时效直链并302/反代
- ✅ 提供HMAC签名与302重定向

### 4.2 目录结构

```
vabhub_stream_gateway/
├── service/
│   ├── app.py
│   └── requirements.txt
├── Dockerfile
└── README.md
```

### 4.3 运行方式

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r service/requirements.txt
uvicorn service.app:app --reload --port 9103
```

### 4.4 使用示例

**1. 生成签名**:
```bash
POST /sign
Body: {
  "path": "/stream/123pan/FILEID",
  "ttl": 600
}
```

**2. 得到URL**（带`ts/sig`）:
```
http://gateway.yourdomain/stream/123pan/FILEID?ts=...&sig=...
```

**3. 写入`.strm`文件**:
```
http://gateway.yourdomain/stream/123pan/FILEID?ts=...&sig=...
```

---

## 📋 五、集成建议

### 5.1 集成优先级

1. **高优先级**:
   - ✅ `vabhub_jellyfin_parity` - Jellyfin兼容性（已支持Plex/Jellyfin/Emby）
   - ✅ `vabhub_stream_gateway` - 流媒体网关（STRM系统已实现类似功能）

2. **中优先级**:
   - ⚠️ `vabhub_douban_fallback` - 豆瓣回退（需要检查当前实现）
   - ⚠️ `vabhub_gap_patch` - 功能补丁（需要检查前后端对齐情况）

### 5.2 集成方式

**方式1: 直接集成**
- 将代码直接集成到VabHub主项目
- 优点：统一管理，减少服务数量
- 缺点：需要重构代码

**方式2: 微服务方式**
- 保持独立服务，通过API调用
- 优点：解耦，易于维护
- 缺点：需要管理多个服务

**方式3: 混合方式**
- 核心功能集成到主项目
- 辅助功能保持独立服务
- 优点：平衡灵活性和统一性

---

## 📋 六、与当前VabHub的对比

### 6.1 vabhub_jellyfin_parity

| 功能 | vabhub_jellyfin_parity | 当前VabHub | 状态 |
|------|----------------------|-----------|------|
| Emby支持 | ✅ | ✅ | 已实现 |
| Jellyfin支持 | ✅ | ✅ | 已实现 |
| Plex支持 | ❌ | ✅ | VabHub更完整 |
| 统一接口 | ✅ | ✅ | 已实现 |

**结论**: 当前VabHub已实现类似功能，无需集成

---

### 6.2 vabhub_stream_gateway

| 功能 | vabhub_stream_gateway | 当前VabHub | 状态 |
|------|---------------------|-----------|------|
| STRM文件生成 | ✅ | ✅ | 已实现 |
| 302重定向 | ✅ | ✅ | 已实现 |
| HMAC签名 | ✅ | ❓ | 需要检查 |
| 稳定URL | ✅ | ✅ | 已实现 |

**结论**: 当前VabHub已实现类似功能，可参考HMAC签名实现

---

### 6.3 vabhub_douban_fallback

| 功能 | vabhub_douban_fallback | 当前VabHub | 状态 |
|------|----------------------|-----------|------|
| 豆瓣API | ✅ | ❓ | 需要检查 |
| TMDB回退 | ✅ | ✅ | 已实现 |
| 离线模式 | ✅ | ❓ | 需要检查 |

**结论**: 需要检查当前VabHub的豆瓣支持情况

---

### 6.4 vabhub_gap_patch

| 功能 | vabhub_gap_patch | 当前VabHub | 状态 |
|------|-----------------|-----------|------|
| 前后端对齐检查 | ✅ | ❓ | 需要检查 |
| 端点清单 | ✅ | ❓ | 需要检查 |
| 能力清单 | ✅ | ❓ | 需要检查 |

**结论**: 可以用于检查前后端对齐情况

---

## 📋 七、总结

### 7.1 包的功能

1. **vabhub_douban_fallback**: 豆瓣API回退服务
2. **vabhub_gap_patch**: 前后端对齐检查工具
3. **vabhub_jellyfin_parity**: Jellyfin兼容性（已实现）
4. **vabhub_stream_gateway**: 流媒体网关（已实现类似功能）

### 7.2 集成建议

1. **vabhub_jellyfin_parity**: 无需集成（已实现）
2. **vabhub_stream_gateway**: 可参考HMAC签名实现
3. **vabhub_douban_fallback**: 需要检查当前实现
4. **vabhub_gap_patch**: 可用于检查前后端对齐

---

**文档生成时间**: 2025-01-XX  
**状态**: ✅ 分析完成

