# 用户偏好设置与财务指标计算优化：TTM 计算、WebSocket 连接、UI 改进

**日期**: 2025-10-26  
**作者**: QuantScope 开发团队  
**标签**: `feature`, `bug-fix`, `optimization`, `ui`, `websocket`, `financial-metrics`

---

## 📋 概述

2025年10月26日，我们完成了一次全面的系统优化工作。通过 **36 个提交**，完成了 **用户偏好设置系统重构**、**财务指标计算优化**、**WebSocket 连接修复**、**UI 体验改进**等多项工作。本次更新显著提升了系统的数据准确性、用户体验和稳定性。

---

## 🎯 核心改进

### 1. 用户偏好设置系统重构

#### 1.1 修复所有设置保存问题

**提交记录**：
- `41ca79f` - fix: 修复所有设置保存到localStorage的问题
- `6283a5c` - fix: 修复所有个人设置保存问题（外观、分析偏好、通知设置）
- `e2fef6b` - fix: 修复通用设置（邮箱地址）保存后刷新恢复原值的问题
- `e56c571` - fix: 修复主题设置保存后刷新不生效的问题

**问题背景**：

用户在前端修改个人设置后，刷新页面设置会恢复到原值：
- ❌ 主题设置（深色/浅色）不生效
- ❌ 分析偏好设置（模型、分析师）不生效
- ❌ 通知设置不生效
- ❌ 邮箱地址不生效

**根本原因**：

1. **前端保存到 localStorage，后端保存到数据库**
   - 前端使用 `localStorage` 存储设置
   - 后端使用 MongoDB `users` 集合存储
   - 两者不同步

2. **页面刷新时优先读取后端数据**
   - `authStore` 初始化时从后端 `/api/auth/me` 获取用户信息
   - 覆盖了 `localStorage` 中的设置

3. **后端未正确保存用户偏好**
   - `/api/auth/me` 接口未返回 `preferences` 字段
   - 用户偏好设置未持久化到数据库

**解决方案**：

**步骤 1：后端返回用户偏好设置**

```python
# app/routers/auth_db.py
@router.get("/me")
async def get_current_user(current_user: dict = Depends(get_current_user_from_db)):
    """获取当前用户信息"""
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "name": user.username,
        "is_admin": user.is_admin,
        "roles": ["admin"] if user.is_admin else ["user"],
        "preferences": user.preferences.model_dump() if user.preferences else {}  # ← 新增
    }
```

**步骤 2：前端同步用户偏好到 appStore**

```typescript
// frontend/src/stores/auth.ts
setAuthInfo(token: string, refreshToken: string, user: User) {
  this.token = token
  this.refreshToken = refreshToken
  this.user = user
  
  // 同步用户偏好设置到 appStore
  this.syncUserPreferencesToAppStore()
}

syncUserPreferencesToAppStore() {
  const appStore = useAppStore()
  
  if (this.user?.preferences) {
    // 同步主题设置
    if (this.user.preferences.theme) {
      appStore.theme = this.user.preferences.theme
      appStore.applyTheme()
    }
    
    // 同步分析偏好
    if (this.user.preferences.analysis) {
      appStore.analysisPreferences = this.user.preferences.analysis
    }
    
    // 同步通知设置
    if (this.user.preferences.notifications) {
      appStore.notificationSettings = this.user.preferences.notifications
    }
  }
}
```

**步骤 3：添加用户偏好设置迁移脚本**

```python
# scripts/migrate_user_preferences.py
async def migrate_user_preferences():
    """迁移用户偏好设置到数据库"""
    db = get_database()
    users_collection = db[settings.USERS_COLLECTION]
    
    # 查找所有用户
    users = await users_collection.find({}).to_list(None)
    
    for user in users:
        # 如果用户没有 preferences 字段，添加默认值
        if "preferences" not in user or not user["preferences"]:
            default_preferences = {
                "theme": "light",
                "analysis": {
                    "default_model": "gpt-4o-mini",
                    "default_analysts": ["market", "fundamentals", "news", "social"]
                },
                "notifications": {
                    "email_enabled": False,
                    "browser_enabled": True
                }
            }
            
            await users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"preferences": default_preferences}}
            )
```

**效果**：
- ✅ 用户设置保存到数据库
- ✅ 刷新页面设置不丢失
- ✅ 前后端数据同步
- ✅ 支持多设备同步

#### 1.2 优化分析偏好设置

**提交记录**：
- `767ac03` - fix: 修正分析偏好默认值，与单股分析模块保持一致
- `25de33c` - feat: 单股分析和批量分析优先读取用户偏好设置

