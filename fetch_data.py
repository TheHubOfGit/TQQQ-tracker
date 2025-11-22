import yfinance as yf
import pandas as pd
import json
import os

def fetch_and_process_data():
    # Create public directory if it doesn't exist
    if not os.path.exists('public'):
        os.makedirs('public')

    # Fetch TQQQ data
    # Interval: 1d, Period: 2y (to support SMA100 and give context)
    ticker = yf.Ticker("TQQQ")
    df = ticker.history(period="2y", interval="1d")

    # Calculate SMAs
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA100'] = df['Close'].rolling(window=100).mean()

    # Get previous day's close for "Today's Return" calculation
    if len(df) >= 2:
        prev_close = df['Close'].iloc[-2]
    else:
        prev_close = df['Close'].iloc[0]

    current_price = df['Close'].iloc[-1]
    price_change = current_price - prev_close
    percent_change = (price_change / prev_close) * 100

    # Format dates
    # For historical days: Nov 21, 2025
    # For today (last point): Nov 21, 2025, 11:08 PM
    dates = df.index.strftime('%b %d, %Y').tolist()
    
    # Add current time to the last date point to satisfy "latest datapoint" visibility
    from datetime import datetime
    import pytz
    
    # Get current time in ET (Market time)
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    dates[-1] = now.strftime('%b %d, %Y, %I:%M %p')

    # Prepare data for JSON export
    data = {
        'dates': dates,
        'prices': df['Close'].round(2).tolist(),
        'sma50': df['SMA50'].round(2).fillna(0).tolist(),
        'sma100': df['SMA100'].round(2).fillna(0).tolist(),
        'meta': {
            'current_price': round(current_price, 2),
            'price_change': round(price_change, 2),
            'percent_change': round(percent_change, 2),
            'is_positive': bool(price_change >= 0)
        }
    }

    # Save to JSON
    with open('public/data.json', 'w') as f:
        json.dump(data, f)
    
    print("Data updated successfully!")

if __name__ == "__main__":
    fetch_and_process_data()
