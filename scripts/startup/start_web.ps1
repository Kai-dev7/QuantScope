# QuantScope Web应用启动脚本

Write-Host "🚀 启动QuantScope Web应用..." -ForegroundColor Green
Write-Host ""

# 激活虚拟环境
& ".\env\Scripts\Activate.ps1"

# 检查项目是否已安装
try {
    python -c "import tradingagents" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "📦 安装项目到虚拟环境..." -ForegroundColor Yellow
        pip install -e .
    }
} catch {
    Write-Host "📦 安装项目到虚拟环境..." -ForegroundColor Yellow
    pip install -e .
}

# 启动Streamlit应用
python start_web.py

Write-Host "按任意键退出..." -ForegroundColor Yellow
Read-Host
