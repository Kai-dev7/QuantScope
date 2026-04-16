#!/usr/bin/env python3
"""
QuantScope v0.1.9 版本发布脚本
CLI用户体验重大优化与统一日志管理版本
"""

import os
import sys
import subprocess
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def run_command(command, cwd=None):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd or project_root,
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_version_consistency():
    """检查版本号一致性"""
    print("🔍 检查版本号一致性...")
    
    # 检查VERSION文件
    version_file = os.path.join(project_root, "VERSION")
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            version_content = f.read().strip()
        print(f"   VERSION文件: {version_content}")
    else:
        print("   ❌ VERSION文件不存在")
        return False
    
    # 检查pyproject.toml
    pyproject_file = os.path.join(project_root, "pyproject.toml")
    if os.path.exists(pyproject_file):
        with open(pyproject_file, 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.strip().startswith('version ='):
                    pyproject_version = line.split('=')[1].strip().strip('"')
                    print(f"   pyproject.toml: {pyproject_version}")
                    break
    
    # 检查README.md
    readme_file = os.path.join(project_root, "README.md")
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "cn--0.1.9" in content:
                print("   README.md: cn-0.1.9 ✅")
            else:
                print("   README.md: 版本号未更新 ❌")
                return False
    
    return True

def create_git_tag():
    """创建Git标签"""
    print("🏷️ 创建Git标签...")
    
    tag_name = "v0.1.9"
    tag_message = "QuantScope v0.1.9: CLI用户体验重大优化与统一日志管理"
    
    # 检查标签是否已存在
    success, stdout, stderr = run_command(f"git tag -l {tag_name}")
    if tag_name in stdout:
        print(f"   标签 {tag_name} 已存在")
        return True
    
    # 创建标签
    success, stdout, stderr = run_command(f'git tag -a {tag_name} -m "{tag_message}"')
    if success:
        print(f"   ✅ 标签 {tag_name} 创建成功")
        return True
    else:
        print(f"   ❌ 标签创建失败: {stderr}")
        return False

def generate_release_summary():
    """生成发布摘要"""
    print("📋 生成发布摘要...")
    
    summary = {
        "version": "cn-0.1.9",
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "title": "CLI用户体验重大优化与统一日志管理",
        "highlights": [
            "🎨 CLI界面重构 - 界面与日志分离，提供清爽用户体验",
            "🔄 进度显示优化 - 解决重复提示，添加多阶段进度跟踪", 
            "⏱️ 时间预估功能 - 智能分析阶段添加10分钟时间预估",
            "📝 统一日志管理 - 配置化日志系统，支持多环境",
            "🇭🇰 港股数据优化 - 改进数据获取稳定性和容错机制",
            "🔑 OpenAI配置修复 - 解决配置混乱和错误处理问题"
        ],
        "key_features": {
            "cli_optimization": {
                "interface_separation": "用户界面与系统日志完全分离",
                "progress_display": "智能进度显示，防止重复提示",
                "time_estimation": "分析阶段时间预估，管理用户期望",
                "visual_enhancement": "Rich彩色输出，专业视觉效果"
            },
            "logging_system": {
                "unified_management": "LoggingManager统一日志管理",
                "configurable": "TOML配置文件，灵活控制日志级别",
                "tool_logging": "详细记录工具调用过程和结果",
                "multi_environment": "本地和Docker环境差异化配置"
            },
            "data_source_improvements": {
                "hk_stocks": "港股数据获取优化和容错机制",
                "openai_config": "OpenAI配置统一和错误处理",
                "caching_strategy": "智能缓存和多级fallback"
            }
        },
        "user_experience": {
            "before": "技术日志干扰、重复提示、等待焦虑",
            "after": "清爽界面、智能进度、时间预估、专业体验"
        },
        "technical_improvements": [
            "代码质量提升 - 统一导入方式，增强错误处理",
            "测试覆盖增加 - CLI和日志系统测试套件",
            "文档完善 - 设计文档和配置管理指南",
            "架构优化 - 模块化设计，提升可维护性"
        ],
        "files_changed": {
            "core_files": [
                "cli/main.py - CLI界面重构和进度显示优化",
                "tradingagents/utils/logging_manager.py - 统一日志管理器",
                "tradingagents/utils/tool_logging.py - 工具调用日志记录",
                "config/logging.toml - 日志配置文件"
            ],
            "documentation": [
                "docs/releases/v0.1.9.md - 详细发布说明",
                "docs/releases/CHANGELOG.md - 更新日志",
                "README.md - 版本信息更新"
            ],
            "tests": [
                "test_cli_logging_fix.py - CLI日志修复测试",
                "test_cli_progress_display.py - 进度显示测试",
                "test_duplicate_progress_fix.py - 重复提示修复测试",
                "test_detailed_progress_display.py - 详细进度显示测试"
            ]
        }
    }
    
    # 保存发布摘要
    summary_file = os.path.join(project_root, "docs", "releases", "v0.1.9_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 发布摘要已保存到: {summary_file}")
    return True

def validate_release():
    """验证发布准备"""
    print("✅ 验证发布准备...")
    
    checks = []
    
    # 检查关键文件是否存在
    key_files = [
        "VERSION",
        "README.md", 
        "docs/releases/v0.1.9.md",
        "docs/releases/CHANGELOG.md",
        "cli/main.py",
        "tradingagents/utils/logging_manager.py"
    ]
    
    for file_path in key_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            checks.append(f"   ✅ {file_path}")
        else:
            checks.append(f"   ❌ {file_path} 缺失")
    
    # 检查Git状态
    success, stdout, stderr = run_command("git status --porcelain")
    if success:
        if stdout.strip():
            checks.append("   ⚠️ 有未提交的更改")
        else:
            checks.append("   ✅ Git工作区干净")
    
    for check in checks:
        print(check)
    
    return all("✅" in check for check in checks)

def main():
    """主函数"""
    print("🚀 QuantScope v0.1.9 版本发布")
    print("=" * 60)
    print("📋 版本主题: CLI用户体验重大优化与统一日志管理")
    print("📅 发布日期:", datetime.now().strftime("%Y年%m月%d日"))
    print("=" * 60)
    
    steps = [
        ("检查版本号一致性", check_version_consistency),
        ("验证发布准备", validate_release),
        ("生成发布摘要", generate_release_summary),
        ("创建Git标签", create_git_tag)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}")
        if not step_func():
            print(f"❌ {step_name}失败，发布中止")
            return False
    
    print("\n" + "=" * 60)
    print("🎉 v0.1.9 版本发布准备完成！")
    print("=" * 60)
    
    print("\n📋 发布亮点:")
    highlights = [
        "🎨 CLI界面重构 - 专业、清爽、用户友好",
        "🔄 进度显示优化 - 智能跟踪，消除重复",
        "⏱️ 时间预估功能 - 管理期望，减少焦虑",
        "📝 统一日志管理 - 配置化，多环境支持",
        "🇭🇰 港股数据优化 - 稳定性和容错性提升",
        "🔑 配置问题修复 - OpenAI配置统一管理"
    ]
    
    for highlight in highlights:
        print(f"   {highlight}")
    
    print("\n🎯 用户体验提升:")
    print("   - 界面清爽美观，没有技术信息干扰")
    print("   - 实时进度反馈，消除等待焦虑") 
    print("   - 专业分析流程展示，增强系统信任")
    print("   - 时间预估管理，提升等待体验")
    
    print("\n📚 相关文档:")
    print("   - 详细发布说明: docs/releases/v0.1.9.md")
    print("   - 完整更新日志: docs/releases/CHANGELOG.md")
    print("   - 发布摘要: docs/releases/v0.1.9_summary.json")
    
    print("\n🔄 下一步操作:")
    print("   1. git push origin main")
    print("   2. git push origin v0.1.9")
    print("   3. 在GitHub创建Release")
    print("   4. 更新Docker镜像")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
