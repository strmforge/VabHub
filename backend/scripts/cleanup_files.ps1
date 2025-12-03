# 文件整理脚本
# 将项目根目录的临时文件移动到正确位置

$projectRoot = "F:\VabHub项目"
$backendDir = "$projectRoot\VabHub\backend"
$tmpDir = "$backendDir\tmp"

# 切换到项目根目录
Set-Location $projectRoot

Write-Host "=" * 60
Write-Host "文件整理脚本"
Write-Host "=" * 60
Write-Host ""

# 1. 处理数据库文件
Write-Host "[1] 检查数据库文件..."
if (Test-Path "$projectRoot\vabhub.db") {
    if (Test-Path "$backendDir\vabhub.db") {
        Write-Host "  [INFO] backend目录已有vabhub.db"
        Write-Host "  [INFO] 根目录的vabhub.db可能是重复的，建议删除"
        Write-Host "  [WARN] 如果后端服务正在运行，数据库文件可能被锁定"
    } else {
        Write-Host "  [INFO] 移动vabhub.db到backend目录..."
        try {
            Move-Item "$projectRoot\vabhub.db" "$backendDir\vabhub.db" -Force
            Write-Host "  [OK] 已移动vabhub.db到backend目录"
        } catch {
            Write-Host "  [FAIL] 移动失败: $_"
            Write-Host "  [INFO] 可能原因: 数据库文件被后端服务锁定"
            Write-Host "  [INFO] 解决方案: 先停止后端服务，然后手动移动"
        }
    }
} else {
    Write-Host "  [INFO] 根目录没有vabhub.db"
}
Write-Host ""

# 2. 确保tmp目录存在
Write-Host "[2] 检查tmp目录..."
if (-not (Test-Path $tmpDir)) {
    New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
    Write-Host "  [OK] 已创建tmp目录"
} else {
    Write-Host "  [INFO] tmp目录已存在"
}
Write-Host ""

# 3. 移动test_results.json
Write-Host "[3] 移动test_results.json..."
if (Test-Path "$projectRoot\test_results.json") {
    try {
        Move-Item "$projectRoot\test_results.json" "$tmpDir\test_results.json" -Force
        Write-Host "  [OK] 已移动test_results.json到tmp目录"
    } catch {
        Write-Host "  [FAIL] 移动失败: $_"
    }
} else {
    Write-Host "  [INFO] test_results.json不存在"
}
Write-Host ""

# 4. 移动slow_queries_analysis.json
Write-Host "[4] 移动slow_queries_analysis.json..."
if (Test-Path "$projectRoot\slow_queries_analysis.json") {
    try {
        Move-Item "$projectRoot\slow_queries_analysis.json" "$tmpDir\slow_queries_analysis.json" -Force
        Write-Host "  [OK] 已移动slow_queries_analysis.json到tmp目录"
    } catch {
        Write-Host "  [FAIL] 移动失败: $_"
    }
} else {
    Write-Host "  [INFO] slow_queries_analysis.json不存在"
}
Write-Host ""

# 5. 移动cookies.txt
Write-Host "[5] 移动cookies.txt..."
if (Test-Path "$projectRoot\cookies.txt") {
    try {
        Move-Item "$projectRoot\cookies.txt" "$tmpDir\cookies.txt" -Force
        Write-Host "  [OK] 已移动cookies.txt到tmp目录"
    } catch {
        Write-Host "  [FAIL] 移动失败: $_"
    }
} else {
    Write-Host "  [INFO] cookies.txt不存在"
}
Write-Host ""

Write-Host "=" * 60
Write-Host "文件整理完成"
Write-Host "=" * 60

