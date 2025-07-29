    # === MACD指标计算 ===
    df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal']

    # === RSI指标计算 ===
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # === KDJ指标计算 ===
    low_min = df['low'].rolling(window=9).min()
    high_max = df['high'].rolling(window=9).max()
    rsv = 100 * (df['close'] - low_min) / (high_max - low_min)
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']

    # === Stochastic指标计算 ===
    low_stoch = df['low'].rolling(window=14).min()
    high_stoch = df['high'].rolling(window=14).max()
    df['%K'] = 100 * (df['close'] - low_stoch) / (high_stoch - low_stoch)
    df['%D'] = df['%K'].rolling(window=3).mean()

    return df
