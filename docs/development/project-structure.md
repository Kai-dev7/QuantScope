# 项目结构规范

## 📁 目录组织原则

QuantScope 项目遵循清晰的目录结构规范，确保代码组织有序、易于维护。

## 🏗️ 项目根目录结构

```
TradingAgentsCN/
├── 📁 tradingagents/          # 核心代码包
├── 📁 web/                    # Web界面代码
├── 📁 docs/                   # 项目文档
├── 📁 tests/                  # 所有测试文件
├── 📁 scripts/                # 工具脚本
├── 📁 env/                    # Python虚拟环境
├── 📄 README.md               # 项目说明
├── 📄 requirements.txt        # 依赖列表
├── 📄 .env.example           # 环境变量模板
├── 📄 VERSION                 # 版本号
└── 📄 CHANGELOG.md           # 更新日志
```

## 📋 目录职责说明

### 🧪 tests/ - 测试目录
**规则**: 所有测试相关的文件必须放在此目录下

#### 允许的文件类型：
- ✅ `test_*.py` - 单元测试文件
- ✅ `*_test.py` - 快速测试脚本
- ✅ `test_*_integration.py` - 集成测试
- ✅ `test_*_performance.py` - 性能测试
- ✅ `check_*.py` - 检查脚本
- ✅ `debug_*.py` - 调试脚本

#### 子目录组织：
```
tests/
├── 📄 README.md                    # 测试说明文档
├── 📄 __init__.py                  # Python包初始化
├── 📁 integration/                 # 集成测试
├── 📄 test_*.py                   # 单元测试
├── 📄 *_test.py                   # 快速测试
└── 📄 test_*_performance.py       # 性能测试
```

#### 示例文件：
- `test_analysis.py` - 分析功能单元测试
- `fast_tdx_test.py` - Tushare数据接口快速测试
- `test_tdx_integration.py` - Tushare数据接口集成测试
- `test_redis_performance.py` - Redis性能测试

### 🔧 scripts/ - 工具脚本目录
**规则**: 仅放置非测试的工具脚本

#### 允许的文件类型：
- ✅ `release_*.py` - 发布脚本
- ✅ `setup_*.py` - 安装配置脚本
- ✅ `deploy_*.py` - 部署脚本
- ✅ `migrate_*.py` - 数据迁移脚本
- ✅ `backup_*.py` - 备份脚本

#### 不允许的文件：
- ❌ `test_*.py` - 测试文件应放在tests/
- ❌ `*_test.py` - 测试脚本应放在tests/
- ❌ `check_*.py` - 检查脚本应放在tests/

### 📚 docs/ - 文档目录
**规则**: 所有项目文档按类型组织

#### 目录结构：
```
docs/
├── 📁 guides/                     # 使用指南
├── 📁 development/                # 开发文档
├── 📁 data/                       # 数据源文档
├── 📁 api/                        # API文档
└── 📁 localization/               # 本土化文档
```

### 🌐 web/ - Web界面目录
**规则**: Web相关代码统一管理

#### 目录结构：
```
web/
├── 📄 app.py                      # 主应用入口
├── 📁 components/                 # UI组件
├── 📁 utils/                      # Web工具函数
├── 📁 static/                     # 静态资源
└── 📁 templates/                  # 模板文件
```

### 🧠 tradingagents/ - 核心代码包
**规则**: 核心业务逻辑代码

#### 目录结构：
```
tradingagents/
├── 📁 agents/                     # 智能体代码
├── 📁 dataflows/                  # 数据流处理
├── 📁 tools/                      # 工具函数
└── 📁 utils/                      # 通用工具
```

## 🚫 禁止的文件位置

### 根目录禁止项：
- ❌ `test_*.py` - 必须放在tests/
- ❌ `*_test.py` - 必须放在tests/
- ❌ `debug_*.py` - 必须放在tests/
- ❌ `check_*.py` - 必须放在tests/
- ❌ 临时文件和调试文件
- ❌ IDE配置文件（应在.gitignore中）

### scripts/目录禁止项：
- ❌ 任何测试相关文件
- ❌ 调试脚本
- ❌ 检查脚本

## ✅ 文件命名规范

### 测试文件命名：
- **单元测试**: `test_<module_name>.py`
- **集成测试**: `test_<feature>_integration.py`
- **性能测试**: `test_<component>_performance.py`
- **快速测试**: `<component>_test.py`
- **检查脚本**: `check_<feature>.py`
- **调试脚本**: `debug_<issue>.py`

### 工具脚本命名：
- **发布脚本**: `release_v<version>.py`
- **安装脚本**: `setup_<component>.py`
- **部署脚本**: `deploy_<environment>.py`

### 文档文件命名：
- **使用指南**: `<feature>-guide.md`
- **技术文档**: `<component>-integration.md`
- **API文档**: `<api>-api.md`

## 🔍 项目结构检查

### 自动检查脚本
创建 `tests/check_project_structure.py` 来验证项目结构：

```python
def check_no_tests_in_root():
    """检查根目录没有测试文件"""
    
def check_no_tests_in_scripts():
    """检查scripts目录没有测试文件"""
    
def check_all_tests_in_tests_dir():
    """检查所有测试文件都在tests目录"""
```

### 手动检查清单
发布前检查：
- [ ] 根目录没有test_*.py文件
- [ ] 根目录没有*_test.py文件
- [ ] scripts/目录没有测试文件
- [ ] 所有测试文件都在tests/目录
- [ ] tests/README.md已更新
- [ ] 文档中的路径引用正确

## 📝 最佳实践

### 1. 新增测试文件
```bash
# ✅ 正确：在tests目录创建
touch tests/test_new_feature.py

# ❌ 错误：在根目录创建
touch test_new_feature.py
```

### 2. 运行测试
```bash
# ✅ 正确：指定tests目录
python tests/fast_tdx_test.py
python -m pytest tests/

# ❌ 错误：从根目录运行
python fast_tdx_test.py
```

### 3. 文档引用
```markdown
<!-- ✅ 正确：使用完整路径 -->
运行测试：`python tests/fast_tdx_test.py`

<!-- ❌ 错误：使用相对路径 -->
运行测试：`python fast_tdx_test.py`
```

## 🔧 迁移现有文件

如果发现文件位置不符合规范：

### 移动测试文件到tests目录：
```bash
# Windows
move test_*.py tests\
move *_test.py tests\

# Linux/macOS
mv test_*.py tests/
mv *_test.py tests/
```

### 更新引用：
1. 更新文档中的路径引用
2. 更新脚本中的import路径
3. 更新CI/CD配置中的测试路径

## 🎯 遵循规范的好处

1. **清晰的项目结构** - 新开发者容易理解
2. **便于维护** - 文件位置可预测
3. **自动化友好** - CI/CD脚本更简单
4. **避免混乱** - 测试和业务代码分离
5. **专业形象** - 符合开源项目标准

---

**请严格遵循此项目结构规范，确保代码库的整洁和专业性！** 📁✨
