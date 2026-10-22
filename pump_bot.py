import time
import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import telebot

TOKEN = '8805980552:AAHZwYR6Xu11PY8nQxEeBv6zlcgRb5ii9Ic'  # توکن ربات تلگرام خود را اینجا بگذارید
CHAT_ID = '6254027493'            # آیدی عددی تلگرام خود را اینجا بگذارید

bot = telebot.TeleBot(TOKEN)
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def fetch_data(symbol, timeframe='1d', limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"خطا: {e}")
        return None

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def check_fibonacci_support(df_btc):
    high = df_btc['high'].max()
    low = df_btc['low'].min()
    diff = high - low
    fib_50 = high - (diff * 0.5)
    fib_618 = high - (diff * 0.618)
    current_price = df_btc['close'].iloc[-1]
    in_support = (abs(current_price - fib_50) / fib_50 < 0.02) or (abs(current_price - fib_618) / fib_618 < 0.02)
    return in_support

def generate_chart_image(df_usdt, symbol):
    plt.figure(figsize=(10, 6))
    plt.plot(df_usdt['timestamp'], df_usdt['close'], label='USDT Price', color='cyan')
    plt.title(f'{symbol} - Pump Signal')
    plt.grid(True)
    image_path = 'signal_chart.png'
    plt.savefig(image_path)
    plt.close()
    return image_path

def analyze_market():
    symbols = ['SOL/USDT', 'XRP/USDT', 'AXS/USDT']
    for base_symbol in symbols:
        coin = base_symbol.split('/')[0]
        usdt_symbol = f"{coin}/USDT"
        btc_symbol = f"{coin}/BTC"
        
        df_usdt = fetch_data(usdt_symbol, '1d', 100)
        df_btc = fetch_data(btc_symbol, '1d', 100)
        
        if df_usdt is None or df_btc is None:
            continue
            
        df_usdt['rsi'] = calculate_rsi(df_usdt['close'])
        df_btc['rsi'] = calculate_rsi(df_btc['close'])
        
        cond_1 = (df_usdt['close'].iloc[-1] > df_usdt['close'].iloc[-5]) and \
                 (df_btc['close'].iloc[-1] <= df_btc['close'].iloc[-5])
        cond_2 = check_fibonacci_support(df_btc)
        cond_3 = (df_usdt['close'].iloc[-1] > df_usdt['close'].iloc[-20]) and \
                 (df_usdt['rsi'].iloc[-1] < df_usdt['rsi'].iloc[-20])
        cond_4 = (df_btc['close'].iloc[-1] < df_btc['close'].iloc[-20]) and \
                 (df_btc['rsi'].iloc[-1] > df_btc['rsi'].iloc[-20])
                 
        matched = sum([cond_1, cond_2, cond_3, cond_4])
        
        if matched >= 3:
            img_path = generate_chart_image(df_usdt, base_symbol)
            message = f"🔔 سیگنال پامپ برای {usdt_symbol} تایید شد! ({matched} شرط از ۴ شرط)"
            with open(img_path, 'rb') as photo:
                bot.send_photo(CHAT_ID, photo, caption=message)

if __name__ == '__main__':
    while True:
        analyze_market()
        time.sleep(14400)
