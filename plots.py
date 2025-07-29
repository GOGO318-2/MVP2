import plotly.graph_objs as go

def plot_price_chart(df, ticker):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close'))
    fig.update_layout(title=f'{ticker} - Price Chart', xaxis_title='Date', yaxis_title='Price')
    return fig

def plot_macd(macd, signal, df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=macd, name='MACD'))
    fig.add_trace(go.Scatter(x=df.index, y=signal, name='Signal'))
    fig.update_layout(title='MACD Indicator', xaxis_title='Date', yaxis_title='Value')
    return fig
