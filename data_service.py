import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
from xml.etree import ElementTree as ET
from urllib.parse import quote

from config import CONFIG
from utils import process_hk_ticker, process_finnhub_ticker, logger

warnings.filterwarnings('ignore')

# -------------------- 数据获取函数 --------------------
@st.cache_data(ttl=CONFIG['cache_timeout'])
def get_stock_info(ticker: str) -> Tuple[Dict, pd.DataFrame]:
    """获取股票基本信息，优化港股支持"""
    try:
        processed_ticker = process_hk_ticker(ticker)
        
        # 尝试使用yfinance获取数据
        try:
            stock = yf.Ticker(processed_ticker)
            info = stock.info
            
            # 检查是否获取到有效数据
            if not info or 'currentPrice' not in info:
                raise ValueError("yfinance返回空数据")
                
            return info, pd.DataFrame()
        except Exception as e:
            logger.warning(f"yfinance获取股票信息失败 {processed_ticker}: {e}")
            
        # yfinance失败时使用Finnhub作为备用（特别是港股）
        url = f"https://finnhub.io/api/v1/stock/profile2?symbol={processed_ticker}"
        response = requests.get(url, params={"token": CONFIG['api_keys']['finnhub']}, timeout=10)
        if response.status_code == 200:
            info = response.json()
            if not info:
                return {}, pd.DataFrame()
            
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
            
            # 获取公司名称
            if 'name' not in info:
                info['longName'] = processed_ticker
                
            return info, pd.DataFrame()
        else:
            return {}, pd.DataFrame()
    except Exception as e:
        logger.error(f"获取股票信息失败 {ticker}: {e}")
        return {}, pd.DataFrame()

@st.cache_data(ttl=CONFIG['cache_timeout'])
def get_historical_data(ticker: str, period: str) -> pd.DataFrame:
    """获取历史数据，优化港股支持"""
    try:
        processed_ticker = process_hk_ticker(ticker)
        
        # 尝试使用yfinance获取数据
        try:
            stock = yf.Ticker(processed_ticker)
            hist = stock.history(period=period)
            if not hist.empty:
                return hist
        except Exception as e:
            logger.warning(f"yfinance获取历史数据失败 {processed_ticker}: {e}")
        
        # yfinance失败时使用Finnhub作为备用
        end_date = datetime.now()
        
        # 根据period调整时间范围
        if period == "1d":
            days = 1
        elif period == "5d":
            days = 5
        elif period == "1mo":
            days = 30
        elif period == "3mo":
            days = 90
        elif period == "1y":
            days = 365
        else:  # 5y
            days = 365 * 5
            
        start_date = end_date - timedelta(days=days)
        
        url = f"https://finnhub.io/api/v1/stock/candle"
        params = {
            'symbol': processed_ticker,
            'resolution': 'D',
            'from': int(start_date.timestamp()),
            'to': int(end_date.timestamp()),
            'token': CONFIG['api_keys']['finnhub']
        }
        
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('s') == 'ok' and 't' in data:
                df = pd.DataFrame({
                    'Date': pd.to_datetime(data['t'], unit='s'),
                    'Open': data['o'],
                    'High': data['h'],
                    'Low': data['l'],
                    'Close': data['c'],
                    'Volume': data['v']
                })
                df.set_index('Date', inplace=True)
                return df
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"获取历史数据失败 {ticker}: {e}")
        return pd.DataFrame()

