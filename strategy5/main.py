"""

This is for INTRA DAY TRADING   --- NOT SWING

This finds super performer stocks a/c to Rising Moving Average 44 and tells entry point
Criteria:
    1. Moving Average 44 should be rising, not falling or sideways
    2. Time frame is 5 min / 15 min
    3. The Last candle stick should be bullish (green or hammer)
    4. The Last price should be near the 44 Moving Average
"""
import csv
import os
from datetime import datetime
from pprint import pprint

from data.nse import (
    get_top_stocks_by_market_cap,
    get_nifty50_stocks,
    get_nifty500_stocks,
    stocks_to_ignore
)
from data.from_yfinance import get_data


def get_price_data(stock):
    data = get_data(stock, period='1d', interval='15m')
    # start = '2021-01-01'
    # end = '2021-11-30'
    # data = get_data(stock, start=start, end=end, interval='15m')
    return data


def is_stock_rising(df):
    trend = df['44MA'][-10:].to_list()
    # 44 MA should go up for last 25 candles
    return sorted(trend) == trend


def is_probable_buy(df):
    # check for red candle, skip
    # if df['Open'][-1] >= df['Close'][-1]:
    #     return
    # check for bearish green candle, skip
    # if df['Close'][-1] - df['Open'][-1] < df['High'][-1] - df['Close'][-1]:
    #     return
    high = df['High'][-1]
    low = df['Low'][-1]
    # 44 MA should lie between green candle's high-low range +- 1%
    return (low - .01 * low) <= df['44MA'][-1] <= (high + .01 * high)


def calculate_buy_details(stock, df):
    entry = round(1.001 * df['High'][-1])
    stop_loss = round(0.999 * min(df['Low'][-1], df['Low'][-2]))
    if entry == stop_loss:
        return
    risk = 500
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
    }


def export_to_csv(trades):
    try:
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        file_name = curr_dir + "/" + datetime.today().strftime('%d-%m-%Y') + ".csv"
        with open(file_name, "w", newline="") as f:
            title = "stock,entry,stop_loss,target,quantity,money_to_trade".split(",")
            cw = csv.DictWriter(f, title, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            cw.writeheader()
            cw.writerows(trades)
    except Exception as e:
        print("FAILED TO EXPORT TO CSV")
        print(e)


def get_trades(stocks):
    trades = []
    count = 1
    for stock in stocks:
        print("Scanning stock number: ", count)
        count += 1
        try:
            df = get_price_data(stock)
            # Add 44 Moving Average
            df['44MA'] = df['Close'].rolling(window=44).mean()
            if not is_stock_rising(df):
                continue
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
    return trades


def run():
    stocks = [x + ".NS" for x in get_nifty50_stocks()] + \
             [x + ".NS" for x in get_top_stocks_by_market_cap()] + \
             [x + ".NS" for x in get_nifty500_stocks()]
    stocks = [x for x in stocks if x not in [x + ".NS" for x in stocks_to_ignore()]]
    stocks = list(set(stocks))
    print(len(stocks), " Stock are getting scanned")
    trades = get_trades(stocks)
    pprint(trades)
    # optional, comment if not needed
    export_to_csv(trades)