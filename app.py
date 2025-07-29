from flask import Flask, render_template, request
import requests
import datetime
import random

app = Flask(__name__)

# 多API Key支持
finnhub_keys = [
    "d1p1qv9r01qi9vk2517gd1p1qv9r01qi9vk25180",
    # 可添加更多Key
]
polygon_keys = [
    "2CDgF277xEhkhKndj5yFMVONxBGFFShg",
    # 可添加更多Key
]
fmp_keys = [
    "8n2nsHP2Lj1uHkPRrtcQ8a63Lf95VjbU",
    # 可添加更多Key
]

def get_api_key(api_list):
    return random.choice(api_list)

def get_price_data(symbol):
    key = get_api_key(finnhub_keys)
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={key}"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        return {
            "current": data.get("c"),
            "open": data.get("o"),
            "high": data.get("h"),
            "low": data.get("l"),
            "prevClose": data.get("pc"),
            "timestamp": data.get("t"),
        }
    return {}

def get_kline_data(symbol):
    key = get_api_key(finnhub_keys)
    end = int(datetime.datetime.now().timestamp())
    start = end - 60 * 60 * 24 * 30  # 近30天
    url = f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=D&from={start}&to={end}&token={key}"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        if data.get("s") == "ok":
            return {
                "t": data["t"],
                "c": data["c"],
                "h": data["h"],
                "l": data["l"],
                "o": data["o"],
                "v": data["v"],
            }
    return {}

def get_macd(symbol):
    key = get_api_key(fmp_keys)
    url = f"https://financialmodelingprep.com/api/v3/technical_indicator/daily/{symbol}?period=10&type=macd&apikey={key}"
    r = requests.get(url)
    if r.status_code == 200:
        items = r.json()
        if items:
            latest = items[0]
            return {
                "macd": latest.get("macd"),
                "signal": latest.get("signal"),
            }
    return {}

def get_rsi(symbol):
    key = get_api_key(fmp_keys)
    url = f"https://financialmodelingprep.com/api/v3/technical_indicator/daily/{symbol}?period=14&type=rsi&apikey={key}"
    r = requests.get(url)
    if r.status_code == 200:
        items = r.json()
        if items:
            return items[0].get("rsi")
    return None

def get_kdj(symbol):
    key = get_api_key(fmp_keys)
    url = f"https://financialmodelingprep.com/api/v3/technical_indicator/daily/{symbol}?period=14&type=stochastic&apikey={key}"
    r = requests.get(url)
    if r.status_code == 200:
        items = r.json()
        if items:
            return {
                "k": items[0].get("k"),
                "d": items[0].get("d"),
            }
    return {}

def get_recommendation():
    candidates = ["AAPL", "MSFT", "NVDA", "GOOG", "META", "TSLA", "AMD"]
    for symbol in candidates:
        price = get_price_data(symbol)
        macd = get_macd(symbol)
        rsi = get_rsi(symbol)
        if price and macd and rsi:
            if macd["macd"] > macd["signal"] and rsi < 70:
                return {
                    "symbol": symbol,
                    "price": price["current"],
                    "suggest_buy": round(price["current"] * 0.98, 2),
                    "suggest_sell": round(price["current"] * 1.05, 2),
                    "reason": f"MACD金叉，RSI={rsi:.1f}，短期有上涨动能",
                }
    return None

@app.route("/", methods=["GET", "POST"])
def index():
    stock_data = {}
    kline_data = {}
    macd = {}
    rsi = None
    kdj = {}
    recommendation = get_recommendation()

    if request.method == "POST":
        symbol = request.form["symbol"].upper()
        stock_data = get_price_data(symbol)
        kline_data = get_kline_data(symbol)
        macd = get_macd(symbol)
        rsi = get_rsi(symbol)
        kdj = get_kdj(symbol)

        logic = []
        if macd:
            logic.append(f"MACD: {macd.get('macd', '-')} / Signal: {macd.get('signal', '-')}")
        if rsi:
            logic.append(f"RSI: {rsi:.1f}")
        if kdj:
            logic.append(f"KDJ: K={kdj.get('k', '-')}, D={kdj.get('d', '-')}")
        suggest = "持币观望"
        if macd and macd["macd"] > macd["signal"] and rsi and rsi < 70:
            suggest = "建议买入"
        elif rsi and rsi > 80:
            suggest = "建议卖出"

        stock_data["logic"] = "；".join(logic)
        stock_data["suggest"] = suggest
        stock_data["buy"] = round(stock_data["current"] * 0.98, 2) if "current" in stock_data else "-"
        stock_data["sell"] = round(stock_data["current"] * 1.05, 2) if "current" in stock_data else "-"

    return render_template("index.html", stock=stock_data, kline=kline_data, recommend=recommendation)

if __name__ == "__main__":
    app.run(port=5001)
