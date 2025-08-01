import streamlit as st

from utils import process_hk_ticker
from data_service import get_news

def render_news_page(ticker: str):
    processed_ticker = process_hk_ticker(ticker)
    st.title(f"📰 {processed_ticker} 新闻")
    
    # 添加新闻加载状态
    with st.spinner("正在加载最新新闻..."):
        news_list = get_news(ticker)
    
    # 添加新闻刷新按钮
    if st.button("🔄 刷新新闻数据", key="refresh_news"):
        # 清除缓存并重新加载
        get_news.clear()
        st.rerun()
    
    if not news_list:
        st.warning("⚠️ 无法获取相关新闻，请稍后再试")
        return
    
    # 只显示标题、时间和外链
    st.markdown("### 最新10条新闻")
    
    # 创建简单的卡片式布局
    for news in news_list:
        # 创建卡片容器
        with st.container():
            # 标题和时间在同一行
            col1, col2 = st.columns([4, 1])
            col1.subheader(news['title'])
            col2.caption(f"📅 {news['publish_date']}")
            
            # 来源和链接
            st.markdown(f"来源: **{news['source']}**")
            st.markdown(f"[阅读原文 ↗]({news['link']})")
            
            # 分隔线
            st.divider()
