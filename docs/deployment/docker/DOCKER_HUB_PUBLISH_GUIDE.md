# Docker Hub 镜像发布指南

## 📋 概述

本文档说明如何构建 QuantScope 的 Docker 镜像并发布到 Docker Hub。

---

## 🎯 使用的脚本

### ✅ 正确的脚本（推荐使用）

- **Windows**: `scripts/publish-docker-images.ps1`
- **Linux/Mac**: `scripts/publish-docker-images.sh`

这两个脚本是**最新的、正确的**发布脚本，会：
1. 登录 Docker Hub
2. 构建前端和后端镜像
3. 标记镜像（版本号 + latest）
4. 推送到 Docker Hub

### ⚠️ 其他脚本说明

项目中还有一些其他 Docker 相关脚本，但**不用于发布镜像**：

- `scripts/docker-init.ps1` / `docker-init.sh` - 初始化 Docker 环境
- `scripts/start_docker.ps1` / `start_docker.sh` - 启动本地 Docker 服务
- `scripts/docker/start_docker_services.sh` - 启动 Docker Compose 服务
- `.github/workflows/docker-publish.yml` - GitHub Actions 自动发布（CI/CD）

---

## 🚀 使用方法

### Windows (PowerShell)

```powershell
# 基本用法（会提示输入密码）
.\scripts\publish-docker-images.ps1 -DockerHubUsername "your-username"

# 指定版本号
.\scripts\publish-docker-images.ps1 -DockerHubUsername "your-username" -Version "v1.0.0"

# 跳过构建（使用已有镜像）
.\scripts\publish-docker-images.ps1 -DockerHubUsername "your-username" -SkipBuild

# 不推送 latest 标签
.\scripts\publish-docker-images.ps1 -DockerHubUsername "your-username" -PushLatest:$false

# 完整示例
.\scripts\publish-docker-images.ps1 `
  -DockerHubUsername "hsliuping" `
  -Version "v1.0.0-preview" `
  -PushLatest
```

### Linux/Mac (Bash)

```bash
# 基本用法
./scripts/publish-docker-images.sh your-username

# 指定版本号
./scripts/publish-docker-images.sh your-username v1.0.0

# 跳过构建
SKIP_BUILD=true ./scripts/publish-docker-images.sh your-username

# 不推送 latest 标签
PUSH_LATEST=false ./scripts/publish-docker-images.sh your-username

# 完整示例
./scripts/publish-docker-images.sh hsliuping v1.0.0-preview
```

---

## 📦 发布的镜像

脚本会发布以下镜像到 Docker Hub：

### 后端镜像
- `your-username/tradingagents-backend:v1.0.0-preview`
- `your-username/tradingagents-backend:latest`

### 前端镜像
- `your-username/tradingagents-frontend:v1.0.0-preview`
- `your-username/tradingagents-frontend:latest`

---

## 🔧 发布流程

### 步骤 1: 准备工作

1. **确保代码已提交**
   ```bash
   git status
   git add .
   git commit -m "feat: 新功能"
   git push origin v1.0.0-preview
   ```

2. **确保 Docker 正在运行**
   ```bash
   docker --version
   docker ps
   ```

3. **登录 Docker Hub**（脚本会自动执行，但可以提前测试）
   ```bash
   docker login -u your-username
   ```

### 步骤 2: 运行发布脚本

```powershell
# Windows
.\scripts\publish-docker-images.ps1 -DockerHubUsername "hsliuping"

# Linux/Mac
./scripts/publish-docker-images.sh hsliuping
```

### 步骤 3: 验证发布

1. **访问 Docker Hub**
   - https://hub.docker.com/repositories/your-username

2. **检查镜像**
   - 确认 `tradingagents-backend` 和 `tradingagents-frontend` 都已发布
   - 确认版本标签正确（如 `v1.0.0-preview` 和 `latest`）

3. **测试拉取**
   ```bash
   docker pull your-username/tradingagents-backend:latest
   docker pull your-username/tradingagents-frontend:latest
   ```

### 步骤 4: 更新部署配置

更新 `docker-compose.hub.yml` 或 `docker-compose.hub.nginx.yml` 中的镜像地址：

```yaml
services:
  tradingagents-backend:
    image: hsliuping/tradingagents-backend:latest  # 替换为你的用户名
    
  tradingagents-frontend:
    image: hsliuping/tradingagents-frontend:latest  # 替换为你的用户名
