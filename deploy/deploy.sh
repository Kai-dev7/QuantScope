#!/usr/bin/env bash
# QuantScope 腾讯云部署脚本
# 在腾讯云服务器上运行，或通过 CI/CD SSH 远程执行
#
# 使用方式:
#   bash deploy/deploy.sh                    # 交互式
#   bash deploy/deploy.sh --non-interactive  # 自动部署（用于 CI/CD）
#
set -euo pipefail

# ═══════════════════════════════════════════════════════════
# 配置区域（根据你的服务器修改）
# ═══════════════════════════════════════════════════════════
APP_DIR="/opt/QuantScope"
GIT_REPO="${GIT_REPO:-https://github.com/<your-username>/QuantScope.git}"
GIT_BRANCH="${GIT_BRANCH:-release}"
SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/quantscope_deploy}"
LOG_FILE="/var/log/quantscope-deploy.log"

# ═══════════════════════════════════════════════════════════
# 颜色输出
# ═══════════════════════════════════════════════════════════
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}   $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ═══════════════════════════════════════════════════════════
# 前置检查
# ═══════════════════════════════════════════════════════════
preflight_check() {
    log_info "执行前置检查..."

    # 检查是否为 root
    if [[ $EUID -ne 0 ]]; then
        log_error "必须以 root 身份运行此脚本"
        exit 1
    fi

    # 检查操作系统
    if [[ ! -f /etc/debian_version ]]; then
        log_warn "此脚本针对 Debian/Ubuntu 测试，其他发行版可能需要调整"
    fi

    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi

    # 检查 pip
    if ! python3 -m pip --version &> /dev/null; then
        log_error "pip 未安装"
        exit 1
    fi

    log_ok "前置检查通过"
}

# ═══════════════════════════════════════════════════════════
# 安装依赖
# ═══════════════════════════════════════════════════════════
install_dependencies() {
    log_info "安装系统依赖..."

    export DEBIAN_FRONTEND=noninteractive

    apt-get update -qq
    apt-get install -y -qq \
        curl \
        wget \
        git \
        nginx \
        certbot \
        python3-certbot-nginx \
        redis-server \
        build-essential \
        python3-dev \
        uvicorn \
        gunicorn \
        2>&1 | tail -5

    # 启动 Redis
    systemctl enable redis-server
    systemctl start redis-server

    # 配置 Redis 密码
    if ! grep -q "^requirepass" /etc/redis/redis.conf 2>/dev/null; then
        echo "requirepass tradingagents123" >> /etc/redis/redis.conf
        systemctl restart redis-server
    fi

    log_ok "系统依赖安装完成"
}

# ═══════════════════════════════════════════════════════════
# 部署应用
# ═══════════════════════════════════════════════════════════
deploy_app() {
    log_info "部署 QuantScope 到 $APP_DIR ..."

    # 创建目录
    mkdir -p "$APP_DIR/logs" "$APP_DIR/data" "$APP_DIR/config"

    # 如果是 Git 仓库则拉取
    if [[ -d "$APP_DIR/.git" ]]; then
        log_info "更新现有 Git 仓库..."
        cd "$APP_DIR"
        git fetch origin "$GIT_BRANCH"
        git checkout "$GIT_BRANCH"
        git pull origin "$GIT_BRANCH"
    else
        log_info "克隆 Git 仓库..."
        git clone -b "$GIT_BRANCH" "$GIT_REPO" "$APP_DIR"
    fi

    log_ok "代码部署完成"
}

# ═══════════════════════════════════════════════════════════
# 安装 Python 依赖
# ═══════════════════════════════════════════════════════════
install_python_deps() {
    log_info "安装 Python 依赖..."

    cd "$APP_DIR"

    # 使用阿里云镜像加速
    pip install --upgrade pip \
        -i https://mirrors.aliyun.com/pypi/simple/ \
        --quiet

    pip install -e . \
        gunicorn \
        uvicorn[standard] \
        httptools \
        uvloop \
        -i https://mirrors.aliyun.com/pypi/simple/ \
        --quiet

    log_ok "Python 依赖安装完成"
}

