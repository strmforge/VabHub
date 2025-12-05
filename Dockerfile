# VabHub All-in-One Dockerfile
# CI-DOCKER-ONE-IMAGE-1 实现
# 多阶段构建：前端 + 后端 → 单一运行镜像

# ============== Stage 1: 前端构建 ==============
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 安装 pnpm
RUN npm install -g pnpm

# 复制依赖文件
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY frontend/ .

# 构建参数 - API 使用相对路径，因为前后端在同一容器
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# 构建前端
RUN pnpm run build

# ============== Stage 2: 后端依赖构建 ==============
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ============== Stage 3: 最终运行镜像 ==============
FROM python:3.11-slim AS runtime

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制虚拟环境
COPY --from=backend-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制后端代码
COPY backend/ ./backend/

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./frontend_dist/

# 创建必要目录
RUN mkdir -p /app/data /app/logs /config

# 创建非 root 用户
RUN useradd -m -u 1000 vabhub && \
    chown -R vabhub:vabhub /app /config

USER vabhub

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    TZ=Asia/Shanghai \
    # 前端静态文件路径
    FRONTEND_DIST_PATH=/app/frontend_dist

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 工作目录切换到 backend
WORKDIR /app/backend

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
