#!/usr/bin/env python3
"""
自定义股票分析演示
展示如何使用QuantScope进行个性化投资分析
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

from dotenv import load_dotenv
from tradingagents.llm_adapters import ChatDashScope
from langchain_core.messages import HumanMessage, SystemMessage

# 加载 .env 文件
load_dotenv()

def analyze_stock_custom(symbol, analysis_focus="comprehensive"):
    """
    自定义股票分析函数
    
    Args:
        symbol: 股票代码 (如 "AAPL", "TSLA", "MSFT")
        analysis_focus: 分析重点
            - "comprehensive": 全面分析
            - "technical": 技术面分析
            - "fundamental": 基本面分析
            - "risk": 风险评估
            - "comparison": 行业比较
    """
    
    logger.info(f"\n🚀 开始分析股票: {symbol}")
    logger.info(f"📊 分析重点: {analysis_focus}")
    logger.info(f"=")
    
    # 检查API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error(f"❌ 错误: 请设置 DASHSCOPE_API_KEY 环境变量")
        return
    
    logger.info(f"✅ 阿里百炼 API 密钥: {api_key[:12]}...")
    
    try:
        # 初始化阿里百炼模型
        logger.info(f"\n🤖 正在初始化阿里百炼模型...")
        llm = ChatDashScope(
            model="qwen-plus-latest",  # 使用平衡性能的模型
            temperature=0.1,    # 降低随机性，提高分析的一致性
            max_tokens=4000     # 允许更长的分析报告
        )
        logger.info(f"✅ 模型初始化成功!")
        
        # 根据分析重点定制提示词
        analysis_prompts = {
            "comprehensive": f"""
请对股票 {symbol} 进行全面的投资分析，包括：
1. 技术面分析（价格趋势、技术指标、支撑阻力位）
2. 基本面分析（财务状况、业务表现、竞争优势）
3. 市场情绪分析（投资者情绪、分析师观点）
4. 风险评估（各类风险因素）
5. 投资建议（评级、目标价、时间框架）

请用中文撰写详细的分析报告，格式清晰，逻辑严谨。
""",
            "technical": f"""
请专注于股票 {symbol} 的技术面分析，详细分析：
1. 价格走势和趋势判断
2. 主要技术指标（MA、MACD、RSI、KDJ等）
3. 支撑位和阻力位
4. 成交量分析
5. 图表形态识别
6. 短期交易建议

请提供具体的买卖点位建议。
""",
            "fundamental": f"""
请专注于股票 {symbol} 的基本面分析，详细分析：
1. 公司财务状况（营收、利润、现金流）
2. 业务模式和竞争优势
3. 行业地位和市场份额
4. 管理层质量
5. 未来增长前景
6. 估值水平分析

请评估公司的内在价值和长期投资价值。
""",
            "risk": f"""
请专注于股票 {symbol} 的风险评估，详细分析：
1. 宏观经济风险
2. 行业周期性风险
3. 公司特定风险
4. 监管政策风险
5. 市场流动性风险
6. 技术和竞争风险

请提供风险控制建议和应对策略。
""",
            "comparison": f"""
请将股票 {symbol} 与同行业主要竞争对手进行比较分析：
1. 财务指标对比
2. 业务模式比较
3. 市场地位对比
4. 估值水平比较
5. 增长前景对比
6. 投资价值排序

请说明该股票相对于竞争对手的优劣势。
"""
        }
        
        # 构建消息
        system_message = SystemMessage(content="""
你是一位专业的股票分析师，具有丰富的金融市场经验。请基于你的专业知识，
为用户提供客观、详细、实用的股票分析报告。分析应该：

1. 基于事实和数据
2. 逻辑清晰，结构完整
3. 包含具体的数字和指标
4. 提供可操作的建议
5. 明确风险提示

