import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from groq import Groq
from dateutil.relativedelta import relativedelta

client = Groq(api_key="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")

def calc_stats(df):
    df = df.copy()
    df['Return'] = df['Close'].pct_change()
    returns = df['Return'].dropna()
    volatility = returns.std() * np.sqrt(252)
    sharpe = returns.mean() / (returns.std() + 1e-9) * np.sqrt(252)

    cummax = df['Close'].cummax()
    drawdown = (df['Close'] / cummax - 1).min()

    return volatility, sharpe, drawdown

def compute_return(prices, end_date, months):
    start = pd.to_datetime(end_date) - relativedelta(months=months)
    prices = prices.copy()
    prices.index = pd.to_datetime(prices.index)
    df = prices[(prices.index >= start) & (prices.index <= end_date)]
    if len(df) >= 2:
        return ((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100
    return np.nan

def summarize_all_price_months():
    with open("data/peer_map.json") as f:
        peer_map = json.load(f)

    base_path = "data/prices"
    months = sorted([m for m in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, m))])

    for month in months:
        print(f"\n[PROCESSING] Month: {month}")
        month_path = os.path.join(base_path, month)
        symbols = [f.replace(".csv", "") for f in os.listdir(month_path) if f.endswith(".csv")]

        os.makedirs(f"results/summaries_price/{month}", exist_ok=True)

        for symbol in symbols:
            try:
                df = pd.read_csv(f"{month_path}/{symbol}.csv", index_col="Date", parse_dates=True)
                if df.empty or len(df) < 5:
                    print(f"[SKIP] {symbol} - Not enough data")
                    continue

                # Basic Metrics
                start_price = df["Close"].iloc[0]
                end_price = df["Close"].iloc[-1]
                volatility, sharpe, max_dd = calc_stats(df)
                end_date = df.index[-1]

                # Historical return
                df_all = pd.read_csv(f"data/prices/{month}/{symbol}.csv", index_col="Date", parse_dates=True)
                r12m = compute_return(df_all, end_date, 12)
                r6m = compute_return(df_all, end_date, 6)
                r3m = compute_return(df_all, end_date, 3)

                # Peer Correlation
                peers = peer_map.get(symbol, [])
                peer_corrs = []
                for peer in peers:
                    peer_file = f"{month_path}/{peer}.csv"
                    if os.path.exists(peer_file):
                        pdf = pd.read_csv(peer_file, index_col="Date", parse_dates=True)
                        merged = df["Close"].pct_change().dropna().to_frame("r1").join(
                            pdf["Close"].pct_change().dropna().to_frame("r2"), how="inner"
                        )
                        if not merged.empty:
                            corr = merged["r1"].corr(merged["r2"])
                            peer_corrs.append((peer, round(corr, 4)))
                avg_corr = round(np.mean([c[1] for c in peer_corrs]), 4) if peer_corrs else "N/A"

                # Format prompt
                summary_text = f"""
Symbol: {symbol}
Month: {month}
Start Price: ₹{start_price:.2f}
End Price: ₹{end_price:.2f}
12M Return: {r12m:.2f}%
6M Return: {r6m:.2f}%
3M Return: {r3m:.2f}%
Volatility: {volatility:.3f}
Sharpe Ratio: {sharpe:.3f}
Max Drawdown: {max_dd:.3f}
"""

                for peer, corr in peer_corrs:
                    summary_text += f"Peer Correlation ({peer}): {corr}\n"
                summary_text += f"Average Peer Correlation: {avg_corr}\n"
                summary_text += "\nGenerate a short summary and suggest whether to BUY, SELL, or HOLD."

                # LLM Completion
                chat_completion = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[
                        {"role": "system", "content": "You are a financial analyst."},
                        {"role": "user", "content": summary_text.strip()}
                    ],
                    temperature=0.7
                )

                output = chat_completion.choices[0].message.content.strip()
                out_path = f"results/summaries_price/{month}/{symbol}_price.txt"
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(summary_text.strip())
                    f.write("\n\n--- LLM Output ---\n")
                    f.write(output)
                print(f"[OK] {symbol} - Summary written")

            except Exception as e:
                print(f"[ERROR] {symbol}: {e}")

if __name__ == "__main__":
    summarize_all_price_months()

