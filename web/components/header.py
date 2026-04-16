"""
页面头部组件
"""

import streamlit as st

def render_header():
    """渲染页面头部"""
    
    # 主标题
    st.markdown("""
    <div class="main-header">
        <h1>🚀 QuantScope 股票分析平台</h1>
        <p>基于多智能体大语言模型的中文金融交易决策框架</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 功能特性展示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>🤖 智能体协作</h4>
            <p>专业分析师团队协同工作</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>🇨🇳 中文优化</h4>
            <p>针对中文用户优化的模型</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>📊 实时数据</h4>
            <p>获取最新的股票市场数据</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h4>🎯 专业建议</h4>
            <p>基于AI的投资决策建议</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 分隔线
    st.markdown("---")
