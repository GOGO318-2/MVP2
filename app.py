import streamlit as st
import yfinance as yf
import pandas as pd
from utils.stock_utils import (
    fetch_recommendation,
    fetch_stock_data,
    calculate_indicators,
    format_analysis
)

st.set_page_config(layout="wide")

st.title("📈 股票推荐与查询系统")

# 推荐部分
st.header("🔥 今日股票推荐")
recommendation = fetch_recommendation()

if recommendation:
    for stock in recommendation:
        symbol = stock["symbol"]
        price = stock["price"]
        reason = stock["reason"]
        buy_price = stock["buy_price"]
        sell_price = stock["sell_price"]

        st.subheader(f"【{symbol}】当前价格: {price:.2f} USD")
        st.markdown(f"推荐理由：{reason}")
        st.markdown(f"建议买入价：{buy_price}，建议卖出价：{sell_price}")

        df = fetch_stock_data(symbol)
        if not df.empty:
            st.components.v1.html(f"""
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <canvas id="chart_{symbol}"></canvas>
            <script>
                const ctx = document.getElementById("chart_{symbol}").getContext("2d");
                new Chart(ctx, {{
                    type: "line",
                    data: {{
                        labels: {df.index.strftime('%Y-%m-%d').tolist()},
                        datasets: [{{
                            label: "{symbol} 收盘价",
                            data: {df["Close"].round(2).tolist()},
                            borderColor: "rgba(75, 192, 192, 1)",
                            fill: false
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{ display: true }},
                        }}
                    }}
                }});
            </script>
            """, height=300)
else:
    st.write("暂无推荐")

st.markdown("---")

# 查询部分
st.header("🔍 股票查询")
ticker_input = st.text_input("请输入股票代码（如 AAPL 或 00700.HK）:")

if ticker_input:
    ticker = ticker_input.strip().upper()
    df = fetch_stock_data(ticker)

    if df.empty:
        st.warning("无法获取数据，请检查代码。")
    else:
        st.subheader(f"【{ticker}】行情概览")
        st.write(f"当前价格：{df['Close'][-1]:.2f} USD")
        indicators = calculate_indicators(df)
        suggestion = format_analysis(indicators)

        st.markdown("### 分析指标")
        st.write(f"MACD: {indicators['MACD']:.2f}, Signal: {indicators['Signal']:.2f}")
        st.write(f"RSI: {indicators['RSI']:.2f}")
        st.write(f"KDJ: K={indicators['K']:.2f}, D={indicators['D']:.2f}, J={indicators['J']:.2f}")

        st.markdown("### 建议")
        st.write(suggestion["advice"])
        st.write(f"建议买入价：{suggestion['buy_price']}, 卖出价：{suggestion['sell_price']}")
        st.write(f"理由：{suggestion['reason']}")

        st.components.v1.html(f"""
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <canvas id="chart_{ticker}"></canvas>
        <script>
            const ctx = document.getElementById("chart_{ticker}").getContext("2d");
            new Chart(ctx, {{
                type: "line",
                data: {{
                    labels: {df.index.strftime('%Y-%m-%d').tolist()},
                    datasets: [{{
                        label: "{ticker} 收盘价",
                        data: {df["Close"].round(2).tolist()},
                        borderColor: "rgba(255, 99, 132, 1)",
                        fill: false
                    }}]
                }},
                options: {{
                    responsive: true
                }}
            }});
        </script>
        """, height=300)
