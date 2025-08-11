# src/weekly_llama70b/generate_price_summaries.py
import time
import os
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from groq_manager import GroqAPIManager

# === Paths ===
price_base = Path("data/prices/weekly")
output_base = Path("results/summaries_price/weekly")
output_base.mkdir(parents=True, exist_ok=True)

# === Load Peer Map ===
with open("data/peer_map.json", "r") as f:
    peer_map = json.load(f)

# === Init GROQ Manager ===
groq = GroqAPIManager()

# === Date Folders ===
weekly_folders = sorted([d for d in price_base.iterdir() if d.is_dir()])

# === Helper: Compute metrics from price data ===
def compute_price_metrics(df):
    df = df.sort_index()
    returns = df["Close"].pct_change().dropna()
    volatility = returns.std() * (252 ** 0.5) * 100  # Annualized Volatility in %
    sharpe = returns.mean() / returns.std() if returns.std() != 0 else 0
    drawdown = ((df["Close"] / df["Close"].cummax()) - 1).min() * 100
    total_return = ((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100
    return {
        "weekly_return": round(total_return, 2),
        "volatility": round(volatility, 2),
        "sharpe": round(sharpe, 2),
        "max_drawdown": round(drawdown, 2),
    }

# === Helper: Generate Prompt ===
def build_prompt(ticker, week, self_metrics, peer_metrics):
    peer_summary = "\n".join([
        f"- {p['ticker']}: Return={p['weekly_return']}%, Volatility={p['volatility']}%, Sharpe={p['sharpe']:.2f}"
        for p in peer_metrics
    ]) if peer_metrics else "No peer data available."

    prompt = f"""
You are a financial analyst AI. Analyze the weekly performance of stock **{ticker}** for the week starting {week} based on the following metrics:

### This stock's metrics:
- Weekly Return: {self_metrics['weekly_return']}%
- Volatility: {self_metrics['volatility']}%
- Sharpe Ratio: {self_metrics['sharpe']:.2f}
- Max Drawdown: {self_metrics['max_drawdown']}%

### Peer Comparison:
{peer_summary}
### Task:
Write a concise summary (3-5 lines) about the stock's weekly performance and volatility. Also briefly mention whether it outperformed or underperformed peers and how risky the stock was this week.
End the response with:
[Volatility: {self_metrics['volatility']}%]
"""
    return prompt.strip()

# === MAIN GENERATION LOOP ===
def generate_all_summaries():
    for week_dir in tqdm(weekly_folders, desc="Processing Weeks"):
        week = week_dir.name
        out_dir = output_base / week
        out_dir.mkdir(parents=True, exist_ok=True)

        for file in week_dir.glob("*.csv"):
            ticker = file.stem

            # Read price CSV
            df = pd.read_csv(file, index_col="Date", parse_dates=True)
            if len(df) < 3:  # Too little data
                continue

            # Compute this stock's metrics
            metrics = compute_price_metrics(df)

            # Get peers
            peers = peer_map.get(ticker, [])
            peer_metrics = []
            for peer in peers:
                peer_file = week_dir / f"{peer}.csv"
                if peer_file.exists():
                    df_peer = pd.read_csv(peer_file, index_col="Date", parse_dates=True)
                    if len(df_peer) >= 3:
                        peer_metrics.append({**compute_price_metrics(df_peer), "ticker": peer})

            # Build prompt
            prompt = build_prompt(ticker, week, metrics, peer_metrics)

            # Query LLM
            try:
                response = groq.generate(prompt)
                output_path = out_dir / f"{ticker}.txt"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(response)
                print(f"[ok] {ticker} - {week}")
                time.sleep(3)
            except Exception as e:
                print(f"[ERROR] {ticker} - {week}: {e}")

if __name__ == "__main__":
    generate_all_summaries()
