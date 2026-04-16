#!/usr/bin/env python3
"""
数据目录配置演示
展示如何使用新的数据目录配置功能
"""

import os
import sys
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('default')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.config.config_manager import config_manager
from tradingagents.dataflows.config import get_config, set_data_dir, get_data_dir
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def show_current_config():
    """显示当前配置"""
    logger.info(f"\n[bold blue]📁 当前数据目录配置[/bold blue]")
    
    # 从配置管理器获取设置
    settings = config_manager.load_settings()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("配置项", style="cyan")
    table.add_column("路径", style="green")
    table.add_column("状态", style="yellow")
    
    # 检查各个目录
    directories = {
        "数据目录": settings.get("data_dir", "未配置"),
        "缓存目录": settings.get("cache_dir", "未配置"),
        "结果目录": settings.get("results_dir", "未配置")
    }
    
    for name, path in directories.items():
        if path and path != "未配置":
            status = "✅ 存在" if os.path.exists(path) else "❌ 不存在"
        else:
            status = "⚠️ 未配置"
        table.add_row(name, str(path), status)
    
    console.print(table)
    
    # 显示环境变量配置
    logger.info(f"\n[bold blue]🌍 环境变量配置[/bold blue]")
    env_table = Table(show_header=True, header_style="bold magenta")
    env_table.add_column("环境变量", style="cyan")
    env_table.add_column("值", style="green")
    
    env_vars = {
        "TRADINGAGENTS_DATA_DIR": os.getenv("TRADINGAGENTS_DATA_DIR", "未设置"),
        "TRADINGAGENTS_CACHE_DIR": os.getenv("TRADINGAGENTS_CACHE_DIR", "未设置"),
        "TRADINGAGENTS_RESULTS_DIR": os.getenv("TRADINGAGENTS_RESULTS_DIR", "未设置")
    }
    
    for var, value in env_vars.items():
        env_table.add_row(var, value)
    
    console.print(env_table)

