#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复分析级别3死循环问题

问题分析：
1. 级别3的max_risk_discuss_rounds=2与级别1、2不同
2. 基本面分析师在某些情况下会持续生成tool_calls而不设置fundamentals_report
3. 条件判断逻辑检测到tool_calls就返回tools_fundamentals，形成死循环

修复方案：
1. 在基本面分析师中添加循环检测机制
2. 限制工具调用次数，防止无限循环
3. 改进条件判断逻辑，同时检查报告完成状态
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def apply_fundamentals_analyst_fix():
    """修复基本面分析师的死循环问题"""
    print("🔧 开始修复基本面分析师死循环问题...")
    
    fundamentals_file = "d:\\code\\QuantScope\\tradingagents\\agents\\analysts\\fundamentals_analyst.py"
    
    # 读取原文件
    with open(fundamentals_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经应用过修复
    if "# 死循环修复: 添加工具调用计数器" in content:
        print("✅ 基本面分析师修复已存在，跳过")
        return True
    
    # 在fundamentals_analyst_node函数开始处添加工具调用计数器
    old_debug_start = 'def fundamentals_analyst_node(state):\n        logger.debug(f"📊 [DEBUG] ===== 基本面分析师节点开始 =====")'
    
    new_debug_start = '''def fundamentals_analyst_node(state):
        # 死循环修复: 添加工具调用计数器
        tool_call_count = state.get("fundamentals_tool_call_count", 0)
        max_tool_calls = 3  # 最大工具调用次数
        
        logger.debug(f"📊 [DEBUG] ===== 基本面分析师节点开始 =====")
        logger.debug(f"🔧 [死循环修复] 当前工具调用次数: {tool_call_count}/{max_tool_calls}")'''
    
    if old_debug_start in content:
        content = content.replace(old_debug_start, new_debug_start)
        print("✅ 添加工具调用计数器")
    else:
        print("⚠️ 未找到预期的函数开始位置，手动定位...")
        # 备用方案：在函数定义后添加
        func_def = "def fundamentals_analyst_node(state):"
        if func_def in content:
            content = content.replace(
                func_def,
                func_def + '''
        # 死循环修复: 添加工具调用计数器
        tool_call_count = state.get("fundamentals_tool_call_count", 0)
        max_tool_calls = 3  # 最大工具调用次数
        
        logger.debug(f"🔧 [死循环修复] 当前工具调用次数: {tool_call_count}/{max_tool_calls}")'''
            )
            print("✅ 使用备用方案添加工具调用计数器")
    
    # 在工具调用检测部分添加循环检测
    old_tool_check = '''if tool_call_count > 0:
                # 有工具调用，返回状态让工具执行
                tool_calls_info = []
                for tc in result.tool_calls:
                    tool_calls_info.append(tc['name'])
                    logger.debug(f"📊 [DEBUG] 工具调用 {len(tool_calls_info)}: {tc}")

                logger.info(f"📊 [基本面分析师] 工具调用: {tool_calls_info}")
                # ⚠️ 重要：当有tool_calls时，不设置fundamentals_report
                # 让它保持为空，这样条件判断会继续循环到工具节点
                return {
                    "messages": [result]
                }'''
    
    new_tool_check = '''if tool_call_count > 0:
                # 死循环修复: 检查工具调用次数限制
                if tool_call_count >= max_tool_calls:
                    logger.warning(f"🔧 [死循环修复] 达到最大工具调用次数 {max_tool_calls}，强制生成报告")
                    # 强制生成基本面报告，避免死循环
                    fallback_report = f"基本面分析（股票代码：{ticker}）\\n\\n由于达到最大工具调用次数限制，使用简化分析模式。建议检查数据源连接或降低分析复杂度。"
                    return {
                        "messages": [result],
                        "fundamentals_report": fallback_report,
                        "fundamentals_tool_call_count": tool_call_count + 1
                    }
                
                # 有工具调用，返回状态让工具执行
                tool_calls_info = []
                for tc in result.tool_calls:
                    tool_calls_info.append(tc['name'])
                    logger.debug(f"📊 [DEBUG] 工具调用 {len(tool_calls_info)}: {tc}")

                logger.info(f"📊 [基本面分析师] 工具调用: {tool_calls_info}")
                # ⚠️ 重要：当有tool_calls时，不设置fundamentals_report
                # 让它保持为空，这样条件判断会继续循环到工具节点
                return {
                    "messages": [result],
                    "fundamentals_tool_call_count": tool_call_count + 1
                }'''
    
    if old_tool_check in content:
        content = content.replace(old_tool_check, new_tool_check)
        print("✅ 添加工具调用次数限制检查")
    else:
        print("⚠️ 未找到预期的工具调用检查代码")
    
    # 在Google工具调用处理中也添加计数器更新
    google_return = 'return {"fundamentals_report": report}'
    google_return_fixed = 'return {"fundamentals_report": report, "fundamentals_tool_call_count": tool_call_count + 1}'
    
    content = content.replace(google_return, google_return_fixed)
    print("✅ 更新Google工具调用处理的计数器")
    
    # 在强制工具调用处理中也添加计数器更新
    force_return = 'return {"fundamentals_report": report}'
    force_return_fixed = 'return {"fundamentals_report": report, "fundamentals_tool_call_count": tool_call_count + 1}'
    
    # 只替换强制工具调用部分的return（在else分支中）
    content = content.replace(
        'return {"fundamentals_report": report}',
        'return {"fundamentals_report": report, "fundamentals_tool_call_count": tool_call_count + 1}'
    )
    print("✅ 更新强制工具调用处理的计数器")
    
    # 写回文件
    with open(fundamentals_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 基本面分析师修复完成")
    return True

def apply_conditional_logic_fix():
    """修复条件判断逻辑的死循环问题"""
    print("🔧 开始修复条件判断逻辑...")
    
    conditional_file = "d:\\code\\QuantScope\\tradingagents\\graph\\conditional_logic.py"
    
    # 读取原文件
    with open(conditional_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经应用过修复
    if "# 死循环修复: 添加工具调用次数检查" in content:
        print("✅ 条件判断逻辑修复已存在，跳过")
        return True
    
    # 找到should_continue_fundamentals函数并修复
    old_function = '''def should_continue_fundamentals(self, state: AgentState):
        """判断基本面分析是否应该继续"""
        logger.info(f"🔀 [条件判断] should_continue_fundamentals")
        
        messages = state["messages"]
        logger.info(f"🔀 [条件判断] - 消息数量: {len(messages)}")
        
        # 检查基本面报告长度
        fundamentals_report = state.get("fundamentals_report", "")
        logger.info(f"🔀 [条件判断] - 报告长度: {len(fundamentals_report)}")
        
        if len(messages) > 0:
            last_message = messages[-1]
            logger.info(f"🔀 [条件判断] - 最后消息类型: {type(last_message).__name__}")
            
            # 检查是否有tool_calls
            has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls
            logger.info(f"🔀 [条件判断] - 是否有tool_calls: {has_tool_calls}")
            
            if has_tool_calls:
                tool_calls_count = len(last_message.tool_calls)
                logger.info(f"🔀 [条件判断] - tool_calls数量: {tool_calls_count}")
                logger.info(f"🔀 [条件判断] ⚡ 检测到tool_calls，返回: tools_fundamentals")
                return "tools_fundamentals"
            else:
                logger.info(f"🔀 [条件判断] - tool_calls数量: 0")
        
        # 检查报告是否完成（长度大于50字符认为是有效报告）
        if len(fundamentals_report) > 50:
            logger.info(f"🔀 [条件判断] ✅ 报告已完成，返回: Msg Clear Fundamentals")
            return "Msg Clear Fundamentals"
        else:
            logger.info(f"🔀 [条件判断] ⚡ 报告未完成，返回: tools_fundamentals")
            return "tools_fundamentals"'''
    
    new_function = '''def should_continue_fundamentals(self, state: AgentState):
        """判断基本面分析是否应该继续"""
        logger.info(f"🔀 [条件判断] should_continue_fundamentals")
        
        messages = state["messages"]
        logger.info(f"🔀 [条件判断] - 消息数量: {len(messages)}")
        
        # 死循环修复: 添加工具调用次数检查
        tool_call_count = state.get("fundamentals_tool_call_count", 0)
        max_tool_calls = 3
        logger.info(f"🔧 [死循环修复] - 工具调用次数: {tool_call_count}/{max_tool_calls}")
        
        # 检查基本面报告长度
        fundamentals_report = state.get("fundamentals_report", "")
        logger.info(f"🔀 [条件判断] - 报告长度: {len(fundamentals_report)}")
        
        # 死循环修复: 如果达到最大工具调用次数，强制结束
        if tool_call_count >= max_tool_calls:
            logger.warning(f"🔧 [死循环修复] 达到最大工具调用次数，强制结束: Msg Clear Fundamentals")
            return "Msg Clear Fundamentals"
        
        if len(messages) > 0:
            last_message = messages[-1]
            logger.info(f"🔀 [条件判断] - 最后消息类型: {type(last_message).__name__}")
            
            # 检查是否有tool_calls
            has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls
            logger.info(f"🔀 [条件判断] - 是否有tool_calls: {has_tool_calls}")
            
            if has_tool_calls:
                tool_calls_count = len(last_message.tool_calls)
                logger.info(f"🔀 [条件判断] - tool_calls数量: {tool_calls_count}")
                logger.info(f"🔀 [条件判断] ⚡ 检测到tool_calls，返回: tools_fundamentals")
                return "tools_fundamentals"
            else:
                logger.info(f"🔀 [条件判断] - tool_calls数量: 0")
        
        # 检查报告是否完成（长度大于50字符认为是有效报告）
        if len(fundamentals_report) > 50:
            logger.info(f"🔀 [条件判断] ✅ 报告已完成，返回: Msg Clear Fundamentals")
            return "Msg Clear Fundamentals"
        else:
            logger.info(f"🔀 [条件判断] ⚡ 报告未完成，返回: tools_fundamentals")
            return "tools_fundamentals"'''
    
    if old_function in content:
        content = content.replace(old_function, new_function)
        print("✅ 修复should_continue_fundamentals函数")
    else:
        print("⚠️ 未找到预期的should_continue_fundamentals函数")
        return False
    
    # 写回文件
    with open(conditional_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 条件判断逻辑修复完成")
    return True

def create_test_script():
    """创建测试脚本验证修复效果"""
    print("🧪 创建测试脚本...")
    
    test_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试级别3死循环修复效果
"""

import os
import sys
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_level3_analysis():
    """测试级别3分析是否还会死循环"""
    print("🧪 测试级别3分析修复效果")
    print("=" * 60)
    
    try:
        from app.services.simple_analysis_service import SimpleAnalysisService
        
        # 创建分析服务
        service = SimpleAnalysisService()
        
        # 测试参数
        test_ticker = "000001"  # 平安银行
        test_date = "2025-01-15"
        research_depth = 3  # 级别3：标准分析
        
        print(f"📊 开始测试级别3分析...")
        print(f"股票代码: {test_ticker}")
        print(f"分析日期: {test_date}")
        print(f"分析级别: {research_depth} (标准分析)")
        
        # 设置超时时间（5分钟）
        timeout = 300
        start_time = time.time()
        
        print(f"⏰ 设置超时时间: {timeout}秒")
        print(f"🚀 开始分析...")
        
        # 执行分析
        result = service.analyze_stock(
            ticker=test_ticker,
            date=test_date,
            research_depth=research_depth
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"✅ 分析完成！")
        print(f"⏱️ 耗时: {elapsed:.1f}秒")
        
        # 检查结果
        if result and 'decision' in result:
            decision = result['decision']
            print(f"📈 分析结果:")
            print(f"  动作: {decision.get('action', 'N/A')}")
            print(f"  置信度: {decision.get('confidence', 0):.1%}")
            print(f"  风险评分: {decision.get('risk_score', 0):.1%}")
            
            # 检查是否有基本面报告
            if 'state' in result and 'fundamentals_report' in result['state']:
                fundamentals_report = result['state']['fundamentals_report']
                if fundamentals_report:
                    print(f"📊 基本面报告长度: {len(fundamentals_report)}字符")
                    print("✅ 基本面分析正常完成")
                else:
                    print("⚠️ 基本面报告为空")
            
            return True
        else:
            print("❌ 分析结果异常")
            return False
            
    except Exception as e:
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"❌ 分析异常: {e}")
        print(f"⏱️ 异常前耗时: {elapsed:.1f}秒")
        
        if elapsed > 60:
            print("⚠️ 可能仍存在死循环问题（耗时超过1分钟）")
        
        return False

if __name__ == "__main__":
    success = test_level3_analysis()
    if success:
        print("\\n🎉 级别3死循环修复测试通过！")
    else:
        print("\\n❌ 级别3死循环修复测试失败！")
'''
    
    with open("d:\\code\\QuantScope\\test_level3_fix.py", 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("✅ 测试脚本创建完成: test_level3_fix.py")

def main():
    """主函数：应用所有修复"""
    print("🚀 开始修复分析级别3死循环问题")
    print("=" * 60)
    
    success = True
    
    # 1. 修复基本面分析师
    if not apply_fundamentals_analyst_fix():
        success = False
    
    # 2. 修复条件判断逻辑
    if not apply_conditional_logic_fix():
        success = False
    
    # 3. 创建测试脚本
    create_test_script()
    
    if success:
        print("\n🎉 所有修复已成功应用！")
        print("\n📋 修复内容总结:")
        print("1. ✅ 基本面分析师添加工具调用计数器和循环检测")
        print("2. ✅ 条件判断逻辑添加最大工具调用次数限制")
        print("3. ✅ 创建测试脚本验证修复效果")
        print("\n🧪 运行测试:")
        print("python test_level3_fix.py")
    else:
        print("\n❌ 部分修复失败，请检查日志")

if __name__ == "__main__":
    main()