**问题背景**：

1. **默认值不一致**
   - 个人设置页面默认值：`gpt-4o-mini`
   - 单股分析页面默认值：`gpt-4o`
   - 导致用户困惑

2. **分析页面不读取用户偏好**
   - 每次打开分析页面都使用硬编码的默认值
   - 用户需要重新选择模型和分析师

**解决方案**：

```typescript
// frontend/src/views/Analysis/SingleStock.vue
onMounted(async () => {
  // 优先读取用户偏好设置
  const appStore = useAppStore()
  if (appStore.analysisPreferences) {
    analysisForm.model = appStore.analysisPreferences.default_model || 'gpt-4o-mini'
    analysisForm.analysts = appStore.analysisPreferences.default_analysts || ['market', 'fundamentals', 'news', 'social']
  }
})
```

**效果**：
- ✅ 默认值统一为 `gpt-4o-mini`
- ✅ 分析页面自动读取用户偏好
- ✅ 提高用户体验

---

### 2. 财务指标计算优化

#### 2.1 修复 TTM（Trailing Twelve Months）计算问题

**提交记录**：
- `9c11d98` - fix: 重构TTM计算逻辑，正确处理累计值和基准期选择
- `5de898e` - fix: 移除TTM计算中不准确的简单年化降级策略
- `b0413c6` - fix: Tushare数据源添加TTM营业收入和净利润计算
- `5384339` - fix: 修复AKShare数据源的TTM计算和估值指标
- `8077316` - fix: 修复基本面分析实时API调用中的TTM计算问题

**问题背景**：

TTM（Trailing Twelve Months）是计算动态市盈率（PE_TTM）和市销率（PS_TTM）的关键指标，但原有计算存在严重问题：

1. **累计值处理错误**
   - 财报数据是累计值（如 Q3 = 前三季度累计）
   - 直接相加会重复计算
   - 例如：Q1 + Q2 + Q3 = 前三季度 × 2（错误）

2. **基准期选择不当**
   - 使用 Q4 作为基准期
   - 但 Q4 数据通常延迟发布
   - 导致 TTM 数据不及时

3. **简单年化策略不准确**
   - 当没有完整 4 个季度数据时，简单年化（Q1 × 4）
   - 忽略了季节性因素
   - 导致估值指标严重失真

**解决方案**：

**正确的 TTM 计算公式**：

```
TTM = 最新年报 + (最新季报 - 去年同期季报)
```

**示例**：

假设现在是 2024-10-26，最新财报是 2024Q3：

```
TTM_营业收入 = 2023年报营业收入 + (2024Q3营业收入 - 2023Q3营业收入)
TTM_净利润 = 2023年报净利润 + (2024Q3净利润 - 2023Q3净利润)
```

**实现代码**：

```python
# tradingagents/data_sources/tushare_adapter.py
def _calculate_ttm_metrics(self, reports: List[Dict]) -> Optional[Dict]:
    """计算TTM指标（正确处理累计值）"""
    # 1. 找到最新年报
    annual_reports = [r for r in reports if r["report_type"] == "年报"]
    if not annual_reports:
        return None
    latest_annual = annual_reports[0]
    
    # 2. 找到最新季报
    quarterly_reports = [r for r in reports if r["report_type"] in ["一季报", "中报", "三季报"]]
    if not quarterly_reports:
        # 如果没有季报，直接使用年报数据
        return {
            "revenue_ttm": latest_annual.get("revenue"),
            "net_profit_ttm": latest_annual.get("net_profit")
        }
    
    latest_quarterly = quarterly_reports[0]
    
    # 3. 找到去年同期季报
    latest_quarter = latest_quarterly["report_type"]
    latest_year = int(latest_quarterly["end_date"][:4])
    last_year = latest_year - 1
    
    last_year_same_quarter = None
    for report in reports:
        if (report["report_type"] == latest_quarter and 
            int(report["end_date"][:4]) == last_year):
            last_year_same_quarter = report
            break
    
    if not last_year_same_quarter:
        # 如果没有去年同期数据，使用年报数据
        return {
            "revenue_ttm": latest_annual.get("revenue"),
            "net_profit_ttm": latest_annual.get("net_profit")
        }
    
    # 4. 计算 TTM
    revenue_ttm = (
        latest_annual.get("revenue", 0) +
        latest_quarterly.get("revenue", 0) -
        last_year_same_quarter.get("revenue", 0)
    )
    
    net_profit_ttm = (
        latest_annual.get("net_profit", 0) +
        latest_quarterly.get("net_profit", 0) -
        last_year_same_quarter.get("net_profit", 0)
    )
    
    return {
        "revenue_ttm": revenue_ttm if revenue_ttm > 0 else None,
        "net_profit_ttm": net_profit_ttm if net_profit_ttm != 0 else None
    }
```

