# 数据源优先级统一与系统稳定性优化

**日期**: 2025-10-30  
**作者**: QuantScope 开发团队  
**标签**: `数据源优先级` `重试机制` `MongoDB优化` `实时行情` `代码标准化` `系统稳定性`

---

## 📋 概述

2025年10月30日，我们完成了一次全面的系统稳定性和数据一致性优化工作。通过 **19 个提交**，解决了数据源优先级不统一、MongoDB批量写入超时、实时行情数据缺失等关键问题。本次更新显著提升了系统的稳定性、数据一致性和用户体验。

**核心改进**：
- 🎯 **数据源优先级统一**：修复优先级逻辑，实现端到端一致性
- 🔄 **重试机制完善**：为批量操作和数据同步添加智能重试
- ⚡ **MongoDB超时优化**：解决大批量数据处理超时问题
- 📊 **实时行情增强**：启动时自动回填历史收盘数据
- 🔧 **代码标准化**：修复AKShare接口返回代码格式问题
- 🛠️ **工具优化**：改进Tushare配置、数据源测试和日志系统

---

## 🎯 核心改进

### 1. 数据源优先级统一

#### 1.1 问题背景

**提交记录**：
- `719b9da` - feat: 优化数据源优先级管理和股票筛选功能
- `f632395` - fix: 修复数据查询不按优先级的问题
- `586e3dc` - fix: 修复数据源状态列表排序顺序
- `f094a62` - docs: 添加数据源优先级修复说明文档

**问题描述**：

系统中存在多处数据源优先级逻辑不一致的问题：

1. **优先级判断错误**
   - 代码中使用升序排序（数字越小优先级越高）
   - 但配置中期望降序（数字越大优先级越高）
   - 导致实际使用的数据源与配置相反

2. **查询不遵循优先级**
   - `app/routers/reports.py` 中 `get_stock_name()` 直接查询，不按优先级
   - `app/services/database_screening_service.py` 聚合查询混用不同数据源
   - `app/routers/stocks.py` 中 `get_fundamentals()` 按时间戳而非优先级查询

3. **前端显示顺序混乱**
   - 数据源状态列表排序与配置不一致
   - 用户无法直观看到当前使用的数据源

**示例问题**：
```python
# ❌ 错误的优先级逻辑（升序）
source_priority = ["baostock", "akshare", "tushare"]  # 实际使用 baostock

# ✅ 正确的优先级逻辑（降序）
source_priority = ["tushare", "akshare", "baostock"]  # 实际使用 tushare
```

#### 1.2 解决方案

**步骤 1：统一优先级定义**

明确优先级规则：**数字越大，优先级越高**

```python
# 默认优先级配置
DEFAULT_PRIORITIES = {
    "tushare": 3,    # 最高优先级
    "akshare": 2,    # 中等优先级
    "baostock": 1    # 最低优先级
}
```

**步骤 2：从数据库动态加载优先级**

```python
# app/services/data_sources/base.py
class BaseDataSourceAdapter(ABC):
    def __init__(self):
        self._priority = None
    
    async def load_priority_from_db(self):
        """从数据库加载优先级配置"""
        db = await get_mongo_db()
        config = await db.datasource_groupings.find_one(
            {"source": self.source_name}
        )
        if config:
            self._priority = config.get("priority", 1)
        else:
            self._priority = DEFAULT_PRIORITIES.get(self.source_name, 1)
```

**步骤 3：修复所有查询接口**

```python
# app/routers/reports.py - 按优先级查询股票名称
async def get_stock_name(code: str) -> str:
    """按数据源优先级查询股票名称"""
    db = await get_mongo_db()
    
    # 按优先级顺序尝试
    for source in ["tushare", "akshare", "baostock"]:
        doc = await db.stock_basic_info.find_one(
            {"code": code, "source": source},
            {"name": 1}
        )
        if doc:
            return doc.get("name", code)
    
    # 兼容旧数据（没有 source 字段）
    doc = await db.stock_basic_info.find_one(
        {"code": code},
        {"name": 1}
    )
    return doc.get("name", code) if doc else code
```

