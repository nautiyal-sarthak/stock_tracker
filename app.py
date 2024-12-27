import numpy as np
import pandas as pd
import streamlit as st
from utility import fetch_stock_details, fetch_indicators, evaluate_stock, recommend_strike_price, calculate_bollinger_percentage
import matplotlib.pyplot as plt
import seaborn as sns


def style_bollinger_high(df):
    """
    Style the Bollinger High % column with a gradient color from white to red.

    :param df: The DataFrame containing the Bollinger High % column
    :return: A styled DataFrame
    """
    def color_gradient(val):
        red_intensity = int(255 * min(max(val, 0), 100) / 100)
        return f'background-color: rgb(255, {255 - red_intensity}, {255 - red_intensity})'

    return df.style.applymap(color_gradient, subset=['Bollinger High %'])


def main():
    st.set_page_config(layout="wide")  # Set the page layout to wide mode

    st.title("Stock Analysis and Option Recommendations")

    # Add a note explaining how a stock is marked good for selling an option
    st.markdown("""
    ### How a Stock is Marked Good for Selling an Option:
    - <span style="color:blue">**Good for selling puts**</span>: If the RSI is below 30, the current price is below the lower Bollinger Band, and the current price is above the 200-day moving average.
    - <span style="color:red">**Good for selling calls**</span>: If the RSI is above 70, the current price is above the upper Bollinger Band, and the current price is below the 200-day moving average.
    """, unsafe_allow_html=True)


    # Multi-choice input for ticker symbols
    tickers = st.multiselect(
        "Select Ticker Symbols",
        options=["AAPL", "PLTR", "GOOGL", "MSFT", "SHOP", "RKLB", "SOFI", "SPY", "NVDA", "NIO", "TSLA", "IONQ", "ASTS", "TMDX", "ENVX", "DOCN", "EOSE", "LMND", "AMZN", "AXON", "ALAB"],  # Add more options as needed
        default=["AAPL", "PLTR", "GOOGL", "MSFT", "SHOP", "RKLB", "SOFI", "SPY", "NVDA", "NIO", "TSLA", "IONQ", "ASTS", "TMDX", "ENVX", "DOCN", "EOSE", "LMND", "AMZN", "AXON", "ALAB"]
    )

    if tickers:
        results = []

        for ticker in tickers:
            details = fetch_stock_details(ticker)
            indicators = fetch_indicators(ticker)
            evaluation = evaluate_stock(indicators)

            put_strike_price, call_strike_price, expiration_date, current_price, put_premium, call_premium, put_delta, call_delta = recommend_strike_price(ticker)
            high_percentage, low_percentage = calculate_bollinger_percentage(current_price, indicators["Bollinger High"], indicators["Bollinger Low"])

            result = {
                "Ticker": ticker,
                "Current Price": current_price,
                "RSI": indicators["RSI"],
                "Bollinger High": indicators["Bollinger High"],
                "Bollinger High %": high_percentage,
                "Bollinger Low": indicators["Bollinger Low"],
                "Bollinger Low %": low_percentage,
                "200-day MA": indicators["200-day MA"],
                "Evaluation": evaluation,
                "Put Strike Price": put_strike_price,
                "Call Strike Price": call_strike_price,
                "Expiration Date": expiration_date,
                "Put Premium": put_premium,
                "Call Premium": call_premium,
                "Put Delta": put_delta,
                "Call Delta": call_delta
            }
            results.append(result)

        df = pd.DataFrame(results)
        pd.set_option('display.max_columns', None)  # Ensure all columns are printed

        # Define a custom color map for the RSI gradient
        cmap_rsi = sns.diverging_palette(250, 10, as_cmap=True)

        # Apply the gradient to the RSI column
        styled_df = df.style.background_gradient(cmap=cmap_rsi, subset=['RSI','Bollinger High %', 'Bollinger Low %'])
        

        st.dataframe(styled_df, height=800)  # Adjust the height as needed to fit all rows

if __name__ == "__main__":
    main()