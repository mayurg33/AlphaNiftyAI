import os
import pandas as pd
from datetime import datetime

# Configuration
DATA_DIR = "data/prices/weekly"   # Folder where weekly data is stored
BENCHMARK = "NSEI"                # Change to "^NSEI" if your file is named with caret
BUY_DATE = datetime(2024, 3, 3)
SELL_DATE = datetime(2025, 6, 1)

def get_all_nifty_prices():
    prices = []
    for folder in sorted(os.listdir(DATA_DIR)):
        week_path = os.path.join(DATA_DIR, folder)
        if not os.path.isdir(week_path):
            continue
        file_path = os.path.join(week_path, f"{BENCHMARK}.csv")
        if not os.path.exists(file_path):
            continue
        df = pd.read_csv(file_path)
        if 'Date' not in df.columns or 'Close' not in df.columns:
            continue
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)  # 🟢 Fix timezone error
        prices.append(df)
    if prices:
        return pd.concat(prices).sort_values('Date').reset_index(drop=True)
    return pd.DataFrame()

def compute_return():
    df = get_all_nifty_prices()
    if df.empty:
        print(" No benchmark data found.")
        return

    try:
        buy_row = df[df['Date'] >= BUY_DATE].iloc[0]
        sell_row = df[df['Date'] <= SELL_DATE].iloc[-1]
    except IndexError:
        print(" Could not find valid buy or sell date in dataset.")
        return

    buy_price = buy_row['Close']
    sell_price = sell_row['Close']

    buy_date = buy_row['Date'].date()
    sell_date = sell_row['Date'].date()

    total_return = (sell_price - buy_price) / buy_price

    print(f" Buy on: {buy_date} at {buy_price:.2f}")
    print(f" Sell on: {sell_date} at {sell_price:.2f}")
    print(f"\n Total Return: {total_return:.2%}")

if __name__ == "__main__":
    compute_return()