# -------------------- 新闻获取函数（增强版） --------------------
@st.cache_data(ttl=3600)  # 新闻缓存1小时
def get_news(ticker: str) -> List[Dict]:
    """
    获取股票相关新闻，使用多种备用方案：
    1. 首先尝试Finnhub API
    2. 如果失败，尝试yfinance新闻
    3. 最后尝试Google搜索新闻
    """
    news_list = []
    
    # 方案1：尝试Finnhub API
    try:
        # 处理股票代码用于Finnhub API
        finnhub_ticker = process_finnhub_ticker(ticker)
        logger.info(f"使用Finnhub获取新闻: {finnhub_ticker}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # 转换为时间戳（秒）
        from_timestamp = int(start_date.timestamp())
        to_timestamp = int(end_date.timestamp())
        
        params = {
            'symbol': finnhub_ticker,
            'from': from_timestamp,
            'to': to_timestamp,
            'token': CONFIG['news_api']['key']
        }
        
        response = requests.get(CONFIG['news_api']['url'], params=params, timeout=15)
        logger.info(f"Finnhub新闻API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            news_items = response.json()
            # 过滤掉无效新闻
            news_items = [item for item in news_items if item.get('headline') and item.get('url')]
            
            # 只保留最新的10条新闻
            news_items = sorted(news_items, key=lambda x: x.get('datetime', 0), reverse=True)[:10]
            
            for item in news_items:
                title = item.get('headline', '')
                
                try:
                    publish_date = datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d %H:%M')
                except:
                    publish_date = "未知时间"
                
                news_list.append({
                    'title': title,
                    'link': item.get('url', ''),
                    'publish_date': publish_date,
                    'source': item.get('source', 'Unknown')
                })
            
            # 如果Finnhub返回了新闻，直接返回
            if news_list:
                logger.info(f"从Finnhub获取到 {len(news_list)} 条新闻")
                return news_list
    except Exception as e:
        logger.error(f"Finnhub获取新闻失败 {ticker}: {e}")
    
    # 方案2：尝试yfinance新闻
    try:
        logger.info(f"尝试使用yfinance获取新闻: {ticker}")
        processed_ticker = process_hk_ticker(ticker)
        stock = yf.Ticker(processed_ticker)
        yf_news = stock.news
        
        if yf_news:
            # 只保留最新的10条新闻
            yf_news = sorted(yf_news, key=lambda x: x.get('providerPublishTime', 0), reverse=True)[:10]
            
            for item in yf_news:
                title = item.get('title', '')
                
                # 发布时间
                pub_time = item.get('providerPublishTime')
                if pub_time:
                    publish_date = datetime.fromtimestamp(pub_time).strftime('%Y-%m-%d %H:%M')
                else:
                    publish_date = "未知时间"
                
                news_list.append({
                    'title': title,
                    'link': item.get('link', ''),
                    'publish_date': publish_date,
                    'source': item.get('publisher', '未知来源')
                })
            
            if news_list:
                logger.info(f"从yfinance获取到 {len(news_list)} 条新闻")
                return news_list
    except Exception as e:
        logger.error(f"yfinance获取新闻失败 {ticker}: {e}")
    
    # 方案3：Google搜索作为最后备用
    try:
        logger.info(f"尝试使用Google搜索获取新闻: {ticker}")
        # 获取公司名称用于搜索
        info, _ = get_stock_info(ticker)
        company_name = info.get('longName', ticker)
        
        # 创建搜索查询
        query = f"{company_name} 股票 新闻"
        search_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        
        response = requests.get(search_url, timeout=15)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            # 只保留最新的10条新闻
            items = items[:10]
            
            for item in items:
                title = item.find('title').text if item.find('title') is not None else "无标题"
                link = item.find('link').text if item.find('link') is not None else "#"
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else "未知时间"
                source = item.find('source').text if item.find('source') is not None else "未知来源"
                
                news_list.append({
                    'title': title,
                    'link': link,
                    'publish_date': pub_date,
                    'source': source
                })
            
            if news_list:
                logger.info(f"从Google搜索获取到 {len(news_list)} 条新闻")
                return news_list
    except Exception as e:
        logger.error(f"Google搜索获取新闻失败 {ticker}: {e}")
    
    # 所有方案都失败时返回空列表
    return []

# -------------------- AI分析函数 --------------------
@st.cache_data(ttl=600)
def get_sentiment(ticker: str) -> str:
    try:
        # 使用Finnhub新闻情绪API
        url = f"https://finnhub.io/api/v1/news-sentiment?symbol={ticker}&token={CONFIG['api_keys']['finnhub']}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            score = data.get('sentiment', {}).get('bullishPercent', 0.5)
            return "正面" if score > 0.6 else "负面" if score < 0.4 else "中性"
        return "中性"
    except:
        return "中性"