```python
# app/services/database_screening_service.py - 筛选时按优先级
async def screen(self, criteria: ScreeningCriteria) -> List[Dict]:
    """股票筛选，只使用优先级最高的数据源"""
    # 获取优先级最高的数据源
    primary_source = await self._get_primary_source()
    
    # 聚合查询时添加数据源过滤
    pipeline = [
        {"$match": {"source": primary_source}},  # 🔥 只查询主数据源
        # ... 其他筛选条件
    ]
    
    results = await db.stock_basic_info.aggregate(pipeline).to_list(None)
    return results
```

**步骤 4：修复前端排序**

```typescript
// frontend/src/components/Sync/DataSourceStatus.vue
const sortedSources = computed(() => {
  return [...dataSources.value].sort((a, b) => 
    b.priority - a.priority  // 🔥 降序：优先级高的在前
  );
});
```

**步骤 5：添加当前数据源显示**

```vue
<!-- frontend/src/views/Screening/index.vue -->
<template>
  <div class="screening-page">
    <el-alert type="info" :closable="false">
      <template #title>
        当前数据源：{{ currentDataSource }}
        <el-tag :type="getSourceTagType(currentDataSource)">
          优先级 {{ currentPriority }}
        </el-tag>
      </template>
    </el-alert>
    <!-- 筛选表单 -->
  </div>
</template>
```

**效果**：
- ✅ 所有查询统一按优先级执行
- ✅ 前端显示顺序与配置一致
- ✅ 用户可以清楚看到当前使用的数据源
- ✅ 避免混用不同数据源的数据

---

### 2. 批量操作重试机制

#### 2.1 问题背景

**提交记录**：
- `1b97aed` - feat: 为批量操作添加重试机制，改进超时处理
- `281587e` - feat: 为多源基础数据同步添加重试机制
- `4da35a0` - feat: 为Tushare基础数据同步添加重试机制

**问题描述**：

在批量写入和数据同步过程中，经常遇到以下问题：

1. **网络波动导致失败**
   - 临时网络抖动导致写入失败
   - 一次失败就放弃，数据丢失

2. **MongoDB临时超时**
   - 高负载时偶尔超时
   - 没有重试机制，数据不完整

3. **API限流**
   - 数据源接口偶尔限流
   - 没有自动重试，同步失败

**错误示例**：
```
❌ 批量写入失败: mongodb:27017: timed out
❌ 同步失败: Connection reset by peer
❌ API调用失败: Rate limit exceeded
```

#### 2.2 解决方案

**步骤 1：实现通用重试方法**

```python
# app/services/historical_data_service.py
async def _execute_bulk_write_with_retry(
    self,
    symbol: str,
    operations: List,
    max_retries: int = 3
) -> int:
    """
    执行批量写入，支持重试
    
    Args:
        symbol: 股票代码
        operations: 批量操作列表
        max_retries: 最大重试次数
    
    Returns:
        成功写入的记录数
    """
    saved_count = 0
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            result = await self.collection.bulk_write(
                operations, 
                ordered=False  # 🔥 非顺序执行，最大化成功率
            )
            saved_count = result.upserted_count + result.modified_count
            
            if retry_count > 0:
                logger.info(
                    f"✅ {symbol} 重试成功 "
                    f"(第{retry_count}次重试，保存{saved_count}条)"
                )
            
            return saved_count
            
        except asyncio.TimeoutError as e:
            retry_count += 1
            if retry_count < max_retries:
                wait_time = 2 ** retry_count  # 🔥 指数退避：2秒、4秒、8秒
                logger.warning(
                    f"⚠️ {symbol} 批量写入超时 "
                    f"(第{retry_count}/{max_retries}次重试)，"
                    f"等待{wait_time}秒后重试..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"❌ {symbol} 批量写入失败，"
                    f"已重试{max_retries}次: {e}"
                )
                return 0
                
        except Exception as e:
            # 🔥 非超时错误，直接返回，避免无限重试
            logger.error(f"❌ {symbol} 批量写入失败: {e}")
            return 0
    
    return saved_count
```

**步骤 2：应用到历史数据同步**

