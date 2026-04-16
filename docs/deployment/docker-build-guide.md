# 🐳 Docker镜像构建指南

## 📋 概述

QuantScope采用本地构建Docker镜像的方式，而不是提供预构建镜像。本文档详细说明了Docker镜像的构建过程、优化方法和常见问题解决方案。

## 🎯 为什么需要本地构建？

### 设计理念

1. **🔧 定制化需求**
   - 用户可能需要不同的配置选项
   - 支持自定义依赖和扩展
   - 适应不同的部署环境

2. **🔒 安全考虑**
   - 避免在公共镜像中包含敏感信息
   - 用户完全控制构建过程
   - 减少供应链安全风险

3. **📦 版本灵活性**
   - 支持用户自定义修改
   - 便于开发和调试
   - 适应快速迭代需求

4. **⚡ 依赖优化**
   - 根据实际需求安装依赖
   - 避免不必要的组件
   - 优化镜像大小

## 🏗️ 构建过程详解

### Dockerfile结构

```dockerfile
# 基础镜像
FROM python:3.10-slim

# 系统依赖安装
RUN apt-get update && apt-get install -y \
    pandoc \
    wkhtmltopdf \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# Python依赖安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码复制
COPY . /app
WORKDIR /app

# 运行配置
EXPOSE 8501
CMD ["streamlit", "run", "web/app.py"]
```

### 构建阶段分析

#### 阶段1: 基础镜像下载
```bash
# 下载python:3.10-slim镜像
大小: ~200MB
时间: 1-3分钟 (取决于网络)
缓存: Docker会自动缓存，后续构建更快
```

#### 阶段2: 系统依赖安装
```bash
# 安装系统包
包含: pandoc, wkhtmltopdf, 中文字体
大小: ~300MB
时间: 2-4分钟
优化: 清理apt缓存减少镜像大小
```

#### 阶段3: Python依赖安装
```bash
# 安装Python包
来源: requirements.txt
大小: ~500MB
时间: 2-5分钟
优化: 使用--no-cache-dir减少镜像大小
```

#### 阶段4: 应用代码复制
```bash
# 复制源代码
大小: ~50MB
时间: <1分钟
优化: 使用.dockerignore排除不必要文件
```

## ⚡ 构建优化

### 1. 使用构建缓存

```bash
# 利用Docker层缓存
# 将不经常变化的步骤放在前面
COPY requirements.txt .
RUN pip install -r requirements.txt
# 将经常变化的代码放在后面
COPY . /app
```

### 2. 多阶段构建 (高级)

```dockerfile
# 构建阶段
FROM python:3.10-slim as builder
RUN pip install --user -r requirements.txt

# 运行阶段
FROM python:3.10-slim
COPY --from=builder /root/.local /root/.local
COPY . /app
```

### 3. 使用国内镜像源

```dockerfile
# 加速pip安装
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 加速apt安装
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
```

### 4. .dockerignore优化

```bash
# .dockerignore文件内容
.git
.gitignore
README.md
Dockerfile
.dockerignore
.env
.env.*
node_modules
.pytest_cache
.coverage
.vscode
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.DS_Store
.mypy_cache
.pytest_cache
.hypothesis
```

## 🚀 构建命令详解

### 基础构建

```bash
# 标准构建
docker-compose build

# 强制重新构建 (不使用缓存)
docker-compose build --no-cache

# 构建并启动
docker-compose up --build

# 后台构建并启动
docker-compose up -d --build
```

### 高级构建选项

```bash
# 并行构建 (如果有多个服务)
docker-compose build --parallel

# 指定构建参数
docker-compose build --build-arg HTTP_PROXY=http://proxy:8080

# 查看构建过程
docker-compose build --progress=plain

# 构建特定服务
docker-compose build web
```

## 📊 构建性能监控

### 构建时间优化

```bash
# 测量构建时间
time docker-compose build

# 分析构建层
docker history tradingagents-cn:latest

# 查看镜像大小
docker images tradingagents-cn
```

### 资源使用监控

```bash
# 监控构建过程资源使用
docker stats

# 查看磁盘使用
docker system df

# 清理构建缓存
docker builder prune
```

## 🚨 常见问题解决

### 1. 构建失败

#### 网络问题
```bash
# 症状: 下载依赖失败
# 解决: 使用国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 内存不足
```bash
# 症状: 构建过程中内存耗尽
# 解决: 增加Docker内存限制
# Docker Desktop -> Settings -> Resources -> Memory (建议4GB+)
```

#### 权限问题
```bash
# 症状: 文件权限错误
# 解决: 在Dockerfile中设置正确权限
RUN chmod +x /app/scripts/*.sh
```

### 2. 构建缓慢

#### 网络优化
```bash
# 使用多线程下载
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

#### 缓存优化
```bash
# 合理安排Dockerfile层顺序
# 将不变的依赖放在前面，变化的代码放在后面
```

### 3. 镜像过大

#### 清理优化
```bash
# 在同一RUN指令中清理缓存
RUN apt-get update && apt-get install -y package && rm -rf /var/lib/apt/lists/*
```

#### 多阶段构建
```bash
# 使用多阶段构建减少最终镜像大小
FROM python:3.10-slim as builder
# 构建步骤...
FROM python:3.10-slim
COPY --from=builder /app /app
```

## 📈 最佳实践

### 1. 构建策略

```bash
# 开发环境
docker-compose up --build  # 每次都重新构建

# 测试环境  
docker-compose build && docker-compose up -d  # 先构建再启动

# 生产环境
docker-compose build --no-cache && docker-compose up -d  # 完全重新构建
```

### 2. 版本管理

```bash
# 为镜像打标签
docker build -t tradingagents-cn:v0.1.7 .
docker build -t tradingagents-cn:latest .

# 推送到私有仓库 (可选)
docker tag tradingagents-cn:latest your-registry/tradingagents-cn:latest
docker push your-registry/tradingagents-cn:latest
```

### 3. 安全考虑

```bash
# 使用非root用户运行
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# 扫描安全漏洞
docker scan tradingagents-cn:latest
```

## 🔮 未来优化方向

### 1. 预构建镜像

考虑在未来版本提供官方预构建镜像：
- 🏷️ 稳定版本的预构建镜像
- 🔄 自动化CI/CD构建流程
- 📦 多架构支持 (amd64, arm64)

### 2. 构建优化

- ⚡ 更快的构建速度
- 📦 更小的镜像大小
- 🔧 更好的缓存策略

### 3. 部署简化

- 🎯 一键部署脚本
- 📋 预配置模板
- 🔧 自动化配置检查

---

*最后更新: 2025-07-13*  
*版本: cn-0.1.7*  
*贡献者: [@breeze303](https://github.com/breeze303)*
