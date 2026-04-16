#!/usr/bin/env python3
"""
QuantScope 安装验证脚本
用于验证系统安装是否正确
"""

import sys
import os
import importlib
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class InstallationTester:
    """安装验证测试器"""
    
    def __init__(self):
        self.results = []
        self.errors = []
        
    def test_python_version(self) -> bool:
        """测试Python版本"""
        print("🐍 检查Python版本...")
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 10:
            self.results.append(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.errors.append(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro} (需要3.10+)")
            return False
    
    def test_virtual_environment(self) -> bool:
        """测试虚拟环境"""
        print("🔧 检查虚拟环境...")
        
        in_venv = (
            hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        )
        
        if in_venv:
            self.results.append("✅ 虚拟环境: 已激活")
            return True
        else:
            self.errors.append("⚠️ 虚拟环境: 未激活 (建议使用虚拟环境)")
            return False
    
    def test_core_modules(self) -> bool:
        """测试核心模块导入"""
        print("📦 检查核心模块...")
        
        core_modules = [
            'tradingagents',
            'tradingagents.config',
            'tradingagents.llm_adapters',
            'tradingagents.agents',
            'tradingagents.dataflows'
        ]
        
        success = True
        for module in core_modules:
            try:
                importlib.import_module(module)
                self.results.append(f"✅ 核心模块: {module}")
            except ImportError as e:
                self.errors.append(f"❌ 核心模块导入失败: {module} - {e}")
                success = False
        
        return success
    
    def test_dependencies(self) -> bool:
        """测试依赖包"""
        print("📚 检查依赖包...")
        
        dependencies = [
            ('streamlit', 'Web框架'),
            ('pandas', '数据处理'),
            ('numpy', '数值计算'),
            ('requests', 'HTTP请求'),
            ('yfinance', '股票数据'),
            ('openai', 'OpenAI客户端'),
            ('langchain', 'LangChain框架'),
            ('plotly', '图表绘制'),
            ('redis', 'Redis客户端'),
            ('pymongo', 'MongoDB客户端')
        ]
        
        success = True
        for package, description in dependencies:
            try:
                importlib.import_module(package)
                self.results.append(f"✅ 依赖包: {package} ({description})")
            except ImportError:
                self.errors.append(f"❌ 依赖包缺失: {package} ({description})")
                success = False
        
        return success
    
    def test_config_files(self) -> bool:
        """测试配置文件"""
        print("⚙️ 检查配置文件...")
        
        config_files = [
            ('VERSION', '版本文件'),
            ('.env.example', '环境变量模板'),
            ('config/settings.json', '设置配置'),
            ('config/models.json', '模型配置'),
            ('config/pricing.json', '价格配置'),
            ('config/logging.toml', '日志配置')
        ]
        
        success = True
        for file_path, description in config_files:
            full_path = project_root / file_path
            if full_path.exists():
                self.results.append(f"✅ 配置文件: {file_path} ({description})")
            else:
                self.errors.append(f"❌ 配置文件缺失: {file_path} ({description})")
                success = False
        
        return success
    
    def test_environment_variables(self) -> bool:
        """测试环境变量"""
        print("🔑 检查环境变量...")
        
        # 检查.env文件
        env_file = project_root / '.env'
        if env_file.exists():
            self.results.append("✅ 环境变量文件: .env 存在")
            
            # 读取并检查关键配置
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否有API密钥配置
                api_keys = [
                    'OPENAI_API_KEY',
                    'DASHSCOPE_API_KEY', 
                    'DEEPSEEK_API_KEY',
                    'QIANFAN_ACCESS_KEY',
                    'TUSHARE_TOKEN'
                ]
                
                configured_apis = []
                for key in api_keys:
                    if key in content and not content.count(f'{key}=your_') > 0:
                        configured_apis.append(key)
                
                if configured_apis:
                    self.results.append(f"✅ 已配置API: {', '.join(configured_apis)}")
                else:
                    self.errors.append("⚠️ 未发现已配置的API密钥")
                
            except Exception as e:
                self.errors.append(f"❌ 读取.env文件失败: {e}")
                return False
        else:
            self.errors.append("⚠️ 环境变量文件: .env 不存在 (请复制.env.example)")
            return False
        
        return True
    
    def test_web_application(self) -> bool:
        """测试Web应用"""
        print("🌐 检查Web应用...")
        
        web_files = [
            ('web/app.py', 'Streamlit主应用'),
            ('web/components/sidebar.py', '侧边栏组件'),
            ('start_web.py', '启动脚本')
        ]
        
        success = True
        for file_path, description in web_files:
            full_path = project_root / file_path
            if full_path.exists():
                self.results.append(f"✅ Web文件: {file_path} ({description})")
            else:
                self.errors.append(f"❌ Web文件缺失: {file_path} ({description})")
                success = False
        
        return success
    
    def test_data_directories(self) -> bool:
        """测试数据目录"""
        print("📁 检查数据目录...")
        
        data_dirs = [
            'data',
            'data/cache',
            'logs'
        ]
        
        for dir_path in data_dirs:
            full_path = project_root / dir_path
            if not full_path.exists():
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                    self.results.append(f"✅ 数据目录: {dir_path} (已创建)")
                except Exception as e:
                    self.errors.append(f"❌ 创建目录失败: {dir_path} - {e}")
                    return False
            else:
                self.results.append(f"✅ 数据目录: {dir_path} (已存在)")
        
        return True
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        print("🚀 开始安装验证测试...")
        print("=" * 60)
        
        tests = [
            ('Python版本', self.test_python_version),
            ('虚拟环境', self.test_virtual_environment),
            ('核心模块', self.test_core_modules),
            ('依赖包', self.test_dependencies),
            ('配置文件', self.test_config_files),
            ('环境变量', self.test_environment_variables),
            ('Web应用', self.test_web_application),
            ('数据目录', self.test_data_directories)
        ]
        
        test_results = {}
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results[test_name] = result
                print()
            except Exception as e:
                self.errors.append(f"❌ 测试异常: {test_name} - {e}")
                test_results[test_name] = False
                print()
        
        return test_results
    
    def print_summary(self, test_results: Dict[str, bool]):
        """打印测试总结"""
        print("=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        
        # 成功的测试
        if self.results:
            print("\n✅ 成功项目:")
            for result in self.results:
                print(f"  {result}")
        
        # 失败的测试
        if self.errors:
            print("\n❌ 问题项目:")
            for error in self.errors:
                print(f"  {error}")
        
        # 总体状态
        total_tests = len(test_results)
        passed_tests = sum(test_results.values())
        
        print(f"\n📈 测试统计:")
        print(f"  总测试数: {total_tests}")
        print(f"  通过测试: {passed_tests}")
        print(f"  失败测试: {total_tests - passed_tests}")
        print(f"  成功率: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 恭喜！安装验证全部通过！")
            print("   你可以开始使用QuantScope了！")
            print("   运行: python start_web.py")
        else:
            print("\n⚠️ 安装验证发现问题，请根据上述错误信息进行修复。")
            print("   参考文档: docs/guides/installation-guide.md")

def main():
    """主函数"""
    tester = InstallationTester()
    test_results = tester.run_all_tests()
    tester.print_summary(test_results)
    
    # 返回退出码
    if all(test_results.values()):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
