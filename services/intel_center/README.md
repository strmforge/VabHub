# VabHub Intel Center

共享智能大脑，提供别名识别和发布索引查询。

## 功能

- 别名识别（alias_terms）
- 发布索引（release_index / release_sites）
- 规则包管理
- 轻量API查询

## API端点

### GET /v1/rules/latest
获取最新规则包。

### GET /v1/index/{release_key}
获取发布索引。

**路径参数**:
- `release_key`: 发布键

### GET /v1/alias/search
模糊搜索别名。

**查询参数**:
- `q`: 搜索关键词

### GET /v1/alias/resolve
解析别名，返回标准化作品信息。

**查询参数**:
- `q`: 需要解析的原始标题

## 配置

### 环境变量

```env
APP_ENV=production
DATA_DIR=./data
```

## 部署

### Deta.Space部署

1. 创建Deta.Space项目
2. 创建Base：alias/index/rules
3. 部署FastAPI服务
4. Cloudflare反代 intel.hbnetwork.top → Deta

### Docker部署

```bash
docker build -t vabhub-intel-center .
docker run -p 8000:8000 --env-file .env vabhub-intel-center
```

## 数据存储

当前使用文件存储（JSON文件），可替换为：
- Deta Base
- Supabase
- 其他数据库

