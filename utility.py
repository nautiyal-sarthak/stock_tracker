import yfinance as yf
import ta
from datetime import datetime, timedelta
from scipy.stats import norm
import numpy as np

def fetch_stock_details(ticker):
    stock = yf.Ticker(ticker)
    stock_info = stock.info
    return stock_info

def fetch_indicators(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")

    # Calculate RSI
    rsi = ta.momentum.RSIIndicator(hist['Close']).rsi()

    # Calculate Bollinger Bands
    bollinger = ta.volatility.BollingerBands(hist['Close'])
    bb_high = bollinger.bollinger_hband()
    bb_low = bollinger.bollinger_lband()

    # Calculate 200-day moving average
    ma_200 = ta.trend.SMAIndicator(hist['Close'], window=200).sma_indicator()

    indicators = {
        "RSI": rsi.iloc[-1],
        "Bollinger High": bb_high.iloc[-1],
        "Bollinger Low": bb_low.iloc[-1],
        "200-day MA": ma_200.iloc[-1],
        "Current Price": hist['Close'].iloc[-1]
    }
    return indicators

def evaluate_stock(indicators):
    rsi = indicators["RSI"]
    current_price = indicators["Current Price"]
    bb_high = indicators["Bollinger High"]
    bb_low = indicators["Bollinger Low"]
    ma_200 = indicators["200-day MA"]

    if rsi < 30 and current_price < bb_low and current_price > ma_200:
        return "Good for selling puts"
    elif rsi > 70 and current_price > bb_high and current_price < ma_200:
        return "Good for selling calls"
    else:
        return "Not a good time for selling puts or calls"

def black_scholes_delta(S, K, T, r, sigma, option_type="call"):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    if option_type == "call":
        delta = norm.cdf(d1)
    elif option_type == "put":
        delta = norm.cdf(d1) - 1
    return delta

def recommend_strike_price(ticker):
    stock = yf.Ticker(ticker)
    current_price = stock.history(period="1d")['Close'].iloc[-1]

    # Find the expiration date 2 weeks out
    expiration_dates = stock.options
    two_weeks_out = datetime.now() + timedelta(weeks=2)
    # Adjust to the nearest Friday
    while two_weeks_out.weekday() != 4:
        two_weeks_out += timedelta(days=1)
    expiration_date = two_weeks_out.strftime('%Y-%m-%d')

    # Check if the expiration date is available, if not choose the next available date
    if expiration_date not in expiration_dates:
        expiration_date = min(expiration_dates, key=lambda d: datetime.strptime(d, '%Y-%m-%d') > datetime.strptime(expiration_date, '%Y-%m-%d'))

    options = stock.option_chain(expiration_date)

    puts = options.puts
    calls = options.calls

    # Calculate delta for each option
    r = 0.01  # risk-free rate
    T = 14 / 365  # time to expiration in years
    sigma = stock.history(period="1y")['Close'].pct_change().std() * np.sqrt(252)  # annualized volatility

    puts['delta'] = puts.apply(lambda row: black_scholes_delta(current_price, row['strike'], T, r, sigma, option_type="put"), axis=1)
    calls['delta'] = calls.apply(lambda row: black_scholes_delta(current_price, row['strike'], T, r, sigma, option_type="call"), axis=1)

    # Find the nearest favorable strike price for puts
    puts_filtered = puts[(puts['strike'] < current_price) & (puts['delta'] >= -0.40) & (puts['delta'] <= -0.30)]
    if not puts_filtered.empty:
        put_strike_price = puts_filtered.iloc[-1]['strike']
        put_premium = puts_filtered.iloc[-1]['lastPrice']
        put_delta = puts_filtered.iloc[-1]['delta']
    else:
        nearest_put = puts[puts['strike'] < current_price].iloc[-1]
        put_strike_price = nearest_put['strike']
        put_premium = nearest_put['lastPrice']
        put_delta = nearest_put['delta']

    # Find the nearest favorable strike price for calls
    calls_filtered = calls[(calls['strike'] > current_price) & (calls['delta'] >= 0.30) & (calls['delta'] <= 0.40)]
    if not calls_filtered.empty:
        call_strike_price = calls_filtered.iloc[0]['strike']
        call_premium = calls_filtered.iloc[0]['lastPrice']
        call_delta = calls_filtered.iloc[0]['delta']
    else:
        nearest_call = calls[calls['strike'] > current_price].iloc[0]
        call_strike_price = nearest_call['strike']
        call_premium = nearest_call['lastPrice']
        call_delta = nearest_call['delta']

    return put_strike_price, call_strike_price, expiration_date, current_price, put_premium, call_premium, put_delta, call_delta

def calculate_bollinger_percentage(current_price, bollinger_high, bollinger_low):
    """
    Calculate the percentage difference between the current price and the Bollinger High and Low values.

    :param current_price: The current price of the stock
    :param bollinger_high: The Bollinger High value
    :param bollinger_low: The Bollinger Low value
    :return: A tuple containing the percentage difference for Bollinger High and Bollinger Low
    """
    high_percentage = -1 * ((bollinger_high - current_price) / current_price) * 100 
    low_percentage = ((bollinger_low - current_price) / current_price) * 100
    return high_percentage, low_percentage
