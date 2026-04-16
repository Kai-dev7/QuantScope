# MongoDB ObjectId 序列化错误修复

**日期**: 2025-10-12  
**问题**: `Unable to serialize unknown type: <class 'bson.objectid.ObjectId'>`

---

## 问题描述

### 错误信息

```
Unable to serialize unknown type: <class 'bson.objectid.ObjectId'>
```

### 错误场景

当从 MongoDB 查询数据并尝试返回 JSON 响应时，BSON 的 `ObjectId` 类型无法直接序列化为 JSON。

### 触发条件

1. 从 MongoDB 查询数据
2. 查询结果包含 `_id` 字段（默认的 ObjectId 类型）
3. 尝试将结果序列化为 JSON 返回给前端

### 错误堆栈

```python
File "D:\code\QuantScope\app\services\news_data_service.py", line 325
    self.logger.info(f"📊 查询新闻数据返回 {len(results)} 条记录")
    return results  # ❌ results 包含 ObjectId，无法序列化
```

---

## 根本原因

MongoDB 的 `_id` 字段默认是 `ObjectId` 类型，这是 BSON 特有的类型，不是标准的 JSON 类型。当使用 FastAPI 或其他 JSON 序列化器时，会抛出序列化错误。

### 为什么会有这个问题？

1. **MongoDB 默认行为**: 每个文档都有一个 `_id` 字段，类型为 `ObjectId`
2. **JSON 标准**: JSON 只支持基本类型（string, number, boolean, null, array, object）
3. **FastAPI 序列化**: FastAPI 使用 Pydantic 进行 JSON 序列化，不支持 `ObjectId`

---

## 解决方案

### 方案1: 查询时排除 `_id` 字段（推荐用于不需要 ID 的场景）

```python
# 在查询时排除 _id
doc = await collection.find_one(
    {"symbol": symbol},
    {"_id": 0}  # ✅ 排除 _id 字段
)
```

**优点**:
- ✅ 简单直接
- ✅ 不需要额外处理

**缺点**:
- ❌ 无法获取文档 ID
- ❌ 不适用于需要 ID 的场景

### 方案2: 转换 ObjectId 为字符串（推荐用于需要 ID 的场景）

```python
# 查询后转换 ObjectId
results = await cursor.to_list(length=None)

# 转换 ObjectId 为字符串
for result in results:
    if '_id' in result:
        result['_id'] = str(result['_id'])

return results  # ✅ 可以正常序列化
```

**优点**:
- ✅ 保留文档 ID
- ✅ 前端可以使用 ID 进行操作

**缺点**:
- ❌ 需要额外的转换步骤

### 方案3: 使用辅助函数（推荐用于多处使用）

```python
def convert_objectid_to_str(data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
    """
    转换 MongoDB ObjectId 为字符串，避免 JSON 序列化错误
    
    Args:
        data: 单个文档或文档列表
        
    Returns:
        转换后的数据
    """
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and '_id' in item:
                item['_id'] = str(item['_id'])
        return data
    elif isinstance(data, dict):
        if '_id' in data:
            data['_id'] = str(data['_id'])
        return data
    return data

# 使用
results = await cursor.to_list(length=None)
results = convert_objectid_to_str(results)  # ✅ 统一处理
return results
```

**优点**:
- ✅ 代码复用
- ✅ 统一处理逻辑
- ✅ 易于维护

---

## 已修复的文件

### 1. `app/services/news_data_service.py`

#### 修复位置

- `query_news()` 方法（第323-331行）
- `search_messages()` 方法（第549-556行）

#### 修复内容

```python
# 添加辅助函数
from bson import ObjectId

def convert_objectid_to_str(data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
    """转换 MongoDB ObjectId 为字符串"""
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and '_id' in item:
                item['_id'] = str(item['_id'])
        return data
    elif isinstance(data, dict):
        if '_id' in data:
            data['_id'] = str(data['_id'])
        return data
    return data

# 在查询后使用
results = await cursor.to_list(length=None)
results = convert_objectid_to_str(results)  # ✅ 转换 ObjectId
return results
```