请用专业但易懂的中文进行分析。
""")
        
        human_message = HumanMessage(content=analysis_prompts[analysis_focus])
        
        # 生成分析
        logger.info(f"\n⏳ 正在生成{analysis_focus}分析，请稍候...")
        response = llm.invoke([system_message, human_message])
        
        logger.info(f"\n🎯 {symbol} 分析报告:")
        logger.info(f"=")
        print(response.content)
        logger.info(f"=")
        
        return response.content
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {str(e)}")
        return None

def interactive_analysis():
    """交互式分析界面"""
    
    logger.info(f"🚀 QuantScope 自定义股票分析工具")
    logger.info(f"=")
    
    while True:
        logger.info(f"\n📊 请选择分析选项:")
        logger.info(f"1. 全面分析 (comprehensive)")
        logger.info(f"2. 技术面分析 (technical)")
        logger.info(f"3. 基本面分析 (fundamental)")
        logger.info(f"4. 风险评估 (risk)")
        logger.info(f"5. 行业比较 (comparison)")
        logger.info(f"6. 退出")
        
        choice = input("\n请输入选项 (1-6): ").strip()
        
        if choice == "6":
            logger.info(f"👋 感谢使用，再见！")
            break
            
        if choice not in ["1", "2", "3", "4", "5"]:
            logger.error(f"❌ 无效选项，请重新选择")
            continue
            
        # 获取股票代码
        symbol = input("\n请输入股票代码 (如 AAPL, TSLA, MSFT): ").strip().upper()
        if not symbol:
            logger.error(f"❌ 股票代码不能为空")
            continue
            
        # 映射选项到分析类型
        analysis_types = {
            "1": "comprehensive",
            "2": "technical", 
            "3": "fundamental",
            "4": "risk",
            "5": "comparison"
        }
        
        analysis_type = analysis_types[choice]
        
        # 执行分析
        result = analyze_stock_custom(symbol, analysis_type)
        
        if result:
            # 询问是否保存报告
            save_choice = input("\n💾 是否保存分析报告到文件? (y/n): ").strip().lower()
            if save_choice == 'y':
                filename = f"{symbol}_{analysis_type}_analysis.txt"
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"股票代码: {symbol}\n")
                        f.write(f"分析类型: {analysis_type}\n")
                        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("=" * 60 + "\n")
                        f.write(result)
                    logger.info(f"✅ 报告已保存到: {filename}")
                except Exception as e:
                    logger.error(f"❌ 保存失败: {e}")
        
        # 询问是否继续
        continue_choice = input("\n🔄 是否继续分析其他股票? (y/n): ").strip().lower()
        if continue_choice != 'y':
            logger.info(f"👋 感谢使用，再见！")
            break

def batch_analysis_demo():
    """批量分析演示"""
    
    logger.info(f"\n🔄 批量分析演示")
    logger.info(f"=")
    
    # 预定义的股票列表
    stocks = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
    
    logger.info(f"📊 将分析以下股票: {', '.join(stocks)}")
    
    for i, stock in enumerate(stocks, 1):
        logger.info(f"\n[{i}/{len(stocks)}] 正在分析 {stock}...")
        
        # 进行简化的技术面分析
        result = analyze_stock_custom(stock, "technical")
        
        if result:
            # 保存到文件
            filename = f"batch_analysis_{stock}.txt"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(result)
                logger.info(f"✅ {stock} 分析完成，已保存到 {filename}")
            except Exception as e:
                logger.error(f"❌ 保存 {stock} 分析失败: {e}")
        
        # 添加延迟避免API限制
        import time
        time.sleep(2)
    
    logger.info(f"\n🎉 批量分析完成！共分析了 {len(stocks)} 只股票")

def main():
    """主函数"""
    
    logger.info(f"🚀 QuantScope 自定义分析演示")
    logger.info(f"=")
    logger.info(f"选择运行模式:")
    logger.info(f"1. 交互式分析")
    logger.info(f"2. 批量分析演示")
    logger.info(f"3. 单股票快速分析")
    
    mode = input("\n请选择模式 (1-3): ").strip()
    
    if mode == "1":
        interactive_analysis()
    elif mode == "2":
        batch_analysis_demo()
    elif mode == "3":
        symbol = input("请输入股票代码: ").strip().upper()
        if symbol:
            analyze_stock_custom(symbol, "comprehensive")
    else:
        logger.error(f"❌ 无效选项")

if __name__ == "__main__":
    import datetime

    main()