**效果**：
- ✅ TTM 计算准确
- ✅ 正确处理累计值
- ✅ 基准期选择合理
- ✅ 移除不准确的年化策略

#### 2.2 修复市销率（PS）计算问题

**提交记录**：
- `f333020` - fix: 修复市销率(PS)计算使用季度/半年报数据的bug
- `c522523` - docs: 标记Tushare和实时行情数据源的PS/PE计算问题
- `ad69c71` - fix: 修复Tushare数据源市值计算和删除未使用的估算函数

**问题背景**：

市销率（PS）计算使用季度或半年报数据，导致严重失真：

```
错误计算：PS = 市值 / Q3营业收入（前三季度累计）
正确计算：PS = 市值 / TTM营业收入（最近12个月）
```

**示例**：

某股票：
- 市值：100 亿
- 2024Q3 营业收入（累计）：60 亿
- TTM 营业收入：80 亿

```
错误 PS = 100 / 60 = 1.67
正确 PS = 100 / 80 = 1.25
```

**解决方案**：

```python
# tradingagents/data_sources/tushare_adapter.py
def get_fundamental_data(self, code: str) -> Dict:
    """获取基本面数据"""
    # 1. 获取财报数据
    reports = self._get_financial_reports(code)
    
    # 2. 计算 TTM 指标
    ttm_metrics = self._calculate_ttm_metrics(reports)
    
    # 3. 获取实时股价和市值
    quote = self.get_realtime_quote(code)
    market_cap = quote.get("market_cap")  # 总市值（亿元）
    
    # 4. 计算估值指标
    if ttm_metrics and market_cap:
        # 市销率 = 市值 / TTM营业收入
        ps = market_cap / ttm_metrics["revenue_ttm"] if ttm_metrics["revenue_ttm"] else None
        
        # 市盈率 = 市值 / TTM净利润
        pe_ttm = market_cap / ttm_metrics["net_profit_ttm"] if ttm_metrics["net_profit_ttm"] else None
    
    return {
        "ps": ps,
        "pe_ttm": pe_ttm,
        # ... 其他指标
    }
```

**效果**：
- ✅ PS 计算准确
- ✅ 使用 TTM 营业收入
- ✅ 避免季节性失真

#### 2.3 修复 Tushare Token 配置优先级问题

**提交记录**：
- `75edbc8` - fix: 修复Tushare Token配置优先级问题，支持Web后台修改立即生效
- `da3406b` - fix: 修复数据源优先级读取时的异步/同步冲突问题

**问题背景**：

用户在 Web 后台修改 Tushare Token 后，系统仍然使用环境变量中的旧 Token：

1. **配置优先级不合理**
   - 环境变量优先级高于数据库配置
   - 用户在 Web 后台修改无效

2. **异步/同步冲突**
   - 配置读取使用异步方法
   - 部分代码在同步上下文中调用
   - 导致配置读取失败

**解决方案**：

**步骤 1：调整配置优先级**

```python
# app/services/config_service.py
async def get_data_source_config(self, source_name: str) -> Optional[Dict]:
    """获取数据源配置（数据库优先）"""
    # 1. 优先从数据库读取
    db_config = await self._get_from_database(source_name)
    if db_config and db_config.get("api_key"):
        return db_config
    
    # 2. 降级使用环境变量
    env_key = f"{source_name.upper()}_TOKEN"
    env_value = os.getenv(env_key)
    if env_value:
        return {"api_key": env_value}
    
    return None
```

**步骤 2：修复异步/同步冲突**

```python
# tradingagents/data_sources/tushare_adapter.py
class TushareAdapter:
    def __init__(self):
        # 同步初始化，使用环境变量
        self.token = os.getenv("TUSHARE_TOKEN")
        self._provider = None
    
    async def initialize(self):
        """异步初始化，从数据库读取配置"""
        config_service = ConfigService()
        config = await config_service.get_data_source_config("tushare")
        if config and config.get("api_key"):
            self.token = config["api_key"]
        
        # 初始化 provider
        if self.token:
            self._provider = ts.pro_api(self.token)
```

**效果**：
- ✅ Web 后台修改立即生效
- ✅ 数据库配置优先级高于环境变量
- ✅ 修复异步/同步冲突