### 2. `app/services/internal_message_service.py`

#### 修复位置

- `query_internal_messages()` 方法（第232-239行）

#### 修复内容

```python
# 添加相同的辅助函数
from bson import ObjectId

def convert_objectid_to_str(data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
    """转换 MongoDB ObjectId 为字符串"""
    # ... 同上

# 在查询后使用
messages = await cursor.to_list(length=params.limit)
messages = convert_objectid_to_str(messages)  # ✅ 转换 ObjectId
return messages
```

---

## 其他需要注意的服务

以下服务已经正确处理了 ObjectId（使用 `{"_id": 0}` 排除）：

### ✅ `app/services/stock_data_service.py`

```python
# 已正确排除 _id
doc = await db[self.basic_info_collection].find_one(
    {"$or": [{"symbol": symbol6}, {"code": symbol6}]},
    {"_id": 0}  # ✅ 排除 _id
)
```

### ✅ `app/services/operation_log_service.py`

```python
# 已正确转换 ObjectId
doc = await db[self.collection_name].find_one({"_id": ObjectId(log_id)})
if not doc:
    return None

doc = convert_objectid_to_str(doc)  # ✅ 转换 ObjectId
return OperationLogResponse(**doc)
```

### ✅ `app/services/tags_service.py`

```python
# 已正确转换 ObjectId
def _format_doc(self, doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id")),  # ✅ 转换为字符串
        "name": doc.get("name"),
        # ...
    }
```

---

## 验证方法

### 1. 测试新闻数据接口

```bash
# 测试获取最新新闻
curl http://localhost:8000/api/news-data/latest

# 应该返回正常的 JSON，不会报错
```

### 2. 测试内部消息接口

```bash
# 测试查询内部消息
curl http://localhost:8000/api/internal-messages/query

# 应该返回正常的 JSON，不会报错
```

### 3. 检查日志

```bash
# 查看日志，确认没有序列化错误
Get-Content logs/webapi.log -Tail 50 | Select-String "ObjectId|serialize"
```

---

## 最佳实践

### 1. 新增 MongoDB 查询服务时

**选择合适的方案**:

- **不需要 ID**: 使用 `{"_id": 0}` 排除
- **需要 ID**: 使用 `convert_objectid_to_str()` 转换

### 2. 统一的辅助函数

在每个需要的服务文件中添加：

```python
from bson import ObjectId

def convert_objectid_to_str(data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
    """转换 MongoDB ObjectId 为字符串，避免 JSON 序列化错误"""
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and '_id' in item:
                item['_id'] = str(item['_id'])
        return data
    elif isinstance(data, dict):
        if '_id' in data:
            data['_id'] = str(data['_id'])
        return data
    return data
```

### 3. 代码审查清单

在添加新的 MongoDB 查询时，检查：

- [ ] 是否使用了 `find()` 或 `find_one()`？
- [ ] 是否使用了 `to_list()` 或 `aggregate()`？
- [ ] 返回的数据是否包含 `_id` 字段？
- [ ] 是否需要返回 `_id` 给前端？
- [ ] 如果需要，是否已转换 ObjectId 为字符串？
- [ ] 如果不需要，是否已排除 `_id` 字段？

---

## 总结

### ✅ 问题已解决

1. ✅ `news_data_service.py` - 2处修复
2. ✅ `internal_message_service.py` - 1处修复

### 📝 修复方法

- 添加 `convert_objectid_to_str()` 辅助函数
- 在查询后统一转换 ObjectId 为字符串
- 保持代码一致性和可维护性

### 🎯 预防措施

- 新增 MongoDB 查询时，记得处理 ObjectId
- 使用统一的辅助函数
- 代码审查时检查 ObjectId 处理

---

## 参考资料

- [MongoDB ObjectId 文档](https://docs.mongodb.com/manual/reference/method/ObjectId/)
- [FastAPI JSON 序列化](https://fastapi.tiangolo.com/tutorial/encoder/)
- [Pydantic 自定义类型](https://pydantic-docs.helpmanual.io/usage/types/)

