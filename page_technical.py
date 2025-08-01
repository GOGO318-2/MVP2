import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils import process_hk_ticker, calculate_rsi, calculate_macd, calculate_support_resistance
from data_service import get_stock_info, get_historical_data

def render_technical_page(ticker: str):
    processed_ticker = process_hk_ticker(ticker)
    hist = get_historical_data(processed_ticker, "1y")
    info = get_stock_info(processed_ticker)[0]
    if hist.empty or not info:
        st.error("❌ 数据获取失败")
        return
    
    st.title(f"📈 {processed_ticker} 技术分析")
    rsi = calculate_rsi(hist['Close'])
    macd, signal = calculate_macd(hist['Close'])
    support, resistance = calculate_support_resistance(hist['Close'])
    
    col1, col2 = st.columns(2)
    col1.metric("RSI(14)", f"{rsi:.2f}", "超卖" if rsi < 30 else "超买" if rsi > 70 else "正常")
    col2.metric("MACD", f"{macd:.4f} / {signal:.4f}", "看涨" if macd > signal else "看跌")
    
    tech_data = {
        "指标": ["支撑位", "阻力位", "RSI状态", "MACD状态"],
        "数值/描述": [
            f"{support:.2f}", f"{resistance:.2f}",
            "超卖" if rsi < 30 else "超买" if rsi > 70 else "正常",
            "看涨" if macd > signal else "看跌"
        ]
    }
    st.dataframe(pd.DataFrame(tech_data), hide_index=True)
    
    if len(hist) >= 14:
        # 计算RSI曲线
        rsi_values = []
        for i in range(14, len(hist)):
            rsi_values.append(calculate_rsi(hist['Close'].iloc[:i]))
        
        rsi_df = pd.DataFrame({
            'Date': hist.index[14:],
            'RSI': rsi_values
        }).set_index('Date')
        
        fig = go.Figure(go.Scatter(
            x=rsi_df.index, 
            y=rsi_df['RSI'], 
            name='RSI',
            line=dict(color='#3498DB', width=2)
        ))
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超买线")
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超卖线")
        fig.update_layout(
            title="RSI趋势", 
            height=300,
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)
