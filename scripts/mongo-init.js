// MongoDB初始化脚本 - QuantScope v1.0.0-preview
// 创建TradingAgents数据库、用户、集合和索引

print('开始初始化TradingAgents数据库...');

// 切换到admin数据库
db = db.getSiblingDB('admin');

// 创建应用用户
try {
  db.createUser({
    user: 'tradingagents',
    pwd: 'tradingagents123',
    roles: [
      {
        role: 'readWrite',
        db: 'tradingagents'
      }
    ]
  });
  print('✓ 创建应用用户成功');
} catch (e) {
  print('⚠ 用户可能已存在: ' + e.message);
}

// 切换到应用数据库
db = db.getSiblingDB('tradingagents');

// ===== 创建集合 =====

print('\n创建集合...');

// 用户相关
db.createCollection('users');
db.createCollection('user_sessions');
db.createCollection('user_activities');

// 股票数据
db.createCollection('stock_basic_info');
db.createCollection('stock_financial_data');
db.createCollection('market_quotes');
db.createCollection('stock_news');

// 分析相关
db.createCollection('analysis_tasks');
db.createCollection('analysis_reports');
db.createCollection('analysis_progress');

// 筛选和收藏
db.createCollection('screening_results');
db.createCollection('favorites');
db.createCollection('tags');

// 系统配置
db.createCollection('system_config');
db.createCollection('model_config');
db.createCollection('sync_status');

// 日志和统计
db.createCollection('system_logs');
db.createCollection('token_usage');

print('✓ 集合创建完成');

// ===== 创建索引 =====

print('\n创建索引...');

// 用户索引
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true, sparse: true });
db.users.createIndex({ "created_at": 1 });

// 用户会话索引
db.user_sessions.createIndex({ "session_id": 1 }, { unique: true });
db.user_sessions.createIndex({ "user_id": 1 });
db.user_sessions.createIndex({ "created_at": 1 }, { expireAfterSeconds: 86400 }); // 24小时过期

// 用户活动索引
db.user_activities.createIndex({ "user_id": 1, "timestamp": -1 });
db.user_activities.createIndex({ "action_type": 1, "timestamp": -1 });

// 股票基础信息索引
// 🔥 联合唯一索引：(code, source) - 允许同一股票有多个数据源
db.stock_basic_info.createIndex({ "code": 1, "source": 1 }, { unique: true });
db.stock_basic_info.createIndex({ "code": 1 });  // 非唯一索引，用于查询所有数据源
db.stock_basic_info.createIndex({ "source": 1 });  // 数据源索引
db.stock_basic_info.createIndex({ "market": 1 });
db.stock_basic_info.createIndex({ "industry": 1 });
db.stock_basic_info.createIndex({ "updated_at": 1 });

// 股票财务数据索引
db.stock_financial_data.createIndex({ "code": 1, "report_date": 1 });
db.stock_financial_data.createIndex({ "updated_at": 1 });

// 实时行情索引
db.market_quotes.createIndex({ "code": 1 }, { unique: true });
db.market_quotes.createIndex({ "updated_at": 1 });

// 股票新闻索引
db.stock_news.createIndex({ "code": 1, "published_at": -1 });
db.stock_news.createIndex({ "title": "text", "content": "text" });
db.stock_news.createIndex({ "published_at": -1 });

// 分析任务索引
db.analysis_tasks.createIndex({ "task_id": 1 }, { unique: true });
db.analysis_tasks.createIndex({ "user_id": 1, "created_at": -1 });
db.analysis_tasks.createIndex({ "status": 1, "created_at": -1 });
db.analysis_tasks.createIndex({ "symbol": 1, "created_at": -1 });

// 分析报告索引
db.analysis_reports.createIndex({ "task_id": 1 });
db.analysis_reports.createIndex({ "symbol": 1, "created_at": -1 });
db.analysis_reports.createIndex({ "user_id": 1, "created_at": -1 });
db.analysis_reports.createIndex({ "market_type": 1, "created_at": -1 });
db.analysis_reports.createIndex({ "created_at": -1 });

// 分析进度索引
db.analysis_progress.createIndex({ "task_id": 1 }, { unique: true });
db.analysis_progress.createIndex({ "updated_at": 1 }, { expireAfterSeconds: 3600 }); // 1小时过期

// 筛选结果索引
db.screening_results.createIndex({ "user_id": 1, "created_at": -1 });
db.screening_results.createIndex({ "created_at": -1 });

// 收藏索引
db.favorites.createIndex({ "user_id": 1, "symbol": 1 }, { unique: true });
db.favorites.createIndex({ "user_id": 1, "created_at": -1 });

// 标签索引
db.tags.createIndex({ "user_id": 1, "name": 1 }, { unique: true });
db.tags.createIndex({ "user_id": 1 });

// 系统配置索引
db.system_config.createIndex({ "key": 1 }, { unique: true });

// 模型配置索引
db.model_config.createIndex({ "provider": 1, "model_name": 1 }, { unique: true });

// 同步状态索引
db.sync_status.createIndex({ "data_type": 1 }, { unique: true });
db.sync_status.createIndex({ "last_sync_at": 1 });

// 系统日志索引
db.system_logs.createIndex({ "level": 1, "timestamp": -1 });
db.system_logs.createIndex({ "timestamp": -1 }, { expireAfterSeconds: 604800 }); // 7天过期

// Token使用统计索引
db.token_usage.createIndex({ "user_id": 1, "timestamp": -1 });
db.token_usage.createIndex({ "model": 1, "timestamp": -1 });
db.token_usage.createIndex({ "timestamp": -1 });

print('✓ 索引创建完成');

// ===== 插入初始数据 =====

print('\n插入初始数据...');

// 插入默认系统配置
db.system_config.insertMany([
  {
    key: 'system_version',
    value: 'v1.0.0-preview',
    description: '系统版本号',
    updated_at: new Date()
  },
  {
    key: 'max_concurrent_tasks',
    value: 3,
    description: '最大并发分析任务数',
    updated_at: new Date()
  },
  {
    key: 'default_research_depth',
    value: 2,
    description: '默认分析深度',
    updated_at: new Date()
  },
  {
    key: 'enable_realtime_pe_pb',
    value: true,
    description: '启用实时PE/PB计算',
    updated_at: new Date()
  }
]);

print('✓ 初始数据插入完成');

// ===== 验证 =====

print('\n验证数据库初始化...');

var collections = db.getCollectionNames();
print('✓ 集合数量: ' + collections.length);

var indexes = 0;
collections.forEach(function(collName) {
  indexes += db.getCollection(collName).getIndexes().length;
});
print('✓ 索引数量: ' + indexes);

var configCount = db.system_config.count();
print('✓ 系统配置数量: ' + configCount);

print('\n========================================');
print('TradingAgents数据库初始化完成！');
print('========================================');
print('数据库: tradingagents');
print('用户: tradingagents');
print('密码: tradingagents123');
print('集合数: ' + collections.length);
print('索引数: ' + indexes);
print('========================================');
