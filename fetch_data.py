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

    # Calculate SMAs and EMAs
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA100'] = df['Close'].rolling(window=100).mean()
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()

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
    # Replace NaN with None (becomes null in JSON)
    import numpy as np
    data = {
        'dates': dates,
        'prices': df['Close'].round(2).tolist(),
        'sma50': [x if pd.notnull(x) else None for x in df['SMA50'].round(2)],
        'sma100': [x if pd.notnull(x) else None for x in df['SMA100'].round(2)],
        'ema9': [x if pd.notnull(x) else None for x in df['EMA9'].round(2)],
        'ema12': [x if pd.notnull(x) else None for x in df['EMA12'].round(2)],
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

    # --- Notification Logic ---
    # Check for crossover TODAY (last data point)
    # We only notify if the crossover happened on the LAST day to avoid spamming old alerts
    import requests
    
    # Get last two valid values for SMA50 and SMA100
    # We need to filter out None values to check crossover
    valid_sma50 = [x for x in data['sma50'] if x is not None]
    valid_sma100 = [x for x in data['sma100'] if x is not None]
    
    if len(valid_sma50) >= 2 and len(valid_sma100) >= 2:
        today_sma50 = valid_sma50[-1]
        prev_sma50 = valid_sma50[-2]
        today_sma100 = valid_sma100[-1]
        prev_sma100 = valid_sma100[-2]
        
        msg = ""
        title = ""
        tags = ""
        
        # Bullish Crossover
        if prev_sma50 < prev_sma100 and today_sma50 > today_sma100:
            title = "🚀 TQQQ Bullish Crossover!"
            msg = f"SMA50 ({today_sma50}) has crossed ABOVE SMA100 ({today_sma100}). Potential buy signal."
            tags = "rocket,moneybag"
            
        # Bearish Crossover
        elif prev_sma50 > prev_sma100 and today_sma50 < today_sma100:
            title = "⚠️ TQQQ Bearish Crossover!"
            msg = f"SMA50 ({today_sma50}) has crossed BELOW SMA100 ({today_sma100}). Potential sell signal."
            tags = "warning,chart_with_downwards_trend"
            
        if msg:
            try:
                requests.post("https://ntfy.sh/tqqq_tracker_alerts",
                    data=msg.encode('utf-8'),
                    headers={
                        "Title": title.encode('utf-8'),
                        "Tags": tags,
                        "Click": "https://tqqq-tracker.pages.dev"
                    }
                )
                print(f"Notification sent: {title}")
            except Exception as e:
                print(f"Failed to send notification: {e}")


if __name__ == "__main__":
    fetch_and_process_data()
