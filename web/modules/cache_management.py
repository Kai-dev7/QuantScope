#!/usr/bin/env python3
"""
缓存管理页面
用户可以查看、管理和清理股票数据缓存
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 导入UI工具函数
sys.path.append(str(Path(__file__).parent.parent))
from utils.ui_utils import apply_hide_deploy_button_css

try:
    from tradingagents.dataflows.cache import get_cache
    CACHE_AVAILABLE = True
except ImportError as e:
    CACHE_AVAILABLE = False
    st.error(f"缓存管理器不可用: {e}")

try:
    from tradingagents.dataflows.optimized_china_data import get_optimized_china_data_provider
    OPTIMIZED_CHINA_AVAILABLE = True
except ImportError:
    OPTIMIZED_CHINA_AVAILABLE = False

# 注意：optimized_us_data 模块不存在，使用 providers.us.optimized 替代
try:
    from tradingagents.dataflows.providers.us.optimized import OptimizedUSDataProvider
    OPTIMIZED_US_AVAILABLE = True
except ImportError:
    OPTIMIZED_US_AVAILABLE = False

OPTIMIZED_PROVIDERS_AVAILABLE = OPTIMIZED_CHINA_AVAILABLE or OPTIMIZED_US_AVAILABLE

def main():
    st.set_page_config(
        page_title="缓存管理 - QuantScope",
        page_icon="💾",
        layout="wide"
    )
    
    # 应用隐藏Deploy按钮的CSS样式
    apply_hide_deploy_button_css()
    
    st.title("💾 股票数据缓存管理")
    st.markdown("---")
    
    if not CACHE_AVAILABLE:
        st.error("❌ 缓存管理器不可用，请检查系统配置")
        return
    
    # 获取缓存实例
    cache = get_cache()
    
    # 侧边栏操作
    with st.sidebar:
        st.header("🛠️ 缓存操作")
        
        # 刷新按钮
        if st.button("🔄 刷新统计", type="primary"):
            st.rerun()
        
        st.markdown("---")
        
        # 清理操作
        st.subheader("🧹 清理缓存")
        
        max_age_days = st.slider(
            "清理多少天前的缓存",
            min_value=1,
            max_value=30,
            value=7,
            help="删除指定天数之前的缓存文件"
        )
        
        if st.button("🗑️ 清理过期缓存", type="secondary"):
            with st.spinner("正在清理过期缓存..."):
                cache.clear_old_cache(max_age_days)
            st.success(f"✅ 已清理 {max_age_days} 天前的缓存")
            st.rerun()
    
    # 主要内容区域
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 缓存统计")
        
        # 获取缓存统计
        try:
            stats = cache.get_cache_stats()
            
            # 显示统计信息
            metric_col1, metric_col2 = st.columns(2)
            
            with metric_col1:
                st.metric(
                    label="总文件数",
                    value=stats['total_files'],
                    help="缓存中的总文件数量"
                )
                
                st.metric(
                    label="股票数据",
                    value=f"{stats['stock_data_count']}个",
                    help="缓存的股票数据文件数量"
                )
            
            with metric_col2:
                st.metric(
                    label="总大小",
                    value=f"{stats['total_size_mb']} MB",
                    help="缓存文件占用的磁盘空间"
                )
                
                st.metric(
                    label="新闻数据",
                    value=f"{stats['news_count']}个",
                    help="缓存的新闻数据文件数量"
                )
            
            # 基本面数据
            st.metric(
                label="基本面数据",
                value=f"{stats['fundamentals_count']}个",
                help="缓存的基本面数据文件数量"
            )
            
        except Exception as e:
            st.error(f"获取缓存统计失败: {e}")

    with col2:
        st.subheader("⚙️ 缓存配置")

        # 显示缓存配置信息
        if hasattr(cache, 'cache_config'):
            config_tabs = st.tabs(["美股配置", "A股配置"])

            with config_tabs[0]:
                st.markdown("**美股数据缓存配置**")
                us_configs = {k: v for k, v in cache.cache_config.items() if k.startswith('us_')}
                for config_name, config_data in us_configs.items():
                    st.info(f"""
                    **{config_data.get('description', config_name)}**
                    - TTL: {config_data.get('ttl_hours', 'N/A')} 小时
                    - 最大文件数: {config_data.get('max_files', 'N/A')}
                    """)

            with config_tabs[1]:
                st.markdown("**A股数据缓存配置**")
                china_configs = {k: v for k, v in cache.cache_config.items() if k.startswith('china_')}
                for config_name, config_data in china_configs.items():
                    st.info(f"""
                    **{config_data.get('description', config_name)}**
                    - TTL: {config_data.get('ttl_hours', 'N/A')} 小时
                    - 最大文件数: {config_data.get('max_files', 'N/A')}
                    """)
        else:
            st.warning("缓存配置信息不可用")

    # 缓存测试功能
    st.markdown("---")
    st.subheader("🧪 缓存测试")

    if OPTIMIZED_PROVIDERS_AVAILABLE:
        test_col1, test_col2 = st.columns(2)

        with test_col1:
            st.markdown("**测试美股数据缓存**")
            us_symbol = st.text_input("美股代码", value="AAPL", key="us_test")
            if st.button("测试美股缓存", key="test_us"):
                if us_symbol:
                    with st.spinner(f"测试 {us_symbol} 缓存..."):
                        try:
                            from datetime import datetime, timedelta
                            provider = get_optimized_us_data_provider()
                            result = provider.get_stock_data(
                                symbol=us_symbol,
                                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                                end_date=datetime.now().strftime('%Y-%m-%d')
                            )
                            st.success("✅ 美股缓存测试成功")
                            with st.expander("查看结果"):
                                st.text(result[:500] + "..." if len(result) > 500 else result)
                        except Exception as e:
                            st.error(f"❌ 美股缓存测试失败: {e}")

        with test_col2:
            st.markdown("**测试A股数据缓存**")
            china_symbol = st.text_input("A股代码", value="000001", key="china_test")
            if st.button("测试A股缓存", key="test_china"):
                if china_symbol:
                    with st.spinner(f"测试 {china_symbol} 缓存..."):
                        try:
                            from datetime import datetime, timedelta
                            provider = get_optimized_china_data_provider()
                            result = provider.get_stock_data(
                                symbol=china_symbol,
                                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                                end_date=datetime.now().strftime('%Y-%m-%d')
                            )
                            st.success("✅ A股缓存测试成功")
                            with st.expander("查看结果"):
                                st.text(result[:500] + "..." if len(result) > 500 else result)
                        except Exception as e:
                            st.error(f"❌ A股缓存测试失败: {e}")
    else:
        st.warning("优化数据提供器不可用，无法进行缓存测试")

    # 原有的缓存详情部分
    with col2:
        st.subheader("⚙️ 缓存配置")
        
        # 缓存设置
        st.info("""
        **缓存机制说明：**
        
        🔹 **股票数据缓存**：6小时有效期
        - 减少API调用次数
        - 提高数据获取速度
        - 支持离线分析
        
        🔹 **新闻数据缓存**：24小时有效期
        - 避免重复获取相同新闻
        - 节省API配额
        
        🔹 **基本面数据缓存**：24小时有效期
        - 减少基本面分析API调用
        - 提高分析响应速度
        """)
        
        # 缓存目录信息
        cache_dir = cache.cache_dir
        st.markdown(f"**缓存目录：** `{cache_dir}`")
        
        # 子目录信息
        st.markdown("**子目录结构：**")
        st.code(f"""