```python
# app/services/historical_data_service.py
async def save_historical_data(
    self,
    symbol: str,
    data: List[Dict],
    period: str = "daily"
) -> int:
    """保存历史数据，使用重试机制"""
    operations = []
    
    for record in data:
        operations.append(
            UpdateOne(
                {"code": symbol, "date": record["date"], "period": period},
                {"$set": record},
                upsert=True
            )
        )
    
    # 🔥 使用重试机制执行批量写入
    saved_count = await self._execute_bulk_write_with_retry(
        symbol, 
        operations
    )
    
    logger.info(
        f"✅ {symbol} 保存完成: "
        f"新增{saved_count}条，共{len(data)}条"
    )
    
    return saved_count
```

**效果**：
- ✅ 网络波动时自动重试，避免数据丢失
- ✅ 指数退避策略，避免频繁重试加重负载
- ✅ 区分超时和其他错误，避免无限重试
- ✅ 详细的重试日志，便于问题诊断

---

### 3. MongoDB超时优化

#### 3.1 问题背景

**提交记录**：
- `45a306b` - fix: 增加MongoDB超时参数配置，解决大量历史数据处理超时问题
- `c3b0a33` - fix: 改进MongoDB数据源日志，明确显示具体数据源类型

**问题描述**：

在处理大量历史数据时，频繁出现MongoDB超时错误：

```
❌ 000597 批量写入失败: mongodb:27017: timed out 
(configured timeouts: socketTimeoutMS: 20000.0ms, connectTimeoutMS: 10000.0ms)
```

**根本原因**：
1. **超时配置过短**
   - `socketTimeoutMS: 20秒` - 对于大批量写入不够
   - `connectTimeoutMS: 10秒` - 高负载时连接慢

2. **日志不够明确**
   - 显示 `[数据来源: MongoDB]` 不够具体
   - 无法判断是哪个数据源（tushare/akshare/baostock）

#### 3.2 解决方案

**步骤 1：增加超时配置参数**

```python
# app/core/config.py
class Settings(BaseSettings):
    # MongoDB超时参数（毫秒）
    MONGO_CONNECT_TIMEOUT_MS: int = 30000      # 30秒（原10秒）
    MONGO_SOCKET_TIMEOUT_MS: int = 60000       # 60秒（原20秒）
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = 5000  # 5秒
```

```env
# .env.example / .env.docker
# MongoDB连接池与超时配置
MONGO_MAX_CONNECTIONS=100
MONGO_MIN_CONNECTIONS=10

# MongoDB超时参数（毫秒）- 用于处理大量历史数据
MONGO_CONNECT_TIMEOUT_MS=30000      # 连接超时：30秒
MONGO_SOCKET_TIMEOUT_MS=60000       # 套接字超时：60秒
MONGO_SERVER_SELECTION_TIMEOUT_MS=5000  # 服务器选择超时：5秒
```

**步骤 2：应用到所有MongoDB连接**

```python
# app/core/database.py
async def get_mongo_db() -> AsyncIOMotorDatabase:
    """获取MongoDB数据库连接（异步）"""
    global _mongo_client

    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(
            settings.MONGO_URI,
            maxPoolSize=settings.MONGO_MAX_CONNECTIONS,
            minPoolSize=settings.MONGO_MIN_CONNECTIONS,
            connectTimeoutMS=settings.MONGO_CONNECT_TIMEOUT_MS,  # 🔥 30秒
            socketTimeoutMS=settings.MONGO_SOCKET_TIMEOUT_MS,    # 🔥 60秒
            serverSelectionTimeoutMS=settings.MONGO_SERVER_SELECTION_TIMEOUT_MS
        )
        logger.info(
            f"✅ MongoDB连接已建立 "
            f"(connectTimeout={settings.MONGO_CONNECT_TIMEOUT_MS}ms, "
            f"socketTimeout={settings.MONGO_SOCKET_TIMEOUT_MS}ms)"
        )

    return _mongo_client[settings.MONGO_DB_NAME]
```

**步骤 3：改进数据源日志**

