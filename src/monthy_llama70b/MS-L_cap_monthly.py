import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

SIGNAL_DIR = "results/signals"
PRICE_DIR = "data/prices"
MARKETCAP_PATH = "data/market_cap/marketcap.csv"
BENCHMARK = "^NSEI"
OUTPUT_CSV = "results/backtests/ms_l_cap_monthly.csv"
TOP_N = 10

def get_next_month(month_str):
    dt = datetime.strptime(month_str, "%Y-%m")
    return (dt + relativedelta(months=1)).strftime("%Y-%m")

def get_return(price_path):
    try:
        df = pd.read_csv(price_path)
        return (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
    except:
        return None

def get_top_n_by_marketcap(buy_tickers, month, marketcap_df):
    month_df = marketcap_df[marketcap_df["Month"] == month]
    sub_df = month_df[month_df["Ticker"].isin(buy_tickers)]
    return sub_df.sort_values("MarketCap", ascending=False).head(TOP_N)["Ticker"].tolist()

def calculate_drawdown(cum_returns):
    peak = cum_returns.cummax()
    dd = (cum_returns - peak) / peak
    return dd.min()

def backtest_ms_l_cap():
    marketcap_df = pd.read_csv(MARKETCAP_PATH)
    months = sorted([m for m in os.listdir(SIGNAL_DIR) if m <= "2025-05"])
    strategy_returns, benchmark_returns, valid_months = [], [], []
    portfolios = {}

    for month in months:
        signal_path = os.path.join(SIGNAL_DIR, month)
        next_month = get_next_month(month)
        price_path = os.path.join(PRICE_DIR, next_month)
        if not os.path.exists(price_path):
            print(f"[SKIP] Missing prices for {next_month}")
            continue

        buy_candidates = []

        for file in os.listdir(signal_path):
            if not file.endswith(".json"): continue
            ticker = file.replace(".json", "")
            try:
                with open(os.path.join(signal_path, file)) as f:
                    data = json.load(f)
                    if data.get("decision", "").strip().upper() == "BUY":
                        buy_candidates.append(ticker)
            except:
                continue

        if not buy_candidates:
            strategy_returns.append(0)
            benchmark_returns.append(0)
            valid_months.append(month)
            portfolios[month] = []
            continue

        top_n_tickers = get_top_n_by_marketcap(buy_candidates, month, marketcap_df)
        returns = []
        for ticker in top_n_tickers:
            price_file = os.path.join(price_path, f"{ticker}.csv")
            ret = get_return(price_file)
            if ret is not None:
                returns.append(ret)

        avg_return = np.mean(returns) if returns else 0
        strategy_returns.append(avg_return)

        bench_file = os.path.join(price_path, f"{BENCHMARK}.csv")
        bench_return = get_return(bench_file) or 0
        benchmark_returns.append(bench_return)

        valid_months.append(month)
        portfolios[month] = top_n_tickers

        print(f"[{month}] Strategy: {avg_return:.2%} | Benchmark: {bench_return:.2%} | Portfolio: {top_n_tickers}")

    df = pd.DataFrame({
        "month": valid_months,
        "strategy_return": strategy_returns,
        "benchmark_return": benchmark_returns
    })

    df["excess_return"] = df["strategy_return"] - df["benchmark_return"]
    df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
    df["cumulative_benchmark"] = (1 + df["benchmark_return"]).cumprod()

    final_return = df["cumulative_strategy"].iloc[-1] - 1
    benchmark_final = df["cumulative_benchmark"].iloc[-1] - 1
    volatility = np.std(df["strategy_return"])* np.sqrt(15)
    sharpe = (final_return-0.06)/volatility
    sortino = (final_return-0.06) / ((np.std([r for r in df["strategy_return"] if r < 0]))*np.sqrt(15))
    max_dd = calculate_drawdown(df["cumulative_strategy"])
    winrate = np.mean(df["strategy_return"] > df["benchmark_return"])

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    with open(OUTPUT_CSV.replace(".csv", "_portfolio.json"), "w") as f:
        json.dump(portfolios, f, indent=2)

    print("\n MS-L-Cap Backtest Complete.")
    print(df.tail())
    print(f"\n Final Strategy Return: {final_return:.2%}")
    print(f" Final Benchmark Return: {benchmark_final:.2%}")
    print(f" Volatility: {volatility:.2%}")
    print(f" Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {max_dd:.2%}")
    print(f" Win Rate: {winrate:.2%}")

if __name__ == "__main__":
    backtest_ms_l_cap()
