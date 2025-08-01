import yfinance as yf
import pandas as pd
import requests
import time
import random
from datetime import datetime, timedelta
import streamlit as st

class StockDataService:
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 2
    
    def format_stock_symbol(self, symbol):
        """格式化股票代码"""
        symbol = symbol.upper().strip()
        
        # 港股处理
        if symbol.isdigit() and len(symbol) <= 5:
            # 确保港股代码是4位数
            symbol = symbol.zfill(4) + ".HK"
        elif not symbol.endswith(".HK") and symbol.isdigit():
            symbol = symbol + ".HK"
        
        return symbol
    
    def get_stock_data_yfinance(self, symbol, period="1y"):
        """使用yfinance获取股票数据，带重试机制"""
        for attempt in range(self.max_retries):
            try:
                # 添加随机延迟避免被封IP
                if attempt > 0:
                    time.sleep(random.uniform(1, 3))
                
                ticker = yf.Ticker(symbol)
                
                # 尝试获取历史数据
                data = ticker.history(period=period)
                
                if data.empty:
                    if attempt < self.max_retries - 1:
                        continue
                    return None, f"未找到股票代码 '{symbol}' 的数据"
                
                return data, None
                
            except Exception as e:
                error_msg = str(e)
                
                # 如果是429错误或连接错误，重试
                if "429" in error_msg or "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                    if attempt < self.max_retries - 1:
                        wait_time = (attempt + 1) * self.retry_delay
                        time.sleep(wait_time)
                        continue
                
                return None, f"yfinance错误: {error_msg}"
        
        return None, "多次重试后仍无法获取数据"
    
    def get_stock_data_alpha_vantage(self, symbol, api_key):
        """使用Alpha Vantage API获取股票数据"""
        try:
            # 移除港股后缀，Alpha Vantage不支持
            clean_symbol = symbol.replace('.HK', '').replace('.SS', '').replace('.SZ', '')
            
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': clean_symbol,
                'apikey': api_key,
                'outputsize': 'full'
            }
            
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if 'Error Message' in data:
                return None, f"Alpha Vantage: {data['Error Message']}"
            
            if 'Note' in data:
                return None, "Alpha Vantage: API调用频率限制，请稍后重试"
            
            if 'Time Series (Daily)' not in data:
                return None, "Alpha Vantage: 数据格式错误或股票代码无效"
            
            # 转换为pandas DataFrame
            time_series = data['Time Series (Daily)']
            df_data = []
            
            for date_str, values in time_series.items():
                df_data.append({
                    'Date': pd.to_datetime(date_str),
                    'Open': float(values['1. open']),
                    'High': float(values['2. high']),
                    'Low': float(values['3. low']),
                    'Close': float(values['4. close']),
                    'Volume': int(float(values['5. volume']))
                })
            
            df = pd.DataFrame(df_data)
            df.set_index('Date', inplace=True)
            df = df.sort_index()
            
            # 只返回最近一年的数据
            one_year_ago = datetime.now() - timedelta(days=365)
            df = df[df.index >= one_year_ago]
            
            return df, None
            
        except requests.RequestException as e:
            return None, f"Alpha Vantage网络错误: {str(e)}"
        except Exception as e:
            return None, f"Alpha Vantage处理错误: {str(e)}"
    
    def get_stock_data_with_fallback(self, symbol, period="1y", alpha_api_key=None):
        """多重数据源获取股票数据"""
        formatted_symbol = self.format_stock_symbol(symbol)
        
        # 方法1: 尝试yfinance
        with st.spinner("正在从Yahoo Finance获取数据..."):
            data, error = self.get_stock_data_yfinance(formatted_symbol, period)
            
        if data is not None and not data.empty:
            st.success("✅ 成功从Yahoo Finance获取数据")
            return data, "Yahoo Finance", None
        
        st.warning(f"Yahoo Finance失败: {error}")
        
        # 方法2: 如果有Alpha Vantage API密钥，尝试使用
        if alpha_api_key and alpha_api_key.strip():
            with st.spinner("正在从Alpha Vantage获取数据..."):
                data, error = self.get_stock_data_alpha_vantage(formatted_symbol, alpha_api_key.strip())
                
            if data is not None and not data.empty:
                st.success("✅ 成功从Alpha Vantage获取数据")
                return data, "Alpha Vantage", None
            
            st.error(f"Alpha Vantage也失败了: {error}")
        
        # 所有方法都失败
        error_msg = f"""
        ❌ 无法获取股票数据 '{formatted_symbol}'
        
        **可能原因：**
        1. Yahoo Finance API在2025年出现限制问题
        2. 股票代码格式不正确
        3. 网络连接问题
        
        **解决方案：**
        1. 检查股票代码格式：
           - 港股: 0700 (腾讯)
           - 美股: AAPL (苹果)
           - A股: 000001.SZ (平安银行)
        
        2. 获取免费Alpha Vantage API密钥：
           - 访问: https://www.alphavantage.co/support/#api-key
           - 每天500次免费请求
        
        3. 稍后重试，避开高峰期
        """
        
        return None, "所有数据源", error_msg
    
    def get_stock_info(self, symbol):
        """获取股票基本信息"""
        try:
            formatted_symbol = self.format_stock_symbol(symbol)
            ticker = yf.Ticker(formatted_symbol)
            info = ticker.info
            
            return {
                'name': info.get('longName', info.get('shortName', symbol)),
                'sector': info.get('sector', '未知'),
                'industry': info.get('industry', '未知'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0)
            }
        except:
            return {
                'name': symbol,
                'sector': '未知',
                'industry': '未知', 
                'market_cap': 0,
                'pe_ratio': 0,
                'dividend_yield': 0
            }
    
    def validate_symbol(self, symbol):
        """验证股票代码格式"""
        if not symbol or not symbol.strip():
            return False, "股票代码不能为空"
        
        symbol = symbol.strip().upper()
        
        # 基本格式检查
        if len(symbol) < 1:
            return False, "股票代码太短"
        
        if len(symbol) > 10:
            return False, "股票代码太长"
        
        return True, "格式正确"
