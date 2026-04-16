# QuantScope v1.0.0-preview 安装指南

> **版本**: v1.0.0-preview  
> **最后更新**: 2025-11-10  
> **状态**: ✅ 最新版本

## 📋 目录

- [部署方式选择](#部署方式选择)
- [方式一：绿色版（推荐新手）](#方式一绿色版推荐新手)
- [方式二：Docker版（推荐生产环境）](#方式二docker版推荐生产环境)
- [方式三：本地代码版（推荐开发者）](#方式三本地代码版推荐开发者)
- [首次使用配置](#首次使用配置)
- [常见问题](#常见问题)

---

## 🎯 部署方式选择

QuantScope 提供三种部署方式，请根据您的需求选择：

| 部署方式 | 适用场景 | 优点 | 缺点 | 难度 |
|---------|---------|------|------|------|
| **🟢 绿色版** | 快速体验、个人使用 | 开箱即用、无需配置环境 | 仅支持 Windows | ⭐ 简单 |
| **🐳 Docker版** | 生产环境、多用户 | 跨平台、易维护、隔离性好 | 需要学习 Docker | ⭐⭐ 中等 |
| **💻 本地代码版** | 开发、定制、学习 | 灵活、可调试、可定制 | 环境配置复杂 | ⭐⭐⭐ 较难 |

### 快速决策

- **我是新手，只想快速体验** → 选择 [绿色版](#方式一绿色版推荐新手)
- **我要部署到服务器，多人使用** → 选择 [Docker版](#方式二docker版推荐生产环境)
- **我是开发者，想研究代码** → 选择 [本地代码版](#方式三本地代码版推荐开发者)
- **我用的是 Mac/Linux** → 选择 [Docker版](#方式二docker版推荐生产环境) 或 [本地代码版](#方式三本地代码版推荐开发者)

---

## 方式一：绿色版（推荐新手）

### 📦 特点

- ✅ **免安装**：解压即用，无需安装 Python、MongoDB、Redis
- ✅ **便携式**：可放在 U 盘或移动硬盘中
- ✅ **一键启动**：双击启动脚本即可
- ⚠️ **仅支持 Windows 10/11 (64位)**

### 🖥️ 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| **操作系统** | Windows 10 (64位) | Windows 11 (64位) |
| **CPU** | 双核处理器 | 四核或更高 |
| **内存** | 4GB RAM | 8GB RAM 或更高 |
| **磁盘空间** | 5GB 可用空间 | 10GB 可用空间 |
| **网络** | 需要联网 | 稳定的网络连接 |

### 📥 下载与安装

#### 1. 下载安装包

访问以下任一渠道下载最新版本：

- **GitHub Releases**: [https://github.com/hsliuping/QuantScope/releases](https://github.com/hsliuping/QuantScope/releases)
- **百度网盘**: 关注公众号 "QuantScope" 获取下载链接
- **阿里云盘**: 关注公众号 "QuantScope" 获取下载链接

文件名格式：`TradingAgentsCN-Portable-v1.0.0-preview.zip` 或 `.7z`

#### 2. 解压安装包

1. 将下载的压缩包解压到任意目录
2. **建议路径不包含中文和空格**，例如：
   ```
   D:\TradingAgentsCN-portable
   ```

3. 解压后的目录结构：
   ```
   TradingAgentsCN-portable/
   ├── app/                    # 后端应用代码
   ├── tradingagents/          # 核心库代码
   ├── frontend/               # 前端代码
   ├── vendors/                # 第三方依赖
   │   ├── mongodb/            # MongoDB 数据库
   │   ├── redis/              # Redis 缓存
   │   ├── nginx/              # Nginx 服务器
   │   └── python/             # Python 环境
   ├── data/                   # 数据目录
   ├── logs/                   # 日志目录
   ├── config/                 # 配置文件
   ├── scripts/                # 脚本目录
   ├── .env                    # 环境变量配置
   ├── start_all.ps1           # 启动脚本
   └── README.md               # 说明文档
   ```

#### 3. 配置 API 密钥

在启动前，需要配置至少一个 LLM API 密钥：

1. 用记事本打开 `.env` 文件
2. 配置以下任一 API 密钥：

```env
# 阿里百炼（推荐，性价比高）
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# DeepSeek（推荐，价格便宜）
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Google AI（推荐，免费额度）
GOOGLE_API_KEY=your_google_api_key_here

# OpenAI（可选）
OPENAI_API_KEY=your_openai_api_key_here
```

**如何获取 API 密钥？**
- **阿里百炼**: [https://dashscope.console.aliyun.com/](https://dashscope.console.aliyun.com/)
- **DeepSeek**: [https://platform.deepseek.com/](https://platform.deepseek.com/)
- **Google AI**: [https://aistudio.google.com/](https://aistudio.google.com/)
- **OpenAI**: [https://platform.openai.com/](https://platform.openai.com/)

#### 4. 启动应用

1. 以**管理员身份**运行 PowerShell
2. 进入安装目录：
   ```powershell
   cd D:\TradingAgentsCN-portable
   ```

3. 运行启动脚本：
   ```powershell
   powershell -ExecutionPolicy Bypass -File start_all.ps1
   ```

4. 等待所有服务启动（约 30-60 秒）

5. 看到以下提示表示启动成功：
   ```
   ✅ MongoDB 已启动
   ✅ Redis 已启动
   ✅ 后端服务已启动
   ✅ 前端服务已启动
   
   🎉 QuantScope 已成功启动！
   
   📱 访问地址:
      前端: http://localhost:5173
      后端: http://localhost:8000
      API文档: http://localhost:8000/docs
   ```

6. 打开浏览器访问 `http://localhost:5173`

#### 5. 首次登录

默认管理员账号：
- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **重要**: 首次登录后请立即修改密码！

### 🛑 停止应用

1. 在 PowerShell 中按 `Ctrl+C` 停止服务
2. 或运行停止脚本：
   ```powershell
   powershell -ExecutionPolicy Bypass -File stop_all.ps1
   ```

### 📚 详细文档

更多详细信息请参考：
- [绿色版完整使用手册](./portable-installation-guide.md)
- [绿色版端口配置说明](https://mp.weixin.qq.com/s/o5QdNuh2-iKkIHzJXCj7vQ)

---

## 方式二：Docker版（推荐生产环境）

### 🐳 特点

- ✅ **跨平台**：支持 Windows、macOS、Linux
- ✅ **隔离性好**：不影响系统环境
- ✅ **易于维护**：一键更新、备份、恢复
- ✅ **生产就绪**：适合多用户、长期运行
- ✅ **多架构支持**：支持 x86_64 和 ARM64（Apple Silicon、树莓派）

### 🖥️ 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| **操作系统** | Windows 10/macOS 10.15/Ubuntu 20.04 | 最新版本 |
| **CPU** | 双核处理器 | 四核或更高 |
| **内存** | 4GB RAM | 8GB RAM 或更高 |
| **磁盘空间** | 10GB 可用空间 | 20GB 可用空间 |
| **Docker** | 20.0+ | 最新版本 |
| **Docker Compose** | 2.0+ | 最新版本 |

### 📥 安装 Docker

#### Windows

1. 下载 Docker Desktop：[https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. 安装并启动 Docker Desktop
3. 验证安装：
   ```powershell
   docker --version
   docker-compose --version
   ```

#### macOS

```bash
# 使用 Homebrew 安装
brew install --cask docker

# 启动 Docker Desktop

# 验证安装
docker --version
docker-compose --version
```

#### Linux (Ubuntu/Debian)

```bash
# 更新包索引
sudo apt update

# 安装 Docker
sudo apt install docker.io docker-compose

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到 docker 组
sudo usermod -aG docker $USER

# 验证安装
docker --version
docker-compose --version
```

### 🚀 部署步骤

#### 方法 A：使用 Docker Hub 镜像（推荐）

1. **创建项目目录**：
   ```bash
   mkdir tradingagents-cn
   cd tradingagents-cn
   ```

2. **下载 docker-compose.yml**：
   ```bash
   # 从 GitHub 下载
   curl -O https://raw.githubusercontent.com/hsliuping/QuantScope/main/docker-compose.yml
   
   # 或手动创建（见下方配置）
   ```

3. **创建 .env 文件**：
   ```bash
   # 复制示例配置
   curl -O https://raw.githubusercontent.com/hsliuping/QuantScope/main/.env.example
   mv .env.example .env
   
   # 编辑配置
   nano .env  # 或使用其他编辑器
   ```

4. **配置 API 密钥**（编辑 `.env` 文件）：
   ```env
   # 至少配置一个 LLM API 密钥
   DASHSCOPE_API_KEY=your_dashscope_api_key_here
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   ```

5. **启动服务**：
   ```bash
   docker-compose up -d
   ```

6. **查看日志**：
   ```bash
   docker-compose logs -f
   ```

7. **访问应用**：
   - 前端: `http://localhost:5173`
   - 后端: `http://localhost:8000`
   - API文档: `http://localhost:8000/docs`

#### 方法 B：从源码构建

1. **克隆代码**：
   ```bash
   git clone https://github.com/hsliuping/QuantScope.git
   cd QuantScope
   ```

2. **配置环境变量**：
   ```bash
   cp .env.example .env
   nano .env  # 编辑配置
   ```

3. **构建并启动**：
   ```bash
   docker-compose up -d --build
   ```

### 🔄 更新应用

```bash
# 拉取最新镜像
docker-compose pull

# 重启服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 🛑 停止应用

```bash
# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器和数据卷（⚠️ 会删除所有数据）
docker-compose down -v
```

### 📚 详细文档

更多详细信息请参考：
- [Docker 部署完整指南](./docker-deployment-guide.md)
- [从 Docker Hub 更新镜像](https://mp.weixin.qq.com/s/WKYhW8J80Watpg8K6E_dSQ)

---

## 方式三：本地代码版（推荐开发者）

### 💻 特点

- ✅ **完全控制**：可以修改代码、调试、定制功能
- ✅ **学习研究**：适合学习项目架构和实现
- ✅ **开发环境**：适合参与项目开发
- ⚠️ **配置复杂**：需要手动配置 Python、MongoDB、Redis 等环境

### 🖥️ 系统要求

| 项目 | 版本要求 |
|------|---------|
| **Python** | 3.10+ (必需) |
| **Git** | 最新版本 |
| **MongoDB** | 4.4+ (必需) |
| **Redis** | 6.2+ (必需) |
| **Node.js** | 18+ (前端开发需要) |

### 📥 环境准备

#### 1. 安装 Python 3.10+

**Windows**:
```powershell
# 下载并安装 Python 3.10+
# 访问 https://www.python.org/downloads/
# 确保勾选 "Add Python to PATH"

# 验证安装
python --version
```

**macOS**:
```bash
# 使用 Homebrew 安装
brew install python@3.10

# 验证安装
python3.10 --version
```

**Linux (Ubuntu)**:
```bash
# 安装 Python 3.10
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-pip

# 验证安装
python3.10 --version
```

#### 2. 安装 MongoDB

**Windows**:
```powershell
# 下载 MongoDB Community Server
# https://www.mongodb.com/try/download/community

# 安装后启动服务
net start MongoDB
```

**macOS**:
```bash
# 使用 Homebrew 安装
brew tap mongodb/brew
brew install mongodb-community

# 启动服务
brew services start mongodb-community
```

**Linux (Ubuntu)**:
```bash
# 导入公钥
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# 添加源
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# 安装
sudo apt update
sudo apt install -y mongodb-org

# 启动服务
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### 3. 安装 Redis

**Windows**:
```powershell
# 下载 Redis for Windows
# https://github.com/microsoftarchive/redis/releases

# 或使用 WSL2 安装 Linux 版本
```

**macOS**:
```bash
# 使用 Homebrew 安装
brew install redis

# 启动服务
brew services start redis
```

**Linux (Ubuntu)**:
```bash
# 安装 Redis
sudo apt update
sudo apt install redis-server

# 启动服务
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 🚀 安装步骤

#### 1. 克隆代码

```bash
git clone https://github.com/hsliuping/QuantScope.git
cd QuantScope
```

#### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv env

# 激活虚拟环境
# Windows
env\Scripts\activate

# macOS/Linux
source env/bin/activate
```

#### 3. 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

#### 4. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
# Windows: notepad .env
# macOS/Linux: nano .env
```

配置内容：
```env
# MongoDB 配置
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=tradingagents

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM API 密钥（至少配置一个）
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

#### 5. 初始化数据库

```bash
# 导入初始配置
python scripts/import_config_and_create_user.py

# 创建默认管理员账号
# 用户名: admin
# 密码: admin123
```

#### 6. 启动后端服务

```bash
# 启动 FastAPI 后端
python -m app

# 或使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 7. 启动前端服务（可选）

如果需要开发前端：

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 8. 访问应用

- 后端 API: `http://localhost:8000`
- API 文档: `http://localhost:8000/docs`
- 前端（开发模式）: `http://localhost:5173`

### 📚 详细文档

更多详细信息请参考：
- [本地安装完整指南](./installation-guide.md)
- [开发环境配置](../development/setup.md)

---

## 首次使用配置

无论使用哪种部署方式，首次使用都需要进行以下配置：

### 1. 登录系统

默认管理员账号：
- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **重要**: 首次登录后请立即修改密码！

### 2. 配置 LLM 模型

1. 登录后进入 **配置管理** → **大模型配置**
2. 检查已配置的模型是否正常
3. 可以添加更多模型或修改现有配置

### 3. 配置数据源（可选）

如果需要使用 Tushare 等数据源：

1. 进入 **配置管理** → **数据源配置**
2. 配置 Tushare Token：
   - 注册账号：[https://tushare.pro/register](https://tushare.pro/register)
   - 获取 Token：[https://tushare.pro/user/token](https://tushare.pro/user/token)
3. 启用数据源

### 4. 开始分析

1. 进入 **股票分析** 页面
2. 输入股票代码（如：600519、00700.HK、AAPL）
3. 选择分析参数
4. 点击 **开始分析**

---

## 常见问题

### Q1: 启动失败，提示端口被占用

**问题**: `Error: Port 8000 is already in use`

**解决方案**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

或修改 `.env` 文件中的端口配置。

### Q2: MongoDB 连接失败

**问题**: `pymongo.errors.ServerSelectionTimeoutError`

**解决方案**:
1. 检查 MongoDB 是否正在运行
2. 检查 `.env` 中的 `MONGODB_URL` 配置
3. 检查防火墙设置

### Q3: API 密钥无效

**问题**: `Invalid API key`

**解决方案**:
1. 检查 `.env` 文件中的 API 密钥是否正确
2. 确认 API 密钥有足够的额度
3. 检查 API 密钥是否过期

### Q4: 前端无法访问后端

**问题**: 前端显示 `Network Error`

**解决方案**:
1. 检查后端服务是否正常运行
2. 检查防火墙设置
3. 检查前端配置中的 API 地址

### Q5: Docker 容器启动失败

**问题**: `docker-compose up` 失败

**解决方案**:
```bash
# 查看详细日志
docker-compose logs

# 重新构建
docker-compose up -d --build --force-recreate

# 清理并重启
docker-compose down -v
docker-compose up -d
```

---

## 📞 获取帮助

如果遇到问题，可以通过以下方式获取帮助：

1. **查看文档**: [docs/](../)
2. **GitHub Issues**: [https://github.com/hsliuping/QuantScope/issues](https://github.com/hsliuping/QuantScope/issues)
3. **微信公众号**: QuantScope
4. **QQ 群**: 关注公众号获取群号

---

## 📝 下一步

安装完成后，建议阅读：

- [快速开始指南](./quick-start-guide.md)
- [使用指南](https://mp.weixin.qq.com/s/ppsYiBncynxlsfKFG8uEbw)
- [配置管理指南](./config-management-guide.md)
- [API 文档](http://localhost:8000/docs)

祝您使用愉快！🎉

