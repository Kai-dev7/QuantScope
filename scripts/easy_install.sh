#!/bin/bash
# QuantScope 一键安装脚本 (Linux/Mac)
# 功能：自动检测环境、安装依赖、配置API密钥、启动应用

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# 输出函数
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_step() { echo -e "\n${MAGENTA}🔹 $1${NC}"; }

# 显示欢迎信息
show_welcome() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🚀 QuantScope 一键安装向导                         ║
║                                                              ║
║     让AI驱动的股票分析触手可及                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}\n"
}

# 检查Python版本
check_python() {
    print_step "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "未找到Python3，请先安装Python 3.10+"
        print_info "Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
        print_info "CentOS/RHEL: sudo yum install python3 python3-pip"
        print_info "macOS: brew install python@3.10"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_info "发现Python: $python_version"
    
    # 检查版本号
    major=$(echo $python_version | cut -d. -f1)
    minor=$(echo $python_version | cut -d. -f2)
    
    if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
        print_success "Python版本符合要求 (需要3.10+)"
        return 0
    else
        print_error "Python版本过低，需要3.10或更高版本"
        exit 1
    fi
}

# 检查网络连接
check_network() {
    print_step "检查网络连接..."
    
    if curl -s --head --request GET https://pypi.org | grep "200 OK" > /dev/null; then
        print_success "网络连接正常"
        return 0
    else
        print_warning "网络连接可能存在问题，但将继续安装"
        return 0
    fi
}

# 创建虚拟环境
create_venv() {
    print_step "创建Python虚拟环境..."
    
    if [ -d ".venv" ]; then
        print_info "虚拟环境已存在"
        return 0
    fi
    
    python3 -m venv .venv
    print_success "虚拟环境创建成功"
}

# 激活虚拟环境
activate_venv() {
    print_info "激活虚拟环境..."
    source .venv/bin/activate
    print_success "虚拟环境已激活"
}

# 升级pip
upgrade_pip() {
    print_step "升级pip..."
    python -m pip install --upgrade pip --quiet
    print_success "pip升级完成"
}

# 安装依赖
install_dependencies() {
    print_step "安装项目依赖..."
    print_info "这可能需要几分钟时间，请耐心等待..."
    
    # 尝试多个镜像源
    mirrors=(
        "https://mirrors.aliyun.com/pypi/simple"
        "https://pypi.tuna.tsinghua.edu.cn/simple"
        "https://pypi.org/simple"
    )
    
    for mirror in "${mirrors[@]}"; do
        print_info "尝试使用镜像: $mirror"
        if pip install -e . -i $mirror --quiet; then
            print_success "依赖安装成功"
            return 0
        else
            print_warning "镜像 $mirror 安装失败，尝试下一个..."
        fi
    done
    
    print_error "所有镜像都安装失败"
    exit 1
}

# 选择LLM提供商
select_llm_provider() {
    print_step "选择大语言模型提供商..."
    echo ""
    echo -e "${YELLOW}请选择您要使用的LLM提供商（至少选择一个）：${NC}"
    echo ""
    echo "1. DeepSeek V3      - 推荐 ⭐ (性价比最高，中文优化)"
    echo "2. 通义千问         - 推荐 ⭐ (国产稳定，响应快)"
    echo "3. Google Gemini    - 推荐 ⭐ (免费额度大，能力强)"
    echo "4. OpenAI GPT       - 可选 (通用能力强，成本较高)"
    echo "5. 跳过配置         - 稍后手动配置"
    echo ""
    
    read -p "请输入选项 (1-5): " choice
    
    case $choice in
        1)
            PROVIDER="DeepSeek"
            API_KEY_NAME="DEEPSEEK_API_KEY"
            API_URL="https://platform.deepseek.com/"
            ;;
        2)
            PROVIDER="通义千问"
            API_KEY_NAME="DASHSCOPE_API_KEY"
            API_URL="https://dashscope.aliyun.com/"
            ;;
        3)
            PROVIDER="Google Gemini"
            API_KEY_NAME="GOOGLE_API_KEY"
            API_URL="https://aistudio.google.com/"
            ;;
        4)
            PROVIDER="OpenAI"
            API_KEY_NAME="OPENAI_API_KEY"
            API_URL="https://platform.openai.com/"
            ;;
        5)
            PROVIDER=""
            return 0
            ;;
        *)
            print_warning "无效选项，默认选择DeepSeek"
            PROVIDER="DeepSeek"
            API_KEY_NAME="DEEPSEEK_API_KEY"
            API_URL="https://platform.deepseek.com/"
            ;;
    esac
}

