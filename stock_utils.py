import yfinance as yf
import pandas as pd
import numpy as np

def fetch_stock_data(symbol):
    try:
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)
        df.dropna(inplace=True)
        return df
    except:
        return pd.DataFrame()

def fetch_recommendation():
    return [
        {
            "symbol": "AAPL",
            "price": yf.Ticker("AAPL").history(period="1d")["Close"].iloc[-1],
            "reason": "近期表现强劲，技术指标良好",
            "buy_price": "175",
            "sell_price": "190"
        },
        {
            "symbol": "TSLA",
            "price": yf.Ticker("TSLA").history(period="1d")["Close"].iloc[-1],
            "reason": "RSI处于低位，有反弹可能",
            "buy_price": "240",
            "sell_price": "270"
        }
    ]

def calculate_indicators(df):
    close = df['Close']
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / (avg_loss + 1e-6)
    rsi = 100 - (100 / (1 + rs))

    low_9 = df['Low'].rolling(9).min()
    high_9 = df['High'].rolling(9).max()
    rsv = (close - low_9) / (high_9 - low_9 + 1e-6) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    j = 3 * k - 2 * d

    return {
        "MACD": macd.iloc[-1],
        "Signal": signal.iloc[-1],
        "RSI": rsi.iloc[-1],
        "K": k.iloc[-1],
        "D": d.iloc[-1],
        "J": j.iloc[-1]
    }

def format_analysis(indicators):
    advice = "持币观望"
    if indicators["MACD"] > indicators["Signal"] and indicators["RSI"] < 70:
        advice = "可考虑买入"
    elif indicators["RSI"] > 80:
        advice = "超买风险，建议卖出或等待回调"

    return {
        "advice": advice,
        "buy_price": "动态判断",
        "sell_price": "动态判断",
        "reason": "结合MACD和RSI判断"
    }
