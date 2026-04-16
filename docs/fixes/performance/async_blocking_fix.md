# 异步阻塞问题修复文档

## 📋 问题描述

### 现象
在执行 `/api/sync/multi-source/test-sources` 接口时，其他API接口（如 `/api/notifications/unread_count`）会出现超时错误：

```
❌ API错误: undefined /api/notifications/unread_count 
{
  error: AxiosError, 
  message: 'timeout of 30000ms exceeded', 
  code: 'ECONNABORTED'
}
```

### 触发条件
- **只在数据源测试时出现**：执行 `POST /api/sync/multi-source/test-sources`
- **其他时候正常**：单独调用 `/api/notifications/unread_count` 不会超时
- **等待期间超时**：在数据源测试完成之前，其他接口无法响应

## 🔍 根本原因分析

### 1. 事件循环阻塞

`/api/sync/multi-source/test-sources` 接口虽然定义为 `async def`，但内部调用的是**同步方法**：

```python
@router.post("/test-sources")
async def test_data_sources():
    for adapter in available_adapters:
        # ❌ 这是同步调用，会阻塞事件循环
        df = adapter.get_stock_list()  
        trade_date = adapter.find_latest_trade_date()
        df = adapter.get_daily_basic(trade_date)
```

### 2. 耗时操作

每个数据源的测试都包含：
- **获取股票列表**：5000+ 只股票，需要 5-10 秒
- **查找最新交易日期**：需要 1-2 秒
- **获取每日基础数据**：5000+ 只股票，需要 10-20 秒

**总耗时**：3个数据源 × 20秒 = **60秒左右**

### 3. 资源竞争

在测试期间：
- **事件循环被阻塞**：无法处理其他请求
- **MongoDB连接被占用**：数据源测试可能访问MongoDB
- **其他请求排队等待**：超过30秒就会超时

### 4. 架构问题

```
┌─────────────────────────────────────────┐
│  FastAPI 异步事件循环                    │
│  ┌─────────────────────────────────┐    │
│  │ test-sources 接口                │    │
│  │ ❌ 同步调用阻塞事件循环           │    │
│  │    adapter.get_stock_list()     │    │
│  │    (耗时 60 秒)                  │    │
│  └─────────────────────────────────┘    │
│                                          │
│  ┌─────────────────────────────────┐    │
│  │ notifications/unread_count      │    │
│  │ ⏱️  等待事件循环...               │    │
│  │ ⏱️  等待事件循环...               │    │
│  │ ❌ 超时 (30秒)                   │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## ✅ 解决方案

### 核心思路
将**同步的、耗时的操作**放到**后台线程**中执行，避免阻塞事件循环。

### 实现方式

#### 1. 使用 `asyncio.to_thread()`

```python
# ❌ 修复前：同步调用阻塞事件循环
df = adapter.get_stock_list()

# ✅ 修复后：在后台线程中执行
df = await asyncio.to_thread(adapter.get_stock_list)
```

#### 2. 提取测试函数

```python
async def _test_single_adapter(adapter) -> dict:
    """
    在后台线程中测试单个数据源适配器
    避免阻塞事件循环
    """
    result = {
        "name": adapter.name,
        "priority": adapter.priority,
        "available": True,
        "tests": {}
    }
    
    # 测试股票列表获取（在后台线程中执行）
    try:
        df = await asyncio.to_thread(adapter.get_stock_list)
        if df is not None and not df.empty:
            result["tests"]["stock_list"] = {
                "success": True,
                "count": len(df),
                "message": f"Successfully fetched {len(df)} stocks"
            }
    except Exception as e:
        result["tests"]["stock_list"] = {
            "success": False,
            "message": f"Error: {str(e)}"
        }
    
    # 测试最新交易日期（在后台线程中执行）
    try:
        trade_date = await asyncio.to_thread(adapter.find_latest_trade_date)
        # ...
    except Exception as e:
        # ...
    
    # 测试每日基础数据（在后台线程中执行）
    try:
        trade_date = result["tests"]["trade_date"].get("date")
        if trade_date:
            df = await asyncio.to_thread(adapter.get_daily_basic, trade_date)
            # ...
    except Exception as e:
        # ...
    
    return result
```

#### 3. 并发测试所有适配器

```python
@router.post("/test-sources")
async def test_data_sources():
    """
    测试所有数据源的连接和数据获取能力
    
    注意：此接口会执行耗时操作（获取股票列表等），
    所有同步操作都在后台线程中执行，避免阻塞事件循环
    """
    manager = DataSourceManager()
    available_adapters = manager.get_available_adapters()
    
    # 并发测试所有适配器（在后台线程中执行）
    test_tasks = [_test_single_adapter(adapter) for adapter in available_adapters]
    test_results = await asyncio.gather(*test_tasks, return_exceptions=True)
    
    # 处理结果...
    return SyncResponse(
        success=True,
        message=f"Tested {len(test_results)} data sources",
        data={"test_results": test_results}
    )
