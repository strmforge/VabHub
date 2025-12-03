# PowerShell script to move all script files to organized directories

# .bat files to scripts/windows
$batFiles = @(
    "安装依赖并启动.bat",
    "测试登录功能.bat",
    "测试订阅管理.bat",
    "测试环境.bat",
    "创建测试账号.bat",
    "创建admin账号.bat",
    "忽略脚本安装.bat",
    "检查用户.bat",
    "快速启动服务.bat",
    "快速预览.bat",
    "立即启动前端.bat",
    "启动并测试.bat",
    "启动并测试API.bat",
    "启动服务并测试.bat",
    "启动前端-稳定版.bat",
    "启动前端-直接.bat",
    "启动前端-PowerShell.bat",
    "启动前端.bat",
    "启动预览服务.bat",
    "使用短路径启动.bat",
    "手动启动前端.bat",
    "完整修复步骤.bat",
    "修复依赖并启动.bat",
    "运行测试.bat",
    "运行数据库迁移.bat",
    "诊断服务状态.bat",
    "诊断前端问题.bat",
    "执行漫画追更.bat",
    "重新启动服务-双宽带.bat",
    "重置测试密码.bat",
    "start_backend.bat",
    "test_auth.bat"
)

foreach ($file in $batFiles) {
    if (Test-Path $file) {
        Write-Host "Moving $file to scripts/windows/"
        git mv $file "scripts/windows/$file"
    }
}

# .ps1 files
Write-Host "\nMoving PowerShell scripts..."
if (Test-Path "启动前端.ps1") {
    Write-Host "Moving 启动前端.ps1 to scripts/windows/launch_frontend.ps1"
    git mv "启动前端.ps1" "scripts/windows/launch_frontend.ps1"
}

if (Test-Path "backup_and_remove_root_md.ps1") {
    Write-Host "Moving backup_and_remove_root_md.ps1 to scripts/tools/"
    git mv "backup_and_remove_root_md.ps1" "scripts/tools/"
}

# .py files
Write-Host "\nMoving Python scripts..."
if (Test-Path "测试推荐设置和文件上传功能.py") {
    Write-Host "Moving 测试推荐设置和文件上传功能.py to scripts/python/test_recommendation_and_upload.py"
    git mv "测试推荐设置和文件上传功能.py" "scripts/python/test_recommendation_and_upload.py"
}

if (Test-Path "test_video_autoloop.py") {
    Write-Host "Moving test_video_autoloop.py to scripts/python/"
    git mv "test_video_autoloop.py" "scripts/python/"
}

Write-Host "\nAll script files moved successfully!"
