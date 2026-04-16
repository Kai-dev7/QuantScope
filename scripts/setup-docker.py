#!/usr/bin/env python3
"""
Docker环境快速配置脚本
帮助用户快速配置Docker部署环境
"""

import os
import shutil
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')

def setup_docker_env():
    """配置Docker环境"""
    project_root = Path(__file__).parent.parent
    env_example = project_root / ".env.example"
    env_file = project_root / ".env"
    
    logger.info(f"🐳 QuantScope Docker环境配置向导")
    logger.info(f"=")
    
    # 检查.env文件
    if env_file.exists():
        logger.info(f"📁 发现现有的.env文件")
        choice = input("是否要备份现有配置并重新配置？(y/N): ").lower()
        if choice == 'y':
            backup_file = project_root / f".env.backup.{int(time.time())}"
            shutil.copy(env_file, backup_file)
            logger.info(f"✅ 已备份到: {backup_file}")
        else:
            logger.error(f"❌ 取消配置")
            return False
    
    # 复制模板文件
    if not env_example.exists():
        logger.error(f"❌ 找不到.env.example文件")
        return False
    
    shutil.copy(env_example, env_file)
    logger.info(f"✅ 已复制配置模板")
    
    # 读取配置文件
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Docker环境配置
    docker_configs = {
        'MONGODB_ENABLED': 'true',
        'REDIS_ENABLED': 'true',
        'MONGODB_HOST': 'mongodb',
        'REDIS_HOST': 'redis',
        'MONGODB_PORT': '27017',
        'REDIS_PORT': '6379'
    }
    
    logger.info(f"\n🔧 配置Docker环境变量...")
    for key, value in docker_configs.items():
        # 替换配置值
        import re
        pattern = f'^{key}=.*$'
        replacement = f'{key}={value}'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 写回文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✅ Docker环境配置完成")
    
    # API密钥配置提醒
    logger.info(f"\n🔑 API密钥配置")
    logger.info(f"请编辑.env文件，配置以下API密钥（至少配置一个）：")
    logger.info(f"- TRADINGAGENTS_DEEPSEEK_API_KEY")
    logger.info(f"- TRADINGAGENTS_DASHSCOPE_API_KEY")
    logger.info(f"- TRADINGAGENTS_TUSHARE_TOKEN")
    logger.info(f"- TRADINGAGENTS_FINNHUB_API_KEY")
    
    # 显示下一步操作
    logger.info(f"\n🚀 下一步操作：")
    logger.info(f"1. 编辑.env文件，填入您的API密钥")
    logger.info(f"2. 运行: docker-compose up -d")
    logger.info(f"3. 访问: http://localhost:8501")
    
    return True

def check_docker():
    """检查Docker环境"""
    logger.debug(f"🔍 检查Docker环境...")
    
    # 检查Docker
    if shutil.which('docker') is None:
        logger.error(f"❌ 未找到Docker，请先安装Docker Desktop")
        return False
    
    # 检查docker-compose
    if shutil.which('docker-compose') is None:
        logger.error(f"❌ 未找到docker-compose，请确保Docker Desktop已正确安装")
        return False
    
    # 检查Docker是否运行
    try:
        import subprocess
        result = subprocess.run(['docker', 'info'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            logger.error(f"❌ Docker未运行，请启动Docker Desktop")
            return False
    except Exception as e:
        logger.error(f"❌ Docker检查失败: {e}")
        return False
    
    logger.info(f"✅ Docker环境检查通过")
    return True

def main():
    """主函数"""
    import time

    
    if not check_docker():
        logger.info(f"\n💡 请先安装并启动Docker Desktop:")
        logger.info(f"- Windows/macOS: https://www.docker.com/products/docker-desktop")
        logger.info(f"- Linux: https://docs.docker.com/engine/install/")
        return
    
    if setup_docker_env():
        logger.info(f"\n🎉 Docker环境配置完成！")
        logger.info(f"\n📚 更多信息请参考:")
        logger.info(f"- Docker部署指南: docs/DOCKER_GUIDE.md")
        logger.info(f"- 项目文档: README.md")
    else:
        logger.error(f"\n❌ 配置失败")

if __name__ == "__main__":
    main()
