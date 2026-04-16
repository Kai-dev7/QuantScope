# 使用统计功能快速测试指南

## 🎯 测试目标

验证使用统计和定价配置功能是否正常工作。

## 📋 测试前准备

### 1. 启动后端服务

```powershell
# 进入项目目录
cd d:\code\QuantScope

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 启动后端
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端服务

```powershell
# 新开一个终端
cd d:\code\QuantScope\frontend

# 启动前端
npm run dev
```

### 3. 登录系统

访问 `http://localhost:5173` 并登录。

## ✅ 测试步骤

### 测试 1：配置模型定价

#### 步骤
1. 访问 `http://localhost:5173/settings/config`
2. 点击"大模型配置"标签
3. 找到一个模型（如 qwen-max）
4. 点击"编辑"按钮
5. 滚动到"定价配置"部分
6. 填写：
   - 输入价格: `0.0200`
   - 输出价格: `0.0600`
   - 货币单位: `CNY`
7. 点击"保存"

#### 预期结果
- ✅ 保存成功提示
- ✅ 模型卡片显示定价信息：
  ```
  💰 定价:
    输入: 0.0200 CNY/1K
    输出: 0.0600 CNY/1K
  ```

### 测试 2：访问使用统计页面（方式 1）

#### 步骤
1. 点击左侧导航栏的"设置"
2. 在设置页面顶部，确认当前在"系统配置"标签
3. 在左侧菜单中点击"使用统计"
4. 点击"查看使用统计"按钮

#### 预期结果
- ✅ 跳转到使用统计页面
- ✅ URL 变为 `/settings/usage`
- ✅ 页面正常加载

### 测试 3：访问使用统计页面（方式 2）

#### 步骤
1. 直接在浏览器地址栏输入：`http://localhost:5173/settings/usage`
2. 按回车

#### 预期结果
- ✅ 页面正常加载
- ✅ 显示使用统计界面

### 测试 4：查看统计概览

#### 步骤
1. 在使用统计页面顶部查看 4 个统计卡片

#### 预期结果
- ✅ 显示"总请求数"卡片
- ✅ 显示"总输入 Token"卡片
- ✅ 显示"总输出 Token"卡片
- ✅ 显示"总成本"卡片
- ✅ 如果没有数据，显示 0

### 测试 5：查看图表

#### 步骤
1. 滚动到图表区域
2. 查看三个图表

#### 预期结果
- ✅ 显示"按供应商统计"饼图
- ✅ 显示"按模型统计"柱状图
- ✅ 显示"每日成本趋势"折线图
- ✅ 如果没有数据，显示"暂无数据"

### 测试 6：时间范围筛选

#### 步骤
1. 点击右上角的时间范围选择器
2. 选择"最近 30 天"
3. 等待数据刷新

#### 预期结果
- ✅ 数据重新加载
- ✅ 图表更新
- ✅ 统计卡片更新

### 测试 7：查看使用记录表格

#### 步骤
1. 滚动到页面底部
2. 查看使用记录表格

#### 预期结果
- ✅ 显示表格
- ✅ 显示列：时间、供应商、模型、输入Token、输出Token、成本、分析类型、会话ID
- ✅ 如果没有数据，显示"暂无数据"
- ✅ 显示分页控件

### 测试 8：刷新数据

#### 步骤
1. 点击右上角的"刷新"按钮

#### 预期结果
- ✅ 显示加载状态
- ✅ 数据重新加载
- ✅ 显示成功提示

### 测试 9：清理旧记录

#### 步骤
1. 点击"清理旧记录"按钮
2. 在确认对话框中点击"确定"

#### 预期结果
- ✅ 显示确认对话框
- ✅ 显示删除成功提示
- ✅ 数据刷新

## 🔧 生成测试数据

如果没有使用数据，可以通过以下方式生成：

### 方式 1：运行股票分析

1. 访问"股票分析 > 单股分析"
2. 输入股票代码（如 600519）
3. 点击"开始分析"
4. 等待分析完成

### 方式 2：使用 API 直接添加测试数据

