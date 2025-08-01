import os

# -------------------- 配置信息 --------------------
CONFIG = {
    'page_title': '智能股票分析平台',
    'layout': 'wide',
    'api_keys': {
        "finnhub": os.getenv("FINNHUB_API_KEY", "ckq0dahr01qj3j9g4vrgckq0dahr01qj3j9g4vs0"),
        "alpha_vantage": "Z45S0SLJGM378PIO",
        "polygon": "2CDgF277xEhkhKndj5yFMVONxBGFFShg"
    },
    'cache_timeout': 300,  # 5分钟缓存
    'news_api': {
        'url': 'https://finnhub.io/api/v1/company-news',
        'key': os.getenv("FINNHUB_API_KEY", "ckq0dahr01qj3j9g4vrgckq0dahr01qj3j9g4vs0")
    }
}

# 热门股票列表
HOT_STOCKS = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "0700"]

# 默认股票代码
DEFAULT_TICKER = "TSLA"
