# REPO-SCRIPTS-ORGANIZE-1_PLAN

## 根目录脚本初始清单

### .bat 文件
- 安装依赖并启动.bat
- 测试登录功能.bat
- 测试订阅管理.bat
- 测试环境.bat
- 创建测试账号.bat
- 创建admin账号.bat
- 忽略脚本安装.bat
- 检查用户.bat
- 快速启动服务.bat
- 快速预览.bat
- 立即启动前端.bat
- 启动并测试.bat
- 启动并测试API.bat
- 启动服务并测试.bat
- 启动前端-稳定版.bat
- 启动前端-直接.bat
- 启动前端-PowerShell.bat
- 启动前端.bat
- 启动预览服务.bat
- 使用短路径启动.bat
- 手动启动前端.bat
- 完整修复步骤.bat
- 修复依赖并启动.bat
- 运行测试.bat
- 运行数据库迁移.bat
- 诊断服务状态.bat
- 诊断前端问题.bat
- 执行漫画追更.bat
- 重新启动服务-双宽带.bat
- 重置测试密码.bat
- start_backend.bat
- test_auth.bat

### .ps1 文件
- 启动前端.ps1
- backup_and_remove_root_md.ps1

### .py 文件
- 测试推荐设置和文件上传功能.py
- test_video_autoloop.py

## 规划的 scripts 目录结构

```
scripts/
├── windows/          # 所有 Windows .bat / .ps1 脚本
├── python/           # 测试 / 辅助用 Python 脚本
└── tools/            # 仓库维护/运维类工具脚本
```

## 脚本移动计划

### Windows 批处理脚本（.bat）
- 全部移动到 `scripts/windows/`

### PowerShell 脚本（.ps1）
- 启动前端.ps1 → `scripts/windows/launch_frontend.ps1`
- backup_and_remove_root_md.ps1 → `scripts/tools/backup_and_remove_root_md.ps1`

### Python 测试脚本（.py）
- 测试推荐设置和文件上传功能.py → `scripts/python/test_recommendation_and_upload.py`
- test_video_autoloop.py → `scripts/python/test_video_autoloop.py`

## 文档更新计划

- 更新 README.md、GETTING_STARTED.md 等文档中的脚本路径
- 为 scripts 目录编写 README.md
- 更新 SSoT 文档，记录脚本归档里程碑
- 在预发布检查中添加根目录脚本检查项