# 系统更新Docker支持说明

## 问题解答

**用户疑问**：为什么是从GitHub仓库拉取更新而不是Docker？

**回答**：这是一个很好的问题！之前的实现确实只支持源代码部署方式的更新。现在已经增强为**自动检测部署方式**，支持两种更新模式：

1. **Docker部署** → 拉取Docker镜像并重启容器
2. **源代码部署** → 从GitHub拉取代码更新

## 实现原理

### 1. 自动检测部署方式

系统启动时会自动检测运行环境：

```python
def _detect_deployment_type(self) -> DeploymentType:
    # 方法1: 检查/.dockerenv文件
    if Path("/.dockerenv").exists():
        return DeploymentType.DOCKER
    
    # 方法2: 检查环境变量
    if os.getenv("DOCKER_CONTAINER") == "true":
        return DeploymentType.DOCKER
    
    # 方法3: 检查cgroup（Linux）
    if "docker" in cgroup_content:
        return DeploymentType.DOCKER
    
    # 方法4: 检查Git仓库
    if Path(".git").exists():
        return DeploymentType.SOURCE
```

### 2. 根据部署方式选择更新策略

```python
async def update_system(self):
    if self.deployment_type == DeploymentType.DOCKER:
        return await self._update_docker_system()  # Docker更新
    elif self.deployment_type == DeploymentType.SOURCE:
        return await self._update_source_system()  # Git更新
```

### 3. Docker更新流程

```python
async def _update_docker_system(self):
    # 1. 获取镜像名称
    image_name = await self._get_docker_image_name(container_name)
    
    # 2. 拉取新镜像
    await docker_pull(image_name)
    
    # 3. 重启容器
    await docker_restart(container_name)
```

## 使用场景

### 场景1：Docker部署（生产环境）

```yaml
# docker-compose.yml
services:
  vabhub-backend:
    image: vabhub/vabhub:latest
    container_name: vabhub-backend
    environment:
      - CONTAINER_NAME=vabhub-backend
      - DOCKER_CONTAINER=true
```

**更新流程**：
1. 系统检测到Docker环境
2. 执行`docker pull vabhub/vabhub:latest`
3. 执行`docker restart vabhub-backend`
4. 容器自动使用新镜像重启

### 场景2：源代码部署（开发环境）

```bash
# 直接运行Python代码
cd /path/to/vabhub
python main.py
```

**更新流程**：
1. 系统检测到Git仓库
2. 执行`git fetch origin`
3. 执行`git checkout <tag>`或`git pull origin main`
4. 需要手动重启服务

## 配置说明

### Docker部署配置

在`docker-compose.yml`中配置：

```yaml
services:
  vabhub-backend:
    image: vabhub/vabhub:latest
    container_name: vabhub-backend
    environment:
      # 必需：容器名称（用于重启）
      - CONTAINER_NAME=vabhub-backend
      
      # 可选：镜像名称（如果无法自动检测）
      - IMAGE_NAME=vabhub/vabhub:latest
      
      # 可选：标识Docker环境（如果/.dockerenv不存在）
      - DOCKER_CONTAINER=true
```

### 源代码部署配置

无需特殊配置，系统会自动检测`.git`目录。

## 更新模式

两种部署方式都支持相同的更新模式：

- **never** - 从不更新
- **release** - 仅更新到发行版本（Git标签/Docker标签）
- **dev** - 更新到开发版本（main分支/latest标签）

## 注意事项

### Docker更新

1. **需要Docker权限**：容器内需要能够执行`docker`命令
2. **需要挂载Docker socket**：如果从容器内更新，需要挂载`/var/run/docker.sock`
3. **容器名称**：确保`CONTAINER_NAME`环境变量正确设置

### 源代码更新

1. **Git仓库**：需要是Git仓库才能更新
2. **网络连接**：需要能够访问GitHub
3. **本地修改**：更新可能会覆盖本地未提交的修改

## 推荐配置

### 生产环境（Docker）

```yaml
# docker-compose.yml
services:
  vabhub-backend:
    image: vabhub/vabhub:latest
    container_name: vabhub-backend
    environment:
      - CONTAINER_NAME=vabhub-backend
      - DOCKER_CONTAINER=true
    # 如果需要从容器内更新，挂载Docker socket
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
```

### 开发环境（源代码）

```bash
# 直接运行，系统会自动检测Git仓库
cd /path/to/vabhub
python main.py
```

## 总结

现在系统更新功能已经支持：

✅ **自动检测部署方式**（Docker vs 源代码）  
✅ **Docker镜像更新**（生产环境推荐）  
✅ **Git代码更新**（开发环境常用）  
✅ **统一的更新接口**（用户无需关心底层实现）

这样可以让系统更新功能适用于各种部署场景，提供更好的用户体验！

