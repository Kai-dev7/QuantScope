# 🐳 Docker容器化部署指南

## 🎯 功能概述

QuantScope 提供了完整的Docker容器化部署方案，支持一键启动完整的分析环境，包括Web应用、数据库、缓存系统和管理界面。

## 🏗️ 架构设计

### 容器化架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ TradingAgents│  │   MongoDB   │  │    Redis    │     │
│  │     Web     │  │   Database  │  │    Cache    │     │
│  │  (Streamlit)│  │             │  │             │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│         │                 │                 │          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Volume    │  │  Mongo      │  │   Redis     │     │
│  │   Mapping   │  │  Express    │  │ Commander   │     │
│  │ (开发环境)   │  │ (管理界面)   │  │ (管理界面)   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 服务组件

1. **🌐 TradingAgents-Web**
   - Streamlit Web应用
   - 端口: 8501
   - 功能: 股票分析、报告导出

2. **🗄️ MongoDB**
   - 数据持久化存储
   - 端口: 27017
   - 功能: 分析结果、用户数据

3. **🔄 Redis**
   - 高性能缓存
   - 端口: 6379
   - 功能: 数据缓存、会话管理

4. **📊 MongoDB Express**
   - 数据库管理界面
   - 端口: 8081
   - 功能: 数据库可视化管理

5. **🎛️ Redis Commander**
   - 缓存管理界面
   - 端口: 8082
   - 功能: 缓存数据查看和管理

## 🚀 快速开始

### 环境要求

- Docker 20.0+
- Docker Compose 2.0+
- 4GB+ 可用内存
- 10GB+ 可用磁盘空间

### 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/hsliuping/QuantScope.git
cd QuantScope

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入API密钥

# 3. 构建并启动所有服务
docker-compose up -d --build
# 注意：首次运行会构建Docker镜像，需要5-10分钟

# 4. 验证部署
docker-compose ps
```

### 📦 Docker镜像构建说明

**重要提醒**: QuantScope不提供预构建的Docker镜像，需要本地构建。

#### 构建过程详解

```bash
# 构建过程包括以下步骤：
1. 📥 下载基础镜像 (python:3.10-slim)
2. 🔧 安装系统依赖 (pandoc, wkhtmltopdf, 中文字体)
3. 📦 安装Python依赖包 (requirements.txt)
4. 📁 复制应用代码到容器
5. ⚙️ 配置运行环境和权限

# 预期构建时间和资源：
- ⏱️ 构建时间: 5-10分钟 (取决于网络速度)
- 💾 镜像大小: 约1GB
- 🌐 网络需求: 下载约800MB依赖
- 💻 内存需求: 构建时需要2GB+内存
```

#### 构建优化建议

```bash
# 1. 使用国内镜像源加速 (可选)
# 编辑 Dockerfile，添加：
# RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 多阶段构建缓存
# 如果需要频繁重建，可以分步构建：
docker-compose build --no-cache  # 完全重建
docker-compose build             # 使用缓存构建

# 3. 查看构建进度
docker-compose up --build        # 显示详细构建日志
```

### 访问服务

部署完成后，可以通过以下地址访问各个服务：

- **🌐 主应用**: http://localhost:8501
- **📊 数据库管理**: http://localhost:8081
- **🎛️ 缓存管理**: http://localhost:8082

## ⚙️ 配置详解

### Docker Compose配置

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - .env:/app/.env
      # 开发环境映射（可选）
      - ./web:/app/web
      - ./tradingagents:/app/tradingagents
    depends_on:
      - mongodb
      - redis
    environment:
      - MONGODB_URL=mongodb://mongodb:27017/tradingagents
      - REDIS_URL=redis://redis:6379

  mongodb:
    image: mongo:4.4
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=tradingagents

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  mongo-express:
    image: mongo-express
    ports:
      - "8081:8081"
    environment:
      - ME_CONFIG_MONGODB_SERVER=mongodb
      - ME_CONFIG_MONGODB_PORT=27017
    depends_on:
      - mongodb

  redis-commander:
    image: rediscommander/redis-commander
    ports:
      - "8082:8081"
    environment:
      - REDIS_HOSTS=local:redis:6379
    depends_on:
      - redis

volumes:
  mongodb_data:
  redis_data:
```

