#!/usr/bin/env python3
"""
QuantScope 快速安装脚本
自动检测环境并引导用户完成安装配置
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

class Colors:
    """控制台颜色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text, color=Colors.GREEN):
    """打印彩色文本"""
    print(f"{color}{text}{Colors.END}")

def print_header():
    """打印欢迎信息"""
    print_colored("=" * 60, Colors.BLUE)
    print_colored("🚀 QuantScope 快速安装向导", Colors.BOLD)
    print_colored("=" * 60, Colors.BLUE)
    print()

def check_python_version():
    """检查Python版本"""
    print_colored("🔍 检查Python版本...", Colors.BLUE)
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print_colored(f"✅ Python {version.major}.{version.minor}.{version.micro} - 版本符合要求", Colors.GREEN)
        return True
    else:
        print_colored(f"❌ Python {version.major}.{version.minor}.{version.micro} - 需要Python 3.10+", Colors.RED)
        print_colored("请升级Python版本: https://www.python.org/downloads/", Colors.YELLOW)
        return False

def check_git():
    """检查Git是否安装"""
    print_colored("🔍 检查Git...", Colors.BLUE)
    
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_colored(f"✅ {result.stdout.strip()}", Colors.GREEN)
            return True
    except FileNotFoundError:
        pass
    
    print_colored("❌ Git未安装", Colors.RED)
    print_colored("请安装Git: https://git-scm.com/downloads", Colors.YELLOW)
    return False

def check_docker():
    """检查Docker是否安装"""
    print_colored("🔍 检查Docker...", Colors.BLUE)
    
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_colored(f"✅ {result.stdout.strip()}", Colors.GREEN)
            
            # 检查Docker Compose
            try:
                result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    print_colored(f"✅ {result.stdout.strip()}", Colors.GREEN)
                    return True
            except FileNotFoundError:
                pass
            
            print_colored("❌ Docker Compose未安装", Colors.YELLOW)
            return False
    except FileNotFoundError:
        pass
    
    print_colored("❌ Docker未安装", Colors.YELLOW)
    return False

def choose_installation_method():
    """选择安装方式"""
    print_colored("\n📋 请选择安装方式:", Colors.BLUE)
    print("1. Docker安装 (推荐，简单稳定)")
    print("2. 本地安装 (适合开发者)")
    
    while True:
        choice = input("\n请输入选择 (1/2): ").strip()
        if choice in ['1', '2']:
            return choice
        print_colored("请输入有效选择 (1或2)", Colors.YELLOW)

