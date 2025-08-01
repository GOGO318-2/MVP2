import streamlit as st
import pandas as pd
import requests
from typing import List, Tuple

from config import CONFIG
from utils import calculate_rsi, calculate_macd, calculate_support_resistance, logger
from data_service import get_stock_info, get_sentiment

# -------------------- 投资建议函数（分短期、中期、长期） --------------------
def get_investment_advice(ticker: str, hist: pd.DataFrame, info: dict) -> Tuple[str, str, str, List[float]]:
    """分短期、中期、长期给出投资建议和买入价格范围，基于实时数据分析"""
    try:
        # 获取当前价格
        current_price = info.get('currentPrice', 0)
        currency = info.get('currency', 'USD')
        
        # 计算技术指标
        rsi = calculate_rsi(hist['Close'])
        macd, signal = calculate_macd(hist['Close'])
        
        # 计算不同时间段的均线
        ma_short = hist['Close'].rolling(5).mean().iloc[-1] if len(hist) >= 5 else current_price
        ma_medium = hist['Close'].rolling(20).mean().iloc[-1] if len(hist) >= 20 else current_price
        ma_long = hist['Close'].rolling(60).mean().iloc[-1] if len(hist) >= 60 else current_price
        
        # 获取市场情绪
        sentiment = get_sentiment(ticker)
        
        # 计算支撑位和阻力位
        support, resistance = calculate_support_resistance(hist['Close'])
        
        # 获取基本面数据
        pe_ratio = info.get('trailingPE', 0)
        pb_ratio = info.get('priceToBook', 0)
        dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
        
        # 短期建议 (1周内) - 基于技术指标
        short_term = ""
        short_term_price = []
        if rsi < 30:
            short_term = "短期买入机会：RSI超卖，可能存在反弹机会"
            short_term_price = [support * 0.98, support * 1.02]  # 支撑位附近
        elif rsi > 70:
            short_term = "短期谨慎：RSI超买，可能有回调风险"
            short_term_price = [support * 0.95, support]  # 等待回调到支撑位
        else:
            short_term = "短期中性：技术指标未显示明显信号"
            short_term_price = [support, resistance]  # 在支撑位和阻力位之间
            
        # 中期建议 (1-3个月) - 结合技术和基本面
        medium_term = ""
        medium_term_price = []
        if macd > signal and sentiment == "正面":
            medium_term = "中期看涨：MACD金叉形成，市场情绪积极"
            medium_term_price = [ma_medium * 0.98, ma_medium * 1.05]  # 20日均线附近
        elif macd < signal and sentiment == "负面":
            medium_term = "中期谨慎：MACD死叉形成，市场情绪谨慎"
            medium_term_price = [ma_medium * 0.95, ma_medium]  # 20日均线下方
        else:
            medium_term = "中期中性：技术指标和市场情绪未形成明显趋势"
            medium_term_price = [support, resistance]  # 在支撑位和阻力位之间
            
        # 长期建议 (6个月以上) - 基于基本面和长期趋势
        long_term = ""
        long_term_price = []
        if current_price > ma_long and pe_ratio < 25 and pb_ratio < 3:
            long_term = "长期看涨：股价位于长期均线之上，估值合理"
            long_term_price = [ma_long * 0.95, ma_long * 1.10]  # 长期均线附近
        elif current_price < ma_long and pe_ratio > 30 and pb_ratio > 5:
            long_term = "长期谨慎：股价低于长期均线，估值偏高"
            long_term_price = [ma_long * 0.85, ma_long * 0.95]  # 长期均线下方
        else:
            long_term = "长期中性：基本面和技术面未显示明显优势或风险"
            long_term_price = [ma_long * 0.90, ma_long * 1.05]  # 长期均线附近
            
        # 添加详细分析
        short_term += f"\n- RSI: {rsi:.2f}, 支撑位: {support:.2f}, 阻力位: {resistance:.2f}"
        medium_term += f"\n- MACD: {macd:.4f}, Signal: {signal:.4f}, 市场情绪: {sentiment}"
        long_term += f"\n- 市盈率: {pe_ratio:.2f}, 市净率: {pb_ratio:.2f}, 股息率: {dividend_yield:.2f}%"
            
        return short_term, medium_term, long_term, [
            short_term_price, 
            medium_term_price, 
            long_term_price
        ]
    except Exception as e:
        logger.error(f"生成投资建议失败: {e}")
        return (
            "短期建议：数据不足，无法生成建议",
            "中期建议：数据不足，无法生成建议",
            "长期建议：数据不足，无法生成建议",
            [[0, 0], [0, 0], [0, 0]]
        )

