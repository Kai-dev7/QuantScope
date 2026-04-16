# 股票数据SDK接入指南

本指南详细说明如何在TradingAgents系统中接入新的股票数据SDK，包括架构设计、接入流程、代码规范和测试验证。

## 📋 目录

- [系统架构](#系统架构)
- [接入流程](#接入流程)
- [代码规范](#代码规范)
- [数据标准化](#数据标准化)
- [测试验证](#测试验证)
- [部署配置](#部署配置)
- [常见问题](#常见问题)

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   前端/API      │    │   后端服务层      │    │   数据获取层     │
│                 │    │   (app/)         │    │ (tradingagents/) │
│ • Web界面       │◄──►│ • API路由        │◄──►│ • SDK适配器     │
│ • API接口       │    │ • 业务服务       │    │ • 数据工具      │
│ • CLI工具       │    │ • 数据同步服务   │    │ • 分析算法      │
└─────────────────┘    │ • 定时任务       │    └─────────────────┘
                       └──────────────────┘             │
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  标准化数据库     │    │   外部数据源     │
                       │   (MongoDB)      │    │                 │
                       │ • stock_basic_info│   │ • Tushare       │
                       │ • market_quotes   │    │ • AKShare       │
                       │ • 扩展集合       │    │ • Yahoo Finance │
                       └──────────────────┘    │ • 新SDK...      │
                                               └─────────────────┘
```

### 数据流向

```
外部SDK → tradingagents适配器 → app数据同步服务 → MongoDB存储 → app查询服务 → API/前端
```

### 目录结构说明

```
QuantScope/
├── app/                          # 后端服务 (FastAPI)
│   ├── services/                 # 业务服务层
│   │   └── stock_data_service.py # 数据访问服务
│   ├── worker/                   # 数据同步服务和定时任务
│   │   └── *_sync_service.py     # 各SDK的同步服务
│   ├── routers/                  # API路由
│   └── models/                   # 数据模型
├── tradingagents/                # 核心工具库
│   ├── dataflows/                # 数据获取适配器
│   │   ├── base_provider.py      # 基础接口
│   │   └── *_provider.py         # 各SDK适配器
│   └── agents/                   # 分析算法
└── frontend/                     # 前端界面
```

## 🚀 接入流程

### 步骤1: 创建SDK适配器 (tradingagents层)

在 `tradingagents/dataflows/` 目录下创建新的SDK适配器：

```python
# tradingagents/dataflows/new_sdk_provider.py
from typing import Optional, Dict, Any, List
import pandas as pd
from .base_provider import BaseStockDataProvider

class NewSDKProvider(BaseStockDataProvider):
    """新SDK数据提供器 - 纯数据获取，不涉及数据库操作"""

    def __init__(self, api_key: str = None, **kwargs):
        super().__init__()
        self.api_key = api_key
        self.connected = False

    async def connect(self) -> bool:
        """连接到数据源"""
        try:
            # 实现连接逻辑
            self.connected = True
            return True
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False

    async def get_stock_basic_info(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """获取股票基础信息 - 返回标准化数据"""
        # 1. 调用外部SDK API
        # 2. 数据标准化处理
        # 3. 返回标准格式数据 (不写入数据库)
        pass

    async def get_stock_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情 - 返回标准化数据"""
        # 实现具体逻辑
        pass

    async def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取历史数据 - 返回DataFrame"""
        # 实现具体逻辑
        pass
```

### 步骤2: 实现数据同步服务 (app层)

在 `app/worker/` 目录下创建同步服务：

```python
# app/worker/new_sdk_sync_service.py
from app.services.stock_data_service import get_stock_data_service
from tradingagents.dataflows.new_sdk_provider import NewSDKProvider

class NewSDKSyncService:
    """新SDK数据同步服务 - 负责数据库操作和业务逻辑"""

    def __init__(self):
        self.provider = NewSDKProvider()  # 使用tradingagents的适配器
        self.stock_service = get_stock_data_service()  # 使用app的数据服务

    async def sync_basic_info(self):
        """同步基础信息到数据库"""
        # 1. 从tradingagents适配器获取标准化数据
        raw_data = await self.provider.get_stock_basic_info()

        # 2. 业务逻辑处理 (如需要)
        processed_data = self._process_business_logic(raw_data)

        # 3. 写入MongoDB数据库
        await self.stock_service.update_stock_basic_info(
            code=processed_data['code'],
            update_data=processed_data
        )

    def _process_business_logic(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """业务逻辑处理 - 在app层处理"""
        # 添加业务相关的数据处理
        # 如：数据验证、业务规则应用等
        return raw_data
```

### 步骤3: 注册到数据源管理器 (tradingagents层)

```python
# tradingagents/dataflows/data_source_manager.py
from .new_sdk_provider import NewSDKProvider

class DataSourceManager:
    """数据源管理器 - 管理所有SDK适配器"""
    def __init__(self):
        self.providers = {
            'tushare': TushareProvider,
            'akshare': AKShareProvider,
            'new_sdk': NewSDKProvider,  # 新增
        }
```

### 步骤4: 配置定时任务 (app层)

```python
# app/main.py - 在主应用中配置定时任务
from app.worker.new_sdk_sync_service import NewSDKSyncService

# 创建同步服务实例
new_sdk_sync = NewSDKSyncService()

# 添加定时任务
scheduler.add_job(
    new_sdk_sync.sync_basic_info,
    CronTrigger(hour=2, minute=0, timezone=settings.TIMEZONE),
    id="new_sdk_basic_info_sync"
)
```

### 步骤5: 配置环境变量

```bash
# .env 文件
NEW_SDK_ENABLED=true
NEW_SDK_API_KEY=your_api_key_here
NEW_SDK_BASE_URL=https://api.newsdk.com
NEW_SDK_TIMEOUT=30
```

## 📝 代码规范

### 基础提供器接口

所有SDK适配器必须继承 `BaseStockDataProvider`：

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import pandas as pd

class BaseStockDataProvider(ABC):
    """股票数据提供器基类"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接到数据源"""
        pass
    
    @abstractmethod
    async def get_stock_basic_info(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """获取股票基础信息"""
        pass
    
    @abstractmethod
    async def get_stock_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情"""
        pass
    
    @abstractmethod
    async def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取历史数据"""
        pass
```

### 错误处理规范

```python
import logging
from typing import Optional

class NewSDKProvider(BaseStockDataProvider):
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_stock_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            # API调用
            response = await self._make_api_call(f"/quotes/{symbol}")
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"API返回错误状态: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"获取{symbol}行情失败: {e}")
            return None
```

### 配置管理规范

```python
from tradingagents.config.runtime_settings import get_setting

class NewSDKProvider(BaseStockDataProvider):
    def __init__(self):
        self.api_key = get_setting("NEW_SDK_API_KEY")
        self.base_url = get_setting("NEW_SDK_BASE_URL", "https://api.newsdk.com")
        self.timeout = int(get_setting("NEW_SDK_TIMEOUT", "30"))
        self.enabled = get_setting("NEW_SDK_ENABLED", "false").lower() == "true"
```

## 🔄 数据标准化

### 股票基础信息标准化

```python
def standardize_basic_info(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """标准化股票基础信息"""
    return {
        # 必需字段
        "code": self._normalize_stock_code(raw_data.get("symbol")),
        "name": raw_data.get("name", ""),
        "symbol": self._normalize_stock_code(raw_data.get("symbol")),
        "full_symbol": self._generate_full_symbol(raw_data.get("symbol")),
        
        # 市场信息
        "market_info": {
            "market": self._determine_market(raw_data.get("symbol")),
            "exchange": self._determine_exchange(raw_data.get("symbol")),
            "exchange_name": self._get_exchange_name(raw_data.get("symbol")),
            "currency": self._determine_currency(raw_data.get("symbol")),
            "timezone": self._determine_timezone(raw_data.get("symbol"))
        },
        
        # 可选字段
        "industry": raw_data.get("industry"),
        "area": raw_data.get("region"),
        "list_date": self._format_date(raw_data.get("list_date")),
        "total_mv": self._convert_market_cap(raw_data.get("market_cap")),
        
        # 元数据
        "data_source": "new_sdk",
        "data_version": 1,
        "updated_at": datetime.utcnow()
    }
```

### 实时行情标准化

```python
def standardize_quotes(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """标准化实时行情数据"""
    return {
        # 必需字段
        "code": self._normalize_stock_code(raw_data.get("symbol")),
        "symbol": self._normalize_stock_code(raw_data.get("symbol")),
        "full_symbol": self._generate_full_symbol(raw_data.get("symbol")),
        "market": self._determine_market(raw_data.get("symbol")),
        
        # 价格数据
        "close": float(raw_data.get("price", 0)),
        "current_price": float(raw_data.get("price", 0)),
        "open": float(raw_data.get("open", 0)),
        "high": float(raw_data.get("high", 0)),
        "low": float(raw_data.get("low", 0)),
        "pre_close": float(raw_data.get("prev_close", 0)),
        
        # 变动数据
        "change": self._calculate_change(raw_data),
        "pct_chg": float(raw_data.get("change_percent", 0)),
        
        # 成交数据
        "volume": float(raw_data.get("volume", 0)),
        "amount": float(raw_data.get("turnover", 0)),
        
        # 时间数据
        "trade_date": self._format_trade_date(raw_data.get("date")),
        "timestamp": self._parse_timestamp(raw_data.get("timestamp")),
        
        # 元数据
        "data_source": "new_sdk",
        "data_version": 1,
        "updated_at": datetime.utcnow()
    }
```

## 🧪 测试验证

### 单元测试

创建测试文件 `tests/test_new_sdk_provider.py`：

```python
import pytest
from tradingagents.dataflows.new_sdk_provider import NewSDKProvider

class TestNewSDKProvider:
    @pytest.fixture
    def provider(self):
        return NewSDKProvider(api_key="test_key")
    
    @pytest.mark.asyncio
    async def test_connect(self, provider):
        """测试连接功能"""
        result = await provider.connect()
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_get_stock_basic_info(self, provider):
        """测试获取股票基础信息"""
        result = await provider.get_stock_basic_info("000001")
        
        if result:
            assert "code" in result
            assert "name" in result
            assert "symbol" in result
    
    def test_data_standardization(self, provider):
        """测试数据标准化"""
        raw_data = {
            "symbol": "000001",
            "name": "测试股票",
            "price": 12.34
        }
        
        standardized = provider.standardize_basic_info(raw_data)
        
        assert standardized["code"] == "000001"
        assert standardized["name"] == "测试股票"
        assert "market_info" in standardized
```

### 集成测试

创建集成测试脚本 `scripts/test_new_sdk_integration.py`：

```python
#!/usr/bin/env python3
"""新SDK集成测试"""

import asyncio
import logging
from tradingagents.dataflows.new_sdk_provider import NewSDKProvider
from app.worker.new_sdk_sync_service import NewSDKSyncService

async def test_integration():
    """集成测试"""
    logger = logging.getLogger(__name__)
    
    # 测试SDK连接
    provider = NewSDKProvider()
    connected = await provider.connect()
    
    if not connected:
        logger.error("SDK连接失败")
        return False
    
    # 测试数据获取
    basic_info = await provider.get_stock_basic_info("000001")
    quotes = await provider.get_stock_quotes("000001")
    
    logger.info(f"基础信息: {basic_info}")
    logger.info(f"实时行情: {quotes}")
    
    # 测试数据同步
    sync_service = NewSDKSyncService()
    await sync_service.sync_basic_info()
    
    logger.info("集成测试完成")
    return True

if __name__ == "__main__":
    asyncio.run(test_integration())
```

## ⚙️ 部署配置

### 环境变量配置

```bash
# 新SDK配置
NEW_SDK_ENABLED=true
NEW_SDK_API_KEY=your_api_key
NEW_SDK_BASE_URL=https://api.newsdk.com
NEW_SDK_TIMEOUT=30
NEW_SDK_RATE_LIMIT=100  # 每分钟请求限制
NEW_SDK_RETRY_TIMES=3   # 重试次数
NEW_SDK_RETRY_DELAY=1   # 重试延迟(秒)
```

### 定时任务配置

在 `app/main.py` 中添加定时任务：

```python
from app.worker.new_sdk_sync_service import NewSDKSyncService

# 在scheduler中添加
if settings.NEW_SDK_ENABLED:
    new_sdk_sync = NewSDKSyncService()
    
    # 每小时同步基础信息
    scheduler.add_job(
        new_sdk_sync.sync_basic_info,
        CronTrigger(minute=0, timezone=settings.TIMEZONE)
    )
    
    # 每30秒同步实时行情
    scheduler.add_job(
        new_sdk_sync.sync_quotes,
        IntervalTrigger(seconds=30, timezone=settings.TIMEZONE)
    )
```

## ❓ 常见问题

### Q1: 如何处理API限制？

```python
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def acquire(self):
        now = datetime.now()
        # 清理过期请求
        self.requests = [req for req in self.requests if now - req < timedelta(seconds=self.time_window)]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]).total_seconds()
            await asyncio.sleep(sleep_time)
        
        self.requests.append(now)
```

### Q2: 如何处理数据格式差异？

创建数据映射配置：

```python
# 字段映射配置
FIELD_MAPPING = {
    "new_sdk": {
        "symbol": "code",
        "company_name": "name",
        "current_price": "close",
        "change_percent": "pct_chg",
        "trading_volume": "volume"
    }
}

def map_fields(self, raw_data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """字段映射"""
    mapping = FIELD_MAPPING.get(source, {})
    mapped_data = {}
    
    for new_field, old_field in mapping.items():
        if old_field in raw_data:
            mapped_data[new_field] = raw_data[old_field]
    
    return mapped_data
```

### Q3: 如何处理多市场数据？

```python
def determine_market_info(self, symbol: str) -> Dict[str, Any]:
    """根据股票代码确定市场信息"""
    if symbol.endswith('.HK'):
        return {
            "market": "HK",
            "exchange": "SEHK",
            "currency": "HKD",
            "timezone": "Asia/Hong_Kong"
        }
    elif symbol.endswith('.US'):
        return {
            "market": "US", 
            "exchange": "NYSE",  # 或根据具体情况判断
            "currency": "USD",
            "timezone": "America/New_York"
        }
    else:
        # 默认A股
        return {
            "market": "CN",
            "exchange": "SZSE" if symbol.startswith(('00', '30')) else "SSE",
            "currency": "CNY",
            "timezone": "Asia/Shanghai"
        }
```

## 🚀 快速开始

### 1. 复制示例文件

```bash
# 复制示例适配器 (tradingagents层 - 纯数据获取)
cp tradingagents/dataflows/example_sdk_provider.py tradingagents/dataflows/your_sdk_provider.py

# 复制示例同步服务 (app层 - 数据库操作和业务逻辑)
cp app/worker/example_sdk_sync_service.py app/worker/your_sdk_sync_service.py
```

### 2. 修改配置

```bash
# 在 .env 文件中添加配置
YOUR_SDK_ENABLED=true
YOUR_SDK_API_KEY=your_api_key_here
YOUR_SDK_BASE_URL=https://api.yoursdk.com
YOUR_SDK_TIMEOUT=30
```

### 3. 实现适配器 (tradingagents层)

```python
# 修改 tradingagents/dataflows/your_sdk_provider.py
class YourSDKProvider(BaseStockDataProvider):
    """您的SDK适配器 - 只负责数据获取和标准化"""
    def __init__(self):
        super().__init__("YourSDK")
        # 实现初始化逻辑

    async def get_stock_basic_info(self, symbol: str = None):
        # 1. 调用外部SDK API
        # 2. 数据标准化处理
        # 3. 返回标准格式 (不写数据库)
        pass
```

### 4. 测试适配器

```bash
# 运行测试
python -c "
import asyncio
from tradingagents.dataflows.your_sdk_provider import YourSDKProvider

async def test():
    provider = YourSDKProvider()
    if await provider.connect():
        data = await provider.get_stock_basic_info('000001')
        print(data)
    await provider.disconnect()

asyncio.run(test())
"
```

### 5. 配置定时任务 (app层)

```python
# 在 app/main.py 中添加定时任务
from app.worker.your_sdk_sync_service import run_full_sync, run_incremental_sync

# 每天凌晨2点全量同步 (app层的同步服务)
scheduler.add_job(
    run_full_sync,
    CronTrigger(hour=2, minute=0, timezone=settings.TIMEZONE),
    id="your_sdk_full_sync"
)

# 每30秒增量同步 (app层的同步服务)
scheduler.add_job(
    run_incremental_sync,
    IntervalTrigger(seconds=30, timezone=settings.TIMEZONE),
    id="your_sdk_incremental_sync"
)
```

---

## 📚 参考资料

- [股票数据模型设计文档](../design/stock_data_model_design.md)
- [数据方法分析文档](../design/stock_data_methods_analysis.md)
- [API规范文档](../design/api_specification.md)
- [基础提供器接口](../../tradingagents/dataflows/base_provider.py)
- [示例SDK适配器](../../tradingagents/dataflows/example_sdk_provider.py)
- [示例同步服务](../../app/worker/example_sdk_sync_service.py)

---

*股票数据SDK接入指南 - 最后更新: 2025-09-28*