```python
# tradingagents/dataflows/cache/mongodb_cache_adapter.py
async def get_daily_data(self, symbol: str) -> Optional[pd.DataFrame]:
    """获取日线数据，显示具体数据源"""
    tried_sources = []

    for source in ["tushare", "akshare", "baostock"]:
        logger.debug(f"📊 [MongoDB查询] 尝试数据源: {source}, symbol={symbol}")

        cursor = self.db[collection].find(
            {"code": symbol, "source": source}
        )
        docs = await cursor.to_list(length=None)

        if docs:
            logger.info(f"✅ [MongoDB-{source}] 找到{len(docs)}条daily数据: {symbol}")
            return pd.DataFrame(docs)
        else:
            logger.debug(f"⚠️ [MongoDB-{source}] 未找到daily数据: {symbol}")
            tried_sources.append(source)

    logger.warning(
        f"❌ [数据来源: MongoDB] "
        f"所有数据源({', '.join(tried_sources)})都没有daily数据: {symbol}"
    )
    return None
```

**效果**：
- ✅ 大批量数据处理不再超时
- ✅ 用户可以根据环境灵活调整超时时间
- ✅ 日志清晰显示具体数据源，便于问题定位
- ✅ 向后兼容，使用合理的默认值

---

### 4. 实时行情启动回填

#### 4.1 问题背景

**提交记录**：
- `cf892e3` - feat: 程序启动时自动从历史数据导入收盘数据到market_quotes

**问题描述**：

在非交易时段启动系统时，`market_quotes` 集合为空，导致：

1. **前端显示空白**
   - 股票列表没有价格信息
   - K线图无法显示
   - 用户体验差

2. **筛选功能受限**
   - 无法按涨跌幅筛选
   - 无法按价格筛选

3. **需要手动触发同步**
   - 用户需要手动触发实时行情同步
   - 增加操作复杂度

#### 4.2 解决方案

**步骤 1：实现历史数据回填方法**

```python
# app/services/quotes_ingestion_service.py
async def backfill_from_historical_data(self) -> Dict[str, Any]:
    """
    从历史数据导入最新交易日的收盘数据到 market_quotes

    仅当 market_quotes 集合为空时执行
    """
    db = await get_mongo_db()

    # 1. 检查 market_quotes 是否为空
    count = await db[self.collection_name].count_documents({})
    if count > 0:
        logger.info(f"📊 market_quotes 已有 {count} 条数据，跳过回填")
        return {"skipped": True, "reason": "collection_not_empty"}

    # 2. 检查历史数据集合是否为空
    historical_count = await db.stock_daily_quotes.count_documents({})
    if historical_count == 0:
        logger.warning("⚠️ stock_daily_quotes 集合为空，无法回填")
        return {"skipped": True, "reason": "no_historical_data"}

    # 3. 获取最新交易日
    pipeline = [
        {"$group": {"_id": None, "max_date": {"$max": "$date"}}},
    ]
    result = await db.stock_daily_quotes.aggregate(pipeline).to_list(1)

    if not result:
        logger.warning("⚠️ 无法获取最新交易日")
        return {"skipped": True, "reason": "no_max_date"}

    latest_date = result[0]["max_date"]
    logger.info(f"📅 最新交易日: {latest_date}")

    # 4. 查询最新交易日的所有股票数据
    cursor = db.stock_daily_quotes.find(
        {"date": latest_date},
        {"_id": 0}
    )
    historical_records = await cursor.to_list(length=None)

    if not historical_records:
        logger.warning(f"⚠️ {latest_date} 没有历史数据")
        return {"skipped": True, "reason": "no_data_for_date"}

    # 5. 转换为 market_quotes 格式并批量插入
    operations = []
    for record in historical_records:
        quote = {
            "code": record["code"],
            "name": record.get("name", ""),
            "price": record.get("close", 0),
            "open": record.get("open", 0),
            "high": record.get("high", 0),
            "low": record.get("low", 0),
            "volume": record.get("volume", 0),
            "amount": record.get("amount", 0),
            "change_pct": record.get("change_pct", 0),
            "timestamp": datetime.now(self.tz),
            "source": "historical_backfill",
            "date": latest_date
        }
        operations.append(
            UpdateOne(
                {"code": quote["code"]},
                {"$set": quote},
                upsert=True
            )
        )

    # 6. 批量写入
    result = await db[self.collection_name].bulk_write(operations, ordered=False)

    logger.info(
        f"✅ 从历史数据回填完成: "
        f"日期={latest_date}, "
        f"新增={result.upserted_count}, "
        f"更新={result.modified_count}"
    )

    return {
        "success": True,
        "date": latest_date,
        "total": len(historical_records),
        "upserted": result.upserted_count,
        "modified": result.modified_count
    }
```