# -------------------- 热门股票函数（增强版） --------------------
@st.cache_data(ttl=3600)
def get_trending_stocks() -> pd.DataFrame:
    try:
        # 获取美股大盘指数成分股作为候选池
        url = "https://finnhub.io/api/v1/stock/symbol?exchange=US&token=" + CONFIG['api_keys']['finnhub']
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            all_stocks = response.json()
            # 过滤出活跃的普通股票（排除ETF、基金等）
            constituents = [
                stock['symbol'] for stock in all_stocks 
                if stock['type'] == 'Common Stock' and not stock['symbol'].endswith('.')
            ][:100]  # 取前100只股票
        else:
            # 备用股票池
            constituents = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'JPM', 'JNJ', 'V', 
                           'PG', 'NVDA', 'HD', 'MA', 'DIS', 'ADBE', 'PYPL', 'NFLX', 'CRM', 
                           'INTC', 'CSCO', 'PEP', 'KO', 'T', 'VZ', 'WMT', 'MRK', 'PFE', 
                           'ABT', 'TMO', 'UNH', 'BAC', 'GS', 'MS', 'C', 'BA', 'CAT', 'MMM', 
                           'HON', 'GE', 'IBM', 'ORCL', 'QCOM', 'TXN', 'AMD', 'AVGO', 'AMAT', 
                           'MU', 'LRCX', 'ADI', 'XLNX']
        
        trending_data = []
        progress_bar = st.progress(0)
        total_stocks = len(constituents)
        
        for idx, ticker in enumerate(constituents):
            progress = (idx + 1) / total_stocks
            progress_bar.progress(progress)
            
            try:
                # 获取股票信息
                info, _ = get_stock_info(ticker)
                if not info or 'currentPrice' not in info:
                    continue
                
                # 获取历史数据
                from data_service import get_historical_data
                hist = get_historical_data(ticker, "1y")
                if hist.empty or len(hist) < 20:  # 需要足够的数据
                    continue
                
                # 计算技术指标
                rsi = calculate_rsi(hist['Close'])
                macd, _ = calculate_macd(hist['Close'])
                
                # 获取市场情绪
                sentiment = get_sentiment(ticker)
                
                # 计算推荐得分 (0-100)
                # RSI权重: 30%，MACD权重: 30%，情绪权重: 20%，价格动量权重: 20%
                score = 0
                
                # RSI评分：30以下满分，70以上0分
                if rsi < 30:
                    rsi_score = 100
                elif rsi > 70:
                    rsi_score = 0
                else:
                    rsi_score = 100 - ((rsi - 30) / 40 * 100)
                score += rsi_score * 0.3
                
                # MACD评分：正值加分，负值减分
                macd_score = 50 + (macd * 10)  # 每0.1的MACD值对应1分
                macd_score = max(0, min(100, macd_score))
                score += macd_score * 0.3
                
                # 情绪评分
                sentiment_score = 100 if sentiment == "正面" else 50 if sentiment == "中性" else 0
                score += sentiment_score * 0.2
                
                # 价格动量评分 (最近1个月涨幅)
                monthly_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[-20] - 1) * 100
                momentum_score = min(100, max(0, 50 + monthly_return * 2))  # 每1%涨幅加2分
                score += momentum_score * 0.2
                
                # 确保分数在0-100范围内
                score = max(0, min(100, score))
                
                trending_data.append({
                    '股票代码': ticker,
                    '公司名称': info.get('longName', ticker),
                    '当前价格': info.get('currentPrice', 0),
                    '涨跌幅': monthly_return,  # 使用实际计算的月度
