import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
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

        with st.container():
            st.subheader(f"【{symbol}】当前价格: {price:.2f} USD")
            st.markdown(f"推荐理由：{reason}")
            st.markdown(f"建议买入价：{buy_price}，建议卖出价：{sell_price}")

            df = fetch_stock_data(symbol)
            if not df.empty:
                st.markdown("📊 **交互式趋势图**")
                st.components.v1.html(
                    f"""
                    <canvas id="chart_{symbol}"></canvas>
                    <script>
                        const ctx = document.getElementById('chart_{symbol}').getContext('2d');
                        const chart = new Chart(ctx, {{
                            type: 'line',
                            data: {{
                                labels: {df.index.strftime('%Y-%m-%d').tolist()},
                                datasets: [{{
                                    label: '{symbol} 收盘价',
                                    data: {df['Close'].round(2).tolist()},
                                    borderColor: 'rgba(75, 192, 192, 1)',
                                    fill: false,
                                    tension: 0.1
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                scales: {{
                                    x: {{
                                        display: true,
                                        title: {{ display: true, text: '日期' }}
                                    }},
                                    y: {{
                                        display: true,
                                        title: {{ display: true, text: '价格 (USD)' }}
                                    }}
                                }}
                            }}
                        }});
                    </script>
                    """,
                    height=300,
                )
else:
    st.write("暂无合适推荐，稍后再试。")

st.markdown("---")

# 查询部分
st.header("🔍 股票查询")
ticker_input = st.text_input("请输入美股/港股代码（如 AAPL 或 00700.HK）:")

if ticker_input:
    df = fetch_stock_data(ticker_input.upper())

    if df.empty:
        st.warning("无法获取数据，请检查代码是否正确。")
    else:
        st.subheader(f"【{ticker_input.upper()}】行情概览")
        current_price = df["Close"][-1]
        previous_close = df["Close"][-2] if len(df) > 1 else current_price
        st.write(f"当前价格：{current_price:.2f} USD")
        st.write(f"前一交易日收盘：{previous_close:.2f} USD")

        indicators = calculate_indicators(df)
        suggestion = format_analysis(indicators)

        st.markdown("### 分析指标")
        st.write(f"MACD: {indicators['MACD']:.2f}, Signal: {indicators['Signal']:.2f}")
        st.write(f"RSI: {indicators['RSI']:.2f}")
        st.write(f"KDJ: K={indicators['K']:.2f}, D={indicators['D']:.2f}, J={indicators['J']:.2f}")
        st.write(f"Stochastic Oscillator: K={indicators['slowk']:.2f}, D={indicators['slowd']:.2f}")

        st.markdown("### 建议")
        st.write(suggestion["advice"])
        st.write(f"推荐买入价：{suggestion['buy_price']}, 卖出价：{suggestion['sell_price']}")
        st.write(f"分析逻辑：{suggestion['reason']}")

        st.markdown("📊 **交互式趋势图表**")
        st.components.v1.html(
            f"""
            <canvas id="chart_{ticker_input}"></canvas>
            <script>
                const ctx2 = document.getElementById('chart_{ticker_input}').getContext('2d');
                const chart2 = new Chart(ctx2, {{
                    type: 'line',
                    data: {{
                        labels: {df.index.strftime('%Y-%m-%d').tolist()},
                        datasets: [{{
                            label: '{ticker_input.upper()} 收盘价',
                            data: {df['Close'].round(2).tolist()},
                            borderColor: 'rgba(255, 99, 132, 1)',
                            fill: false,
                            tension: 0.1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        scales: {{
                            x: {{
                                display: true,
                                title: {{ display: true, text: '日期' }}
                            }},
                            y: {{
                                display: true,
                                title: {{ display: true, text: '价格 (USD)' }}
                            }}
                        }}
                    }}
                }});
            </script>
            """,
            height=300,
        )
