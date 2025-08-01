import pandas as pd
import logging

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- 港股代码处理函数 --------------------
def process_hk_ticker(ticker: str) -> str:
    """处理港股代码，转换为正确的yfinance格式（如 00700 → 0700.HK）"""
    ticker = ticker.strip().upper()
    
    # 移除.HK后缀（如果有）
    if ticker.endswith('.HK'):
        ticker = ticker.replace('.HK', '')
    
    # 确保是数字代码
    if not ticker.isdigit():
        return ticker
    
    # 转换格式：保留4位有效数字，不足4位前面补0
    # 港股代码在yfinance中要求4位数字（如0700.HK）
    ticker = ticker.lstrip('0')
    if not ticker:  # 全为0的情况
        return "0000.HK"
    
    # 确保4位长度
    ticker = ticker.zfill(4)
    
    return f"{ticker}.HK"

def process_finnhub_ticker(ticker: str) -> str:
    """处理港股代码用于Finnhub API（如 00700 → 0700-HK）"""
    ticker = ticker.strip().upper()
    
    if ticker.endswith('.HK'):
        ticker = ticker.replace('.HK', '')
    
    if not ticker.isdigit():
        return ticker
    
    ticker = ticker.lstrip('0')
    if not ticker:
        return "0000.HK"
    
    ticker = ticker.zfill(4)
    return f"{ticker}-HK"

# -------------------- 技术分析函数 --------------------
def calculate_rsi(close: pd.Series, period: int = 14) -> float:
    if len(close) < period:
        return 50.0
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    if loss.iloc[-1] == 0:
        return 100.0
    rs = gain.iloc[-1] / loss.iloc[-1]
    rsi = 100 - (100 / (1 + rs))
    return rsi if not pd.isna(rsi) else 50.0

def calculate_macd(close: pd.Series, short: int = 12, long: int = 26, signal: int = 9) -> tuple[float, float]:
    if len(close) < long:
        return 0.0, 0.0
    ema_short = close.ewm(span=short, adjust=False).mean()
    ema_long = close.ewm(span=long, adjust=False).mean()
    macd_line = ema_short - ema_long
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line.iloc[-1], signal_line.iloc[-1]

def calculate_bollinger_bands(close: pd.Series, window: int = 20, std_dev: int = 2) -> tuple[pd.Series, pd.Series, pd.Series]:
    if len(close) < window:
        return pd.Series(), pd.Series(), pd.Series()
    rolling_mean = close.rolling(window=window).mean()
    rolling_std = close.rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * std_dev)
    lower_band = rolling_mean - (rolling_std * std_dev)
    return upper_band, rolling_mean, lower_band

def calculate_support_resistance(close: pd.Series) -> tuple[float, float]:
    if len(close) < 20:
        current_price = close.iloc[-1] if not close.empty else 0
        return current_price * 0.95, current_price * 1.05
    recent_data = close.tail(20)
    return recent_data.min(), recent_data.max()
