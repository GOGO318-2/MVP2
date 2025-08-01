import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

from utils import process_hk_ticker, calculate_bollinger_bands
from data_service import get_stock_info, get_historical_data

def render_realtime_page(ticker: str):
    processed_ticker = process_hk_ticker(ticker)
    info, _ = get_stock_info(processed_ticker)
    if not info or 'currentPrice' not in info:
        st.error(f"❌ 无法获取股票数据，请尝试以下解决方案：\n"
                 f"1. 港股使用4位数字代码（如'0700'代表腾讯）\n"
                 f"2. 美股使用股票代码（如'TSLA'）\n"
                 f"3. 确保输入正确股票代码")
        return
    
    company_name = info.get('longName', processed_ticker)
    currency = info.get('currency', 'USD')
    
    st.title(f"📊 {company_name} ({processed_ticker})")
    
    # 创建列布局
    col1, col2, col3, col4 = st.columns(4)
    
    # 获取并显示实时数据
    current_price = info.get('currentPrice', 0)
    prev_close = info.get('previousClose', current_price)
    change = current_price - prev_close if prev_close != 0 else 0
    change_percent = (change / prev_close * 100) if prev_close != 0 else 0
    
    with col1:
        st.metric(
            "当前价格", 
            f"{current_price:.2f} {currency}" if current_price != 0 else "N/A",
            delta=f"{change:.2f} ({change_percent:+.2f}%)" if prev_close != 0 else "N/A"
        )
    
    with col2:
        day_high = info.get('dayHigh', 'N/A')
        st.metric("今日最高", f"{day_high:.2f} {currency}" if isinstance(day_high, (int, float)) else day_high)
    
    with col3:
        day_low = info.get('dayLow', 'N/A')
        st.metric("今日最低", f"{day_low:.2f} {currency}" if isinstance(day_low, (int, float)) else day_low)
    
    with col4:
        volume = info.get('volume', 'N/A')
        st.metric("成交量", f"{volume:,}" if isinstance(volume, (int, float)) else volume)
    
    st.markdown("---")
    
    # 时间范围选择与K线图
    st.markdown("### 📈 价格走势")
    
    # 精简的时间范围选择器
    period_options = {"1日": "1d", "5日": "5d", "1月": "1mo", "3月": "3mo", "1年": "1y", "5年": "5y"}
    selected_period = st.selectbox("选择时间范围", list(period_options.keys()), index=2, 
                                  key='period_selector')
    
    hist = get_historical_data(processed_ticker, period_options[selected_period])
    
    if hist.empty:
        st.warning("⚠️ 无法获取历史数据")
        return
    
    # 优化K线图样式
    fig = go.Figure()
    
    # 添加K线
    fig.add_trace(go.Candlestick(
        x=hist.index, 
        open=hist['Open'], 
        high=hist['High'], 
        low=hist['Low'], 
        close=hist['Close'], 
        name='K线',
        increasing_line_color='#2ECC71',  # 上涨绿色
        decreasing_line_color='#E74C3C'   # 下跌红色
    ))
    
    # 添加均线
    if len(hist) >= 5:
        fig.add_trace(go.Scatter(
            x=hist.index, 
            y=hist['Close'].rolling(5).mean(), 
            name='MA5', 
            line=dict(color='#3498DB', width=2)
        ))
    
    if len(hist) >= 20:
        fig.add_trace(go.Scatter(
            x=hist.index, 
            y=hist['Close'].rolling(20).mean(), 
            name='MA20', 
            line=dict(color='#F39C12', width=2)
        ))
    
    # 添加布林带
    if len(hist) >= 20:
        upper, mid, lower = calculate_bollinger_bands(hist['Close'])
        fig.add_trace(go.Scatter(
            x=hist.index, 
            y=upper, 
            name='布林上轨', 
            line=dict(color='#E74C3C', width=1, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=hist.index, 
            y=lower, 
            name='布林下轨', 
            line=dict(color='#2ECC71', width=1, dash='dash'),
            fill='tonexty',  # 填充到下一个轨迹
            fillcolor='rgba(231, 76, 60, 0.1)'  # 半透明填充
        ))
    
    # 更新图表布局
    fig.update_layout(
        title=f"{processed_ticker} 价格走势",
        height=500,
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=60, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1月", step="month", stepmode="backward"),
                    dict(count=3, label="3月", step="month", stepmode="backward"),
                    dict(count=6, label="6月", step="month", stepmode="backward"),
                    dict(count=1, label="1年", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        ),
        yaxis=dict(
            title="价格"
        )
    )
    
    # 添加成交量柱状图
    volume_fig = go.Figure(go.Bar(
        x=hist.index,
        y=hist['Volume'],
        name='成交量',
        marker_color=np.where(hist['Close'] > hist['Open'], '#2ECC71', '#E74C3C')
    ))
    
    volume_fig.update_layout(
        height=200,
        showlegend=False,
        margin=dict(l=20, r=20, t=0, b=20),
        template='plotly_white'
    )
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(volume_fig, use_container_width=True)
    
    # 盘前/盘后交易数据（带刷新功能）放在页面底部
    if currency == 'USD':
        st.markdown("### 📈 盘前/盘后交易")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        # 使用会话状态存储盘前盘后数据
        if 'pre_post_data' not in st.session_state:
            st.session_state.pre_post_data = {
                'pre_price': info.get('preMarketPrice'),
                'post_price': info.get('postMarketPrice'),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # 刷新按钮
        if col3.button("🔄 刷新盘前盘后数据"):
            try:
                # 重新获取股票信息
                new_info, _ = get_stock_info(processed_ticker)
                st.session_state.pre_post_data = {
                    'pre_price': new_info.get('preMarketPrice'),
                    'post_price': new_info.get('postMarketPrice'),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                st.success("数据已刷新！")
            except:
                st.error("刷新失败")
        
        with col1:
            pre_price = st.session_state.pre_post_data['pre_price']
            st.metric("盘前价格", f"{pre_price:.2f} {currency}" if pre_price else "暂无数据")
        
        with col2:
            post_price = st.session_state.pre_post_data['post_price']
            st.metric("盘后价格", f"{post_price:.2f} {currency}" if post_price else "暂无数据")
        
        # 显示刷新时间
        st.caption(f"最后更新时间: {st.session_state.pre_post_data['last_updated']}")
