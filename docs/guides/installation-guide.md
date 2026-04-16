---
version: cn-0.1.14-preview
last_updated: 2025-01-13
code_compatibility: cn-0.1.14-preview
status: updated
---

# QuantScope 安装配置指导

> **版本说明**: 本文档基于 `cn-0.1.14-preview` 版本编写  
> **最后更新**: 2025-01-13  
> **状态**: ✅ 已更新 - 包含最新的安装和配置步骤

## 📋 目录

1. [系统要求](#系统要求)
2. [环境准备](#环境准备)
3. [项目安装](#项目安装)
4. [环境配置](#环境配置)
5. [数据库配置](#数据库配置)
6. [启动应用](#启动应用)
7. [验证安装](#验证安装)
8. [常见问题](#常见问题)
9. [高级配置](#高级配置)

## 🖥️ 系统要求

### 操作系统支持
- ✅ **Windows 10/11** (推荐)
- ✅ **macOS 10.15+**
- ✅ **Linux (Ubuntu 20.04+, CentOS 8+)**

### 硬件要求
- **CPU**: 4核心以上 (推荐8核心)
- **内存**: 8GB以上 (推荐16GB)
- **存储**: 10GB可用空间
- **网络**: 稳定的互联网连接

### 软件依赖
- **Python**: 3.10+ (必需)
- **Git**: 最新版本
- **Redis**: 6.2+ (可选，用于缓存)
- **MongoDB**: 4.4+ (可选，用于数据存储)

## 🔧 环境准备

### 1. 安装Python 3.10+

#### Windows
```bash
# 下载并安装Python 3.10+
# 访问 https://www.python.org/downloads/
# 确保勾选 "Add Python to PATH"
```

#### macOS
```bash
# 使用Homebrew安装
brew install python@3.10

# 或使用pyenv
pyenv install 3.10.12
pyenv global 3.10.12
```

#### Linux (Ubuntu)
```bash
# 更新包列表
sudo apt update

# 安装Python 3.10
sudo apt install python3.10 python3.10-venv python3.10-pip

# 验证安装
python3.10 --version
```

### 2. 安装Git
```bash
# Windows: 下载Git for Windows
# https://git-scm.com/download/win

# macOS
brew install git

# Linux
sudo apt install git  # Ubuntu
sudo yum install git   # CentOS
```

### 3. 安装uv (推荐的包管理器)
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 验证安装
uv --version
```

## 📦 项目安装

### 1. 克隆项目
```bash
# 克隆项目到本地
git clone https://github.com/your-repo/QuantScope.git
cd QuantScope

# 查看当前版本
cat VERSION
```

### 2. 创建虚拟环境
```bash
# 使用uv创建虚拟环境 (推荐)
uv venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 验证虚拟环境
which python  # 应该指向虚拟环境中的python
```

### 3. 安装依赖

#### 方法1: 使用uv安装 (推荐)
```bash
# 安装核心依赖
uv pip install -e .

# 安装额外依赖
uv pip install yfinance langgraph dashscope

# 验证安装
python -c "import tradingagents; print('安装成功!')"
```

#### 方法2: 使用传统pip
```bash
# 安装核心依赖
pip install -e .

# 安装缺失的依赖包
pip install yfinance langgraph dashscope

# 或一次性安装所有依赖
pip install -r requirements.txt

# 验证安装
python -c "import tradingagents; print('安装成功!')"
```

#### 方法3: 分步安装 (推荐用于解决依赖冲突)
```bash
# 1. 安装基础依赖
pip install streamlit pandas numpy requests plotly

# 2. 安装LLM相关依赖
pip install openai langchain langgraph dashscope

# 3. 安装数据源依赖
pip install yfinance tushare akshare

# 4. 安装数据库依赖 (可选)
pip install redis pymongo

# 5. 安装项目
pip install -e .
```

## ⚙️ 环境配置

### 1. 创建环境变量文件
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
# Windows: notepad .env
# macOS/Linux: nano .env
```

### 2. 配置API密钥

在 `.env` 文件中添加以下配置：

```bash
# ===========================================
# QuantScope 环境配置
# ===========================================

# 基础配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# ===========================================
# LLM API 配置 (选择一个或多个)
# ===========================================

# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 阿里百炼 (DashScope)
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# DeepSeek配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Google AI配置
GOOGLE_API_KEY=your_google_api_key_here

# 百度千帆配置
QIANFAN_ACCESS_KEY=your_qianfan_access_key_here
QIANFAN_SECRET_KEY=your_qianfan_secret_key_here

# 硅基流动配置
SILICONFLOW_API_KEY=your_siliconflow_api_key_here

# ===========================================
# 数据源API配置
# ===========================================

# Tushare配置 (A股数据)
TUSHARE_TOKEN=your_tushare_token_here

# FinnHub配置 (美股数据)
FINNHUB_API_KEY=your_finnhub_api_key_here

# Alpha Vantage配置
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# ===========================================
# 数据库配置 (可选)
# ===========================================

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# MongoDB配置
MONGODB_URI=mongodb://localhost:27017/tradingagents
MONGODB_DATABASE=tradingagents

# ===========================================
# 应用配置
# ===========================================

# Web应用配置
WEB_HOST=localhost
WEB_PORT=8501
WEB_DEBUG=true

# 数据缓存目录
DATA_CACHE_DIR=./data/cache

# 日志配置
LOG_DIR=./logs
LOG_FILE=tradingagents.log
```

### 3. 获取API密钥指南

#### OpenAI API密钥
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册/登录账户
3. 进入 API Keys 页面
4. 创建新的API密钥

#### 阿里百炼 (DashScope)
1. 访问 [阿里云百炼](https://dashscope.aliyun.com/)
2. 注册/登录阿里云账户
3. 开通百炼服务
4. 获取API Key

#### Tushare Token
1. 访问 [Tushare官网](https://tushare.pro/)
2. 注册账户并实名认证
3. 获取Token (免费用户有调用限制)

#### FinnHub API
1. 访问 [FinnHub](https://finnhub.io/)
2. 注册免费账户
3. 获取API Key

## 🗄️ 数据库配置

### Redis配置 (推荐)

#### Windows
```bash
# 下载Redis for Windows
# https://github.com/microsoftarchive/redis/releases

# 或使用Docker
docker run -d --name redis -p 6379:6379 redis:latest
```

#### macOS
```bash
# 使用Homebrew安装
brew install redis

# 启动Redis服务
brew services start redis

# 验证连接
redis-cli ping
```

#### Linux
```bash
# Ubuntu
sudo apt install redis-server

# CentOS
sudo yum install redis

# 启动服务
sudo systemctl start redis
sudo systemctl enable redis
```

### MongoDB配置 (可选)

#### 使用Docker (推荐)
```bash
# 启动MongoDB容器
docker run -d --name mongodb -p 27017:27017 mongo:latest

# 验证连接
docker exec -it mongodb mongosh
```

#### 本地安装
```bash
# 访问MongoDB官网下载安装包
# https://www.mongodb.com/try/download/community

## 🚀 启动应用

### 1. 启动Web应用

#### 方法1: 使用启动脚本 (推荐)
```bash
# 确保虚拟环境已激活
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# 启动Web应用
python start_web.py
```

#### 方法2: 直接启动Streamlit
```bash
# 进入web目录
cd web

# 启动Streamlit应用
streamlit run app.py --server.port 8501
```

#### 方法3: 使用批处理文件 (Windows)
```bash
# 双击运行
start_web.bat
```

### 2. 访问应用
打开浏览器访问: http://localhost:8501

### 3. 首次使用配置

1. **选择LLM提供商**: 在侧边栏选择已配置的LLM提供商
2. **选择模型**: 根据需要选择具体的模型
3. **配置分析参数**: 设置分析日期、股票代码等
4. **开始分析**: 输入股票代码进行测试

## ✅ 验证安装

### 1. 基础功能测试
```bash
# 测试Python环境
python -c "import tradingagents; print('✅ 模块导入成功')"

# 测试依赖包
python -c "import streamlit, pandas, yfinance; print('✅ 依赖包正常')"

# 测试配置文件
python -c "from tradingagents.config import get_config; print('✅ 配置加载成功')"
```

### 2. API连接测试
```bash
# 进入项目目录
cd examples

# 测试LLM连接
python test_llm_connection.py

# 测试数据源连接
python test_data_sources.py
```

### 3. Web应用测试
1. 启动应用后访问 http://localhost:8501
2. 检查侧边栏是否正常显示
3. 尝试选择不同的LLM提供商
4. 输入测试股票代码 (如: AAPL, 000001)

## 🔧 常见问题

### 1. 模块导入错误
```bash
# 问题: ModuleNotFoundError: No module named 'tradingagents'
# 解决方案:
pip install -e .

# 或重新安装
pip uninstall tradingagents
pip install -e .
```

### 2. 虚拟环境问题
```bash
# 问题: 虚拟环境未激活
# 解决方案:
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 验证
which python
```

### 3. 端口占用问题
```bash
# 问题: Port 8501 is already in use
# 解决方案:
streamlit run app.py --server.port 8502

# 或杀死占用进程
# Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8501 | xargs kill -9
```

### 4. API密钥错误
```bash
# 问题: API密钥验证失败
# 解决方案:
1. 检查.env文件中的API密钥格式
2. 确认API密钥有效性
3. 检查网络连接
4. 查看日志文件: logs/tradingagents.log
```

### 5. 数据获取失败
```bash
# 问题: 无法获取股票数据
# 解决方案:
1. 检查网络连接
2. 验证数据源API密钥
3. 检查股票代码格式
4. 查看缓存目录: data/cache
```

## ⚡ 高级配置

### 1. 性能优化

#### 启用Redis缓存
```bash
# 在.env文件中配置Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=true
```

#### 配置并发设置
```python
# 在config/settings.json中调整
{
  "max_workers": 4,
  "request_timeout": 30,
  "cache_ttl": 3600
}
```

### 2. 日志配置

#### 自定义日志级别
```bash
# 在.env文件中设置
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/tradingagents.log
```

#### 结构化日志
```python
# 编辑config/logging.toml
[loggers.tradingagents]
level = "INFO"
handlers = ["console", "file"]
```

### 3. 数据源配置

#### 优先级设置
```python
# 在config/settings.json中配置数据源优先级
{
  "data_sources": {
    "china_stocks": ["tushare", "akshare", "tdx"],
    "us_stocks": ["yfinance", "finnhub", "alpha_vantage"],
    "hk_stocks": ["akshare", "yfinance"]
  }
}
```

### 4. 模型配置

#### 自定义模型参数
```python
# 在config/models.json中配置
{
  "openai": {
    "temperature": 0.1,
    "max_tokens": 4000,
    "timeout": 60
  }
}
```

## 🐳 Docker部署 (可选)

### 1. 构建Docker镜像
```bash
# 构建镜像
docker build -t tradingagents-cn .

# 运行容器
docker run -d \
  --name tradingagents \
  -p 8501:8501 \
  -v $(pwd)/.env:/app/.env \
  tradingagents-cn
```

### 2. 使用Docker Compose
```bash
# 启动完整服务栈
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 📚 下一步

安装完成后，建议阅读以下文档：

1. **[快速开始指南](../QUICK_START.md)** - 了解基本使用方法
2. **[配置管理指南](./config-management-guide.md)** - 深入了解配置选项
3. **[A股分析指南](./a-share-analysis-guide.md)** - A股市场分析教程
4. **[Docker部署指南](./docker-deployment-guide.md)** - 生产环境部署
5. **[故障排除指南](../troubleshooting/)** - 常见问题解决方案

## 🆘 获取帮助

如果遇到问题，可以通过以下方式获取帮助：

- **GitHub Issues**: [提交问题](https://github.com/your-repo/QuantScope/issues)
- **文档**: [查看完整文档](../README.md)
- **社区**: [加入讨论群](https://your-community-link)

---

**祝你使用愉快！** 🎉
```