**步骤 2：在启动时调用回填**

```python
# app/services/quotes_ingestion_service.py
async def backfill_last_close_snapshot_if_needed(self):
    """
    启动时检查并回填行情数据

    策略：
    1. 如果 market_quotes 为空 -> 从历史数据回填
    2. 如果 market_quotes 不为空但数据陈旧 -> 使用实时接口更新
    """
    db = await get_mongo_db()
    count = await db[self.collection_name].count_documents({})

    if count == 0:
        # 🔥 集合为空，从历史数据回填
        logger.info("📊 market_quotes 为空，尝试从历史数据回填...")
        await self.backfill_from_historical_data()
    else:
        # 集合不为空，检查数据是否陈旧
        latest_doc = await db[self.collection_name].find_one(
            {},
            sort=[("timestamp", -1)]
        )

        if latest_doc:
            latest_time = latest_doc.get("timestamp")
            if latest_time:
                age = datetime.now(self.tz) - latest_time
                if age.total_seconds() > 3600:  # 超过1小时
                    logger.info(f"⚠️ 行情数据已陈旧 {age}，尝试更新...")
                    # 使用实时接口更新
                    await self._fetch_and_save_quotes()
```

**效果**：
- ✅ 非交易时段启动也能看到行情数据
- ✅ 自动化处理，无需手动干预
- ✅ 使用历史收盘价作为基准，数据准确
- ✅ 不影响交易时段的实时更新

---

### 5. AKShare代码标准化

#### 5.1 问题背景

**提交记录**：
- `cc32639` - fix: 修复AKShare新浪接口股票代码带交易所前缀的问题

**问题描述**：

AKShare的新浪财经接口返回的股票代码带有交易所前缀：

```python
# 新浪接口返回的代码格式
"sz000001"  # 深圳平安银行
"sh600036"  # 上海招商银行
"bj430047"  # 北京股票
```

**问题影响**：
1. **数据库查询失败**
   - 数据库中存储的是6位标准码
   - 带前缀的代码无法匹配

2. **前端显示异常**
   - 前端期望6位代码
   - 带前缀的代码显示不正确

3. **跨模块不一致**
   - 不同数据源返回格式不同
   - 增加处理复杂度

#### 5.2 解决方案

**步骤 1：实现代码标准化方法**

```python
# app/services/data_sources/akshare_adapter.py
@staticmethod
def _normalize_stock_code(code: str) -> str:
    """
    标准化股票代码为6位数字

    处理以下格式：
    - sz000001 -> 000001
    - sh600036 -> 600036
    - bj430047 -> 430047
    - 000001 -> 000001 (已标准化)

    Args:
        code: 原始股票代码

    Returns:
        标准化的6位股票代码
    """
    if not code:
        return code

    # 去除交易所前缀（sz/sh/bj）
    code = code.lower()
    if code.startswith(('sz', 'sh', 'bj')):
        code = code[2:]

    # 确保是6位数字
    return code.zfill(6)
```

**步骤 2：应用到实时行情获取**

```python
# app/services/data_sources/akshare_adapter.py
async def get_realtime_quotes(
    self,
    symbols: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """获取实时行情，标准化股票代码"""
    try:
        # 获取新浪接口数据
        df = ak.stock_zh_a_spot()

        quotes = []
        for _, row in df.iterrows():
            # 🔥 标准化股票代码
            code = self._normalize_stock_code(row.get("代码", ""))

            if not code:
                continue

            quote = {
                "code": code,  # 标准化后的6位代码
                "name": row.get("名称", ""),
                "price": float(row.get("最新价", 0)),
                "open": float(row.get("今开", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                # ...
            }
            quotes.append(quote)

        return quotes

    except Exception as e:
        logger.error(f"❌ AKShare获取实时行情失败: {e}")
        return []
```

