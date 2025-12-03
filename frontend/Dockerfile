# VabHub 前端 Dockerfile
# RELEASE-1 R1-2 实现
# 多阶段构建：node 构建，nginx 提供静态文件服务

# ============== Builder 阶段 ==============
FROM node:20-alpine AS builder

WORKDIR /app

# 安装 pnpm
RUN npm install -g pnpm

# 复制依赖文件
COPY package.json pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 构建参数（可在构建时覆盖）
ARG VITE_API_BASE_URL=http://localhost:8000/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# 构建
RUN pnpm run build

# ============== Runtime 阶段 ==============
FROM nginx:alpine AS runtime

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
