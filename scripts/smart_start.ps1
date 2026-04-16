# QuantScope 智能Docker启动脚本 (Windows PowerShell版本)
# 功能：自动判断是否需要重新构建Docker镜像
# 使用：powershell -ExecutionPolicy Bypass -File scripts\smart_start.ps1
# 
# 判断逻辑：
# 1. 检查是否存在tradingagents-cn镜像
# 2. 如果镜像不存在 -> 执行构建启动
# 3. 如果镜像存在但代码有变化 -> 执行构建启动  
# 4. 如果镜像存在且代码无变化 -> 快速启动

Write-Host "=== QuantScope Docker 智能启动脚本 ===" -ForegroundColor Green
Write-Host "适用环境: Windows PowerShell" -ForegroundColor Cyan

# 检查是否有镜像
$imageExists = docker images | Select-String "tradingagents-cn"

if ($imageExists) {
    Write-Host "✅ 发现现有镜像" -ForegroundColor Green
    
    # 检查代码是否有变化（简化版本）
    $gitStatus = git status --porcelain
    if ([string]::IsNullOrEmpty($gitStatus)) {
        Write-Host "📦 代码无变化，使用快速启动" -ForegroundColor Blue
        docker-compose up -d
    } else {
        Write-Host "🔄 检测到代码变化，重新构建" -ForegroundColor Yellow
        docker-compose up -d --build
    }
} else {
    Write-Host "🏗️ 首次运行，构建镜像" -ForegroundColor Yellow
    docker-compose up -d --build
}

Write-Host "🚀 启动完成！" -ForegroundColor Green
Write-Host "Web界面: http://localhost:8501" -ForegroundColor Cyan
Write-Host "Redis管理: http://localhost:8081" -ForegroundColor Cyan