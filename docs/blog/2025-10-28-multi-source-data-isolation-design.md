# 多数据源隔离存储设计与实现

**日期**: 2025-10-28  
**作者**: QuantScope 开发团队  
**标签**: `数据源管理` `数据隔离` `索引优化` `数据迁移`

---

## 📋 背景

### 问题描述

在多数据源同步系统中，Tushare、AKShare、BaoStock 三个数据源的数据都存储在同一个 `stock_basic_info` 集合中，但存在以下问题：

#### 问题1：数据相互覆盖

**现象**：
- 原设计使用 `code` 作为唯一索引
- 后运行的同步任务会覆盖先运行的数据
- 无法保留不同数据源的独立数据

**示例**：
```
1. Tushare 同步：688146 -> source="tushare", pe=75.55, pb=4.20, roe=12.5
2. AKShare 同步：688146 -> source="akshare", pe=NULL, pb=NULL, roe=NULL  ❌ 覆盖了 Tushare 的数据
3. BaoStock 同步：688146 -> source="baostock", pe=NULL, pb=NULL, roe=NULL  ❌ 再次覆盖
```

**影响**：
- ❌ 丢失高质量数据源（Tushare）的财务指标
- ❌ 无法追溯数据来源
- ❌ 数据质量不稳定

#### 问题2：数据质量差异

不同数据源提供的字段和数据质量不同：

| 数据源 | PE/PB/PS | ROE | 总市值 | 流通市值 | 数据时效性 |
|-------|---------|-----|--------|---------|-----------|
| **Tushare** | ✅ 完整 | ✅ 有 | ✅ 有 | ✅ 有 | 最新（T+1） |
| **AKShare** | ⚠️ 部分 | ❌ 无 | ⚠️ 部分 | ⚠️ 部分 | 较新 |
| **BaoStock** | ❌ 无 | ❌ 无 | ❌ 无 | ❌ 无 | 较旧 |

---

## 🎯 解决方案

### 核心思路

**在同一个 `stock_basic_info` 集合中，通过 `(code, source)` 联合唯一索引实现数据源隔离**

### 设计原则

1. **数据源隔离**：同一只股票可以有多条记录（来自不同数据源）
2. **查询灵活**：支持指定数据源查询，或按优先级自动选择
3. **向后兼容**：兼容旧数据（无 `source` 字段）
4. **简单高效**：不增加存储复杂度，查询性能不受影响

---

## 🔧 技术实现

### 1. 索引设计

#### 修改前（单数据源）

```javascript
// 唯一索引：code
db.stock_basic_info.createIndex({ "code": 1 }, { unique: true });
```

**问题**：同一 `code` 只能有一条记录

#### 修改后（多数据源隔离）

```javascript
// 🔥 联合唯一索引：(code, source)
db.stock_basic_info.createIndex({ "code": 1, "source": 1 }, { unique: true });

// 辅助索引
db.stock_basic_info.createIndex({ "code": 1 });    // 查询所有数据源
db.stock_basic_info.createIndex({ "source": 1 });  // 按数据源查询
```

**优点**：
- ✅ 同一 `code` 可以有多条记录（不同 `source`）
- ✅ 保证 `(code, source)` 组合唯一
- ✅ 支持灵活查询

### 2. 同步服务修改

#### Tushare 同步 (`app/services/basics_sync_service.py`)

```python
# 修改前
ops.append(
    UpdateOne({"code": code}, {"$set": doc}, upsert=True)
)

# 修改后
ops.append(
    UpdateOne(
        {"code": code, "source": "tushare"},  # 🔥 联合查询条件
        {"$set": doc}, 
        upsert=True
    )
)
```

#### 多数据源同步 (`app/services/multi_source_basics_sync_service.py`)

```python
# 根据实际使用的数据源设置 source 字段
data_source = source_used if source_used else "multi_source"

doc = {
    "code": code,
    "source": data_source,  # 🔥 使用实际数据源
    ...
}

ops.append(
    UpdateOne(
        {"code": code, "source": data_source},  # 🔥 联合查询条件
        {"$set": doc}, 
        upsert=True
    )
)
```

#### BaoStock 同步 (`app/worker/baostock_sync_service.py`)

