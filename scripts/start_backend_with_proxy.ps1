# QuantScope Backend Startup Script with Proxy Configuration
# 启动后端服务，并配置选择性代理

Write-Host "🚀 启动 QuantScope 后端服务..." -ForegroundColor Green
Write-Host ""

# 检查虚拟环境
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "❌ 虚拟环境不存在，请先运行: python -m venv .venv" -ForegroundColor Red
    exit 1
}

# 激活虚拟环境
Write-Host "🔧 激活虚拟环境..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# 加载 .env 文件中的 NO_PROXY 配置
Write-Host "🔧 加载代理配置..." -ForegroundColor Cyan

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    
    # 提取 NO_PROXY 配置
    if ($envContent -match 'NO_PROXY=(.+)') {
        $noProxy = $matches[1].Trim()
        $env:NO_PROXY = $noProxy
        Write-Host "✅ NO_PROXY 已设置: $noProxy" -ForegroundColor Green
    } else {
        # 如果 .env 中没有配置，使用默认值
        $defaultNoProxy = "localhost,127.0.0.1,*.eastmoney.com,*.push2.eastmoney.com,*.gtimg.cn,*.sinaimg.cn,api.tushare.pro,*.baostock.com"
        $env:NO_PROXY = $defaultNoProxy
        Write-Host "⚠️  .env 中未找到 NO_PROXY 配置，使用默认值" -ForegroundColor Yellow
        Write-Host "   默认值: $defaultNoProxy" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ .env 文件不存在" -ForegroundColor Red
    exit 1
}

# 显示当前代理配置
Write-Host ""
Write-Host "📊 当前代理配置:" -ForegroundColor Cyan
Write-Host "   HTTP_PROXY:  $env:HTTP_PROXY" -ForegroundColor Gray
Write-Host "   HTTPS_PROXY: $env:HTTPS_PROXY" -ForegroundColor Gray
Write-Host "   NO_PROXY:    $env:NO_PROXY" -ForegroundColor Gray
Write-Host ""

# 启动后端
Write-Host "🚀 启动后端服务..." -ForegroundColor Green
Write-Host "   访问地址: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API 文档: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

python -m app