def docker_install():
    """Docker安装流程"""
    print_colored("\n🐳 开始Docker安装...", Colors.BLUE)
    
    # 检查项目目录
    if not Path('docker-compose.yml').exists():
        print_colored("❌ 未找到docker-compose.yml文件", Colors.RED)
        print_colored("请确保在项目根目录运行此脚本", Colors.YELLOW)
        return False
    
    # 检查.env文件
    if not Path('.env').exists():
        print_colored("📝 创建环境配置文件...", Colors.BLUE)
        if Path('.env.example').exists():
            shutil.copy('.env.example', '.env')
            print_colored("✅ 已创建.env文件", Colors.GREEN)
        else:
            print_colored("❌ 未找到.env.example文件", Colors.RED)
            return False
    
    # 提示配置API密钥
    print_colored("\n⚠️  重要提醒:", Colors.YELLOW)
    print_colored("请编辑.env文件，配置至少一个AI模型的API密钥", Colors.YELLOW)
    print_colored("推荐配置DeepSeek或通义千问API密钥", Colors.YELLOW)
    
    input("\n按回车键继续...")
    
    # 启动Docker服务
    print_colored("🚀 启动Docker服务...", Colors.BLUE)
    try:
        result = subprocess.run(['docker-compose', 'up', '-d'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_colored("✅ Docker服务启动成功!", Colors.GREEN)
            print_colored("\n🌐 访问地址:", Colors.BLUE)
            print_colored("主应用: http://localhost:8501", Colors.GREEN)
            print_colored("Redis管理: http://localhost:8081", Colors.GREEN)
            return True
        else:
            print_colored(f"❌ Docker启动失败: {result.stderr}", Colors.RED)
            return False
    except Exception as e:
        print_colored(f"❌ Docker启动异常: {e}", Colors.RED)
        return False

def local_install():
    """本地安装流程"""
    print_colored("\n💻 开始本地安装...", Colors.BLUE)
    
    # 检查虚拟环境
    venv_path = Path('env')
    if not venv_path.exists():
        print_colored("📦 创建虚拟环境...", Colors.BLUE)
        try:
            subprocess.run([sys.executable, '-m', 'venv', 'env'], check=True)
            print_colored("✅ 虚拟环境创建成功", Colors.GREEN)
        except subprocess.CalledProcessError as e:
            print_colored(f"❌ 虚拟环境创建失败: {e}", Colors.RED)
            return False
    
    # 激活虚拟环境的Python路径
    if platform.system() == "Windows":
        python_path = venv_path / "Scripts" / "python.exe"
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        python_path = venv_path / "bin" / "python"
        pip_path = venv_path / "bin" / "pip"
    
    # 升级pip
    print_colored("📦 升级pip...", Colors.BLUE)
    try:
        subprocess.run([str(python_path), '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True, capture_output=True)
        print_colored("✅ pip升级成功", Colors.GREEN)
    except subprocess.CalledProcessError as e:
        print_colored(f"⚠️  pip升级失败，继续安装: {e}", Colors.YELLOW)
    
    # 安装依赖
    print_colored("📦 安装项目依赖...", Colors.BLUE)
    try:
        result = subprocess.run([str(pip_path), 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_colored("✅ 依赖安装成功", Colors.GREEN)
        else:
            print_colored(f"❌ 依赖安装失败: {result.stderr}", Colors.RED)
            return False
    except Exception as e:
        print_colored(f"❌ 依赖安装异常: {e}", Colors.RED)
        return False
    
    # 创建.env文件
    if not Path('.env').exists():
        print_colored("📝 创建环境配置文件...", Colors.BLUE)
        if Path('.env.example').exists():
            shutil.copy('.env.example', '.env')
            print_colored("✅ 已创建.env文件", Colors.GREEN)
        else:
            print_colored("❌ 未找到.env.example文件", Colors.RED)
            return False
    
    # 提示配置API密钥
    print_colored("\n⚠️  重要提醒:", Colors.YELLOW)
    print_colored("请编辑.env文件，配置至少一个AI模型的API密钥", Colors.YELLOW)
    print_colored("推荐配置DeepSeek或通义千问API密钥", Colors.YELLOW)
    
    input("\n按回车键继续...")
    
    # 启动应用
    print_colored("🚀 启动应用...", Colors.BLUE)
    print_colored("应用将在浏览器中打开: http://localhost:8501", Colors.GREEN)
    
    # 提供启动命令
    if platform.system() == "Windows":
        activate_cmd = "env\\Scripts\\activate"
        start_cmd = f"{activate_cmd} && python -m streamlit run web/app.py"
    else:
        activate_cmd = "source env/bin/activate"
        start_cmd = f"{activate_cmd} && python -m streamlit run web/app.py"
    
    print_colored(f"\n📋 启动命令:", Colors.BLUE)
    print_colored(f"  {start_cmd}", Colors.GREEN)
    
    return True

def main():
    """主函数"""
    print_header()
    
    # 检查基础环境
    if not check_python_version():
        return
    
    check_git()
    docker_available = check_docker()
    
    # 选择安装方式
    if docker_available:
        choice = choose_installation_method()
    else:
        print_colored("\n💡 Docker未安装，将使用本地安装方式", Colors.YELLOW)
        choice = '2'
    
    # 执行安装
    success = False
    if choice == '1':
        success = docker_install()
    else:
        success = local_install()
    
    # 安装结果
    if success:
        print_colored("\n🎉 安装完成!", Colors.GREEN)
        print_colored("📖 详细文档: docs/INSTALLATION_GUIDE.md", Colors.BLUE)
        print_colored("❓ 遇到问题: https://github.com/hsliuping/QuantScope/issues", Colors.BLUE)
    else:
        print_colored("\n❌ 安装失败", Colors.RED)
        print_colored("📖 请查看详细安装指南: docs/INSTALLATION_GUIDE.md", Colors.YELLOW)

if __name__ == "__main__":
    main()
