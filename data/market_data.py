import yfinance as yf
import pandas as pd
import streamlit as st

def get_historical_data(ticker: str, period: str = "1y", interval: str = "1d", short_sma: int = 20, long_sma: int = 50) -> pd.DataFrame:
    """Fetches historical stock data and calculates technical indicators."""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    
    if df.empty:
        return df
        
    # Calculate SMA (Simple Moving Average) using custom periods
    df['SMA_20'] = df['Close'].rolling(window=short_sma).mean()
    df['SMA_50'] = df['Close'].rolling(window=long_sma).mean()
    
    # Calculate EMA (Exponential Moving Average)
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # Calculate RSI (Relative Strength Index)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

def get_current_price(ticker: str) -> float:
    """Fetches the current or last closing price of a stock."""
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if not data.empty:
        return data['Close'].iloc[-1]
    return 0.0

def get_stock_info(ticker: str) -> dict:
    """Fetches basic company info."""
    stock = yf.Ticker(ticker)
    return stock.info

@st.cache_data(ttl=300)
def get_market_overview() -> dict:
    """
    Downloads 1 month of daily data for US indices and major tech companies.
    Calculates current price and percentage change.
    """
    tickers = {
        "S&P 500": "^GSPC",
        "Nasdaq 100": "^IXIC",
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "Google": "GOOGL",
        "Nvidia": "NVDA",
        "Tesla": "TSLA",
        "Amazon": "AMZN"
    }
    symbols = list(tickers.values())
    try:
        data = yf.download(symbols, period="1mo", interval="1d", progress=False)
        if data.empty:
            return {}
        
        close_data = data['Close'].ffill()
        
        summary = {}
        for name, sym in tickers.items():
            if sym not in close_data.columns:
                continue
            series = close_data[sym].dropna()
            if len(series) < 2:
                continue
            current_price = float(series.iloc[-1])
            prev_price = float(series.iloc[-2])
            pct_change = float(((current_price - prev_price) / prev_price) * 100)
            
            summary[sym] = {
                "name": name,
                "symbol": sym,
                "price": current_price,
                "change": pct_change,
                "history": series.tolist()
            }
        return summary
    except Exception as e:
        print(f"Error fetching market overview: {e}")
        return {}

def backtest_strategy(ticker: str, short_sma: int = 20, long_sma: int = 50) -> dict:
    """
    Simulates a simple moving average crossover strategy over 1 year
    and compares it to a Buy and Hold strategy.
    """
    df = yf.Ticker(ticker).history(period="1y")
    if df.empty or len(df) < long_sma:
        return {}
    
    df['Short_SMA'] = df['Close'].rolling(window=short_sma).mean()
    df['Long_SMA'] = df['Close'].rolling(window=long_sma).mean()
    df = df.dropna(subset=['Short_SMA', 'Long_SMA']).copy()
    
    initial_capital = 10000.0
    cash = initial_capital
    position = 0.0 # Number of shares held
    
    strategy_values = []
    dates = []
    trades = []
    
    # Standard Buy & Hold
    buy_hold_shares = initial_capital / df['Close'].iloc[0]
    
    for i in range(len(df)):
        date = df.index[i]
        price = df['Close'].iloc[i]
        short_val = df['Short_SMA'].iloc[i]
        long_val = df['Long_SMA'].iloc[i]
        
        # Check signals (crossover)
        if i > 0:
            prev_short = df['Short_SMA'].iloc[i-1]
            prev_long = df['Long_SMA'].iloc[i-1]
            
            # Golden Cross: Short SMA crosses above Long SMA -> BUY
            if prev_short <= prev_long and short_val > long_val and position == 0:
                shares_to_buy = cash / price
                position = shares_to_buy
                cash = 0.0
                trades.append({"type": "BUY", "date": date.strftime("%Y-%m-%d"), "price": float(price)})
            
            # Death Cross: Short SMA crosses below Long SMA -> SELL
            elif prev_short >= prev_long and short_val < long_val and position > 0:
                cash = position * price
                position = 0.0
                trades.append({"type": "SELL", "date": date.strftime("%Y-%m-%d"), "price": float(price)})
        
        portfolio_val = cash + (position * price)
        strategy_values.append(float(portfolio_val))
        dates.append(date)
    
    final_val_strategy = strategy_values[-1]
    final_val_bh = float(buy_hold_shares * df['Close'].iloc[-1])
    
    strategy_return = ((final_val_strategy - initial_capital) / initial_capital) * 100
    bh_return = ((final_val_bh - initial_capital) / initial_capital) * 100
    
    backtest_df = pd.DataFrame({
        "Strategy": strategy_values,
        "Buy_Hold": [float(buy_hold_shares * p) for p in df['Close']]
    }, index=dates)
    
    return {
        "df": backtest_df,
        "strategy_return": strategy_return,
        "bh_return": bh_return,
        "initial_capital": initial_capital,
        "final_strategy": final_val_strategy,
        "final_bh": final_val_bh,
        "trades": trades
    }


