# 本地自检脚本说明

## 概述

VabHub 项目提供了一套本地自检脚本，用于在开发过程中快速检查代码质量和构建状态。这些脚本模拟了未来 CI/CD 流水线中的检查步骤。

## 脚本列表

### 后端自检脚本
- **文件**: `scripts/dev_check_backend.sh`
- **功能**: 执行后端代码的测试检查
- **检查项目**:
  - pytest 单元测试

### 前端自检脚本
- **文件**: `scripts/dev_check_frontend.sh`
- **功能**: 执行前端代码的质量检查
- **检查项目**:
  - ESLint 代码规范检查
  - TypeScript 类型检查
  - 构建检查

## 使用方法

### 运行后端自检
```bash
bash scripts/dev_check_backend.sh
```

### 运行前端自检
```bash
bash scripts/dev_check_frontend.sh
```

### 运行完整自检
```bash
bash scripts/dev_check_backend.sh
bash scripts/dev_check_frontend.sh
```

## 前置要求

### 后端检查要求
- Python 3.8+
- pytest (可通过 `pip install pytest` 安装)

### 前端检查要求
- Node.js 16+
- pnpm (可通过 `npm install -g pnpm` 安装)
- 前端依赖 (在 frontend 目录运行 `pnpm install`)

## 脚本特性

1. **自动目录切换**: 脚本会自动切换到项目根目录执行
2. **错误处理**: 使用 `set -e` 确保脚本在遇到错误时立即退出
3. **工具检查**: 脚本会检查所需工具是否已安装，未安装时给出友好提示
4. **分阶段输出**: 每个检查阶段都有清晰的标题和状态输出

## CI/CD 集成

### GitHub Actions 集成

项目已配置 GitHub Actions 工作流，在以下事件触发时自动执行检查：
- **push** 到任意分支
- **pull_request** 到任意分支

工作流文件：`.github/workflows/ci.yml`

### 本地与云端一致性

GitHub Actions 使用与本地相同的自检脚本，确保本地和云端检查结果一致：
- 后端检查：`scripts/dev_check_backend.sh`
- 前端检查：`scripts/dev_check_frontend.sh`

### 开发建议

在提交代码前，建议先在本地运行自检脚本：
```bash
# 提交前本地检查
bash scripts/dev_check_backend.sh
bash scripts/dev_check_frontend.sh
```

这样可以提前发现潜在问题，确保 CI 流水线能够顺利通过。

## 注意事项

- 脚本设计为在项目根目录执行
- 如果当前代码存在测试失败或构建错误，脚本会正常退出并显示错误信息
- 脚本本身不会修改任何业务代码，只执行检查操作