```python
# 确保 source 字段存在
if "source" not in basic_info:
    basic_info["source"] = "baostock"

# 使用 (code, source) 联合查询条件
await collection.update_one(
    {"code": basic_info["code"], "source": "baostock"},
    {"$set": basic_info},
    upsert=True
)
```

### 3. 查询服务修改

#### 股票数据服务 (`app/services/stock_data_service.py`)

```python
async def get_stock_basic_info(
    self, 
    symbol: str, 
    source: Optional[str] = None  # 🔥 新增参数
) -> Optional[StockBasicInfoExtended]:
    """
    获取股票基础信息
    Args:
        symbol: 6位股票代码
        source: 数据源 (tushare/akshare/baostock/multi_source)
                默认优先级：tushare > multi_source > akshare > baostock
    """
    db = get_mongo_db()
    symbol6 = str(symbol).zfill(6)
    
    if source:
        # 指定数据源
        query = {"code": symbol6, "source": source}
        doc = await db["stock_basic_info"].find_one(query, {"_id": 0})
    else:
        # 🔥 未指定数据源，按优先级查询
        source_priority = ["tushare", "multi_source", "akshare", "baostock"]
        doc = None
        
        for src in source_priority:
            query = {"code": symbol6, "source": src}
            doc = await db["stock_basic_info"].find_one(query, {"_id": 0})
            if doc:
                logger.debug(f"✅ 使用数据源: {src}")
                break
        
        # 兼容旧数据（无 source 字段）
        if not doc:
            doc = await db["stock_basic_info"].find_one(
                {"code": symbol6}, 
                {"_id": 0}
            )
    
    return StockBasicInfoExtended(**doc) if doc else None
```

#### API 路由 (`app/routers/stocks.py`)

```python
@router.get("/{code}/fundamentals", response_model=dict)
async def get_fundamentals(
    code: str, 
    source: Optional[str] = Query(None, description="数据源"),  # 🔥 新增参数
    current_user: dict = Depends(get_current_user)
):
    """
    获取基础面快照
    
    参数：
    - code: 股票代码
    - source: 数据源（可选），默认按优先级：tushare > multi_source > akshare > baostock
    """
    db = get_mongo_db()
    code6 = _zfill_code(code)
    
    if source:
        # 指定数据源
        query = {"code": code6, "source": source}
        b = await db["stock_basic_info"].find_one(query, {"_id": 0})
        if not b:
            raise HTTPException(
                status_code=404, 
                detail=f"未找到该股票在数据源 {source} 中的基础信息"
            )
    else:
        # 按优先级查询
        source_priority = ["tushare", "multi_source", "akshare", "baostock"]
        b = None
        
        for src in source_priority:
            query = {"code": code6, "source": src}
            b = await db["stock_basic_info"].find_one(query, {"_id": 0})
            if b:
                logger.info(f"✅ 使用数据源: {src}")
                break
        
        if not b:
            raise HTTPException(status_code=404, detail="未找到该股票的基础信息")
    
    # ... 后续处理
```

---

## 📊 数据迁移

### 迁移脚本

**文件**: `scripts/migrations/migrate_stock_basic_info_add_source_index.py`

#### 迁移步骤

1. **检查现有数据**：统计各数据源的记录数
2. **添加默认值**：为没有 `source` 字段的数据添加 `source='unknown'`
3. **处理重复数据**：检查并删除重复的 `(code, source)` 组合
4. **删除旧索引**：删除 `code` 唯一索引
5. **创建新索引**：创建 `(code, source)` 联合唯一索引
6. **创建辅助索引**：创建 `code` 和 `source` 非唯一索引
7. **验证结果**：检查迁移后的数据和索引

#### 运行方式

```bash
# 正常迁移
python scripts/migrations/migrate_stock_basic_info_add_source_index.py

# 回滚（恢复到单数据源模式）
python scripts/migrations/migrate_stock_basic_info_add_source_index.py rollback
```

---

## 🎯 使用示例

### 1. 指定数据源查询

```python
# 查询 Tushare 数据源
GET /api/stocks/688146/fundamentals?source=tushare

# 查询 AKShare 数据源
GET /api/stocks/688146/fundamentals?source=akshare
```

### 2. 自动优先级查询

