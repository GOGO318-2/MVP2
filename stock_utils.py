import yfinance as yf
import requests
from bs4 import BeautifulSoup

def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="7d")
    return hist

def fetch_stock_info(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        'name': info.get('shortName', ticker),
        'sector': info.get('sector', 'N/A'),
        'price': info.get('currentPrice', 0),
        'previousClose': info.get('previousClose', 0)
    }

def fetch_news(ticker):
    url = f"https://finance.yahoo.com/quote/{ticker}?p={ticker}"
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(r.text, 'html.parser')
    headlines = soup.find_all('h3')[:5]
    return [h.get_text(strip=True) for h in headlines]