**步骤 3：应用到行情入库服务**

```python
# app/services/quotes_ingestion_service.py
async def _bulk_upsert(self, quotes: List[Dict]) -> int:
    """批量更新行情，标准化股票代码"""
    operations = []

    for quote in quotes:
        # 🔥 标准化股票代码
        code = self._normalize_stock_code(quote.get("code", ""))

        if not code or len(code) != 6:
            logger.warning(f"⚠️ 跳过无效代码: {quote.get('code')}")
            continue

        quote["code"] = code  # 使用标准化代码

        operations.append(
            UpdateOne(
                {"code": code},
                {"$set": quote},
                upsert=True
            )
        )

    result = await self.collection.bulk_write(operations, ordered=False)
    return result.upserted_count + result.modified_count

@staticmethod
def _normalize_stock_code(code: str) -> str:
    """标准化股票代码为6位数字"""
    if not code:
        return code

    code = str(code).lower()
    # 去除交易所前缀
    if code.startswith(('sz', 'sh', 'bj')):
        code = code[2:]

    return code.zfill(6)
```

**效果**：
- ✅ 所有股票代码统一为6位标准格式
- ✅ 数据库查询正常
- ✅ 前端显示正确
- ✅ 跨模块格式一致

---

### 6. 工具与诊断优化

#### 6.1 Tushare配置优化

**提交记录**：
- `fd372c7` - feat: 改进Tushare Token配置优先级和测试超时

**改进内容**：

1. **Token获取优先级调整**
   ```python
   # 优先使用数据库配置
   db_token = await self._get_token_from_db()
   if db_token:
       try:
           # 测试数据库Token（10秒超时）
           await self._test_connection(db_token, timeout=10)
           return db_token
       except Exception:
           logger.warning("⚠️ 数据库Token测试失败，尝试.env配置")

   # 降级到.env配置
   env_token = os.getenv("TUSHARE_TOKEN")
   if env_token:
       return env_token

   raise ValueError("❌ 未找到有效的Tushare Token")
   ```

2. **添加测试连接超时**
   - 测试连接超时设置为10秒
   - 避免长时间等待
   - 超时时自动降级

3. **改进日志**
   - 显示当前尝试的Token来源
   - 显示超时时间
   - 清晰的降级流程日志

**效果**：
- ✅ 用户在Web后台修改Token后立即生效
- ✅ 网络波动或Token失效时自动降级
- ✅ 测试连接更快，不会长时间等待

#### 6.2 数据源测试简化

**提交记录**：
- `8e4eecc` - refactor: 简化数据源连通性测试接口
- `b17deee` - fix: 修复数据源测试接口参数传递问题

**改进内容**：

1. **简化测试逻辑**
   ```python
   # ❌ 之前：获取完整数据（慢）
   stocks = await adapter.get_stock_list()  # 5444条
   financials = await adapter.get_financials()  # 5431条

   # ✅ 现在：只做连通性测试（快）
   await adapter.test_connection()  # 轻量级测试
   ```

2. **快速返回结果**
   - 测试超时：10秒
   - 并发测试所有数据源
   - 快速返回连通性状态

3. **简化响应格式**
   ```python
   # ❌ 之前：复杂的嵌套结构
   {
       "source": "tushare",
       "tests": {
           "connection": {"passed": true},
           "stock_list": {"passed": true, "count": 5444}
       }
   }

   # ✅ 现在：简洁的扁平结构
   {
       "source": "tushare",
       "available": true,
       "message": "连接成功"
   }
   ```

**效果**：
- ✅ 测试速度快10倍以上
- ✅ 减少网络带宽消耗
- ✅ 不占用API配额
- ✅ 用户体验更好

#### 6.3 DeepSeek日志优化

**提交记录**：
- `88149c7` - fix: 修复DeepSeek市场分析问题和日志显示问题
- `66ed4c6` - fix: 改进DeepSeek新闻分析的日志和错误处理

**改进内容**：

1. **修复DeepSeek无法理解任务的问题**
   ```python
   # ❌ 之前：只传股票代码
   initial_message = ("human", "601179")

   # ✅ 现在：传明确的分析请求
   initial_message = HumanMessage(
       content=f"请对股票 {company_name}({symbol}) 进行全面分析"
   )
   ```

