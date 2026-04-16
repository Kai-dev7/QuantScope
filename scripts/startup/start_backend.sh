#!/bin/bash
# QuantScope Backend Launcher for Linux/macOS
# 快速启动脚本

echo "🚀 QuantScope Backend Launcher"
echo "=================================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python is not installed or not in PATH"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 检查Python版本
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.8+ is required, found $PYTHON_VERSION"
    exit 1
fi

# 检查app目录是否存在
if [ ! -d "app" ]; then
    echo "❌ app directory not found"
    exit 1
fi

echo "✅ Environment check passed"
echo "🔄 Starting backend server..."
echo "--------------------------------------------------"

# 启动后端服务
$PYTHON_CMD -m app

if [ $? -ne 0 ]; then
    echo "❌ Failed to start server"
    exit 1
fi

echo "🛑 Server stopped"
