# QuantScope

[![License](https://img.shields.io/badge/License-Mixed-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-1.0.0--preview-green.svg)](./VERSION)
[![Docs](https://img.shields.io/badge/docs-中文文档-green.svg)](./docs/)

面向中文用户的 AI 股票研究与分析平台，提供从数据同步、研究流程编排、多模型接入到报告导出的完整工作流。项目定位为学习、研究与策略实验，不提供实盘交易指令，也不构成投资建议。

## 项目定位

QuantScope 重点解决三类问题：

- 用统一界面管理多模型、多数据源、多市场分析任务
- 用可追踪的任务流承载单股分析、批量分析、筛选、报告导出
- 用工程化后端把研究过程、配置、进度、通知和历史记录沉淀下来

## 核心能力

### 分析能力

- 单股分析与批量分析
- 多角色协作研究流程
- 市场、新闻、社交媒体、基本面联合分析
- Markdown / Word / PDF 报告导出
- 历史记录追踪与分析结果回看

### 平台能力

- FastAPI + Vue 3 架构
- MongoDB + Redis 双存储
- WebSocket + SSE 实时进度与通知
- 用户认证、权限管理、操作日志
- 配置中心、模型管理、数据源管理
- 队列执行、任务状态恢复、使用统计

### 数据与模型

- 支持 A 股、港股、美股等市场场景
- 支持 Tushare、AkShare、BaoStock 等数据源
- 支持 OpenAI、Google、DeepSeek、通义千问等多类模型接入
- 支持自定义 OpenAI 兼容端点

## 技术架构

当前版本以 `FastAPI + Vue 3 + MongoDB + Redis` 为主架构：

- `app/`: FastAPI 后端，负责 API、任务、配置、通知、数据同步
- `frontend/`: Vue 3 前端，负责工作台、配置台、任务中心、报告界面
- `tradingagents/`: 分析引擎与多角色研究流程内核
- `web/`: 保留的 Streamlit 界面与兼容模块
- `docs/`: 中文文档、部署说明、架构说明、功能说明

## 快速开始

### 方式一：Docker Compose

适合大多数体验和部署场景。

启动前建议确认：

- 已安装 Docker Desktop / Docker Engine
- 本机可用端口包括 `3000`、`8000`、`27017`、`6379`
- 已准备好 `.env` 配置，或至少确认仓库中的默认配置可用于本地体验

启动步骤：

```bash
docker compose build
docker compose up -d
```

查看服务状态：

```bash
docker compose ps
```

查看后端日志：

```bash
docker logs -f quantscope-backend
```

默认访问地址：

- 前端: `http://localhost:3000`
- 后端 API: `http://localhost:8000`
- 健康检查: `http://localhost:8000/api/health`

停止服务：

```bash
docker compose down
```

如果只想重启后端：

```bash
docker compose up -d --force-recreate backend
```

如果修改了后端源码，例如 `app/`、`tradingagents/`、`mcp_servers/`，由于这些代码是构建镜像时复制进容器的，通常需要重新构建：

```bash
docker compose build backend
docker compose up -d --force-recreate backend
```

如果修改了前端源码并使用 Docker 镜像部署，同样建议重新构建前端镜像：

```bash
docker compose build frontend
docker compose up -d --force-recreate frontend
```

补充文档：

- [Docker 部署文档](./docs/deployment/docker)
- [快速开始](./docs/guides/quick-start-guide.md)

### 方式二：源码运行

适合开发与定制。

基本要求：

- Python 3.10+
- Node.js 18+
- MongoDB
- Redis
- 推荐使用虚拟环境

建议先准备后端虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
```

后端依赖安装：

```bash
pip install -r requirements.txt
```

前端依赖安装：

```bash
cd frontend
npm install
```

如果需要本地数据库与缓存，可先启动 MongoDB 和 Redis。

一种常见方式是只启动基础依赖容器：

```bash
docker compose up -d mongodb redis
```

后端启动：

```bash
python -m app.main
```

前端启动：

```bash
cd frontend
npm run dev
```

源码运行时默认访问地址：

- 前端开发服务器: `http://localhost:3000`
- 后端 API: `http://localhost:8000`

前端开发模式下会把 `/api` 请求代理到本地后端。

### 常见启动顺序

如果你是第一次在本地拉起项目，推荐顺序：

1. 准备 `.env`
2. 启动 MongoDB 和 Redis
3. 启动后端 `python -m app.main`
4. 启动前端 `cd frontend && npm run dev`
5. 打开 `http://localhost:3000`

### MCP 接入

项目当前已经暴露多组 MCP server。

例如单股分析 MCP endpoint：

```text
http://localhost:8000/mcp/analysis/mcp
```

当前 analysis MCP server 暴露的核心 tool 包括：

- `submit_single_analysis`
- `get_final_report`

更详细的 Hermes 接入方式可参考：

- [Hermes MCP 集成说明](./docs/integration/hermes_mcp_integration.md)

## 使用建议

- 首次使用前，先完成模型配置与数据源配置
- 开始分析前，先执行基础数据同步
- 对需要可比性的任务，固定分析日期、模型组合和市场范围
- 在生产环境优先使用 Docker 和独立数据库实例

## 文档入口

- [文档总览](./docs/README.md)
- [安装指南](./docs/guides/INSTALLATION_GUIDE.md)
- [Docker 部署](./docs/deployment/docker)
- [配置管理](./docs/guides/config-management-guide.md)
- [调度管理](./docs/guides/scheduler_management.md)
- [报告导出](./docs/guides/report-export-guide.md)

## 适用场景

- AI 金融研究学习
- 多模型效果对比
- 数据源接入与分析流程实验
- 内部研究平台原型
- 面向中文用户的研究工具二次开发

## 开发与贡献

欢迎提交 Issue 和 Pull Request。

基础流程：

1. Fork 本仓库
2. 创建分支
3. 提交修改
4. 发起 Pull Request

## 许可证

本项目采用混合许可证，详见 [LICENSE](./LICENSE) 与 [LICENSING.md](./LICENSING.md)。

- 开源部分：除 `app/` 和 `frontend/` 外的大部分文件采用 Apache 2.0
- 专有部分：`app/` 与 `frontend/` 目录需要依据仓库中的专有许可条款使用

如涉及商业使用、分发或定制合作，请先确认许可证范围。

## 风险提示

本项目仅用于研究、教学与策略实验。

- 不构成投资建议
- 不保证分析结果准确性或收益表现
- AI 输出存在不确定性
- 金融决策请结合专业判断与风险控制

---

如果这个项目对你有帮助，可以给仓库一个 Star。
