#!/bin/bash
# 设置Fork环境的脚本

set -e

# 配置变量
UPSTREAM_REPO="https://github.com/TauricResearch/TradingAgents.git"
FORK_REPO="https://github.com/hsliuping/TradingAgents.git"
LOCAL_DIR="TradingAgents-Fork"
TRADINGAGENTS_CN_DIR="../TradingAgentsCN"  # 假设QuantScope在上级目录

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 设置TradingAgents Fork开发环境${NC}"
echo "=================================="

# 1. 克隆Fork仓库
echo -e "${YELLOW}📥 克隆Fork仓库...${NC}"
if [ -d "$LOCAL_DIR" ]; then
    echo "目录已存在，删除旧目录..."
    rm -rf "$LOCAL_DIR"
fi

git clone "$FORK_REPO" "$LOCAL_DIR"
cd "$LOCAL_DIR"

# 2. 添加上游仓库
echo -e "${YELLOW}🔗 添加上游仓库...${NC}"
git remote add upstream "$UPSTREAM_REPO"
git remote -v

# 3. 获取最新代码
echo -e "${YELLOW}📡 获取最新代码...${NC}"
git fetch upstream
git fetch origin

# 4. 确保main分支是最新的
echo -e "${YELLOW}🔄 同步main分支...${NC}"
git checkout main
git merge upstream/main
git push origin main

# 5. 创建开发分支
echo -e "${YELLOW}🌿 创建开发分支...${NC}"
git checkout -b feature/intelligent-caching
git push -u origin feature/intelligent-caching

echo -e "${GREEN}✅ Fork环境设置完成！${NC}"
echo ""
echo "下一步："
echo "1. 准备贡献代码"
echo "2. 创建GitHub Issue讨论"
echo "3. 提交Pull Request"
echo ""
echo "当前分支: feature/intelligent-caching"
echo "远程仓库:"
git remote -v