### 环境变量配置

```bash
# .env 文件示例
# LLM API配置
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key
QWEN_API_KEY=your_qwen_key

# 数据源配置
TUSHARE_TOKEN=your_tushare_token
FINNHUB_API_KEY=your_finnhub_key

# 数据库配置
MONGODB_URL=mongodb://mongodb:27017/tradingagents
REDIS_URL=redis://redis:6379

# 导出功能配置
EXPORT_ENABLED=true
EXPORT_DEFAULT_FORMAT=word,pdf
```

## 🔧 开发环境配置

### Volume映射

开发环境支持实时代码同步：

```yaml
volumes:
  - .env:/app/.env
  - ./web:/app/web                    # Web界面代码
  - ./tradingagents:/app/tradingagents # 核心分析代码
  - ./scripts:/app/scripts            # 脚本文件
  - ./test_conversion.py:/app/test_conversion.py # 测试工具
```

### 开发工作流

```bash
# 1. 启动开发环境
docker-compose up -d

# 2. 修改代码（自动同步到容器）
# 编辑本地文件，容器内立即生效

# 3. 查看日志
docker logs TradingAgents-web --follow

# 4. 进入容器调试
docker exec -it TradingAgents-web bash

# 5. 测试功能
docker exec TradingAgents-web python test_conversion.py
```

## 📊 监控和管理

### 服务状态检查

```bash
# 查看所有服务状态
docker-compose ps

# 查看特定服务日志
docker logs TradingAgents-web
docker logs TradingAgents-mongodb
docker logs TradingAgents-redis

# 查看资源使用情况
docker stats
```

### 数据管理

```bash
# 备份MongoDB数据
docker exec TradingAgents-mongodb mongodump --out /backup

# 备份Redis数据
docker exec TradingAgents-redis redis-cli BGSAVE

# 清理缓存
docker exec TradingAgents-redis redis-cli FLUSHALL
```

### 服务重启

```bash
# 重启单个服务
docker-compose restart web

# 重启所有服务
docker-compose restart

# 重新构建并启动
docker-compose up -d --build
```

## 🚨 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :8501
   
   # 修改端口映射
   # 编辑 docker-compose.yml 中的 ports 配置
   ```

2. **内存不足**
   ```bash
   # 增加Docker内存限制
   # 在 docker-compose.yml 中添加：
   deploy:
     resources:
       limits:
         memory: 4G
   ```

3. **数据库连接失败**
   ```bash
   # 检查数据库服务状态
   docker logs TradingAgents-mongodb
   
   # 检查网络连接
   docker exec TradingAgents-web ping mongodb
   ```

### 性能优化

1. **资源限制**
   ```yaml
   services:
     web:
       deploy:
         resources:
           limits:
             cpus: '2.0'
             memory: 4G
           reservations:
             memory: 2G
   ```

2. **数据持久化**
   ```yaml
   volumes:
     mongodb_data:
       driver: local
       driver_opts:
         type: none
         o: bind
         device: /path/to/mongodb/data
   ```

## 🔒 安全配置

### 生产环境安全

```yaml
# 生产环境配置示例
services:
  mongodb:
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=secure_password
    
  mongo-express:
    environment:
      - ME_CONFIG_BASICAUTH_USERNAME=admin
      - ME_CONFIG_BASICAUTH_PASSWORD=secure_password
```

### 网络安全

```yaml
networks:
  tradingagents:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  web:
    networks:
      - tradingagents
```

## 🙏 致谢

### 功能贡献者

Docker容器化功能由社区贡献者 **[@breeze303](https://github.com/breeze303)** 设计并实现，包括：

- 🐳 Docker Compose多服务编排配置
- 🏗️ 容器化架构设计和优化
- 📊 数据库和缓存服务集成
- 🔧 开发环境Volume映射配置
- 📚 完整的部署文档和最佳实践

感谢他的杰出贡献，让QuantScope拥有了专业级的容器化部署能力！

---

*最后更新: 2025-07-13*  
*版本: cn-0.1.7*  
*功能贡献: [@breeze303](https://github.com/breeze303)*