```

---

## ⚙️ 脚本参数说明

### PowerShell 版本参数

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `-DockerHubUsername` | ✅ | - | Docker Hub 用户名 |
| `-Password` | ❌ | - | Docker Hub 密码（不推荐，建议交互式输入） |
| `-Version` | ❌ | `v1.0.0-preview` | 镜像版本号 |
| `-SkipBuild` | ❌ | `false` | 跳过构建，使用已有镜像 |
| `-PushLatest` | ❌ | `true` | 是否推送 latest 标签 |

### Bash 版本参数

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `dockerhub-username` | 第1个 | - | Docker Hub 用户名（必需） |
| `version` | 第2个 | `v1.0.0-preview` | 镜像版本号 |
| `SKIP_BUILD` | 环境变量 | `false` | 跳过构建 |
| `PUSH_LATEST` | 环境变量 | `true` | 是否推送 latest 标签 |

---

## 🐛 常见问题

### Q1: 构建失败 - "no such file or directory"

**原因**: 在错误的目录运行脚本。

**解决**: 必须在项目根目录运行：
```bash
cd /path/to/QuantScope
./scripts/publish-docker-images.sh your-username
```

### Q2: 推送失败 - "denied: requested access to the resource is denied"

**原因**: 
1. 未登录 Docker Hub
2. 用户名错误
3. 没有权限推送到该仓库

**解决**:
```bash
# 重新登录
docker logout
docker login -u your-username

# 确认用户名正确
docker info | grep Username
```

### Q3: 构建很慢

**原因**: 
1. 网络问题（拉取依赖慢）
2. 没有使用 Docker 缓存

**解决**:
```bash
# 使用国内镜像加速
# 编辑 /etc/docker/daemon.json (Linux) 或 Docker Desktop 设置 (Windows/Mac)
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}

# 重启 Docker
sudo systemctl restart docker  # Linux
# 或在 Docker Desktop 中重启
```

### Q4: 如何只构建不推送？

**解决**: 手动构建镜像：
```bash
# 构建后端
docker build -f Dockerfile.backend -t tradingagents-backend:v1.0.0-preview .

# 构建前端
docker build -f Dockerfile.frontend -t tradingagents-frontend:v1.0.0-preview .
```

### Q5: 如何推送到私有仓库？

**解决**: 修改脚本中的镜像地址：
```bash
# 例如推送到阿里云容器镜像服务
BACKEND_IMAGE_REMOTE="registry.cn-hangzhou.aliyuncs.com/your-namespace/tradingagents-backend"
FRONTEND_IMAGE_REMOTE="registry.cn-hangzhou.aliyuncs.com/your-namespace/tradingagents-frontend"
```

---

## 📝 发布检查清单

发布前请确认：

- [ ] 代码已提交并推送到 Git
- [ ] 版本号已更新（如需要）
- [ ] Docker 服务正在运行
- [ ] 已登录 Docker Hub
- [ ] 网络连接正常
- [ ] 磁盘空间充足（至少 10GB）

发布后请验证：

- [ ] Docker Hub 上能看到新镜像
- [ ] 镜像标签正确（版本号 + latest）
- [ ] 能成功拉取镜像
- [ ] 使用新镜像能正常启动服务
- [ ] 更新了部署文档（如需要）

---

## 🔗 相关文档

- [Docker 部署指南](../../guides/docker-deployment-guide.md)
- [Docker Hub 更新博客](../../blog/2025-10-24-docker-hub-update-and-clean-volumes.md)
- [快速开始](../../QUICK_START.md)

---

## 📞 获取帮助

如果遇到问题：
1. 查看脚本输出的错误信息
2. 检查 Docker 日志：`docker logs <container-id>`
3. 查看本文档的"常见问题"部分
4. 提交 Issue 到 GitHub

---

**最后更新**: 2025-10-25