```python
# 不指定数据源，按优先级自动选择
GET /api/stocks/688146/fundamentals

# 优先级：tushare > multi_source > akshare > baostock
```

### 3. 数据库直接查询

```javascript
// 查询所有数据源的数据
db.stock_basic_info.find({ "code": "688146" })

// 查询特定数据源
db.stock_basic_info.find({ "code": "688146", "source": "tushare" })

// 统计各数据源的记录数
db.stock_basic_info.aggregate([
  { $group: { _id: "$source", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
```

---

## 📈 效果对比

### 修改前

| 方面 | 状态 | 问题 |
|-----|------|-----|
| **数据隔离** | ❌ 无 | 数据相互覆盖 |
| **数据质量** | ❌ 不稳定 | 取决于最后运行的数据源 |
| **可追溯性** | ❌ 差 | 只记录最后一次数据源 |
| **查询灵活性** | ❌ 差 | 无法指定数据源 |

### 修改后

| 方面 | 状态 | 优点 |
|-----|------|-----|
| **数据隔离** | ✅ 完全隔离 | 每个数据源独立存储 |
| **数据质量** | ✅ 稳定 | 保留所有数据源的数据 |
| **可追溯性** | ✅ 完整 | 可追溯每个数据源的数据 |
| **查询灵活性** | ✅ 高 | 支持指定数据源或自动优先级 |

---

## 💡 最佳实践

### 1. 数据源优先级

建议的优先级顺序：

```
tushare > multi_source > akshare > baostock
```

**理由**：
- **Tushare**：数据最全面，包含完整的财务指标
- **multi_source**：多数据源聚合，数据较完整
- **AKShare**：开源免费，数据较新
- **BaoStock**：免费但数据较旧

### 2. 同步顺序

建议按以下顺序运行同步任务：

```
1. BaoStock 同步（基础数据）
2. AKShare 同步（补充数据）
3. Tushare 同步（最优数据）
```

**理由**：确保高质量数据源不被低质量数据源覆盖

### 3. 查询策略

- **默认查询**：不指定 `source`，使用优先级自动选择
- **特定需求**：需要特定数据源时，明确指定 `source` 参数
- **数据对比**：查询所有数据源，对比数据质量

---

## 🚀 后续优化方向

### 1. 数据质量评分

为每个数据源的数据添加质量评分：

```python
{
    "code": "688146",
    "source": "tushare",
    "data_quality_score": 95,  # 数据质量评分（0-100）
    "completeness": 0.98,      # 数据完整度
    ...
}
```

### 2. 智能数据合并

根据字段级别的数据质量，智能合并多个数据源：

```python
{
    "code": "688146",
    "source": "merged",
    "pe": 75.55,              # 来自 tushare
    "pe_source": "tushare",
    "roe": 12.5,              # 来自 akshare
    "roe_source": "akshare",
    ...
}
```

### 3. 数据源健康监控

监控各数据源的可用性和数据质量：

```python
{
    "source": "tushare",
    "status": "healthy",
    "last_sync": "2025-10-28T15:30:00",
    "success_rate": 0.99,
    "avg_response_time": 1.2
}
```

---

## 📦 相关文件

### 修改的文件

1. `scripts/setup/init_mongodb_indexes.py` - 索引初始化脚本
2. `scripts/mongo-init.js` - MongoDB 初始化脚本
3. `app/services/basics_sync_service.py` - Tushare 同步服务
4. `app/services/multi_source_basics_sync_service.py` - 多数据源同步服务
5. `app/worker/baostock_sync_service.py` - BaoStock 同步服务
6. `app/services/stock_data_service.py` - 股票数据服务
7. `app/routers/stocks.py` - API 路由

### 新增的文件

1. `scripts/migrations/migrate_stock_basic_info_add_source_index.py` - 数据迁移脚本
2. `docs/blog/2025-10-28-multi-source-data-isolation-design.md` - 本文档

---

## 🤝 贡献者

- **问题发现**: 用户反馈（多数据源相互覆盖）
- **方案设计**: QuantScope 开发团队
- **代码实现**: QuantScope 开发团队
- **文档编写**: QuantScope 开发团队

---

**最后更新**: 2025-10-28  
**版本**: v1.0.0-preview

