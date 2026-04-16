#!/usr/bin/env python3
"""
API密钥验证脚本
用于验证配置的API密钥是否有效
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    import requests
except ImportError:
    print("❌ 缺少必要的依赖包")
    print("请运行: pip install python-dotenv requests")
    sys.exit(1)

# 加载环境变量
load_dotenv()

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg): print(f"{Colors.GREEN}✅ {msg}{Colors.END}")
def print_warning(msg): print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")
def print_error(msg): print(f"{Colors.RED}❌ {msg}{Colors.END}")
def print_info(msg): print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")
def print_header(msg): print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}\n{msg}\n{'='*60}{Colors.END}\n")

def validate_deepseek(api_key: str) -> Tuple[bool, str]:
    """验证DeepSeek API密钥"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            "https://api.deepseek.com/v1/models",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return True, "API密钥有效"
        elif response.status_code == 401:
            return False, "API密钥无效或已过期"
        else:
            return False, f"验证失败 (状态码: {response.status_code})"
    except requests.exceptions.Timeout:
        return False, "请求超时，请检查网络连接"
    except Exception as e:
        return False, f"验证出错: {str(e)}"

def validate_dashscope(api_key: str) -> Tuple[bool, str]:
    """验证阿里百炼API密钥"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        # 使用一个简单的API调用来验证
        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers=headers,
            json={
                "model": "qwen-turbo",
                "input": {"prompt": "test"},
                "parameters": {"max_tokens": 1}
            },
            timeout=10
        )
        if response.status_code == 200:
            return True, "API密钥有效"
        elif response.status_code == 401:
            return False, "API密钥无效或已过期"
        elif response.status_code == 400:
            # 400可能是参数问题，但密钥是有效的
            return True, "API密钥有效（参数验证）"
        else:
            return False, f"验证失败 (状态码: {response.status_code})"
    except requests.exceptions.Timeout:
        return False, "请求超时，请检查网络连接"
    except Exception as e:
        return False, f"验证出错: {str(e)}"

def validate_google(api_key: str) -> Tuple[bool, str]:
    """验证Google AI API密钥"""
    try:
        response = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            timeout=10
        )
        if response.status_code == 200:
            return True, "API密钥有效"
        elif response.status_code == 400:
            return False, "API密钥无效"
        else:
            return False, f"验证失败 (状态码: {response.status_code})"
    except requests.exceptions.Timeout:
        return False, "请求超时，请检查网络连接"
    except Exception as e:
        return False, f"验证出错: {str(e)}"

def validate_openai(api_key: str) -> Tuple[bool, str]:
    """验证OpenAI API密钥"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return True, "API密钥有效"
        elif response.status_code == 401:
            return False, "API密钥无效或已过期"
        else:
            return False, f"验证失败 (状态码: {response.status_code})"
    except requests.exceptions.Timeout:
        return False, "请求超时，请检查网络连接"
    except Exception as e:
        return False, f"验证出错: {str(e)}"

def main():
    """主函数"""
    print_header("🔐 QuantScope API密钥验证工具")
    
    # 检查.env文件
    env_file = project_root / ".env"
    if not env_file.exists():
        print_error("未找到.env配置文件")
        print_info("请先运行安装脚本或手动创建.env文件")
        sys.exit(1)
    
    print_info(f"配置文件: {env_file}")
    print()
    
    # 定义要验证的API密钥
    api_configs = [
        {
            "name": "DeepSeek",
            "env_key": "DEEPSEEK_API_KEY",
            "validator": validate_deepseek,
            "url": "https://platform.deepseek.com/"
        },
        {
            "name": "阿里百炼",
            "env_key": "DASHSCOPE_API_KEY",
            "validator": validate_dashscope,
            "url": "https://dashscope.aliyun.com/"
        },
        {
            "name": "Google AI",
            "env_key": "GOOGLE_API_KEY",
            "validator": validate_google,
            "url": "https://aistudio.google.com/"
        },
        {
            "name": "OpenAI",
            "env_key": "OPENAI_API_KEY",
            "validator": validate_openai,
            "url": "https://platform.openai.com/"
        }
    ]
    
    results = []
    valid_count = 0
    
    # 验证每个API密钥
    for config in api_configs:
        api_key = os.getenv(config["env_key"])
        
        print(f"🔍 验证 {config['name']}...")
        
        if not api_key:
            print_warning(f"未配置 {config['env_key']}")
            print_info(f"获取地址: {config['url']}")
            results.append((config["name"], False, "未配置"))
        else:
            # 隐藏部分密钥
            masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            print_info(f"密钥: {masked_key}")
            
            # 验证密钥
            is_valid, message = config["validator"](api_key)
            
            if is_valid:
                print_success(message)
                valid_count += 1
                results.append((config["name"], True, message))
            else:
                print_error(message)
                results.append((config["name"], False, message))
        
        print()
    
    # 显示总结
    print_header("📊 验证结果总结")
    
    print(f"{'提供商':<15} {'状态':<10} {'说明'}")
    print("-" * 60)
    
    for name, is_valid, message in results:
        status = f"{Colors.GREEN}✅ 有效{Colors.END}" if is_valid else f"{Colors.RED}❌ 无效{Colors.END}"
        print(f"{name:<15} {status:<20} {message}")
    
    print()
    print(f"有效密钥数: {valid_count}/{len(api_configs)}")
    
    # 给出建议
    if valid_count == 0:
        print()
        print_error("未配置任何有效的API密钥")
        print_info("请至少配置一个LLM提供商的API密钥")
        print_info("运行安装脚本重新配置: python scripts/easy_install.py --reconfigure")
        sys.exit(1)
    elif valid_count < len(api_configs):
        print()
        print_warning(f"仅配置了 {valid_count} 个API密钥")
        print_info("建议配置多个提供商以提高可用性")
    else:
        print()
        print_success("所有配置的API密钥都有效！")
    
    print()
    print_info("提示: 可以在Web界面侧边栏切换不同的LLM模型")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  验证已取消")
        sys.exit(0)
    except Exception as e:
        print_error(f"验证过程出错: {e}")
        sys.exit(1)

