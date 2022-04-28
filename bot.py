import ccxt
import config
import schedule
import pandas as pd
pd.set_option('display.max_rows', None)
import numpy as np
import ta 
from ta.volatility import BollingerBands, AverageTrueRange
import time
import datetime

exchange = ccxt.binance({
    'apiKey': config.BINANCE_API_KEY,
    'secret': config.BINANCE_SECRET_KEY,
})

def supertrend( df, multiplier):
    print("Calculating supertrend...")
    atr_indicator = AverageTrueRange(df['high'], df['low'], df['close'])

    df['atr'] = atr_indicator.average_true_range()
    df['basic_upper_band'] = (df['high'] + df['low'])/2 + (multiplier * df['atr'])
    df['basic_lower_band'] = (df['high'] + df['low'])/2 - (multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range( 1, len(df.index)):
        previous = current - 1
        if df.loc[current, ('close')] > df.loc[previous, ('basic_upper_band')]:
            df.loc[current, ('in_uptrend')] = True
        elif df.loc[current, ('close')] < df.loc[previous, ('basic_lower_band')]:
            df.loc[current, ('in_uptrend')] = False
        else:
            df.loc[current, ('in_uptrend')] = df.loc[previous, ('in_uptrend')]
            if df.loc[current, ('in_uptrend')] and df.loc[current, ('basic_lower_band')] < df.loc[previous, ('basic_lower_band')]:
                df.loc[current, ('basic_lower_band')] = df.loc[previous, ('basic_lower_band')]

            if not df.loc[current, ('in_uptrend')] and df.loc[current, ('basic_upper_band')] > df.loc[previous, ('basic_upper_band')]:
                df.loc[current, ('basic_upper_band')] = df.loc[previous, ('basic_upper_band')]
    return df
in_position = False
def check_buy_sell_signals( df):
    global in_position
    print("Checking for buys and sells")
    print( df.tail(2))
    last_row_index = len( df.index) - 1
    previous_row_index = last_row_index - 1
    if not df.loc[previous_row_index, 'in_uptrend'] and df.loc[last_row_index, 'in_uptrend']:
        print( "Change to uptrend, buy")
        if not in_position:
            order = exchange.create_market_buy_order('ADA/USDT', 17)
            print( order)
            in_position = True
        else:
            print( "Already in position")
    if df.loc[previous_row_index, 'in_uptrend'] and not df.loc[last_row_index, 'in_uptrend']:
        print( "Change to donwtrend, sell")
        if in_position:
            order = exchange.create_market_sell_order('ADA/USDT', 17)
            print( order)
            in_position = False
        else:
            print("You are not in position, nothing to sell")

def run_bot():
    print( f"Fetching new bars for {datetime.datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv('ADA/USDT', timeframe='1m', limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms') + pd.Timedelta('03:00:00')
    df['previous_close'] = df['close'].shift(1)
    supertrend_data = supertrend( df, 3)
    check_buy_sell_signals( supertrend_data)
schedule.every(1).minutes.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)
    

