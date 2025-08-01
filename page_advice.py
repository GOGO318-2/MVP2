import streamlit as st
from datetime import datetime

from utils import process_hk_ticker
from data_service import get_stock_info, get_historical_data
from analysis_service import get_investment_advice

def render_advice_page(ticker: str):
    processed_ticker = process_hk_ticker(ticker)
    hist = get_historical_data(processed_ticker, "1y")  # 获取1年数据用于分析
    info = get_stock_info(processed_ticker)[0]
    if hist.empty or not info:
        st.error("❌ 数据不足，无法生成建议")
        return
    
    # 获取当前价格
    current_price = info.get('currentPrice', 0)
    currency = info.get('currency', 'USD')
    
    # 获取分阶段投资建议和买入价格范围
    short_term, medium_term, long_term, price_ranges = get_investment_advice(processed_ticker, hist, info)
    
    st.title(f"🎯 {processed_ticker} 投资建议")
    st.caption(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 显示当前价格
    st.metric("当前价格", f"{current_price:.2f} {currency}")
    
    # 创建选项卡布局
    tab1, tab2, tab3 = st.tabs(["短期建议 (1周内)", "中期建议 (1-3个月)", "长期建议 (6个月以上)"])
    
    with tab1:
        st.subheader("短期投资建议")
        st.info(short_term)
        st.markdown(f"**建议买入价格范围:** `{price_ranges[0][0]:.2f} - {price_ranges[0][1]:.2f} {currency}`")
        
    with tab2:
        st.subheader("中期投资建议")
        st.info(medium_term)
        st.markdown(f"**建议买入价格范围:** `{price_ranges[1][0]:.2f} - {price_ranges[1][1]:.2f} {currency}`")
        
    with tab3:
        st.subheader("长期投资建议")
        st.info(long_term)
        st.markdown(f"**建议买入价格范围:** `{price_ranges[2][0]:.2f} - {price_ranges[2][1]:.2f} {currency}`")
    
    # 添加风险提示
    st.warning("⚠️ 投资有风险，以上建议仅供参考。实际决策请结合更多因素综合分析。")
