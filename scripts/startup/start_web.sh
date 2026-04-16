#!/bin/bash
# QuantScope Web应用启动脚本

echo "🚀 启动QuantScope Web应用..."
echo

# 激活虚拟环境
source env/bin/activate

# 检查项目是否已安装
if ! python -c "import tradingagents" 2>/dev/null; then
    echo "📦 安装项目到虚拟环境..."
    pip install -e .
fi

# 启动Streamlit应用
python start_web.py

echo "按任意键退出..."
read -n 1