2. **改进日志显示**
   ```python
   # 增加日志长度从200到500字符
   # 添加元组消息的特殊处理
   # 记录LLM原始响应内容
   ```

3. **添加详细的调试日志**
   - 记录调用参数
   - 记录返回结果长度和预览
   - 记录完整异常堆栈

**效果**：
- ✅ DeepSeek能正确理解分析任务
- ✅ 日志更清晰，便于问题诊断
- ✅ 显示真实数据来源而不是current_source

#### 6.4 其他改进

**提交记录**：
- `e2e88c8` - 增加中文字体支持
- `dfbead7` - docs: 添加2025-10-29工作博客
- `1a4b1ca` - docs: 补充系统日志功能说明到2025-10-29工作博客

**改进内容**：
- 添加中文字体支持，优化PDF/Word导出的中文显示
- 完善文档，补充10-29工作日志

---

## 📊 影响范围

### 修改的文件

**后端（15个文件）**：
- `app/core/config.py` - 添加MongoDB超时配置
- `app/core/database.py` - 应用超时配置
- `app/routers/reports.py` - 修复优先级查询
- `app/routers/stocks.py` - 修复优先级查询
- `app/routers/multi_source_sync.py` - 优化测试接口
- `app/services/historical_data_service.py` - 添加重试机制
- `app/services/basics_sync_service.py` - 添加重试机制
- `app/services/multi_source_basics_sync_service.py` - 添加重试机制
- `app/services/database_screening_service.py` - 修复优先级筛选
- `app/services/quotes_ingestion_service.py` - 添加启动回填
- `app/services/data_sources/base.py` - 动态加载优先级
- `app/services/data_sources/akshare_adapter.py` - 代码标准化
- `tradingagents/dataflows/providers/china/tushare.py` - Token优先级
- `tradingagents/dataflows/cache/mongodb_cache_adapter.py` - 改进日志
- `tradingagents/agents/analysts/news_analyst.py` - 改进日志

**前端（4个文件）**：
- `frontend/src/views/Screening/index.vue` - 添加数据源显示
- `frontend/src/components/Sync/DataSourceStatus.vue` - 修复排序
- `frontend/src/components/Dashboard/MultiSourceSyncCard.vue` - 修复排序
- `frontend/src/api/sync.ts` - 更新API接口

**配置文件（2个文件）**：
- `.env.example` - 添加MongoDB超时配置
- `.env.docker` - 添加MongoDB超时配置

**文档（1个文件）**：
- `docs/blog/2025-10-29-data-source-unification-and-report-export-features.md`

---

## ✅ 验证方法

### 1. 数据源优先级验证

```bash
# 1. 检查数据源配置
curl http://localhost:8000/api/multi-source-sync/status

# 2. 测试股票筛选
curl http://localhost:8000/api/screening/screen \
  -H "Content-Type: application/json" \
  -d '{"pe_min": 0, "pe_max": 20}'

# 3. 检查前端显示
# 访问股票筛选页面，查看"当前数据源"显示
```

### 2. 重试机制验证

```bash
# 1. 观察历史数据同步日志
tail -f logs/app.log | grep "重试"

# 2. 模拟网络波动
# 在同步过程中临时断开网络，观察是否自动重试

# 3. 检查同步结果
# 确认数据完整性，没有因临时失败而丢失数据
```

### 3. MongoDB超时验证

```bash
# 1. 检查MongoDB连接日志
tail -f logs/app.log | grep "MongoDB连接"

# 2. 同步大量历史数据
curl -X POST http://localhost:8000/api/scheduler/trigger/sync_historical_data

# 3. 观察是否还有超时错误
tail -f logs/app.log | grep "timed out"
```

### 4. 启动回填验证

```bash
# 1. 清空market_quotes集合
mongo tradingagents --eval "db.market_quotes.deleteMany({})"

# 2. 重启后端服务
# 观察启动日志

# 3. 检查market_quotes是否有数据
mongo tradingagents --eval "db.market_quotes.countDocuments({})"

# 4. 访问前端，确认能看到行情数据
```

### 5. 代码标准化验证

