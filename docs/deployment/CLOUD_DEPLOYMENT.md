# QuantScope 云端部署指南（腾讯云轻量应用服务器）

> 目标：部署 QuantScope 到腾讯云轻量应用服务器，通过 `app.510168.xyz` 域名访问。

---

## 架构总览

```
用户浏览器
    │
    ▼
Cloudflare（免费 CDN + SSL）
    ├── app.510168.xyz  →  腾讯云轻量 (Nginx :80/:443)
    │                          ├── /              → 前端静态文件
    │                          ├── /api/          → FastAPI 后端 (:8000)
    │                          ├── /mcp/analysis/ → MCP 服务 (:8000)
    │                          └── /ws/           → WebSocket (:8000)
    │
    ├── api.510168.xyz   →  （复用同一台服务器）
    │
    ▼
腾讯云轻量应用服务器 (¥34/月)
    ├── Nginx（反向代理）
    ├── FastAPI 后端 (:8000)
    ├── Redis（本地容器，1GB 够用）
    └── Docker Engine
        └── quantscope-backend:v1.0.0-preview

MongoDB Atlas M0（免费）
    └── 512MB 存储，3台副本集（美国/欧洲）
```

---

## 第一步：购买腾讯云轻量应用服务器

### 1.1 注册与选购

1. 访问 [腾讯云轻量应用服务器购买页](https://console.cloud.tencent.com/lighthouse/buy)
2. 选择配置：
   - **地域**：中国内地（上海/广州/成都/南京任选）
   - **套餐**：通用型-1核-2GB（¥68/月）或入门型-1核-1GB（¥34/月，Redis 外置）
   - **镜像**：Ubuntu 22.04 LTS（应用镜像选 Docker CE）
   - **带宽**：5Mbps（够用）或按量付费
   - **流量包**：500GB/月
   - **购买时长**：1年（享折扣）

3. 设置 root 密码，绑定防火墙（开放 80/443/22 端口）

### 1.2 登录服务器

```bash
ssh root@<服务器IP>
# 或使用腾讯云控制台的 Web Shell
```

### 1.3 安装必要软件

```bash
# 安装 Docker（如果选了系统镜像而非 Docker 应用镜像）
curl -fsSL https://get.docker.com | sh
systemctl enable docker

# 安装 Docker Compose（V2）
docker compose version 2>/dev/null || \
  apt-get update && apt-get install -y docker-compose

# 安装 Nginx
apt-get update && apt-get install -y nginx

# 安装 Certbot（Let's Encrypt 自动续期 SSL 证书）
apt-get install -y certbot python3-certbot-nginx

# 安装 Redis（腾讯云轻量 1GB 内存时，Redis 和后端分开跑）
apt-get install -y redis-server
systemctl enable redis-server
systemctl start redis-server
```

---

## 第二步：配置 MongoDB Atlas（免费）

### 2.1 注册 MongoDB Atlas

1. 访问 [cloud.mongodb.com](https://www.mongodb.com/atlas)，用 GitHub 账号注册
2. 选择免费 M0 套餐（Shared RAM, 512MB 存储）
3. 选择区域：**Sydney** 或 **Oregon**（亚太延迟低，但 M0 只有美国/欧洲节点）

### 2.2 创建数据库用户

1. **Security** → **Database Access** → **Add New Database User**
   - Username: `quantscope_admin`
   - Password: （生成强密码，保存好）
   - Role: `Read and write to any database`

### 2.3 配置网络白名单

1. **Security** → **Network Access** → **Add IP Address**
   - 点击 **ALLOW ACCESS FROM ANYWHERE**（或只允许腾讯云 IP 段）
   - 0.0.0.0/0 表示任意来源

### 2.4 获取连接字符串

1. **Deployment** → **Database** → **Connect** → **Connect your application**
2. 复制连接字符串，格式如下：

```bash
mongodb+srv://quantscope_admin:<PASSWORD>@cluster0.xxxxx.mongodb.net/tradingagents?retryWrites=true&w=majority
```

**替换 `<PASSWORD>` 为你设置的密码。**

### 2.5 验证连接（可选）

```bash
# 在腾讯云服务器上测试
apt-get install -y mongosh
mongosh "mongodb+srv://quantscope_admin:<PASSWORD>@cluster0.xxxxx.mongodb.net/tradingagents"
```

---

## 第三步：上传代码到服务器

### 方式 A：Git 拉取（推荐）

```bash
# 在服务器上直接拉取 release 分支
cd /opt
git clone -b release https://github.com/<YourGitHubUsername>/QuantScope.git
cd QuantScope
```

### 方式 B：本地打包上传

```bash
# 本地打包
cd /Users/kaicui/PycharmProjects/QuantScope
git archive -o /tmp/quantscope-release.tar.gz --prefix=quantcope/ release

# 上传到服务器（需要先配置 ssh 密钥或上传到 GitHub）
scp /tmp/quantscope-release.tar.gz root@<服务器IP>:/opt/
ssh root@<服务器IP> "cd /opt && tar -xzf quantscope-release.tar.gz && mv quantcope QuantScope"
```

---

## 第四步：配置环境变量

### 4.1 创建生产环境 .env 文件

```bash
cd /opt/QuantScope
cp .env.docker .env
```

编辑 `.env`，修改以下内容：

```bash
# ════════════════════════════════════════════════════════════
# 数据库配置（重要！）
# ════════════════════════════════════════════════════════════
# 注释掉本地 Docker MongoDB/Redis，改用 Atlas
 TRADINGAGENTS_MONGODB_URL=mongodb+srv://quantscope_admin:<密码>@cluster0.xxxxx.mongodb.net/tradingagents
 TRADINGAGENTS_REDIS_URL=redis://:tradingagents123@localhost:6379
 TRADINGAGENTS_CACHE_TYPE=redis

# ════════════════════════════════════════════════════════════
# API Keys（根据你已有的填写）
# ════════════════════════════════════════════════════════════
DASHSCOPE_API_KEY=<你的阿里云百炼API Key>
DASHSCOPE_ENABLED=true

# 其他 API Key（按需启用）
DEEPSEEK_API_KEY=<你的DeepSeek API Key>
DEEPSEEK_ENABLED=false

# ════════════════════════════════════════════════════════════
# 容器标识
# ════════════════════════════════════════════════════════════
DOCKER_CONTAINER=false          # 改为 false，因为不用 Docker 跑后端
PYTHONUNBUFFERED=1
TZ=Asia/Shanghai

# ════════════════════════════════════════════════════════════
# 日志配置
# ════════════════════════════════════════════════════════════
TRADINGAGENTS_LOG_LEVEL=INFO
TRADINGAGENTS_LOG_DIR=/opt/QuantScope/logs
TRADINGAGENTS_LOG_FILE=/opt/QuantScope/logs/tradingagents.log

# ════════════════════════════════════════════════════════════
# 服务配置
# ════════════════════════════════════════════════════════════
API_HOST=127.0.0.1              # 只监听本地，通过 Nginx 反向代理
API_PORT=8000
CORS_ORIGINS=https://app.510168.xyz,https://510168.xyz

# ════════════════════════════════════════════════════════════
# MCP 服务配置
# ════════════════════════════════════════════════════════════
# MCP_STATELESS_HTTP=false（已在代码中硬编码）
```

---

## 第五步：构建后端

### 5.1 直接运行（开发模式）

```bash
cd /opt/QuantScope
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 5.2 使用 Gunicorn（生产推荐）

```bash
# 安装 Gunicorn + uvloop（高性能 ASGI 服务器）
pip install gunicorn uvicorn uvloop httptools

# 后台启动
nohup gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  --access-logfile /opt/QuantScope/logs/access.log \
  --error-logfile /opt/QuantScope/logs/error.log \
  --log-level info \
  > /opt/QuantScope/logs/gunicorn.log 2>&1 &

echo $! > /tmp/quantscope.pid
```

### 5.3 验证后端启动

```bash
curl http://127.0.0.1:8000/api/health
# 期望返回：{"status":"ok"}
```

---

## 第六步：配置 Nginx 反向代理

### 6.1 创建 Nginx 配置文件

```bash
cat > /etc/nginx/sites-available/quantscope \
  << 'EOF'
server {
    listen 80;
    server_name app.510168.xyz api.510168.xyz;

    # 前端静态文件
    root /opt/QuantScope/frontend-react/dist;

    # 日志
    access_log /var/log/nginx/quantscope_access.log;
    error_log /var/log/nginx/quantscope_error.log;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/javascript application/json application/xml;

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;        # 分析任务可能跑很久
        proxy_send_timeout 600s;
    }

    # MCP 端点
    location /mcp/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # MCP session 管理需要长连接
        proxy_read_timeout 900s;
        proxy_send_timeout 900s;
        # MCP 使用 StreamableHTTP，需要这些 header
        proxy_set_header Accept "application/json, text/event-stream";
    }

    # WebSocket 支持
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # 前端静态资源缓存
    location ~* ^/assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # index.html 不缓存
    location = /index.html {
        expires -1;
        add_header Cache-Control "no-store, no-cache";
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

# 启用配置
ln -sf /etc/nginx/sites-available/quantscope /etc/nginx/sites-enabled/quantscope
rm -f /etc/nginx/sites-enabled/default

# 测试配置
nginx -t

# 重载 Nginx
systemctl reload nginx
```

### 6.2 获取 SSL 证书（Let's Encrypt 免费）

```bash
certbot --nginx -d app.510168.xyz -d api.510168.xyz --noninteractive --agree-tos \
  --email your@email.com --redirect

# 自动续期测试
certbot renew --dry-run
```

---

## 第七步：配置 Systemd 守护进程

### 7.1 创建服务文件

```bash
cat > /etc/systemd/system/quantscope.service \
  << 'EOF'
[Unit]
Description=QuantScope Stock Analysis Backend
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=notify
User=root
WorkingDirectory=/opt/QuantScope
EnvironmentFile=/opt/QuantScope/.env

# 使用 Gunicorn 启动（高并发）
ExecStart=/usr/local/bin/gunicorn app.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /opt/QuantScope/logs/access.log \
    --error-logfile /opt/QuantScope/logs/error.log \
    --log-level info

Restart=always
RestartSec=5
StandardOutput=append:/opt/QuantScope/logs/stdout.log
StandardError=append:/opt/QuantScope/logs/stderr.log

# 进程管理
TimeoutStartSec=300
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF
```

### 7.2 启动服务

```bash
systemctl daemon-reload
systemctl enable quantscope
systemctl start quantscope

# 查看状态
systemctl status quantscope
journalctl -u quantscope -f --no-pager
```

---

## 第八步：部署前端

### 8.1 在本地构建前端

```bash
# 确保在 release 分支
git checkout release

cd frontend-react

# 创建生产环境配置
cat > .env.production << 'EOF'
VITE_API_BASE_URL=https://api.510168.xyz/api
VITE_WS_URL=wss://api.510168.xyz/ws
VITE_APP_TITLE=QuantScope
VITE_DEFAULT_DEPTH=standard
EOF

# 构建
npm ci
npm run build
```

### 8.2 上传前端构建产物

```bash
# 方式 A：rsync（推荐）
rsync -avz --delete dist/ root@<服务器IP>:/opt/QuantScope/frontend-react/dist/

# 方式 B：打包上传
tar -czf frontend-dist.tar.gz -C dist .
scp frontend-dist.tar.gz root@<服务器IP>:/tmp/
ssh root@<服务器IP> "rm -rf /opt/QuantScope/frontend-react/dist && mkdir -p /opt/QuantScope/frontend-react/dist && tar -xzf /tmp/frontend-dist.tar.gz -C /opt/QuantScope/frontend-react/dist"
```

---

## 第九步：域名解析（Cloudflare）

### 9.1 添加 DNS 记录

登录 [Cloudflare Dashboard](https://dash.cloudflare.com)，选择 `510168.xyz` 域名：

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | app | `<腾讯云服务器IP>` | 🟡 Proxied |
| A | api | `<腾讯云服务器IP>` | 🟡 Proxied |

### 9.2 验证访问

```
https://app.510168.xyz      → 前端页面
https://api.510168.xyz/docs → FastAPI 文档
```

---

## 第十步：CI/CD 自动化部署

### 10.1 GitHub Actions 工作流

在 `release` 分支创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy to Tencent Cloud

on:
  push:
    branches: [release]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'frontend-react/node_modules'

      - name: Build Frontend
        run: |
          cd frontend-react
          echo "VITE_API_BASE_URL=https://api.510168.xyz/api" > .env.production
          echo "VITE_WS_URL=wss://api.510168.xyz/ws" >> .env.production
          echo "VITE_APP_TITLE=QuantScope" >> .env.production
          echo "VITE_DEFAULT_DEPTH=standard" >> .env.production
          npm ci
          npm run build

      - name: Deploy to Server via SSH
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.TENCENT_HOST }}
          username: root
          key: ${{ secrets.TENCENT_SSH_KEY }}
          script: |
            cd /opt/QuantScope
            git fetch origin release
            git checkout release
            git pull origin release
            
            # 重启服务
            systemctl restart quantscope
            
            # 同步前端
            rsync -avz --delete frontend-react/dist/ /opt/QuantScope/frontend-react/dist/
            
            # 健康检查
            sleep 5
            curl -f http://127.0.0.1:8000/api/health || exit 1
```

### 10.2 添加 SSH 密钥到 GitHub Secrets

```bash
# 生成本地 SSH 密钥（如果还没有）
ssh-keygen -t ed25519 -C "deploy@quantscope" -f ~/.ssh/quantscope_deploy

# 上传公钥到腾讯云服务器
ssh-copy-id -i ~/.ssh/quantscope_deploy.pub root@<服务器IP>

# 添加到 GitHub Secrets
gh secret set TENCENT_HOST --body "<服务器IP>"
gh secret set TENCENT_SSH_KEY --body "$(cat ~/.ssh/quantscope_deploy)"
```

---

## 数据库迁移（如需从本地导入）

如果你的本地 QuantScope 已有历史数据：

```bash
# 1. 导出本地 MongoDB 数据
mongodump --uri="mongodb://localhost:27017/tradingagents" \
  --archive=/tmp/quantscope_dump.archive --gzip

# 2. 上传到服务器
scp /tmp/quantscope_dump.archive root@<服务器IP>:/tmp/

# 3. 导入到 Atlas
mongorestore \
  --uri="mongodb+srv://quantscope_admin:<PASSWORD>@cluster0.xxxxx.mongodb.net/tradingagents" \
  --archive=/tmp/quantscope_dump.archive --gzip
```

---

## 故障排查

### 1. 后端启动失败

```bash
journalctl -u quantscope -n 50 --no-pager
cat /opt/QuantScope/logs/error.log
```

### 2. 检查端口占用

```bash
ss -tlnp | grep -E ':(80|443|8000|6379)'
```

### 3. Nginx 日志

```bash
tail -50 /var/log/nginx/quantscope_error.log
tail -50 /var/log/nginx/quantscope_access.log
```

### 4. MongoDB 连接问题

```bash
# 测试 Atlas 连通性
curl -s https://api.mongodb.com/some-test 2>/dev/null || true
mongosh "mongodb+srv://quantscope_admin:<PASSWORD>@cluster0.xxxxx.mongodb.net/tradingagents" --eval "db.runCommand({ping:1})"
```

### 5. 查看分析任务状态

```bash
# 通过 Docker（如果有）
docker logs quantscope-backend --tail 100

# 直接看日志
tail -100 /opt/QuantScope/logs/tradingagents.log | grep -i "task\|analysis\|error"
```

---

## 成本汇总

| 项目 | 月费用 |
|------|--------|
| 腾讯云轻量（1核/2GB） | ¥68（首年约 ¥55/月，年付） |
| MongoDB Atlas M0 | 免费 |
| 域名（510168.xyz） | ~¥50/年 |
| **合计** | **约 ¥70/月（约 ¥840/年）** |

如果选 1GB 内存（¥34/月）+ 外置 Redis：
| 项目 | 月费用 |
|------|--------|
| 腾讯云轻量（1核/1GB） | ¥34/月 |
| Redis Cloud 30MB | 免费 |
| MongoDB Atlas M0 | 免费 |
| **合计** | **约 ¥34/月** |