```python
# scripts/add_test_usage_data.py
import asyncio
from datetime import datetime, timedelta
import random
from app.services.usage_statistics_service import usage_statistics_service
from app.models.config import UsageRecord

async def add_test_data():
    """添加测试使用数据"""
    providers = ['dashscope', 'openai', 'google']
    models = {
        'dashscope': ['qwen-max', 'qwen-plus', 'qwen-turbo'],
        'openai': ['gpt-4', 'gpt-3.5-turbo'],
        'google': ['gemini-pro']
    }
    
    # 生成最近 30 天的数据
    for i in range(30):
        date = datetime.now() - timedelta(days=i)
        
        # 每天生成 5-10 条记录
        for _ in range(random.randint(5, 10)):
            provider = random.choice(providers)
            model = random.choice(models[provider])
            
            input_tokens = random.randint(500, 3000)
            output_tokens = random.randint(200, 1500)
            
            # 假设价格
            input_price = 0.02
            output_price = 0.06
            cost = (input_tokens / 1000) * input_price + (output_tokens / 1000) * output_price
            
            record = UsageRecord(
                timestamp=date.isoformat(),
                provider=provider,
                model_name=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                session_id=f"test_session_{i}_{_}",
                analysis_type="stock_analysis"
            )
            
            await usage_statistics_service.add_usage_record(record)
    
    print("测试数据添加完成！")

if __name__ == "__main__":
    asyncio.run(add_test_data())
```

运行脚本：
```powershell
.\.venv\Scripts\python scripts/add_test_usage_data.py
```

## 📊 验证结果

### 成功标准

- ✅ 所有页面正常加载
- ✅ 定价配置可以保存
- ✅ 定价信息正确显示
- ✅ 使用统计页面可以访问
- ✅ 统计数据正确显示
- ✅ 图表正常渲染
- ✅ 时间范围筛选正常工作
- ✅ 刷新功能正常
- ✅ 清理旧记录功能正常

### 检查点

1. **后端 API**
   - 访问 `http://localhost:8000/docs`
   - 查看 `usage-statistics` 标签下的 API
   - 测试各个端点

2. **前端路由**
   - 检查 `/settings/usage` 路由是否注册
   - 检查页面是否可以访问

3. **数据库**
   - 检查 MongoDB 中是否有 `usage_records` 集合
   - 检查数据是否正确存储

4. **浏览器控制台**
   - 检查是否有错误信息
   - 检查 API 请求是否成功

## 🐛 常见问题

### 问题 1：页面 404

**原因**: 路由未正确注册

**解决**:
1. 检查 `frontend/src/router/index.ts`
2. 确认 `UsageStatistics` 路由已添加
3. 重启前端服务

### 问题 2：图表不显示

**原因**: ECharts 未正确加载或没有数据

**解决**:
1. 检查浏览器控制台错误
2. 确认有使用数据
3. 尝试刷新页面

### 问题 3：API 请求失败

**原因**: 后端服务未启动或认证失败

**解决**:
1. 检查后端服务是否运行
2. 检查是否已登录
3. 检查 JWT token 是否有效

### 问题 4：定价不显示

**原因**: 定价配置未保存或数据未刷新

**解决**:
1. 重新保存定价配置
2. 刷新页面
3. 检查 MongoDB 中的数据

## 📝 测试报告模板

```markdown
# 使用统计功能测试报告

## 测试环境
- 操作系统: Windows 11
- 浏览器: Chrome 120
- 后端版本: v1.0.0-preview
- 前端版本: v1.0.0-preview

## 测试结果

| 测试项 | 状态 | 备注 |
|--------|------|------|
| 配置模型定价 | ✅ | 正常 |
| 访问统计页面（方式1） | ✅ | 正常 |
| 访问统计页面（方式2） | ✅ | 正常 |
| 查看统计概览 | ✅ | 正常 |
| 查看图表 | ✅ | 正常 |
| 时间范围筛选 | ✅ | 正常 |
| 查看使用记录 | ✅ | 正常 |
| 刷新数据 | ✅ | 正常 |
| 清理旧记录 | ✅ | 正常 |

## 发现的问题
无

## 建议
无

## 测试人员
[姓名]

## 测试日期
2025-10-07
```

## 🚀 下一步

测试通过后：
1. 提交代码到 Git
2. 更新版本号
3. 部署到生产环境
4. 通知用户新功能上线

