# src/bootstrap.py
import numpy as np
import pandas as pd
import os
import random

def run_bootstrap_test(n_trials=1000):
    print("[Bootstrap] Starting evaluation...")
    signal_file = "results/signals/signals_2025-06.csv"
    if not os.path.exists(signal_file):
        print("[ERROR] Signal file not found.")
        return

    df = pd.read_csv(signal_file)
    df = df.replace({"BUY": 1, "SELL": -1, "HOLD": 0})

    symbols = df["Symbol"].tolist()
    signals = dict(zip(df["Symbol"], df["Signal"]))

    price_data = {}
    for sym in symbols:
        try:
            price_data[sym] = pd.read_csv(f"data/prices/{sym}.NS.csv", index_col=0, parse_dates=True)["Close"]
        except:
            continue

    prices = pd.DataFrame(price_data).dropna(axis=1)
    if prices.empty:
        print("[ERROR] No price data available.")
        return

    real_returns = []
    for sym in prices.columns:
        pct_return = prices[sym].pct_change().dropna()
        monthly_return = pct_return.mean()
        weighted = monthly_return * signals.get(sym, 0)
        real_returns.append(weighted)

    real_score = np.sum(real_returns)

    # Simulate random strategies
    random_scores = []
    for _ in range(n_trials):
        rand_signals = np.random.choice([-1, 0, 1], size=len(prices.columns))
        rand_score = 0
        for i, sym in enumerate(prices.columns):
            pct_return = prices[sym].pct_change().dropna()
            monthly_return = pct_return.mean()
            rand_score += monthly_return * rand_signals[i]
        random_scores.append(rand_score)

    # Percentile comparison
    percentile = sum(1 for score in random_scores if score < real_score) / n_trials * 100

    os.makedirs("results/bootstrap", exist_ok=True)
    with open("results/bootstrap/evaluation.txt", "w") as f:
        f.write(f"Mean Real Score: {real_score:.6f}\n")
        f.write(f"Percentile vs random: {percentile:.2f}%\n")

    print(f"[✓] Bootstrapping complete. Your model beats {percentile:.2f}% of random portfolios.")