```bash
# 1. 触发AKShare实时行情同步
curl -X POST http://localhost:8000/api/scheduler/trigger/akshare_quotes_sync

# 2. 检查market_quotes中的代码格式
mongo tradingagents --eval "db.market_quotes.find({}, {code: 1}).limit(10)"

# 3. 确认所有代码都是6位数字，没有sz/sh/bj前缀
```

---

## 🔄 升级指引

### 1. 更新环境变量

在 `.env` 文件中添加MongoDB超时配置：

```env
# MongoDB超时参数（毫秒）
MONGO_CONNECT_TIMEOUT_MS=30000
MONGO_SOCKET_TIMEOUT_MS=60000
MONGO_SERVER_SELECTION_TIMEOUT_MS=5000
```

### 2. 重启服务

```bash
# Docker部署
docker-compose down
docker-compose up -d

# 本地部署
# 停止后端服务
# 启动后端服务
```

### 3. 验证升级

```bash
# 1. 检查服务状态
curl http://localhost:8000/health

# 2. 检查数据源状态
curl http://localhost:8000/api/multi-source-sync/status

# 3. 测试数据同步
curl -X POST http://localhost:8000/api/scheduler/trigger/sync_stock_basic_info
```

### 4. 可选：清理旧数据

如果需要重新同步数据以应用新的优先级逻辑：

```bash
# ⚠️ 警告：此操作会删除所有基础数据，请谨慎操作

# 1. 备份数据
mongodump --db tradingagents --out /backup/$(date +%Y%m%d)

# 2. 清空基础数据集合
mongo tradingagents --eval "db.stock_basic_info.deleteMany({})"

# 3. 重新同步
curl -X POST http://localhost:8000/api/scheduler/trigger/sync_stock_basic_info
```

---

## 📝 相关提交

完整的19个提交记录（按时间顺序）：

1. `e2e88c8` - 增加中文字体支持
2. `c3b0a33` - fix: 改进MongoDB数据源日志，明确显示具体数据源类型
3. `88149c7` - fix: 修复DeepSeek市场分析问题和日志显示问题
4. `66ed4c6` - fix: 改进DeepSeek新闻分析的日志和错误处理
5. `dfbead7` - docs: 添加2025-10-29工作博客 - 数据源统一与报告导出功能
6. `1a4b1ca` - docs: 补充系统日志功能说明到2025-10-29工作博客
7. `45a306b` - fix: 增加MongoDB超时参数配置，解决大量历史数据处理超时问题
8. `1b97aed` - feat: 为批量操作添加重试机制，改进超时处理
9. `281587e` - feat: 为多源基础数据同步添加重试机制
10. `4da35a0` - feat: 为Tushare基础数据同步添加重试机制
11. `f632395` - fix: 修复数据查询不按优先级的问题
12. `f094a62` - docs: 添加数据源优先级修复说明文档
13. `fd372c7` - feat: 改进Tushare Token配置优先级和测试超时
14. `8e4eecc` - refactor: 简化数据源连通性测试接口
15. `b17deee` - fix: 修复数据源测试接口参数传递问题
16. `719b9da` - feat: 优化数据源优先级管理和股票筛选功能
17. `586e3dc` - fix: 修复数据源状态列表排序顺序
18. `cf892e3` - feat: 程序启动时自动从历史数据导入收盘数据到market_quotes
19. `cc32639` - fix: 修复AKShare新浪接口股票代码带交易所前缀的问题

---

## 🎉 总结

本次更新通过19个提交，全面提升了系统的稳定性和数据一致性：

- **数据源优先级统一**：修复了多处优先级逻辑不一致的问题，实现端到端一致性
- **重试机制完善**：为批量操作和数据同步添加智能重试，大幅提升成功率
- **MongoDB超时优化**：解决大批量数据处理超时问题，支持灵活配置
- **实时行情增强**：启动时自动回填历史收盘数据，提升非交易时段体验
- **代码标准化**：统一股票代码格式，消除跨模块不一致
- **工具优化**：改进Tushare配置、数据源测试和日志系统

这些改进显著提升了系统的可靠性、可维护性和用户体验，为后续功能开发奠定了坚实基础。

