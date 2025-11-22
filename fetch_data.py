import yfinance as yf
import pandas as pd
import json
import os

def fetch_and_process_data():
    # Create public directory if it doesn't exist
    if not os.path.exists('public'):
        os.makedirs('public')

    # Fetch TQQQ data
    # Interval: 15m, Period: 60d (max for 15m data)
    ticker = yf.Ticker("TQQQ")
    df = ticker.history(period="60d", interval="15m")

    # Calculate EMAs
    # Note: yfinance returns a DataFrame with a DatetimeIndex
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()

    # Prepare data for JSON export
    # We need lists for Plotly
    data = {
        'dates': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'prices': df['Close'].round(2).tolist(),
        'ema9': df['EMA9'].round(2).tolist(),
        'ema12': df['EMA12'].round(2).tolist()
    }

    # Save to JSON
    with open('public/data.json', 'w') as f:
        json.dump(data, f)
    
    print("Data updated successfully!")

if __name__ == "__main__":
    fetch_and_process_data()