# 配置API密钥
configure_api_key() {
    if [ -z "$PROVIDER" ]; then
        print_info "跳过API密钥配置"
        return 0
    fi
    
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  配置 $PROVIDER API密钥${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}📝 获取API密钥步骤：${NC}"
    echo "   1. 访问: $API_URL"
    echo "   2. 注册/登录账号"
    echo "   3. 创建API密钥"
    echo "   4. 复制密钥并粘贴到下方"
    echo ""
    
    read -p "请输入API密钥 (或按Enter跳过): " API_KEY_VALUE
    
    if [ -z "$API_KEY_VALUE" ]; then
        print_warning "未配置API密钥，稍后可手动配置"
        API_KEY_VALUE=""
    fi
}

# 生成.env文件
generate_env_file() {
    print_step "生成配置文件..."
    
    # 检查是否使用最小化模式
    MINIMAL_MODE=false
    if ! command -v docker &> /dev/null; then
        MINIMAL_MODE=true
    fi
    
    cat > .env << EOF
# QuantScope 配置文件
# 由一键安装脚本自动生成
# 生成时间: $(date '+%Y-%m-%d %H:%M:%S')

# ==================== LLM配置 ====================
EOF
    
    if [ -n "$API_KEY_VALUE" ]; then
        echo "$API_KEY_NAME=$API_KEY_VALUE" >> .env
    else
        cat >> .env << EOF

# 请手动配置至少一个LLM提供商的API密钥：
# DEEPSEEK_API_KEY=sk-your-key-here
# DASHSCOPE_API_KEY=sk-your-key-here
# GOOGLE_API_KEY=AIzaSy-your-key-here
EOF
    fi
    
    cat >> .env << EOF


# ==================== 数据库配置 ====================
EOF
    
    if [ "$MINIMAL_MODE" = true ]; then
        cat >> .env << EOF

# 极简模式：使用文件存储，无需数据库
MONGODB_ENABLED=false
REDIS_ENABLED=false
EOF
    else
        cat >> .env << EOF

# 标准模式：启用数据库（需要Docker或手动安装）
MONGODB_ENABLED=false
REDIS_ENABLED=false
# 如需启用，请设置为true并确保数据库服务运行
EOF
    fi
    
    cat >> .env << EOF


# ==================== 可选配置 ====================
# 数据源（可选）
# TUSHARE_TOKEN=your-token-here
# FINNHUB_API_KEY=your-key-here

# 日志级别
TRADINGAGENTS_LOG_LEVEL=INFO

# 应用端口
STREAMLIT_PORT=8501
EOF
    
    print_success "配置文件已生成: .env"
}

# 启动应用
start_application() {
    print_step "启动应用..."
    
    print_info "正在启动Web界面..."
    print_info "浏览器将自动打开 http://localhost:8501"
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  🎉 安装完成！应用正在启动...${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    print_info "按 Ctrl+C 停止应用"
    echo ""
    
    python start_web.py
}

# 主函数
main() {
    show_welcome
    
    # 检查环境
    check_python
    check_network
    
    # 安装依赖
    create_venv
    activate_venv
    upgrade_pip
    install_dependencies
    
    # 配置API密钥
    if [ ! -f ".env" ] || [ "$1" = "--reconfigure" ]; then
        select_llm_provider
        configure_api_key
        generate_env_file
    else
        print_info "配置文件已存在，跳过配置步骤"
        print_info "如需重新配置，请运行: ./scripts/easy_install.sh --reconfigure"
    fi
    
    # 启动应用
    start_application
}

# 运行主函数
main "$@"

