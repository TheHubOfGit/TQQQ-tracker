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
    # Check for crossovers TODAY (last data point)
    # We only notify if the crossover happened on the LAST day to avoid spamming old alerts
    import requests
    
    def check_crossover(line1_data, line2_data, name1, name2):
        """Check for crossover between two indicator lines"""
        # Get last two valid values
        valid_line1 = [x for x in line1_data if x is not None]
        valid_line2 = [x for x in line2_data if x is not None]
        
        if len(valid_line1) >= 2 and len(valid_line2) >= 2:
            today_line1 = valid_line1[-1]
            prev_line1 = valid_line1[-2]
            today_line2 = valid_line2[-1]
            prev_line2 = valid_line2[-2]
            
            # Bullish Crossover (faster crosses above slower)
            if prev_line1 < prev_line2 and today_line1 > today_line2:
                return {
                    'type': 'bullish',
                    'title': f'🚀 TQQQ Bullish Crossover! ({name1}/{name2})',
                    'msg': f'{name1} ({today_line1}) has crossed ABOVE {name2} ({today_line2}). Potential buy signal.',
                    'tags': 'rocket,moneybag'
                }
            
            # Bearish Crossover (slower crosses above faster)
            elif prev_line1 > prev_line2 and today_line1 < today_line2:
                return {
                    'type': 'bearish',
                    'title': f'⚠️ TQQQ Bearish Crossover! ({name1}/{name2})',
                    'msg': f'{name1} ({today_line1}) has crossed BELOW {name2} ({today_line2}). Potential sell signal.',
                    'tags': 'warning,chart_with_downwards_trend'
                }
        
        return None
    
    # Check SMA 50/100 crossover
    sma_crossover = check_crossover(data['sma50'], data['sma100'], 'SMA50', 'SMA100')
    
    # Check EMA 9/12 crossover
    ema_crossover = check_crossover(data['ema9'], data['ema12'], 'EMA9', 'EMA12')
    
    # Send notifications for any detected crossovers
    for crossover in [sma_crossover, ema_crossover]:
        if crossover:
            try:
                requests.post("https://ntfy.sh/tqqq_tracker_alerts",
                    data=crossover['msg'].encode('utf-8'),
                    headers={
                        "Title": crossover['title'].encode('utf-8'),
                        "Tags": crossover['tags'],
                        "Click": "https://tqqq-tracker.pages.dev"
                    }
                )
                print(f"Notification sent: {crossover['title']}")
            except Exception as e:
                print(f"Failed to send notification: {e}")



if __name__ == "__main__":
    fetch_and_process_data()
