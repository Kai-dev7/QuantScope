#!/usr/bin/env python3
"""
日志系统初始化模块
在应用启动时初始化统一日志系统
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import setup_logging, get_logger


def init_logging(config_override: Optional[dict] = None) -> None:
    """
    初始化项目日志系统
    
    Args:
        config_override: 可选的配置覆盖
    """
    # 设置日志系统
    logger_manager = setup_logging(config_override)
    
    # 获取初始化日志器
    logger = get_logger('tradingagents.init')
    
    # 记录初始化信息
    logger.info("🚀 QuantScope 日志系统初始化完成")
    logger.info(f"📁 日志目录: {logger_manager.config.get('handlers', {}).get('file', {}).get('directory', 'N/A')}")
    logger.info(f"📊 日志级别: {logger_manager.config.get('level', 'INFO')}")
    
    # Docker环境特殊处理
    if logger_manager.config.get('docker', {}).get('enabled', False):
        logger.info("🐳 Docker环境检测到，使用容器优化配置")
    
    # 记录环境信息
    logger.debug(f"🔧 Python版本: {sys.version}")
    logger.debug(f"📂 工作目录: {os.getcwd()}")
    logger.debug(f"🌍 环境变量: DOCKER_CONTAINER={os.getenv('DOCKER_CONTAINER', 'false')}")


def get_session_logger(session_id: str, module_name: str = 'session') -> 'logging.Logger':
    """
    获取会话专用日志器
    
    Args:
        session_id: 会话ID
        module_name: 模块名称
        
    Returns:
        配置好的日志器
    """
    logger_name = f"{module_name}.{session_id[:8]}"  # 使用前8位会话ID
    
    # 添加会话ID到所有日志记录
    class SessionAdapter:
        def __init__(self, logger, session_id):
            self.logger = logger
            self.session_id = session_id
        
        def debug(self, msg, *args, **kwargs):
            kwargs.setdefault('extra', {})['session_id'] = self.session_id
            return self.logger.debug(msg, *args, **kwargs)
        
        def info(self, msg, *args, **kwargs):
            kwargs.setdefault('extra', {})['session_id'] = self.session_id
            return self.logger.info(msg, *args, **kwargs)
        
        def warning(self, msg, *args, **kwargs):
            kwargs.setdefault('extra', {})['session_id'] = self.session_id
            return self.logger.warning(msg, *args, **kwargs)
        
        def error(self, msg, *args, **kwargs):
            kwargs.setdefault('extra', {})['session_id'] = self.session_id
            return self.logger.error(msg, *args, **kwargs)
        
        def critical(self, msg, *args, **kwargs):
            kwargs.setdefault('extra', {})['session_id'] = self.session_id
            return self.logger.critical(msg, *args, **kwargs)
    
    return SessionAdapter(logger, session_id)


def log_startup_info():
    """记录应用启动信息"""
    logger = get_logger('tradingagents.startup')
    
    logger.info("=" * 60)
    logger.info("🎯 QuantScope 启动")
    logger.info("=" * 60)
    
    # 系统信息
    import platform
    logger.info(f"🖥️  系统: {platform.system()} {platform.release()}")
    logger.info(f"🐍 Python: {platform.python_version()}")
    
    # 环境信息
    env_info = {
        'DOCKER_CONTAINER': os.getenv('DOCKER_CONTAINER', 'false'),
        'TRADINGAGENTS_LOG_LEVEL': os.getenv('TRADINGAGENTS_LOG_LEVEL', 'INFO'),
        'TRADINGAGENTS_LOG_DIR': os.getenv('TRADINGAGENTS_LOG_DIR', './logs'),
    }
    
    for key, value in env_info.items():
        logger.info(f"🔧 {key}: {value}")
    
    logger.info("=" * 60)


def log_shutdown_info():
    """记录应用关闭信息"""
    logger = get_logger('tradingagents.shutdown')
    
    logger.info("=" * 60)
    logger.info("🛑 QuantScope 关闭")
    logger.info("=" * 60)


# 便捷函数
def setup_web_logging():
    """设置Web应用专用日志"""
    init_logging()
    log_startup_info()
    return get_logger('web')


def setup_analysis_logging(session_id: str):
    """设置分析专用日志"""
    return get_session_logger(session_id, 'analysis')


def setup_dataflow_logging():
    """设置数据流专用日志"""
    return get_logger('dataflows')


def setup_llm_logging():
    """设置LLM适配器专用日志"""
    return get_logger('llm_adapters')


if __name__ == "__main__":
    # 测试日志系统
    init_logging()
    log_startup_info()
    
    # 测试不同模块的日志
    web_logger = setup_web_logging()
    web_logger.info("Web模块日志测试")
    
    analysis_logger = setup_analysis_logging("test-session-123")
    analysis_logger.info("分析模块日志测试")
    
    dataflow_logger = setup_dataflow_logging()
    dataflow_logger.info("数据流模块日志测试")
    
    llm_logger = setup_llm_logging()
    llm_logger.info("LLM适配器模块日志测试")
    
    log_shutdown_info()
