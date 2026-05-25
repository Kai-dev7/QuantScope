# QuantScope 多账号配置隔离实施计划

> **目标**: `system_configs`、`llm_providers`、`market_categories`、`datasource_groupings`、`model_catalog` 按 user_id 隔离
> **原则**: 全局配置（user_id=None）作为兜底，用户配置（user_id=X）优先覆盖

---

## 数据模型变更（app/models/config.py）

### ✅ 已完成
- `SystemConfig.user_id: Optional[str]` 加字段
- `LLMProvider.user_id: Optional[str]` 加字段
- `ModelCatalog.user_id: Optional[str]` 加字段
- `MarketCategory.user_id: Optional[str]` 加字段
- `DataSourceGrouping.user_id: Optional[str]` 加字段

---

## ConfigService 改造（app/services/config_service.py）

### ✅ 已完成
1. `get_system_config(user_id)` — 多用户降级逻辑
2. `_create_default_config(user_id)` — 创建时写入 user_id
3. `save_system_config` — 禁用同用户旧配置
4. `get_llm_providers(user_id)` — 用户+全局合并，user 覆盖同 name 全局

### ⬜ 待完成
5. `update_llm_config` — 写入时取当前用户配置，写入 user_id
6. `set_default_llm` — 加 user_id 参数
7. `set_default_data_source` — 加 user_id 参数
8. `update_system_settings` — 加 user_id 参数
9. `add_llm_provider` — 写入时填 user_id
10. `update_llm_provider` — 限制只能修改自己的（或全局）
11. `delete_llm_provider` — 限制只能删除自己的
12. `toggle_llm_provider` — 限制只能切换自己的
13. `get_market_categories(user_id)` — 加 user_id 过滤
14. `add_market_category` — 写入 user_id
15. `update_market_category` — 限制只能修改自己的
16. `delete_market_category` — 限制只能删除自己的
17. `get_datasource_groupings(user_id)` — 加 user_id 过滤
18. `add_datasource_to_category` — 写入 user_id
19. `remove_datasource_from_category` — 限制只能操作自己的
20. `update_datasource_grouping` — 限制只能操作自己的

---

## Router 层改造（app/routers/config.py）

### ⬜ 待完成（传入 user_id 参数）

所有调用 config_service 方法的端点，需要从 `current_user` 提取 user_id 并传给 service：

```
GET  /config/system         → get_system_config(user_id) 
POST /config/llm/providers  → add_llm_provider(provider, user_id)
PUT  /config/llm/providers/{id} → update_llm_provider(id, data, user_id)
DELETE /config/llm/providers/{id} → delete_llm_provider(id, user_id)
POST /config/llm/models     → update_llm_config(cfg, user_id)
PUT  /config/llm/default    → set_default_llm(name, user_id)
PUT  /config/datasource/default → set_default_data_source(name, user_id)
PUT  /config/system/settings → update_system_settings(settings, user_id)
GET  /config/categories      → get_market_categories(user_id)
POST /config/categories      → add_market_category(cat, user_id)
PUT  /config/categories/{id} → update_market_category(id, req, user_id)
DELETE /config/categories/{id} → delete_market_category(id, user_id)
GET  /config/groupings       → get_datasource_groupings(user_id)
POST /config/groupings       → add_datasource_to_category(grp, user_id)
DELETE /config/groupings/{ds}/{cat} → remove_datasource_from_category(ds, cat, user_id)
PUT  /config/groupings/{ds}/{cat}  → update_datasource_grouping(ds, cat, req, user_id)
```

---

## 分析任务/报告隔离（P1 — analysis_tasks / analysis_reports）

### 待完成
- `simple_analysis_service.py` 中写入 `analysis_tasks` 时强制写入 `user_id`
- `reports.py` 中查询加 `user_id` 过滤
- `analysis_service.py` 中写入任务时写入 `user_id`

---

## 调度任务隔离（P2 — scheduler）

### 待完成
- `scheduler_service.py` 中所有 `scheduler_executions` 查询加 `user_id` 过滤
- 写入时写入 `user_id`

---

## 改造策略说明

### 查询逻辑（降级）
```
用户查询配置时：
  1. 查 user_id = 当前用户 → 有则返回
  2. 查 user_id = None（全局）→ 有则返回（兜底）
  3. 无 → 创建用户专属默认配置
```

### 写入逻辑
```
用户保存配置时：
  - 写入 user_id = 当前用户
  - 禁用同用户的旧激活配置（不影响全局和其他用户）
```

### LLM 厂商/模型目录特殊处理
```
用户获取厂商列表时：
  - 全局厂商（user_id=None）为基础
  - 用户专属厂商（user_id=X）覆盖同 name 的全局厂商
  - 返回合并后的列表
```

---

## 验证步骤
1. 账号A配置 glm-4，账号B不配置 → B应看到全局 glm-4
2. 账号A配置自定义厂商，账号B → B不应看到A的厂商
3. 账号A配置保存 → 不影响账号B的配置
4. 已有数据的兼容：user_id=None 视为全局