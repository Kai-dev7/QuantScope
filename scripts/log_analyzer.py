#!/usr/bin/env python3
"""
日志分析工具
分析QuantScope的日志文件，提供统计和洞察
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import argparse

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')



class LogAnalyzer:
    """日志分析器"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.entries = []
        self.structured_entries = []
        
    def parse_logs(self):
        """解析日志文件"""
        if not self.log_file.exists():
            logger.error(f"❌ 日志文件不存在: {self.log_file}")
            return
            
        logger.info(f"📖 解析日志文件: {self.log_file}")
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                # 尝试解析结构化日志（JSON）
                if line.startswith('{'):
                    try:
                        entry = json.loads(line)
                        entry['line_number'] = line_num
                        self.structured_entries.append(entry)
                        continue
                    except json.JSONDecodeError:
                        pass
                
                # 解析普通日志
                entry = self._parse_regular_log(line, line_num)
                if entry:
                    self.entries.append(entry)
        
        logger.info(f"✅ 解析完成: {len(self.entries)} 条普通日志, {len(self.structured_entries)} 条结构化日志")
    
    def _parse_regular_log(self, line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """解析普通日志行"""
        # 匹配格式: 2025-01-15 10:30:45,123 | module_name | INFO | message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \| ([^|]+) \| ([^|]+) \| (.+)'
        match = re.match(pattern, line)
        
        if match:
            timestamp_str, logger_name, level, message = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            except ValueError:
                timestamp = None
                
            return {
                'timestamp': timestamp,
                'logger': logger_name.strip(),
                'level': level.strip(),
                'message': message.strip(),
                'line_number': line_num,
                'raw_line': line
            }
        
        return None
    
    def analyze_performance(self) -> Dict[str, Any]:
        """分析性能相关日志"""
        logger.info(f"\n📊 性能分析")
        logger.info(f"=")
        
        analysis = {
            'slow_operations': [],
            'analysis_times': [],
            'token_usage': [],
            'cost_summary': {'total_cost': 0, 'by_provider': defaultdict(float)}
        }
        
        # 分析所有日志条目
        all_entries = self.entries + self.structured_entries
        
        for entry in all_entries:
            message = entry.get('message', '')
            
            # 检测慢操作
            if '耗时' in message or 'duration' in entry:
                duration = self._extract_duration(message, entry)
                if duration and duration > 5.0:  # 超过5秒
                    analysis['slow_operations'].append({
                        'timestamp': entry.get('timestamp'),
                        'duration': duration,
                        'message': message,
                        'logger': entry.get('logger', '')
                    })
            
            # 分析完成时间
            if '分析完成' in message or 'analysis_complete' in entry.get('event_type', ''):
                duration = self._extract_duration(message, entry)
                if duration:
                    analysis['analysis_times'].append(duration)
            
            # Token使用统计
            if 'Token使用' in message or 'token_usage' in entry.get('event_type', ''):
                cost = self._extract_cost(message, entry)
                provider = self._extract_provider(message, entry)
                if cost:
                    analysis['cost_summary']['total_cost'] += cost
                    if provider:
                        analysis['cost_summary']['by_provider'][provider] += cost
        
        # 输出分析结果
        if analysis['slow_operations']:
            logger.info(f"🐌 慢操作 ({len(analysis['slow_operations'])} 个):")
            for op in analysis['slow_operations'][:5]:  # 显示前5个
                logger.info(f"  - {op['duration']:.2f}s: {op['message'][:80]}...")
        
        if analysis['analysis_times']:
            avg_time = sum(analysis['analysis_times']) / len(analysis['analysis_times'])
            logger.info(f"⏱️  平均分析时间: {avg_time:.2f}s")
            logger.info(f"📈 分析次数: {len(analysis['analysis_times'])}")
        
        if analysis['cost_summary']['total_cost'] > 0:
            logger.info(f"💰 总成本: ¥{analysis['cost_summary']['total_cost']:.4f}")
            for provider, cost in analysis['cost_summary']['by_provider'].items():
                logger.info(f"  - {provider}: ¥{cost:.4f}")
        
        return analysis
    
    def analyze_errors(self) -> Dict[str, Any]:
        """分析错误日志"""
        logger.error(f"\n❌ 错误分析")
        logger.info(f"=")
        
        error_entries = []
        warning_entries = []
        
        all_entries = self.entries + self.structured_entries
        
        for entry in all_entries:
            level = entry.get('level', '').upper()
            if level == 'ERROR':
                error_entries.append(entry)
            elif level == 'WARNING':
                warning_entries.append(entry)
        
        logger.error(f"🔴 错误数量: {len(error_entries)}")
        logger.warning(f"🟡 警告数量: {len(warning_entries)}")
        
        # 错误分类
        error_patterns = defaultdict(int)
        for entry in error_entries:
            message = entry.get('message', '')
            # 简单的错误分类
            if 'API' in message or 'api' in message:
                error_patterns['API错误'] += 1
            elif '网络' in message or 'network' in message or 'connection' in message:
                error_patterns['网络错误'] += 1
            elif '数据库' in message or 'database' in message or 'mongodb' in message:
                error_patterns['数据库错误'] += 1
            elif 'PDF' in message or 'pdf' in message:
                error_patterns['PDF导出错误'] += 1
            else:
                error_patterns['其他错误'] += 1
        
        if error_patterns:
            logger.error(f"\n错误分类:")
            for pattern, count in error_patterns.most_common():
                logger.info(f"  - {pattern}: {count}")
        
        # 显示最近的错误
        if error_entries:
            logger.error(f"\n最近的错误:")
            recent_errors = sorted(error_entries, key=lambda x: x.get('timestamp', datetime.min))[-3:]
            for error in recent_errors:
                timestamp = error.get('timestamp', 'Unknown')
                message = error.get('message', '')[:100]
                logger.info(f"  - {timestamp}: {message}...")
        
        return {
            'error_count': len(error_entries),
            'warning_count': len(warning_entries),
            'error_patterns': dict(error_patterns),
            'recent_errors': error_entries[-5:] if error_entries else []
        }
    
    def analyze_usage(self) -> Dict[str, Any]:
        """分析使用情况"""
        logger.info(f"\n📈 使用情况分析")
        logger.info(f"=")
        
        analysis = {
            'daily_usage': defaultdict(int),
            'hourly_usage': defaultdict(int),
            'module_usage': defaultdict(int),
            'analysis_types': defaultdict(int)
        }
        
        all_entries = self.entries + self.structured_entries
        
        for entry in all_entries:
            timestamp = entry.get('timestamp')
            if timestamp:
                # 按日统计
                date_str = timestamp.strftime('%Y-%m-%d')
                analysis['daily_usage'][date_str] += 1
                
                # 按小时统计
                hour = timestamp.hour
                analysis['hourly_usage'][hour] += 1
            
            # 模块使用统计
            logger = entry.get('logger', '')
            if logger:
                analysis['module_usage'][logger] += 1
            
            # 分析类型统计
            message = entry.get('message', '')
            if '开始分析' in message or 'analysis_start' in entry.get('event_type', ''):
                analysis_type = entry.get('analysis_type', '未知')
                analysis['analysis_types'][analysis_type] += 1
        
        # 输出结果
        if analysis['daily_usage']:
            logger.info(f"📅 每日使用量:")
            for date, count in sorted(analysis['daily_usage'].items())[-7:]:  # 最近7天
                logger.info(f"  - {date}: {count}")
        
        if analysis['module_usage']:
            logger.info(f"\n📦 模块使用情况:")
            for module, count in Counter(analysis['module_usage']).most_common(5):
                logger.info(f"  - {module}: {count}")
        
        if analysis['analysis_types']:
            logger.debug(f"\n🔍 分析类型:")
            for analysis_type, count in Counter(analysis['analysis_types']).most_common():
                logger.info(f"  - {analysis_type}: {count}")
        
        return analysis
    
    def _extract_duration(self, message: str, entry: Dict[str, Any]) -> Optional[float]:
        """从消息中提取耗时"""
        # 从结构化日志中提取
        if 'duration' in entry:
            return entry['duration']
        
        # 从消息中提取
        match = re.search(r'耗时[：:]\s*(\d+\.?\d*)s', message)
        if match:
            return float(match.group(1))
        
        return None
    
    def _extract_cost(self, message: str, entry: Dict[str, Any]) -> Optional[float]:
        """从消息中提取成本"""
        # 从结构化日志中提取
        if 'cost' in entry:
            return entry['cost']
        
        # 从消息中提取
        match = re.search(r'成本[：:]\s*¥(\d+\.?\d*)', message)
        if match:
            return float(match.group(1))
        
        return None
    
    def _extract_provider(self, message: str, entry: Dict[str, Any]) -> Optional[str]:
        """从消息中提取提供商"""
        # 从结构化日志中提取
        if 'provider' in entry:
            return entry['provider']
        
        # 从消息中提取
        providers = ['DeepSeek', 'OpenAI', 'Tongyi', 'Gemini']
        for provider in providers:
            if provider in message:
                return provider
        
        return None
    
    def generate_report(self) -> str:
        """生成分析报告"""
        logger.info(f"\n📋 生成分析报告")
        logger.info(f"=")
        
        performance = self.analyze_performance()
        errors = self.analyze_errors()
        usage = self.analyze_usage()
        
        report = f"""
# QuantScope 日志分析报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
日志文件: {self.log_file}

## 概览
- 普通日志条目: {len(self.entries)}
- 结构化日志条目: {len(self.structured_entries)}
- 错误数量: {errors['error_count']}
- 警告数量: {errors['warning_count']}

## 性能分析
- 慢操作数量: {len(performance['slow_operations'])}
- 平均分析时间: {sum(performance['analysis_times']) / len(performance['analysis_times']):.2f}s (如果有数据)
- 总成本: ¥{performance['cost_summary']['total_cost']:.4f}

## 使用情况
- 活跃模块: {len(usage['module_usage'])}
- 分析类型: {len(usage['analysis_types'])}

## 建议
"""
        
        # 添加建议
        if len(performance['slow_operations']) > 10:
            report += "- ⚠️ 检测到较多慢操作，建议优化性能\n"
        
        if errors['error_count'] > 0:
            report += f"- ❌ 发现 {errors['error_count']} 个错误，建议检查日志\n"
        
        if performance['cost_summary']['total_cost'] > 10:
            report += "- 💰 API成本较高，建议优化调用策略\n"
        
        return report


def main():
    parser = argparse.ArgumentParser(description='QuantScope 日志分析工具')
    parser.add_argument('log_file', help='日志文件路径')
    parser.add_argument('--output', '-o', help='输出报告文件路径')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='输出格式')
    
    args = parser.parse_args()
    
    log_file = Path(args.log_file)
    analyzer = LogAnalyzer(log_file)
    
    try:
        analyzer.parse_logs()
        report = analyzer.generate_report()
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"📄 报告已保存到: {args.output}")
        else:
            print(report)
            
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
