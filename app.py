import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta
import os
import logging

# -------------------- 配置信息 --------------------
CONFIG = {
    'page_title': '股票交易决策助手',
    'api_keys': {
        "finnhub": os.getenv("FINNHUB_API_KEY", "ckq0dahr01qj3j9g4vrgckq0dahr01qj3j9g4vs0")
    },
    'cache_timeout': 300  # 5分钟缓存
}

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- 港股代码处理函数 --------------------
def process_hk_ticker(ticker: str) -> str:
    """处理港股代码，转换为正确的yfinance格式"""
    ticker = ticker.strip().upper()
    
    if ticker.endswith('.HK'):
        ticker = ticker.replace('.HK', '')
    
    if not ticker.isdigit():
        return ticker
    
    ticker = ticker.lstrip('0')
    if not ticker:
        return "0000.HK"
    
    ticker = ticker.zfill(4)
    return f"{ticker}.HK"

# -------------------- 数据获取函数 --------------------
@st.cache_data(ttl=CONFIG['cache_timeout'])
def get_stock_info(ticker: str) -> dict:
    """获取股票基本信息"""
    try:
        processed_ticker = process_hk_ticker(ticker)
        stock = yf.Ticker(processed_ticker)
        info = stock.info
        
        # 获取实时报价
        quote_url = f"https://finnhub.io/api/v1/quote?symbol={processed_ticker}"
        quote_response = requests.get(quote_url, params={"token": CONFIG['api_keys']['finnhub']}, timeout=10)
        if quote_response.status_code == 200:
            quote_data = quote_response.json()
            info['currentPrice'] = quote_data.get('c', 0)
            info['previousClose'] = quote_data.get('pc', 0)
            info['dayHigh'] = quote_data.get('h', 0)
            info['dayLow'] = quote_data.get('l', 0)
            info['volume'] = quote_data.get('v', 0)
        
        return info
    except Exception as e:
        logger.error(f"获取股票信息失败 {ticker}: {e}")
        return {}

@st.cache_data(ttl=CONFIG['cache_timeout'])
def get_historical_data(ticker: str, period: str = "1mo") -> pd.DataFrame:
    """获取历史数据"""
    try:
        processed_ticker = process_hk_ticker(ticker)
        stock = yf.Ticker(processed_ticker)
        hist = stock.history(period=period)
        return hist
    except Exception as e:
        logger.error(f"获取历史数据失败 {ticker}: {e}")
        return pd.DataFrame()

# -------------------- 技术分析函数 --------------------
def calculate_rsi(close: pd.Series, period: int = 14) -> float:
    """计算相对强弱指数(RSI)"""
    if len(close) < period:
        return 50.0
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    if loss.iloc[-1] == 0:
        return 100.0
    rs = gain.iloc[-1] / loss.iloc[-1]
    return 100 - (100 / (1 + rs))

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """计算平均真实波幅(ATR)"""
    if len(close) < period + 1:
        return 0.0
    
    tr = pd.DataFrame({
        'hl': high - low,
        'hc': abs(high - close.shift()),
        'lc': abs(low - close.shift())
    }).max(axis=1)
    
    atr = tr.rolling(period).mean().iloc[-1]
    return atr

def calculate_support_resistance(close: pd.Series) -> Tuple[float, float]:
    """计算支撑位和阻力位"""
    if len(close) < 20:
        current_price = close.iloc[-1] if not close.empty else 0
        return current_price * 0.95, current_price * 1.05
    recent_data = close.tail(20)
    return recent_data.min(), recent_data.max()

