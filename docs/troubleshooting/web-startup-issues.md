# 🔧 Web应用启动问题排除指南

## 🚨 常见问题

### 1. ModuleNotFoundError: No module named 'tradingagents'

**问题描述**:
```bash
ModuleNotFoundError: No module named 'tradingagents'
```

**原因**: 项目没有安装到Python环境中，导致无法导入模块。

**解决方案**:

#### 方案A: 开发模式安装（推荐）
```bash
# 1. 激活虚拟环境
.\env\Scripts\activate  # Windows
source env/bin/activate  # Linux/macOS

# 2. 安装项目到虚拟环境
pip install -e .

# 3. 启动Web应用
python start_web.py
```

#### 方案B: 使用一键安装脚本
```bash
# 1. 激活虚拟环境
.\env\Scripts\activate  # Windows

# 2. 运行一键安装脚本
python scripts/install_and_run.py
```

#### 方案C: 手动设置Python路径
```bash
# Windows
set PYTHONPATH=%CD%;%PYTHONPATH%
streamlit run web/app.py

# Linux/macOS
export PYTHONPATH=$PWD:$PYTHONPATH
streamlit run web/app.py
```

### 2. ModuleNotFoundError: No module named 'streamlit'

**问题描述**:
```bash
ModuleNotFoundError: No module named 'streamlit'
```

**解决方案**:
```bash
# 安装Streamlit和相关依赖
pip install streamlit plotly altair

# 或者安装完整的Web依赖
pip install -r requirements_web.txt
```

### 3. 虚拟环境问题

**问题描述**: 不确定是否在虚拟环境中

**检查方法**:
```bash
# 检查Python路径
python -c "import sys; print(sys.prefix)"

# 检查是否在虚拟环境
python -c "import sys; print(hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))"
```

**解决方案**:
```bash
# 创建虚拟环境（如果不存在）
python -m venv env

# 激活虚拟环境
.\env\Scripts\activate  # Windows
source env/bin/activate  # Linux/macOS
```

### 4. 端口占用问题

**问题描述**:
```bash
OSError: [Errno 48] Address already in use
```

**解决方案**:
```bash
# 方法1: 使用不同端口
streamlit run web/app.py --server.port 8502

# 方法2: 杀死占用端口的进程
# Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:8501 | xargs kill -9
```

### 5. 权限问题

**问题描述**: 在某些系统上可能遇到权限问题

**解决方案**:
```bash
# 确保有执行权限
chmod +x start_web.py
chmod +x web/run_web.py

# 或者使用python命令运行
python start_web.py
```

## 🛠️ 启动方式对比

| 启动方式 | 优点 | 缺点 | 推荐度 |
|---------|------|------|--------|
| `python start_web.py` | 简单，自动处理路径 | 需要在项目根目录 | ⭐⭐⭐⭐⭐ |
| `pip install -e . && streamlit run web/app.py` | 标准方式，稳定 | 需要安装步骤 | ⭐⭐⭐⭐ |
| `python web/run_web.py` | 功能完整，有检查 | 可能有导入问题 | ⭐⭐⭐ |
| `PYTHONPATH=. streamlit run web/app.py` | 不需要安装 | 环境变量设置复杂 | ⭐⭐ |

## 🔍 诊断工具

### 环境检查脚本
```bash
# 运行环境检查
python scripts/check_api_config.py
```

### 手动检查步骤
```python
# 检查Python环境
import sys
print("Python版本:", sys.version)
print("Python路径:", sys.executable)
print("虚拟环境:", hasattr(sys, 'real_prefix'))

# 检查模块导入
try:
    import tradingagents
    print("✅ tradingagents模块可用")
except ImportError as e:
    print("❌ tradingagents模块不可用:", e)

try:
    import streamlit
    print("✅ streamlit模块可用")
except ImportError as e:
    print("❌ streamlit模块不可用:", e)
```

## 📋 完整启动检查清单

### 启动前检查
- [ ] 虚拟环境已激活
- [ ] Python版本 >= 3.10
- [ ] 项目已安装 (`pip install -e .`)
- [ ] Streamlit已安装
- [ ] .env文件已配置
- [ ] 端口8501未被占用

### 启动命令
```bash
# 推荐启动方式
python start_web.py
```

### 启动后验证
- [ ] 浏览器自动打开 http://localhost:8501
- [ ] 页面正常加载，无错误信息
- [ ] 侧边栏配置正常显示
- [ ] 可以选择分析师和股票代码

## 🆘 获取帮助

如果以上方法都无法解决问题：

1. **查看详细错误日志**:
   ```bash
   python start_web.py 2>&1 | tee startup.log
   ```

2. **检查系统环境**:
   ```bash
   python --version
   pip list | grep -E "(streamlit|tradingagents)"
   ```

3. **重新安装**:
   ```bash
   pip uninstall tradingagents
   pip install -e .
   ```

4. **提交Issue**: 
   - 访问 [GitHub Issues](https://github.com/hsliuping/QuantScope/issues)
   - 提供错误日志和系统信息

## 💡 最佳实践

1. **始终使用虚拟环境**
2. **定期更新依赖**: `pip install -U -r requirements.txt`
3. **保持项目结构完整**
4. **定期清理缓存**: `python web/run_web.py --force-clean`
5. **备份配置文件**: 定期备份.env文件
