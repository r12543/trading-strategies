"""

This is for SWING TRADING   --- NOT INTRA DAY

This finds super performer stocks a/c to Rising Moving Average 44 and tells entry point
Criteria:
    1. Moving Average 44 should be rising, not falling or sideways
    2. Time frame is Daily
    3. The Last day should have green candle stick
    4. The last price should be near the 44 Moving Average
"""
import csv
import os
from datetime import datetime
from pprint import pprint

from data.nse import (
    get_nifty50_stocks,
    get_nifty100_stocks,
    get_nifty200_stocks,
    get_nifty500_stocks,
    stocks_to_ignore
)
from data.from_yfinance import get_data


def get_price_data(tickers):
    ohlc_data = {}
    for ticker in tickers:
        ohlc_data[ticker] = get_data(ticker, period='350d', interval='1d')
        # start = '2021-01-01'
        # end = '2021-11-30'
        # ohlc_data[ticker] = get_data(ticker, start=start, end=end, interval='1d')
    return ohlc_data


def is_stock_rising(df):
    last_14_days_trend = df['44MA'][-14:].to_list()
    # 44 MA should go up for last 14 consecutive days
    return sorted(last_14_days_trend) == last_14_days_trend


def is_probable_buy(df):
    # check for red candle, skip
    if df['Open'][-1] >= df['Close'][-1]:
        return
    # check for bearish green candle, skip
    if df['Close'][-1] - df['Open'][-1] < df['High'][-1] - df['Close'][-1]:
        return
    high = df['High'][-1]
    low = df['Low'][-1]
    # 44 MA should lie between green candle's high-low range
    return (low - .05 * low) <= df['44MA'][-1] <= (high + .02 * high) and (df['Close'][-1] >= df['44MA'][-1])


def calculate_buy_details(stock, df):
    entry = round(1.001 * df['High'][-1])
    stop_loss = round(0.999 * min(df['Low'][-1], df['Low'][-2]))
    if entry == stop_loss:
        return
    risk = 500 if df['Close'][-1] < 1000 else 1000
    quantity = round(risk / (entry - stop_loss))
    target = 2 * (entry - stop_loss) + entry
    money_to_trade = round(entry) * quantity + 1
    return {
        'stock': stock.split(".")[0],
        'entry': entry,
        'stop_loss': stop_loss,
        'quantity': quantity,
        'target': target,
        'money_to_trade': money_to_trade,
        'risk': risk,
        'entry_sl_diff': entry - stop_loss,
    }


def export_to_csv(trades):
    try:
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        file_name = curr_dir + "/" + datetime.today().strftime('%d-%m-%Y') + "-TRADES-ANALYSIS.csv"
        with open(file_name, "w", newline="") as f:
            title = "stock,entry,stop_loss,target,quantity,money_to_trade,risk,entry_sl_diff".split(",")
            cw = csv.DictWriter(f, title, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            cw.writeheader()
            cw.writerows(trades)
    except Exception as e:
        print("FAILED TO EXPORT TO CSV")
        print(e)


def get_trades(stocks):
    trades = []
    count = 1
    rising_stocks = []
    for stock in stocks:
        print("Scanning stock number: ", count)
        count += 1
        try:
            df = get_data(stock, period='350d', interval='1d')
            # Add 44 Moving Average
            df['44MA'] = df['Close'].rolling(window=44).mean()
            if not is_stock_rising(df):
                continue
            rising_stocks.append(stock)
            if not is_probable_buy(df):
                continue
            buy_details = calculate_buy_details(stock, df)
            if buy_details is None:
                continue
            print("TRADE FOUND >>>>>>>>>>>>>>>>>>>>>>>\n")
            print("STOCK: ------   " + stock + "    -------")
            pprint(buy_details)
            print("===================================\n")
            trades.append(buy_details)
        except Exception as e:
            print("Exception occurred >>>>>>>>>>>>>>>>>>>>>>>\n")
            print(e)
        count += 1
    print("RISING STOCKS ============================>>>>")
    print(rising_stocks)
    return trades


def run():
    stocks = [x + ".NS" for x in get_nifty500_stocks()]
    stocks = [x for x in stocks if x not in [x + ".NS" for x in stocks_to_ignore()]]
    # stocks = list(set(stocks))
    print(len(stocks))
    trades = get_trades(stocks)
    pprint(trades)
    # optional, comment if not needed
    export_to_csv(trades)