# -------------------- 交易决策函数 --------------------
def generate_trading_decision(ticker: str) -> dict:
    """生成交易决策"""
    try:
        # 获取股票信息
        info = get_stock_info(ticker)
        if not info or 'currentPrice' not in info:
            return {"error": "无法获取股票数据"}
        
        # 获取历史数据
        hist = get_historical_data(ticker, "1mo")
        if hist.empty or len(hist) < 15:
            return {"error": "历史数据不足"}
        
        # 计算技术指标
        current_price = info['currentPrice']
        rsi = calculate_rsi(hist['Close'])
        support, resistance = calculate_support_resistance(hist['Close'])
        atr = calculate_atr(hist['High'], hist['Low'], hist['Close'])
        
        # 计算买入价和卖出价
        buy_price = round(support + 0.2 * atr, 2)
        sell_price = round(resistance - 0.2 * atr, 2)
        
        # 决策逻辑
        decision = "买入" if (current_price < buy_price and rsi < 60) else "观望"
        reason = ""
        
        if decision == "买入":
            reason = f"当前价格({current_price})低于买入价({buy_price})，RSI({rsi:.1f})未超买"
        else:
            if current_price >= buy_price:
                reason = f"当前价格({current_price})高于买入价({buy_price})"
            else:
                reason = f"RSI({rsi:.1f})较高，可能存在超买风险"
        
        # 下个交易日日期
        today = datetime.today()
        if today.weekday() == 4:  # 周五
            next_trading_day = today + timedelta(days=3)
        elif today.weekday() == 5:  # 周六
            next_trading_day = today + timedelta(days=2)
        else:
            next_trading_day = today + timedelta(days=1)
        
        return {
            "ticker": ticker,
            "company": info.get('longName', ticker),
            "current_price": current_price,
            "decision": decision,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "reason": reason,
            "next_trading_day": next_trading_day.strftime("%Y-%m-%d"),
            "currency": info.get('currency', 'USD')
        }
    except Exception as e:
        logger.error(f"生成交易决策失败: {e}")
        return {"error": "分析过程中发生错误"}

# -------------------- 主应用 --------------------
def main():
    st.set_page_config(
        page_title=CONFIG['page_title'],
        layout="centered",
        page_icon="📈"
    )
    
    # 页面标题
    st.title("📈 股票交易决策助手")
    st.markdown("""
    <style>
    .decision-buy { color: #2ECC71; font-weight: bold; font-size: 24px; }
    .decision-wait { color: #F39C12; font-weight: bold; font-size: 24px; }
    .price { font-size: 22px; font-weight: bold; }
    .reason { font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)
    
    # 股票代码输入
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input(
            "输入股票代码",
            placeholder="例如: AAPL (美股), 0700.HK (港股)",
            help="美股: TSLA, AAPL | 港股: 0700 (腾讯), 9988 (阿里)"
        ).strip().upper()
    
    with col2:
        st.write("")
        st.write("")
        analyze_btn = st.button("分析", use_container_width=True)
    
    # 热门股票快速访问
    st.markdown("**热门股票:**")
    hot_cols = st.columns(6)
    hot_stocks = ["AAPL", "MSFT", "TSLA", "0700", "9988", "3690"]
    for i, stock in enumerate(hot_stocks):
        if hot_cols[i].button(stock, use_container_width=True):
            ticker = stock
            analyze_btn = True
    
    # 分析按钮逻辑
    if analyze_btn and ticker:
        with st.spinner("分析中，请稍候..."):
            result = generate_trading_decision(ticker)
            
            if "error" in result:
                st.error(f"❌ {result['error']}")
                st.info("请尝试以下解决方案：\n"
                        "1. 港股使用4位数字代码（如'0700'代表腾讯）\n"
                        "2. 美股使用股票代码（如'TSLA'）\n"
                        "3. 确保输入正确股票代码")
            else:
                st.subheader(f"{result['company']} ({result['ticker']})")
                
                # 显示当前价格
                st.markdown(f"**当前价格:** <span class='price'>{result['current_price']:.2f} {result['currency']}</span>", 
                            unsafe_allow_html=True)
                
                # 显示决策结果
                st.markdown("---")
                st.markdown(f"**下个交易日 ({result['next_trading_day']}) 决策:**")
                
                if result['decision'] == "买入":
                    st.markdown(f"<p class='decision-buy'>✅ {result['decision']}</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p class='decision-wait'>⏳ {result['decision']}</p>", unsafe_allow_html=True)
                
                st.markdown(f"<p class='reason'>{result['reason']}</p>", unsafe_allow_html=True)
                
                # 显示买入卖出价格
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**买入价:** <span class='price'>{result['buy_price']:.2f} {result['currency']}</span>", 
                                unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**卖出价:** <span class='price'>{result['sell_price']:.2f} {result['currency']}</span>", 
                                unsafe_allow_html=True)
                
                # 解释说明
                st.markdown("---")
                st.info("""
                **决策说明:**  
                - 买入价基于支撑位和波动率计算  
                - 卖出价基于阻力位和波动率计算  
                - 决策综合考虑价格位置和相对强弱指数(RSI)
                """)
    
    # 使用说明
    st.markdown("---")
    st.info("""
    **使用指南:**  
    1. 输入股票代码（美股代码如AAPL，港股代码如0700）  
    2. 点击"分析"按钮获取交易决策  
    3. 结果将显示下个交易日是否可以买入及精确价格  
    4. 点击热门股票按钮快速分析常见股票
    """)

if __name__ == "__main__":
    main()
