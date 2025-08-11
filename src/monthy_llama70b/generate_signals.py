# src/generate_signals.py
import os
import pandas as pd
from pathlib import Path
from groq import Groq

client = Groq(api_key="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")

# Updated paths
price_dir = Path("results/summaries_price")
funda_dir = Path("results/summaries_fundamentals")
news_dir = Path("results/summaries_news")
macro_dir = Path("results/summaries_macro")
signal_dir = Path("results/signals")
signal_dir.mkdir(parents=True, exist_ok=True)

def generate_prompt(symbol, month, price_text, funda_text, news_text, macro_text):
    return f"""
You are a financial analyst AI. Based on the following information for {symbol} in {month}, provide an investment recommendation.

### 1. Price Trends & Technicals:
{price_text or 'No price data available.'}

### 2. Fundamentals:
{funda_text or 'No fundamental data available.'}

### 3. News Sentiment:
{news_text or 'No relevant news found.'}

### 4. Macroeconomic Environment:
{macro_text or 'No macro summary available.'}

### Task:
Based on the above sections, recommend one of the following investment signals for {symbol} in {month}:
- BUY (strong conviction in price increase)
- HOLD (neutral outlook or uncertainty)
- SELL (likely to underperform or decrease in price)

Also provide a **3-line reasoning** for your signal that incorporates at least one factor (price, fundamentals, news, or macro).

Respond in the format:

Signal: <BUY/SELL/HOLD>  
Reason: <justification>
"""

def parse_response(text):
    lines = text.strip().split("\n")
    signal = "UNKNOWN"
    reason = "No reasoning provided."

    for line in lines:
        if line.upper().startswith("SIGNAL:"):
            signal = line.split(":", 1)[-1].strip().upper()
        elif line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[-1].strip()
    
    return signal, reason


def run_signal_agent(months=None):
    if months is None:
        months =[f"2025-{str(m).zfill(2)}" for m in range(1, 6)]

    tickers = [f.replace("_price.txt", "") for f in os.listdir(price_dir / months[0]) if f.endswith("_price.txt")]
    all_signals = []

    for month in months:
        print(f"[PROCESSING] {month}")
        out_dir = signal_dir / month
        out_dir.mkdir(parents=True, exist_ok=True)

        for ticker in tickers:
            try:
                price_path = price_dir / month / f"{ticker}_price.txt"
                funda_path = funda_dir / month / f"{ticker}.NS_fundamentals.txt"
                news_path = news_dir / month / f"{ticker}_news.txt"
                macro_path = macro_dir / month / "summary.txt"

                with open(price_path, "r", encoding="utf-8") as f1:
                    price_text = f1.read()
                with open(funda_path, "r", encoding="utf-8") as f2:
                    funda_text = f2.read()
                with open(news_path, "r", encoding="utf-8") as f3:
                    news_text = f3.read()
                with open(macro_path, "r", encoding="utf-8") as f4:
                    macro_text = f4.read()

                prompt = generate_prompt(ticker, month, price_text, funda_text, news_text, macro_text)

                completion = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )

                response_text = completion.choices[0].message.content.strip()
                signal, reason = parse_response(response_text)

                result_path = out_dir / f"{ticker}.txt"
                with open(result_path, "w", encoding="utf-8") as f:
                    f.write(f"Signal: {signal}\nReason: {reason}\n")

                all_signals.append((month, ticker, signal, reason))
                print(f"[ok] {ticker} - {signal} - {reason}")

            except Exception as e:
                print(f"[ERROR] {ticker} in {month}: {e}")
                continue

    df = pd.DataFrame(all_signals, columns=["Month", "Ticker", "Signal", "Reason"])
    df.to_csv("results/signals/signals.csv", index=False)
    print("[ok] Saved all signals to CSV.")

if __name__ == "__main__":
    run_signal_agent()