---

### 3. WebSocket 连接优化

#### 3.1 修复 Docker 部署时 WebSocket 连接失败

**提交记录**：
- `d0512fc` - fix: 修复Docker部署时WebSocket连接失败的问题
- `f176a10` - fix: 优化WebSocket连接逻辑，支持开发和生产环境

**问题背景**：

Docker 部署时 WebSocket 连接失败：
- 前端尝试连接 `ws://localhost:8000`
- 应该连接到服务器的实际地址

**解决方案**：

**步骤 1：启用 Vite WebSocket 代理**

```typescript
// frontend/vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true  // 🔥 启用 WebSocket 代理支持
      }
    }
  }
})
```

**步骤 2：简化连接逻辑**

```typescript
// frontend/src/stores/notifications.ts
const connectWebSocket = () => {
  // 统一使用当前访问的服务器地址
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${wsProtocol}//${host}/api/ws/notifications?token=${token}`
  
  ws = new WebSocket(wsUrl)
}
```

**工作原理**：

| 环境 | 访问地址 | WebSocket 连接 | 代理路径 |
|------|---------|---------------|---------|
| **开发** | `http://localhost:3000` | `ws://localhost:3000/api/ws/...` | Vite 代理到 `ws://localhost:8000/api/ws/...` |
| **生产** | `http://服务器IP` | `ws://服务器IP/api/ws/...` | Nginx 代理到 `ws://backend:8000/api/ws/...` |
| **HTTPS** | `https://域名` | `wss://域名/api/ws/...` | Nginx 代理到 `ws://backend:8000/api/ws/...` |

**效果**：
- ✅ 无需修改代码
- ✅ 自动协议适配
- ✅ 自动地址适配
- ✅ 开发和生产环境统一

---

### 4. UI 体验改进

#### 4.1 添加数据源注册引导功能

**提交记录**：
- `f7e4546` - feat: 添加厂家注册引导功能
- `0ad8489` - fix: 调整注册引导提示的字体大小
- `9a57973` - feat: 为数据源添加注册引导功能
- `d58484e` - fix: 修复 TypeScript 类型错误 - 添加缺失的类型定义

**功能概述**：

在数据源配置页面添加注册引导，帮助用户快速获取 API Key：

```vue
<!-- frontend/src/views/Settings/components/ProviderDialog.vue -->
<el-alert
  v-if="!form.api_key && providerInfo.register_url"
  type="info"
  :closable="false"
  style="margin-bottom: 16px;"
>
  <template #title>
    <div style="display: flex; align-items: center; gap: 8px;">
      <el-icon><InfoFilled /></el-icon>
      <span>还没有 API Key？</span>
      <el-link
        :href="providerInfo.register_url"
        target="_blank"
        type="primary"
        :underline="false"
      >
        点击注册 {{ providerInfo.display_name }}
        <el-icon><Right /></el-icon>
      </el-link>
    </div>
  </template>
</el-alert>
```

**效果**：
- ✅ 用户可快速跳转到注册页面
- ✅ 提高新用户上手速度
- ✅ 减少配置错误

#### 4.2 修复深色主题下的白色背景问题

**提交记录**：
- `f1fe1d0` - fix: 修复深色主题下分析页面的白色背景问题

**问题背景**：

深色主题下，部分页面仍然显示白色背景，对比度不足。

**解决方案**：

```scss
// frontend/src/styles/dark-theme.scss
html.dark {
  // 页面背景
  .page-container {
    background-color: var(--el-bg-color) !important;
  }
  
  // 卡片背景
  .el-card {
    background-color: var(--el-bg-color) !important;
    color: var(--el-text-color-primary) !important;
  }
  
  // 表单背景
  .el-form {
    background-color: transparent !important;
  }
}
```

**效果**：
- ✅ 深色主题下背景统一
- ✅ 提高对比度
- ✅ 改善用户体验

#### 4.3 在关于页面添加原项目介绍和致谢

**提交记录**：
- `70b1971` - feat: 在关于页面添加原项目介绍和致谢

**功能概述**：

在关于页面添加原项目（TradingAgents）的介绍和致谢：

```vue
<el-card>
  <template #header>
    <div class="card-header">
      <span>🙏 致谢</span>
    </div>
  </template>
  <el-descriptions :column="1" border>
    <el-descriptions-item label="原项目">
      <el-link href="https://github.com/virattt/trading-agents" target="_blank">
        TradingAgents by virattt
      </el-link>
    </el-descriptions-item>
    <el-descriptions-item label="说明">
      本项目基于 TradingAgents 进行中文化和功能增强，感谢原作者的开源贡献！
    </el-descriptions-item>
  </el-descriptions>
</el-card>
```

