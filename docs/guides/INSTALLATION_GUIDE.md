# QuantScope 详细安装配置指南

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-支持-blue.svg)](https://www.docker.com/)

> 🎯 **本指南适用于**: 初学者到高级用户，涵盖Docker和本地安装两种方式
> 
> 📋 **预计时间**: Docker安装 15-30分钟 | 本地安装 30-60分钟

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [Docker安装（推荐）](#docker安装推荐)
- [本地安装](#本地安装)
- [环境配置](#环境配置)
- [API密钥配置](#api密钥配置)
- [验证安装](#验证安装)
- [常见问题](#常见问题)
- [故障排除](#故障排除)

## 🔧 系统要求

### 最低配置
- **操作系统**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **内存**: 4GB RAM（推荐 8GB+）
- **存储**: 5GB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **操作系统**: Windows 11, macOS 12+, Ubuntu 20.04+
- **内存**: 16GB RAM
- **存储**: 20GB 可用空间（SSD推荐）
- **CPU**: 4核心以上

### 软件依赖

#### Docker安装方式
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 4.0+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+

#### 本地安装方式
- [Python](https://www.python.org/downloads/) 3.10+
- [Git](https://git-scm.com/downloads) 2.30+
- [Node.js](https://nodejs.org/) 16+ (可选，用于某些功能)

## 🚀 快速开始

### 方式一：Docker一键启动（推荐新手）

```bash
# 1. 克隆项目
git clone https://github.com/hsliuping/QuantScope.git
cd QuantScope

# 2. 复制环境配置
cp .env.example .env

# 3. 编辑API密钥（必须）
# Windows: notepad .env
# macOS/Linux: nano .env

# 4. 启动服务
docker-compose up -d

# 5. 访问应用
# 打开浏览器访问: http://localhost:8501
```

### 方式二：本地快速启动

```bash
# 1. 克隆项目
git clone https://github.com/hsliuping/QuantScope.git
cd QuantScope

# 2. 创建虚拟环境
python -m venv env

# 3. 激活虚拟环境
# Windows:
env\Scripts\activate
# macOS/Linux:
source env/bin/activate

# 4. 升级pip (重要！避免安装错误)
python -m pip install --upgrade pip

# 5. 安装依赖
pip install -e .

# 6. 复制环境配置
cp .env.example .env

# 7. 编辑API密钥（必须）
# Windows: notepad .env
# macOS/Linux: nano .env

# 8. 启动应用
python start_web.py
```

## 🐳 Docker安装（推荐）

Docker安装是最简单、最稳定的方式，适合所有用户。

### 步骤1：安装Docker

#### Windows
1. 下载 [Docker Desktop for Windows](https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe)
2. 运行安装程序，按提示完成安装
3. 重启计算机
4. 启动Docker Desktop，等待启动完成

#### macOS
1. 下载 [Docker Desktop for Mac](https://desktop.docker.com/mac/main/amd64/Docker.dmg)
2. 拖拽到Applications文件夹
3. 启动Docker Desktop，按提示完成设置

#### Linux (Ubuntu/Debian)
```bash
# 更新包索引
sudo apt update

# 安装必要的包
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 将用户添加到docker组（可选）
sudo usermod -aG docker $USER
```

### 步骤2：验证Docker安装

```bash
# 检查Docker版本
docker --version
docker-compose --version

# 测试Docker运行
docker run hello-world
```

### 步骤3：克隆项目

```bash
# 克隆项目到本地
git clone https://github.com/hsliuping/QuantScope.git

# 进入项目目录
cd QuantScope

# 查看项目结构
ls -la
```

### 步骤4：配置环境变量

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑环境配置文件
# Windows: notepad .env
# macOS: open -e .env
# Linux: nano .env
```

**重要**: 必须配置至少一个AI模型的API密钥，否则无法正常使用。

### 步骤5：启动Docker服务

```bash
# 启动所有服务（后台运行）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志（可选）
docker-compose logs -f web
```

### 步骤6：访问应用

打开浏览器访问以下地址：

- **主应用**: http://localhost:8501
- **Redis管理**: http://localhost:8081 (用户名/密码: admin/tradingagents123)
- **MongoDB管理**: http://localhost:8082 (可选，需要启动管理服务)

## 💻 本地安装

本地安装提供更多的控制和自定义选项，适合开发者和高级用户。

### 步骤1：安装Python

#### Windows
1. 访问 [Python官网](https://www.python.org/downloads/windows/)
2. 下载Python 3.10或更高版本
3. 运行安装程序，**确保勾选"Add Python to PATH"**
4. 验证安装：
   ```cmd
   python --version
   pip --version
   ```

#### macOS
```bash
# 使用Homebrew安装（推荐）
brew install python@3.10

# 或者下载官方安装包
# 访问 https://www.python.org/downloads/macos/
```

#### Linux (Ubuntu/Debian)
```bash
# 更新包列表
sudo apt update

# 安装Python 3.10+
sudo apt install python3.10 python3.10-venv python3.10-pip

# 创建软链接（可选）
sudo ln -sf /usr/bin/python3.10 /usr/bin/python
sudo ln -sf /usr/bin/pip3 /usr/bin/pip
```

### 步骤2：克隆项目

```bash
# 克隆项目
git clone https://github.com/hsliuping/QuantScope.git
cd QuantScope
```

### 步骤3：创建虚拟环境

```bash
# 创建虚拟环境
python -m venv env

# 激活虚拟环境
# Windows:
env\Scripts\activate

# macOS/Linux:
source env/bin/activate

# 验证虚拟环境
which python  # 应该显示虚拟环境中的python路径
```

### 步骤4：安装依赖

```bash
# 升级pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 验证关键包安装
python -c "import streamlit; print('Streamlit安装成功')"
python -c "import openai; print('OpenAI安装成功')"
python -c "import akshare; print('AKShare安装成功')"
```

### 步骤5：配置环境

```bash
# 复制环境配置
cp .env.example .env

# 编辑配置文件
# Windows: notepad .env
# macOS: open -e .env  
# Linux: nano .env
```

### 步骤6：可选数据库安装

#### MongoDB (推荐)
```bash
# Windows: 下载MongoDB Community Server
# https://www.mongodb.com/try/download/community

# macOS:
brew tap mongodb/brew
brew install mongodb-community

# Ubuntu/Debian:
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install mongodb-org
```

#### Redis (推荐)
```bash
# Windows: 下载Redis for Windows
# https://github.com/microsoftarchive/redis/releases

# macOS:
brew install redis

# Ubuntu/Debian:
sudo apt install redis-server
```

### 步骤7：启动应用

```bash
# 确保虚拟环境已激活
# Windows: env\Scripts\activate
# macOS/Linux: source env/bin/activate

# 启动Streamlit应用
python -m streamlit run web/app.py

# 或使用启动脚本
# Windows: start_web.bat
# macOS/Linux: ./start_web.sh
```

## ⚙️ 环境配置

### .env文件详细配置

创建`.env`文件并配置以下参数：

```bash
# =============================================================================
# AI模型配置 (至少配置一个)
# =============================================================================

# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，自定义API端点

# DeepSeek配置 (推荐，性价比高)
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 通义千问配置 (阿里云)
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# Google Gemini配置
GOOGLE_API_KEY=your_google_api_key_here

# =============================================================================
# 数据源配置
# =============================================================================

# Tushare配置 (A股数据，推荐)
TUSHARE_TOKEN=your_tushare_token_here

# FinnHub配置 (美股数据)
FINNHUB_API_KEY=your_finnhub_api_key_here

# =============================================================================
# 数据库配置 (可选，提升性能)
# =============================================================================

# MongoDB配置
MONGODB_ENABLED=false  # 设置为true启用MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=your_mongodb_password
MONGODB_DATABASE=tradingagents

# Redis配置
REDIS_ENABLED=false  # 设置为true启用Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0

# =============================================================================
# 应用配置
# =============================================================================

# 日志级别
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# 缓存配置
CACHE_ENABLED=true
CACHE_TTL=3600  # 缓存过期时间（秒）

# 网络配置
REQUEST_TIMEOUT=30  # 网络请求超时时间（秒）
MAX_RETRIES=3  # 最大重试次数
```

### 配置优先级说明

1. **必须配置**: 至少一个AI模型API密钥
2. **推荐配置**: Tushare Token（A股分析）
3. **可选配置**: 数据库（提升性能）
4. **高级配置**: 自定义参数

## 🔑 API密钥配置

### 获取AI模型API密钥

#### 1. DeepSeek (推荐，性价比最高)
1. 访问 [DeepSeek开放平台](https://platform.deepseek.com/)
2. 注册账号并完成实名认证
3. 进入控制台 → API密钥
4. 创建新的API密钥
5. 复制密钥到`.env`文件的`DEEPSEEK_API_KEY`

**费用**: 约 ¥1/万tokens，新用户送免费额度

#### 2. 通义千问 (国产，稳定)
1. 访问 [阿里云DashScope](https://dashscope.aliyun.com/)
2. 登录阿里云账号
3. 开通DashScope服务
4. 获取API-KEY
5. 复制到`.env`文件的`DASHSCOPE_API_KEY`

**费用**: 按量计费，有免费额度

#### 3. OpenAI (功能强大)
1. 访问 [OpenAI平台](https://platform.openai.com/)
2. 注册账号并绑定支付方式
3. 进入API Keys页面
4. 创建新的API密钥
5. 复制到`.env`文件的`OPENAI_API_KEY`

**费用**: 按使用量计费，需要美元支付

#### 4. Google Gemini (免费额度大)
1. 访问 [Google AI Studio](https://aistudio.google.com/)
2. 登录Google账号
3. 创建API密钥
4. 复制到`.env`文件的`GOOGLE_API_KEY`

**费用**: 有较大免费额度

### 获取数据源API密钥

#### Tushare (A股数据，强烈推荐)
1. 访问 [Tushare官网](https://tushare.pro/)
2. 注册账号
3. 获取Token
4. 复制到`.env`文件的`TUSHARE_TOKEN`

**费用**: 免费，有积分限制

#### FinnHub (美股数据)
1. 访问 [FinnHub](https://finnhub.io/)
2. 注册免费账号
3. 获取API密钥
4. 复制到`.env`文件的`FINNHUB_API_KEY`

**费用**: 免费版有限制，付费版功能更全

### API密钥安全建议

1. **不要提交到Git**: 确保`.env`文件在`.gitignore`中
2. **定期轮换**: 定期更换API密钥
3. **权限最小化**: 只给必要的权限
4. **监控使用**: 定期检查API使用情况

## ✅ 验证安装

### 基础功能验证

```bash
# 1. 检查Python环境
python --version  # 应该显示3.10+

# 2. 检查关键依赖
python -c "import streamlit; print('✅ Streamlit正常')"
python -c "import openai; print('✅ OpenAI正常')"
python -c "import akshare; print('✅ AKShare正常')"

# 3. 检查环境变量
python -c "import os; print('✅ API密钥已配置' if os.getenv('DEEPSEEK_API_KEY') else '❌ 需要配置API密钥')"
```

### Web界面验证

1. 启动应用后访问 http://localhost:8501
2. 检查页面是否正常加载
3. 尝试输入股票代码（如：000001）
4. 选择分析师团队
5. 点击"开始分析"按钮
6. 观察是否有错误信息

### Docker环境验证

```bash
# 检查容器状态
docker-compose ps

# 查看应用日志
docker-compose logs web

# 检查数据库连接
docker-compose logs mongodb
docker-compose logs redis
```

### 功能测试

#### 测试A股分析
```bash
# 在Web界面中测试
股票代码: 000001
市场类型: A股
研究深度: 3级
分析师: 市场分析师 + 基本面分析师
```

#### 测试美股分析
```bash
股票代码: AAPL
市场类型: 美股
研究深度: 3级
分析师: 市场分析师 + 基本面分析师
```

#### 测试港股分析
```bash
股票代码: 0700.HK
市场类型: 港股
研究深度: 3级
分析师: 市场分析师 + 基本面分析师
```

## ❓ 常见问题

### Q1: 启动时提示"ModuleNotFoundError"
**A**: 依赖包未正确安装
```bash
# 解决方案
pip install -r requirements.txt --upgrade
```

### Q2: API密钥配置后仍然报错
**A**: 检查密钥格式和权限
```bash
# 检查环境变量是否生效
python -c "import os; print(os.getenv('DEEPSEEK_API_KEY'))"

# 重新启动应用
```

### Q3: Docker启动失败
**A**: 检查Docker服务和端口占用
```bash
# 检查Docker状态
docker info

# 检查端口占用
netstat -an | grep 8501

# 重新构建镜像
docker-compose build --no-cache
```

### Q4: 分析过程中断或失败
**A**: 检查网络连接和API配额
- 确保网络连接稳定
- 检查API密钥余额
- 查看应用日志获取详细错误信息

### Q5: 数据获取失败
**A**: 检查数据源配置
- 确认Tushare Token有效
- 检查股票代码格式
- 验证网络访问权限

### Q6: 中文显示乱码
**A**: 检查系统编码设置
```bash
# Windows: 设置控制台编码
chcp 65001

# Linux/macOS: 检查locale
locale
```

### Q7: 内存不足错误
**A**: 调整分析参数
- 降低研究深度
- 减少分析师数量
- 增加系统内存

### Q8: 报告导出失败
**A**: 检查导出依赖
```bash
# 安装pandoc (PDF导出需要)
# Windows: 下载安装包
# macOS: brew install pandoc
# Linux: sudo apt install pandoc
```

## 🔧 故障排除

### 日志查看

#### Docker环境
```bash
# 查看应用日志
docker-compose logs -f web

# 查看数据库日志
docker-compose logs mongodb
docker-compose logs redis

# 查看所有服务日志
docker-compose logs
```

#### 本地环境
```bash
# 查看应用日志
tail -f logs/tradingagents.log

# 启动时显示详细日志
python -m streamlit run web/app.py --logger.level=debug
```

### 网络问题

#### 代理设置
```bash
# 设置HTTP代理
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# 或在.env文件中设置
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

#### DNS问题
```bash
# 使用公共DNS
# Windows: 设置网络适配器DNS为8.8.8.8
# Linux: 编辑/etc/resolv.conf
nameserver 8.8.8.8
nameserver 8.8.4.4
```

### 性能优化

#### 内存优化
```bash
# 在.env中设置
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
STREAMLIT_SERVER_MAX_MESSAGE_SIZE=200
```

#### 缓存优化
```bash
# 启用Redis缓存
REDIS_ENABLED=true
CACHE_TTL=7200  # 增加缓存时间
```

### 数据库问题

#### MongoDB连接失败
```bash
# 检查MongoDB服务
# Windows: services.msc 查找MongoDB
# Linux: sudo systemctl status mongod
# macOS: brew services list | grep mongodb

# 重置MongoDB
docker-compose down
docker volume rm tradingagents_mongodb_data
docker-compose up -d mongodb
```

#### Redis连接失败
```bash
# 检查Redis服务
redis-cli ping

# 重置Redis
docker-compose down
docker volume rm tradingagents_redis_data
docker-compose up -d redis
```

### 权限问题

#### Linux/macOS权限
```bash
# 给脚本执行权限
chmod +x start_web.sh

# 修复文件所有权
sudo chown -R $USER:$USER .
```

#### Windows权限
- 以管理员身份运行命令提示符
- 检查防火墙设置
- 确保Python在PATH中

### 重置安装

#### 完全重置Docker环境
```bash
# 停止所有服务
docker-compose down

# 删除所有数据
docker volume prune
docker system prune -a

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

#### 重置本地环境
```bash
# 删除虚拟环境
rm -rf env

# 重新创建
python -m venv env
source env/bin/activate  # Linux/macOS
# 或 env\Scripts\activate  # Windows

# 重新安装依赖
pip install -r requirements.txt
```

## 📞 获取帮助

### 官方资源
- **项目主页**: https://github.com/hsliuping/QuantScope
- **文档中心**: https://www.tradingagents.cn/
- **问题反馈**: https://github.com/hsliuping/QuantScope/issues

### 社区支持
- **微信群**: 扫描README中的二维码
- **QQ群**: 详见项目主页
- **邮件支持**: 见项目联系方式

### 贡献代码
欢迎提交Pull Request和Issue，帮助改进项目！

---

🎉 **恭喜！** 您已成功安装QuantScope。开始您的AI股票分析之旅吧！
