# QuantScope Docker 部署初始化脚本
# 用于新机器部署后的快速初始化

param(
    [switch]$QuickFix,
    [switch]$FullInit,
    [switch]$CheckOnly
)

Write-Host "🚀 QuantScope Docker 部署初始化" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Gray

# 检查 Python 环境
function Test-PythonEnvironment {
    Write-Host "🐍 检查 Python 环境..." -ForegroundColor Yellow
    
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Python 已安装: $pythonVersion" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "❌ Python 未安装或不在 PATH 中" -ForegroundColor Red
        return $false
    }
    
    return $false
}

# 检查 Docker 环境
function Test-DockerEnvironment {
    Write-Host "🐳 检查 Docker 环境..." -ForegroundColor Yellow
    
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker 已安装: $dockerVersion" -ForegroundColor Green
        } else {
            Write-Host "❌ Docker 未安装或未启动" -ForegroundColor Red
            return $false
        }
        
        $composeVersion = docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker Compose 已安装: $composeVersion" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Docker Compose 未安装" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Docker 检查失败" -ForegroundColor Red
        return $false
    }
}

# 检查 Docker 服务状态
function Test-DockerServices {
    Write-Host "🔍 检查 Docker 服务状态..." -ForegroundColor Yellow
    
    try {
        $services = docker-compose -f docker-compose.hub.yml ps --format json | ConvertFrom-Json
        
        if ($services) {
            Write-Host "📋 Docker 服务状态:" -ForegroundColor Cyan
            foreach ($service in $services) {
                $status = if ($service.State -eq "running") { "✅" } else { "❌" }
                Write-Host "   $status $($service.Service): $($service.State)" -ForegroundColor White
            }
            return $true
        } else {
            Write-Host "⚠️ 未找到运行中的服务" -ForegroundColor Yellow
            return $false
        }
    }
    catch {
        Write-Host "❌ 检查 Docker 服务失败: $_" -ForegroundColor Red
        return $false
    }
}

# 启动 Docker 服务
function Start-DockerServices {
    Write-Host "🚀 启动 Docker 服务..." -ForegroundColor Yellow
    
    try {
        Write-Host "正在启动服务，请稍候..." -ForegroundColor Cyan
        docker-compose -f docker-compose.hub.yml up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker 服务启动成功" -ForegroundColor Green
            
            # 等待服务启动
            Write-Host "⏳ 等待服务完全启动..." -ForegroundColor Yellow
            Start-Sleep -Seconds 30
            
            return $true
        } else {
            Write-Host "❌ Docker 服务启动失败" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ 启动 Docker 服务时出错: $_" -ForegroundColor Red
        return $false
    }
}

# 运行快速修复
function Invoke-QuickFix {
    Write-Host "🔧 运行快速登录修复..." -ForegroundColor Yellow
    
    try {
        python scripts/quick_login_fix.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 快速修复完成" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ 快速修复失败" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ 运行快速修复时出错: $_" -ForegroundColor Red
        return $false
    }
}

# 运行完整初始化
function Invoke-FullInit {
    Write-Host "🏗️ 运行完整系统初始化..." -ForegroundColor Yellow
    
    try {
        python scripts/docker_deployment_init.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 完整初始化完成" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ 完整初始化失败" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ 运行完整初始化时出错: $_" -ForegroundColor Red
        return $false
    }
}