**效果**：
- ✅ 尊重原作者贡献
- ✅ 说明项目来源
- ✅ 提高项目透明度

---

## 📊 统计数据

### 提交统计
- **总提交数**: 36 个
- **修改文件数**: 120+ 个
- **新增代码**: ~4,000 行
- **删除代码**: ~1,500 行
- **净增代码**: ~2,500 行

### 功能分类
- **用户偏好设置**: 10 项修复
- **财务指标计算**: 12 项优化
- **WebSocket 连接**: 2 项修复
- **UI 体验改进**: 5 项优化
- **文档完善**: 7 篇新增文档

---

## 🔧 技术亮点

### 1. TTM 计算公式
正确处理累计值，避免重复计算：
```
TTM = 最新年报 + (最新季报 - 去年同期季报)
```

### 2. 配置优先级策略
数据库配置优先于环境变量，支持 Web 后台修改立即生效：
```python
# 1. 优先从数据库读取
db_config = await self._get_from_database(source_name)
if db_config and db_config.get("api_key"):
    return db_config

# 2. 降级使用环境变量
env_value = os.getenv(f"{source_name.upper()}_TOKEN")
```

### 3. WebSocket 自动适配
统一开发和生产环境，无需修改代码：
```typescript
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const host = window.location.host
const wsUrl = `${wsProtocol}//${host}/api/ws/notifications?token=${token}`
```

### 4. 用户偏好同步机制
前后端数据同步，支持多设备：
```typescript
syncUserPreferencesToAppStore() {
  const appStore = useAppStore()
  if (this.user?.preferences) {
    appStore.theme = this.user.preferences.theme
    appStore.analysisPreferences = this.user.preferences.analysis
    appStore.notificationSettings = this.user.preferences.notifications
  }
}
```

---

## 🚀 升级指南

### 步骤 1：拉取最新代码

```bash
git pull origin v1.0.0-preview
```

### 步骤 2：运行用户偏好设置迁移脚本

```bash
.\.venv\Scripts\python scripts/migrate_user_preferences.py
```

### 步骤 3：重启服务

```bash
# Docker 环境
docker-compose -f docker-compose.hub.nginx.yml pull
docker-compose -f docker-compose.hub.nginx.yml up -d

# 本地开发环境
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 步骤 4：验证

1. **测试用户偏好设置**
   - 修改主题设置，刷新页面验证是否生效
   - 修改分析偏好，打开分析页面验证是否自动应用

2. **测试财务指标计算**
   - 查看基本面分析页面
   - 验证 PE_TTM、PS 等指标是否准确

3. **测试 WebSocket 连接**
   - 打开浏览器控制台
   - 查看是否有 WebSocket 连接成功的日志

---

## 📖 新增文档

1. **`docs/fixes/user-preferences-fix.md`** - 用户偏好设置修复文档
2. **`docs/fixes/ttm-calculation-fix.md`** - TTM 计算问题修复总结
3. **`docs/fixes/async-sync-conflict-fix.md`** - 异步/同步冲突问题修复
4. **`docs/fixes/financial-metrics-audit.md`** - 估算财务指标审计总结
5. **`docs/configuration/tushare-token-priority.md`** - Tushare Token 配置优先级说明
6. **`docs/configuration/websocket-connection.md`** - WebSocket 连接配置指南
7. **`docs/features/data-source-registration-guide.md`** - 数据源注册引导功能说明

---

## 🎉 总结

### 今日成果

**提交统计**：
- ✅ **36 次提交**
- ✅ **120+ 个文件修改**
- ✅ **4,000+ 行新增代码**
- ✅ **1,500+ 行删除代码**

**核心价值**：

1. **用户体验显著提升**
   - 设置保存不丢失
   - 分析页面自动应用偏好
   - 深色主题体验优化

2. **数据准确性大幅提高**
   - TTM 计算准确
   - PS/PE 指标可靠
   - 财务数据质量提升

3. **系统稳定性增强**
   - WebSocket 连接稳定
   - 配置管理优化
   - 异步/同步冲突修复

4. **开发体验改善**
   - 统一开发和生产环境
   - 配置优先级合理
   - 代码质量提升

---

**感谢使用 QuantScope！** 🚀

如有问题或建议，欢迎在 [GitHub Issues](https://github.com/hsliuping/QuantScope/issues) 中反馈。

