#!/bin/bash
# QuantScope 容器内初始化脚本
# 在Docker容器内执行系统初始化

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}QuantScope 容器内初始化${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检查是否在容器内
if [ ! -f "/.dockerenv" ]; then
    echo -e "${RED}❌ 此脚本必须在Docker容器内执行！${NC}"
    echo -e "${YELLOW}正确用法:${NC}"
    echo -e "${BLUE}  docker exec -it tradingagents-backend bash scripts/container_init.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 检测到Docker容器环境${NC}"
echo ""

# 步骤1: 检查Python环境
echo -e "${YELLOW}步骤1: 检查Python环境...${NC}"
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo -e "${GREEN}  ✅ Python版本: $(python --version)${NC}"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}  ✅ Python版本: $(python3 --version)${NC}"
else
    echo -e "${RED}  ❌ Python未找到！${NC}"
    exit 1
fi
echo ""

# 步骤2: 检查必要的Python包
echo -e "${YELLOW}步骤2: 检查Python依赖...${NC}"
required_packages=("pymongo" "redis" "pydantic")
missing_packages=()

for package in "${required_packages[@]}"; do
    if $PYTHON_CMD -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}  ✅ $package 已安装${NC}"
    else
        echo -e "${RED}  ❌ $package 未安装${NC}"
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    echo -e "${RED}  缺少必要的Python包，请检查容器镜像${NC}"
    exit 1
fi
echo ""

# 步骤3: 检查MongoDB连接
echo -e "${YELLOW}步骤3: 检查MongoDB连接...${NC}"
if $PYTHON_CMD -c "
from pymongo import MongoClient
import os
try:
    # 从环境变量获取MongoDB配置
    mongo_host = os.getenv('MONGODB_HOST', 'mongodb')
    mongo_port = int(os.getenv('MONGODB_PORT', '27017'))
    client = MongoClient(mongo_host, mongo_port, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('MongoDB连接成功')
except Exception as e:
    print(f'MongoDB连接失败: {e}')
    exit(1)
" 2>/dev/null; then
    echo -e "${GREEN}  ✅ MongoDB连接正常${NC}"
else
    echo -e "${RED}  ❌ MongoDB连接失败${NC}"
    echo -e "${YELLOW}  请检查MongoDB服务是否正常运行${NC}"
    exit 1
fi
echo ""

# 步骤4: 运行快速登录修复
echo -e "${YELLOW}步骤4: 运行快速登录修复...${NC}"
if [ -f "scripts/quick_login_fix.py" ]; then
    echo -e "${BLUE}  执行快速登录修复脚本...${NC}"
    if $PYTHON_CMD scripts/quick_login_fix.py; then
        echo -e "${GREEN}  ✅ 快速登录修复完成${NC}"
    else
        echo -e "${RED}  ❌ 快速登录修复失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}  ⚠️  快速登录修复脚本不存在，跳过${NC}"
fi
echo ""

# 步骤5: 运行认证系统迁移
echo -e "${YELLOW}步骤5: 运行认证系统迁移...${NC}"
if [ -f "scripts/simple_auth_migration.py" ]; then
    echo -e "${BLUE}  执行认证系统迁移脚本...${NC}"
    if $PYTHON_CMD scripts/simple_auth_migration.py; then
        echo -e "${GREEN}  ✅ 认证系统迁移完成${NC}"
    else
        echo -e "${YELLOW}  ⚠️  认证系统迁移可能已完成或出现问题${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  认证系统迁移脚本不存在，跳过${NC}"
fi
echo ""

# 步骤6: 验证初始化结果
echo -e "${YELLOW}步骤6: 验证初始化结果...${NC}"
if $PYTHON_CMD -c "
from pymongo import MongoClient
import os
try:
    mongo_host = os.getenv('MONGODB_HOST', 'mongodb')
    mongo_port = int(os.getenv('MONGODB_PORT', '27017'))
    client = MongoClient(mongo_host, mongo_port)
    db = client.tradingagents
    
    # 检查用户集合
    users_count = db.users.count_documents({})
    print(f'用户数量: {users_count}')
    
    # 检查管理员用户
    admin_user = db.users.find_one({'username': 'admin'})
    if admin_user:
        print('管理员用户存在')
    else:
        print('管理员用户不存在')
        
except Exception as e:
    print(f'验证失败: {e}')
    exit(1)
"; then
    echo -e "${GREEN}  ✅ 数据库验证通过${NC}"
else
    echo -e "${RED}  ❌ 数据库验证失败${NC}"
fi
echo ""

# 完成
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}🎉 容器内初始化完成！${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${BLUE}默认登录信息:${NC}"
echo -e "${GREEN}  用户名: admin${NC}"
echo -e "${GREEN}  密码: admin123 或 1234567${NC}"
echo ""
echo -e "${BLUE}访问地址:${NC}"
echo -e "${GREEN}  前端: http://your-server-ip:80${NC}"
echo -e "${GREEN}  后端API: http://your-server-ip:8000${NC}"
echo -e "${GREEN}  API文档: http://your-server-ip:8000/docs${NC}"
echo ""
echo -e "${YELLOW}建议:${NC}"
echo -e "${YELLOW}  1. 立即登录并修改默认密码${NC}"
echo -e "${YELLOW}  2. 检查系统功能是否正常${NC}"
echo ""