# 显示系统状态
function Show-SystemStatus {
    Write-Host "`n📊 系统状态检查" -ForegroundColor Cyan
    Write-Host "-" * 30 -ForegroundColor Gray
    
    # 检查端口占用
    $ports = @(80, 8000, 27017, 6379)
    foreach ($port in $ports) {
        try {
            $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
            if ($connection.TcpTestSucceeded) {
                Write-Host "✅ 端口 $port 正在使用" -ForegroundColor Green
            } else {
                Write-Host "❌ 端口 $port 未使用" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "⚠️ 端口 $port 检查失败" -ForegroundColor Yellow
        }
    }
    
    # 检查配置文件
    $configFiles = @(
        "config/admin_password.json",
        "web/config/users.json",
        ".env"
    )
    
    Write-Host "`n📁 配置文件检查:" -ForegroundColor Cyan
    foreach ($file in $configFiles) {
        if (Test-Path $file) {
            Write-Host "✅ $file 存在" -ForegroundColor Green
        } else {
            Write-Host "❌ $file 不存在" -ForegroundColor Red
        }
    }
}

# 显示使用说明
function Show-Usage {
    Write-Host "`n📖 使用说明:" -ForegroundColor Cyan
    Write-Host "  .\scripts\docker_init.ps1 -QuickFix    # 快速修复登录问题" -ForegroundColor White
    Write-Host "  .\scripts\docker_init.ps1 -FullInit    # 完整系统初始化" -ForegroundColor White
    Write-Host "  .\scripts\docker_init.ps1 -CheckOnly   # 仅检查系统状态" -ForegroundColor White
    Write-Host "  .\scripts\docker_init.ps1              # 交互式选择" -ForegroundColor White
    
    Write-Host "`n🌐 访问地址:" -ForegroundColor Cyan
    Write-Host "  前端应用: http://localhost:80" -ForegroundColor White
    Write-Host "  后端 API: http://localhost:8000" -ForegroundColor White
    Write-Host "  API 文档: http://localhost:8000/docs" -ForegroundColor White
}

# 主函数
function Main {
    # 检查基础环境
    if (-not (Test-PythonEnvironment)) {
        Write-Host "❌ Python 环境检查失败，请先安装 Python" -ForegroundColor Red
        exit 1
    }
    
    if (-not (Test-DockerEnvironment)) {
        Write-Host "❌ Docker 环境检查失败，请先安装 Docker 和 Docker Compose" -ForegroundColor Red
        exit 1
    }
    
    # 根据参数执行不同操作
    if ($CheckOnly) {
        Test-DockerServices
        Show-SystemStatus
        return
    }
    
    if ($QuickFix) {
        # 检查服务状态，如果未运行则启动
        if (-not (Test-DockerServices)) {
            Write-Host "⚠️ Docker 服务未运行，正在启动..." -ForegroundColor Yellow
            if (-not (Start-DockerServices)) {
                Write-Host "❌ 无法启动 Docker 服务" -ForegroundColor Red
                exit 1
            }
        }
        
        Invoke-QuickFix
        Show-SystemStatus
        return
    }
    
    if ($FullInit) {
        # 检查服务状态，如果未运行则启动
        if (-not (Test-DockerServices)) {
            Write-Host "⚠️ Docker 服务未运行，正在启动..." -ForegroundColor Yellow
            if (-not (Start-DockerServices)) {
                Write-Host "❌ 无法启动 Docker 服务" -ForegroundColor Red
                exit 1
            }
        }
        
        Invoke-FullInit
        Show-SystemStatus
        return
    }
    
    # 交互式模式
    Write-Host "`n请选择操作:" -ForegroundColor Cyan
    Write-Host "1. 快速修复登录问题 (推荐)" -ForegroundColor White
    Write-Host "2. 完整系统初始化" -ForegroundColor White
    Write-Host "3. 仅检查系统状态" -ForegroundColor White
    Write-Host "4. 显示使用说明" -ForegroundColor White
    Write-Host "5. 退出" -ForegroundColor White
    
    $choice = Read-Host "`n请输入选择 (1-5)"
    
    switch ($choice) {
        "1" {
            if (-not (Test-DockerServices)) {
                Write-Host "⚠️ Docker 服务未运行，正在启动..." -ForegroundColor Yellow
                if (-not (Start-DockerServices)) {
                    Write-Host "❌ 无法启动 Docker 服务" -ForegroundColor Red
                    exit 1
                }
            }
            Invoke-QuickFix
            Show-SystemStatus
        }
        "2" {
            if (-not (Test-DockerServices)) {
                Write-Host "⚠️ Docker 服务未运行，正在启动..." -ForegroundColor Yellow
                if (-not (Start-DockerServices)) {
                    Write-Host "❌ 无法启动 Docker 服务" -ForegroundColor Red
                    exit 1
                }
            }
            Invoke-FullInit
            Show-SystemStatus
        }
        "3" {
            Test-DockerServices
            Show-SystemStatus
        }
        "4" {
            Show-Usage
        }
        "5" {
            Write-Host "👋 再见！" -ForegroundColor Green
            exit 0
        }
        default {
            Write-Host "❌ 无效选择" -ForegroundColor Red
            Show-Usage
        }
    }
}

# 运行主函数
Main
