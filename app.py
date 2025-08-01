import streamlit as st

from config import CONFIG, HOT_STOCKS, DEFAULT_TICKER
from page_realtime import render_realtime_page
from page_technical import render_technical_page
from page_advice import render_advice_page
from page_trending import render_trending_page
from page_news import render_news_page

# -------------------- 回调函数 --------------------
def update_current_ticker():
    """更新当前选中的股票代码"""
    if st.session_state.search_input and st.session_state.search_input != st.session_state.current_ticker:
        st.session_state.current_ticker = st.session_state.search_input

# -------------------- 主应用 --------------------
def main():
    st.set_page_config(page_title=CONFIG['page_title'], layout='wide')
    st.sidebar.title("🚀 智能股票分析")
    st.sidebar.markdown("---")
    
    # 使用会话状态跟踪当前选中的股票
    if 'current_ticker' not in st.session_state:
        st.session_state.current_ticker = DEFAULT_TICKER  # 默认股票
    
    # 股票代码输入
    st.sidebar.markdown("### 🔍 股票查询")
    
    # 使用on_change回调处理回车提交
    st.sidebar.text_input(
        "输入股票代码", 
        value=st.session_state.current_ticker,
        help="美股: TSLA | 港股: 0700（4位数字）",
        key="search_input",
        on_change=update_current_ticker
    )
    
    # 热门股票快速访问
    st.sidebar.markdown("**🚀 热门股票**")
    hot_cols = st.sidebar.columns(3)
    for i, stock in enumerate(HOT_STOCKS):
        if hot_cols[i % 3].button(stock, use_container_width=True):
            st.session_state.current_ticker = stock
            st.rerun()
    
    st.sidebar.markdown("---")
    page = st.sidebar.radio("📋 功能菜单", [
        "📊 实时数据", "📈 技术分析", 
        "🎯 投资建议", "🌟 热门股票", "📰 新闻"
    ])
    
    # 使用会话状态中的当前股票进行查询
    active_ticker = st.session_state.current_ticker
    
    if page == "📊 实时数据":
        render_realtime_page(active_ticker)
    elif page == "📈 技术分析":
        render_technical_page(active_ticker)
    elif page == "🎯 投资建议":
        render_advice_page(active_ticker)
    elif page == "🌟 热门股票":
        render_trending_page()
    elif page == "📰 新闻":
        render_news_page(active_ticker)

if __name__ == "__main__":
    main()