📁 {cache_dir.name}/
├── 📁 stock_data/     # 股票数据缓存
├── 📁 news_data/      # 新闻数据缓存
├── 📁 fundamentals/   # 基本面数据缓存
└── 📁 metadata/       # 元数据文件
        """)
    
    st.markdown("---")
    
    # 缓存详情
    st.subheader("📋 缓存详情")
    
    # 选择查看的数据类型
    data_type = st.selectbox(
        "选择数据类型",
        ["stock_data", "news", "fundamentals"],
        format_func=lambda x: {
            "stock_data": "📈 股票数据",
            "news": "📰 新闻数据", 
            "fundamentals": "💼 基本面数据"
        }[x]
    )
    
    # 显示缓存文件列表
    try:
        metadata_files = list(cache.metadata_dir.glob("*_meta.json"))
        
        if metadata_files:
            import json
            from datetime import datetime
            
            cache_items = []
            for metadata_file in metadata_files:
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    if metadata.get('data_type') == data_type:
                        cached_at = datetime.fromisoformat(metadata['cached_at'])
                        cache_items.append({
                            'symbol': metadata.get('symbol', 'N/A'),
                            'data_source': metadata.get('data_source', 'N/A'),
                            'cached_at': cached_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'start_date': metadata.get('start_date', 'N/A'),
                            'end_date': metadata.get('end_date', 'N/A'),
                            'file_path': metadata.get('file_path', 'N/A')
                        })
                except Exception:
                    continue
            
            if cache_items:
                # 按缓存时间排序
                cache_items.sort(key=lambda x: x['cached_at'], reverse=True)
                
                # 显示表格
                import pandas as pd
                df = pd.DataFrame(cache_items)
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "symbol": st.column_config.TextColumn("股票代码", width="small"),
                        "data_source": st.column_config.TextColumn("数据源", width="small"),
                        "cached_at": st.column_config.TextColumn("缓存时间", width="medium"),
                        "start_date": st.column_config.TextColumn("开始日期", width="small"),
                        "end_date": st.column_config.TextColumn("结束日期", width="small"),
                        "file_path": st.column_config.TextColumn("文件路径", width="large")
                    }
                )
                
                st.info(f"📊 找到 {len(cache_items)} 个 {data_type} 类型的缓存文件")
            else:
                st.info(f"📭 暂无 {data_type} 类型的缓存文件")
        else:
            st.info("📭 暂无缓存文件")
            
    except Exception as e:
        st.error(f"读取缓存详情失败: {e}")
    
    # 页脚信息
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
        💾 缓存管理系统 | QuantScope v0.1.2 | 
        <a href='https://github.com/your-repo/QuantScope' target='_blank'>GitHub</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
