# QuantScope 用户密码管理工具 (PowerShell版本)
param(
    [Parameter(Position=0)]
    [string]$Command,
    
    [Parameter(Position=1)]
    [string]$Username,
    
    [Parameter(Position=2)]
    [string]$Password,
    
    [Parameter(Position=3)]
    [string]$Role = "user"
)

# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🔧 QuantScope 用户密码管理工具" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# 检查Python是否可用
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ 错误: 未找到Python，请确保Python已安装并添加到PATH" -ForegroundColor Red
    Read-Host "按Enter键继续"
    exit 1
}

# 获取脚本目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManagerScript = Join-Path $ScriptDir "user_password_manager.py"

# 检查管理脚本是否存在
if (-not (Test-Path $ManagerScript)) {
    Write-Host "❌ 错误: 找不到用户管理脚本 $ManagerScript" -ForegroundColor Red
    Read-Host "按Enter键继续"
    exit 1
}

# 如果没有参数，显示帮助
if (-not $Command) {
    Write-Host ""
    Write-Host "使用方法:" -ForegroundColor Yellow
    Write-Host "  .\user_manager.ps1 list                              - 列出所有用户" -ForegroundColor White
    Write-Host "  .\user_manager.ps1 change-password [用户名] [新密码]   - 修改用户密码" -ForegroundColor White
    Write-Host "  .\user_manager.ps1 create-user [用户名] [密码] [角色]   - 创建新用户" -ForegroundColor White
    Write-Host "  .\user_manager.ps1 delete-user [用户名]               - 删除用户" -ForegroundColor White
    Write-Host "  .\user_manager.ps1 reset                             - 重置为默认配置" -ForegroundColor White
    Write-Host ""
    Write-Host "示例:" -ForegroundColor Yellow
    Write-Host "  .\user_manager.ps1 list" -ForegroundColor Green
    Write-Host "  .\user_manager.ps1 change-password admin newpass123" -ForegroundColor Green
    Write-Host "  .\user_manager.ps1 create-user testuser pass123 user" -ForegroundColor Green
    Write-Host "  .\user_manager.ps1 delete-user testuser" -ForegroundColor Green
    Write-Host "  .\user_manager.ps1 reset" -ForegroundColor Green
    Write-Host ""
    Read-Host "按Enter键继续"
    exit 0
}

# 构建参数列表
$args = @($Command)
if ($Username) { $args += $Username }
if ($Password) { $args += $Password }
if ($Role -and $Command -eq "create-user") { $args += "--role"; $args += $Role }

# 执行Python脚本
try {
    & python $ManagerScript @args
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Read-Host "按Enter键继续"
    }
} catch {
    Write-Host "❌ 执行失败: $_" -ForegroundColor Red
    Read-Host "按Enter键继续"
    exit 1
}