# ═══════════════════════════════════════════════════════════
# 配置 Systemd 服务
# ═══════════════════════════════════════════════════════════
setup_systemd() {
    log_info "配置 Systemd 服务..."

    # 复制服务文件
    cp "$APP_DIR/deploy/quantscope.service" /etc/systemd/system/quantscope.service

    # 重新加载 systemd
    systemctl daemon-reload
    systemctl enable quantscope

    log_ok "Systemd 服务配置完成"
}

# ═══════════════════════════════════════════════════════════
# 配置 Nginx
# ═══════════════════════════════════════════════════════════
setup_nginx() {
    log_info "配置 Nginx..."

    # 复制 Nginx 配置
    cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/quantscope
    ln -sf /etc/nginx/sites-available/quantscope /etc/nginx/sites-enabled/quantscope
    rm -f /etc/nginx/sites-enabled/default

    # 测试配置
    nginx -t

    # 启动 Nginx
    systemctl enable nginx
    systemctl reload nginx

    log_ok "Nginx 配置完成"
}

# ═══════════════════════════════════════════════════════════
# 获取 SSL 证书
# ═══════════════════════════════════════════════════════════
setup_ssl() {
    log_info "获取 Let's Encrypt SSL 证书..."

    local domain="${DOMAIN:-app.510168.xyz}"
    local email="${SSL_EMAIL:-}"

    if [[ -z "$email" ]]; then
        read -rp "请输入用于 Let's Encrypt 的邮箱地址: " email
    fi

    certbot --nginx -d "$domain" -d "api.${domain#*.}" \
        --noninteractive \
        --agree-tos \
        --email "$email" \
        --redirect

    # 自动续期
    systemctl enable certbot.timer
    systemctl start certbot.timer

    log_ok "SSL 证书配置完成"
}

# ═══════════════════════════════════════════════════════════
# 启动服务
# ═══════════════════════════════════════════════════════════
start_services() {
    log_info "启动服务..."

    # 启动后端
    systemctl restart quantscope

    # 等待启动
    sleep 5

    # 健康检查
    if curl -sf http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
        log_ok "后端启动成功"
    else
        log_error "后端启动失败，查看日志: journalctl -u quantscope -n 50"
        exit 1
    fi

    log_ok "所有服务启动完成"
}

# ═══════════════════════════════════════════════════════════
# 回滚
# ═══════════════════════════════════════════════════════════
rollback() {
    log_warn "执行回滚..."
    systemctl stop quantscope
    git -C "$APP_DIR" checkout HEAD~1
    systemctl start quantscope
    log_info "回滚完成"
}

# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════
main() {
    local mode="interactive"

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --non-interactive)
                mode="non-interactive"
                shift
                ;;
            --rollback)
                rollback
                exit 0
                ;;
            --help)
                echo "用法: $0 [选项]"
                echo "  --non-interactive  非交互模式（用于 CI/CD）"
                echo "  --rollback        回滚到上一个版本"
                echo "  --help            显示此帮助"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done

    log_info "══════════════════════════════════════════"
    log_info "  QuantScope 腾讯云部署脚本"
    log_info "══════════════════════════════════════════"
    echo

    preflight_check
    install_dependencies
    deploy_app
    install_python_deps
    setup_systemd
    setup_nginx
    start_services

    echo
    log_ok "══════════════════════════════════════════"
    log_ok "  部署完成！"
    log_ok "══════════════════════════════════════════"
    log_info "访问地址: https://app.510168.xyz"
    log_info "API 文档: https://api.510168.xyz/docs"
    log_info ""
    log_info "常用命令:"
    log_info "  查看状态:  systemctl status quantscope"
    log_info "  查看日志:  journalctl -u quantscope -f"
    log_info "  重启服务:  systemctl restart quantscope"
}

main "$@"