def demo_set_custom_data_dir():
    """演示设置自定义数据目录"""
    logger.info(f"\n[bold green]🔧 设置自定义数据目录演示[/bold green]")
    
    # 设置自定义数据目录
    custom_data_dir = os.path.join(os.path.expanduser("~"), "Documents", "TradingAgents_Custom", "data")
    
    logger.info(f"设置数据目录为: {custom_data_dir}")
    set_data_dir(custom_data_dir)
    
    # 验证设置
    current_dir = get_data_dir()
    logger.info(f"当前数据目录: {current_dir}")
    
    if current_dir == custom_data_dir:
        logger.info(f"✅ 数据目录设置成功")
    else:
        logger.error(f"❌ 数据目录设置失败")
    
    # 显示创建的目录结构
    logger.info(f"\n[bold blue]📂 创建的目录结构[/bold blue]")
    if os.path.exists(custom_data_dir):
        for root, dirs, files in os.walk(custom_data_dir):
            level = root.replace(custom_data_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            logger.info(f"{indent}📁 {os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                logger.info(f"{subindent}📄 {file}")

def demo_config_integration():
    """演示配置集成"""
    logger.info(f"\n[bold green]🔗 配置集成演示[/bold green]")
    
    # 通过dataflows.config获取配置
    config = get_config()
    logger.info(f"通过 get_config() 获取的数据目录: {config.get('data_dir')}")
    
    # 通过config_manager获取配置
    manager_data_dir = config_manager.get_data_dir()
    logger.info(f"通过 config_manager 获取的数据目录: {manager_data_dir}")
    
    # 验证一致性
    if config.get('data_dir') == manager_data_dir:
        logger.info(f"✅ 配置一致性验证通过")
    else:
        logger.error(f"❌ 配置一致性验证失败")

def demo_environment_variable_override():
    """演示环境变量覆盖"""
    logger.info(f"\n[bold green]🌍 环境变量覆盖演示[/bold green]")
    
    # 模拟设置环境变量
    test_env_dir = os.path.join(os.path.expanduser("~"), "Documents", "TradingAgents_ENV", "data")
    os.environ["TRADINGAGENTS_DATA_DIR"] = test_env_dir
    
    logger.info(f"设置环境变量 TRADINGAGENTS_DATA_DIR = {test_env_dir}")
    
    # 重新加载配置
    settings = config_manager.load_settings()
    logger.info(f"重新加载后的数据目录: {settings.get('data_dir')}")
    
    # 清理环境变量
    del os.environ["TRADINGAGENTS_DATA_DIR"]
    logger.info(f"清理环境变量")

def demo_directory_auto_creation():
    """演示目录自动创建"""
    logger.info(f"\n[bold green]🏗️ 目录自动创建演示[/bold green]")
    
    # 设置一个新的数据目录
    test_dir = os.path.join(os.path.expanduser("~"), "Documents", "TradingAgents_AutoCreate", "data")
    
    # 确保目录不存在
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(os.path.dirname(test_dir))
    
    logger.info(f"设置新数据目录: {test_dir}")
    set_data_dir(test_dir)
    
    # 检查目录是否被创建
    expected_dirs = [
        test_dir,
        os.path.join(test_dir, "cache"),
        os.path.join(test_dir, "finnhub_data"),
        os.path.join(test_dir, "finnhub_data", "news_data"),
        os.path.join(test_dir, "finnhub_data", "insider_sentiment"),
        os.path.join(test_dir, "finnhub_data", "insider_transactions")
    ]
    
    logger.info(f"\n检查自动创建的目录:")
    for directory in expected_dirs:
        if os.path.exists(directory):
            logger.info(f"✅ {directory}")
        else:
            logger.error(f"❌ {directory}")

def show_configuration_guide():
    """显示配置指南"""
    guide_text = """
[bold blue]📖 数据目录配置指南[/bold blue]

[bold green]1. 通过代码配置:[/bold green]
```python
from tradingagents.dataflows.config import set_data_dir
set_data_dir("/path/to/your/data/directory")
```

[bold green]2. 通过环境变量配置:[/bold green]
```bash
# Windows
set TRADINGAGENTS_DATA_DIR=C:\\path\\to\\data

# Linux/Mac
export TRADINGAGENTS_DATA_DIR=/path/to/data
```

[bold green]3. 通过配置管理器:[/bold green]
```python
from tradingagents.config.config_manager import config_manager
config_manager.set_data_dir("/path/to/your/data/directory")
```

[bold green]4. 配置文件位置:[/bold green]
- 配置文件存储在: config/settings.json
- 支持的配置项:
  - data_dir: 数据目录
  - cache_dir: 缓存目录
  - results_dir: 结果目录
  - auto_create_dirs: 自动创建目录

[bold green]5. 优先级:[/bold green]
1. 环境变量 (最高优先级)
2. 代码中的设置
3. 配置文件中的设置
4. 默认值 (最低优先级)
"""
    
    console.print(Panel(guide_text, title="配置指南", border_style="blue"))

def main():
    """主演示函数"""
    logger.info(f"[bold blue]🎯 QuantScope 数据目录配置演示[/bold blue]")
    logger.info(f"=")
    
    try:
        # 1. 显示当前配置
        show_current_config()
        
        # 2. 演示设置自定义数据目录
        demo_set_custom_data_dir()
        
        # 3. 演示配置集成
        demo_config_integration()
        
        # 4. 演示环境变量覆盖
        demo_environment_variable_override()
        
        # 5. 演示目录自动创建
        demo_directory_auto_creation()
        
        # 6. 显示配置指南
        show_configuration_guide()
        
        logger.info(f"\n[bold green]✅ 演示完成![/bold green]")
        
    except Exception as e:
        logger.error(f"\n[bold red]❌ 演示过程中出现错误: {e}[/bold red]")
        import traceback

        console.print(traceback.format_exc())

if __name__ == "__main__":
    main()