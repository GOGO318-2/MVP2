import streamlit as st
from utils.data import fetch_stock_data, fetch_latest_price, fetch_news
from utils.indicators import compute_indicators
from utils.plots import plot_candlestick_with_indicators
from utils.stock_utils import recommend_stocks

st.set_page_config(layout="wide", page_title="美股分析系统")

# ⬆️ 顶部推荐区
st.title("📈 美股实时分析推荐系统")
st.markdown("---")

# 推荐逻辑
with st.container():
    st.subheader("今日推荐股票")
    recommendations = recommend_stocks()
    if recommendations:
        for rec in recommendations:
            st.markdown(f"**股票代码：** `{rec['symbol']}`")
            st.markdown(f"**当前价格：** ${rec['price']}")
            st.markdown(f"**买入建议价：** ${rec['buy']}")
            st.markdown(f"**卖出建议价：** ${rec['sell']}")
            st.markdown(f"**推荐理由：** {rec['reason']}")
            st.markdown("---")
    else:
        st.info("暂无合适推荐，稍后再试。")

# 🔍 股票查询区
st.subheader("🔎 个股分析查询")
ticker = st.text_input("输入美股或港股代码（如 AAPL 或 00700.HK）")

if ticker:
    try:
        st.markdown(f"## 股票代码： `{ticker.upper()}`")

        # 1. 获取数据
        price, df = fetch_latest_price(ticker), fetch_stock_data(ticker)
        indicators = compute_indicators(df)

        # 2. 当前价格与收盘价展示
        st.write(f"**当前价格：** ${price:.2f}")
        st.write(f"**昨日收盘：** ${df['Close'].iloc[-2]:.2f}")
        st.markdown("---")

        # 3. 图表展示
        st.plotly_chart(plot_candlestick_with_indicators(df, indicators), use_container_width=True)

        # 4. 技术指标解读
        macd_str = f"MACD: {indicators['MACD'][-1]:.2f}, Signal: {indicators['Signal'][-1]:.2f}"
        rsi_str = f"RSI: {indicators['RSI'][-1]:.2f}"
        st.write(f"📉 技术指标：{macd_str} | {rsi_str}")

        # 5. 新闻与情绪
        st.subheader("📰 最新相关新闻")
        news_items = fetch_news(ticker)
        if news_items:
            for item in news_items[:5]:
                st.markdown(f"- [{item['title']}]({item['url']})")
        else:
            st.info("暂无相关新闻")

    except Exception as e:
        st.error(f"加载股票数据失败：{str(e)}")

else:
    st.info("请输入股票代码以开始分析")