```

### 修复后的架构

```
┌─────────────────────────────────────────┐
│  FastAPI 异步事件循环                    │
│  ┌─────────────────────────────────┐    │
│  │ test-sources 接口                │    │
│  │ ✅ 异步调用，不阻塞事件循环       │    │
│  │    await asyncio.to_thread(...)  │    │
│  │    ↓                             │    │
│  │  [后台线程池]                    │    │
│  │    adapter.get_stock_list()     │    │
│  │    (耗时 60 秒)                  │    │
│  └─────────────────────────────────┘    │
│                                          │
│  ┌─────────────────────────────────┐    │
│  │ notifications/unread_count      │    │
│  │ ✅ 立即响应 (< 1秒)              │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## 📊 修复效果

### 修复前
- ❌ 数据源测试期间，其他接口超时（30秒）
- ❌ 用户体验差，前端报错
- ❌ 事件循环被阻塞

### 修复后
- ✅ 数据源测试期间，其他接口正常响应（< 1秒）
- ✅ 用户体验好，前端不报错
- ✅ 事件循环不被阻塞
- ✅ 并发测试所有数据源，速度更快

## 🧪 测试方法

### 1. 使用测试脚本

```bash
python scripts/test_concurrent_api.py
```

这个脚本会：
1. 启动数据源测试
2. 在测试期间每秒发送一次通知接口请求
3. 统计成功率和响应时间

### 2. 手动测试

**终端1：启动后端**
```bash
cd d:\code\QuantScope
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

**终端2：测试数据源**
```bash
curl -X POST http://localhost:8000/api/sync/multi-source/test-sources
```

**终端3：并发测试通知接口**
```bash
# 在数据源测试期间，每秒发送一次请求
for i in {1..10}; do
  curl -H "Authorization: Bearer YOUR_TOKEN" \
       http://localhost:8000/api/notifications/unread_count
  sleep 1
done
```

### 3. 前端测试

1. 打开前端页面
2. 点击"数据源测试"按钮
3. 观察右上角的通知图标是否正常更新
4. 检查浏览器控制台是否有超时错误

## 📝 最佳实践

### 1. 识别阻塞操作

以下操作可能阻塞事件循环：
- ❌ 同步的数据库查询（pymongo）
- ❌ 同步的HTTP请求（requests）
- ❌ 同步的文件I/O（open/read/write）
- ❌ CPU密集型计算（大数据处理）
- ❌ 第三方库的同步方法（tushare/akshare/baostock）

### 2. 使用异步版本

优先使用异步版本：
- ✅ 异步数据库查询（motor）
- ✅ 异步HTTP请求（aiohttp/httpx）
- ✅ 异步文件I/O（aiofiles）

### 3. 无法避免时使用线程池

如果必须使用同步方法：
```python
# 使用 asyncio.to_thread() 在后台线程中执行
result = await asyncio.to_thread(sync_function, arg1, arg2)
```

### 4. 监控和日志

添加日志记录耗时操作：
```python
import time

start = time.time()
result = await asyncio.to_thread(expensive_operation)
elapsed = time.time() - start

if elapsed > 5:
    logger.warning(f"⚠️  耗时操作: {elapsed:.2f}秒")
```

## 🔮 未来改进

### 1. 异步数据源适配器

将数据源适配器改为异步版本：
```python
class AsyncTushareAdapter:
    async def get_stock_list(self):
        # 使用异步HTTP客户端
        async with aiohttp.ClientSession() as session:
            # ...
```

### 2. 缓存机制

添加缓存减少重复请求：
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_stock_list_cached():
    # ...
```

### 3. 后台任务队列

对于非常耗时的操作，使用任务队列：
```python
from app.worker import celery_app

@celery_app.task
def test_data_sources_task():
    # 在后台worker中执行
    # ...
```

## 📚 相关文档

- [FastAPI 并发和异步](https://fastapi.tiangolo.com/async/)
- [Python asyncio 文档](https://docs.python.org/3/library/asyncio.html)
- [asyncio.to_thread() 文档](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread)

## ✅ 总结

这次修复解决了一个典型的**异步编程陷阱**：

1. **问题**：在异步函数中调用同步的耗时操作，阻塞事件循环
2. **症状**：其他API接口超时，用户体验差
3. **解决**：使用 `asyncio.to_thread()` 将同步操作放到后台线程
4. **效果**：事件循环不被阻塞，所有接口正常响应

**关键教训**：
- ⚠️  `async def` 不等于"不会阻塞"
- ⚠️  同步调用会阻塞整个事件循环
- ✅ 使用 `asyncio.to_thread()` 处理同步操作
- ✅ 优先使用异步版本的库和方法

