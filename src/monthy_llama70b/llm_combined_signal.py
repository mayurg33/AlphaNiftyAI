# src/llm_combined_signal.py
import os
import pandas as pd
from groq import Groq

BASE_PRICE_SUMMARY_DIR = "results/summaries"
BASE_FUND_SUMMARY_DIR = "results/summaries_fundamentals"
OUT_BASE_PATH = "results/aggregated_signals"

client = Groq(api_key=os.getenv("GROQ_KEYS"))

def get_summary_text(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read().strip()
    return "N/A"

def get_llm_signal(symbol, price_text, fund_text):
    prompt = f"""
You are a senior investment analyst. Read the following:

---
PRICE TREND SUMMARY for {symbol}:
{price_text}

---
FUNDAMENTAL SUMMARY for {symbol}:
{fund_text}

Based on both the price trend and fundamental performance, should we BUY, HOLD, or SELL the stock? Respond in this exact format:

Final Decision: <BUY/SELL/HOLD>
Reason: <short 1-2 sentence explanation>
"""
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        return f"[ERROR] {e}"

def run_llm_combined_signals_for_month(month_str):
    price_dir = os.path.join(BASE_PRICE_SUMMARY_DIR, month_str)
    fund_dir = os.path.join(BASE_FUND_SUMMARY_DIR, month_str)
    out_path = os.path.join(OUT_BASE_PATH, f"llm_final_signals_{month_str}.csv")

    symbols = [f.replace("_price.txt", "") for f in os.listdir(price_dir) if f.endswith("_price.txt")]
    rows = []
    for symbol in symbols:
        price_path = os.path.join(price_dir, f"{symbol}_price.txt")
        fund_path = os.path.join(fund_dir, f"{symbol}.NS_fundamentals.txt")

        price_summary = get_summary_text(price_path)
        fund_summary = get_summary_text(fund_path)

        decision = get_llm_signal(symbol, price_summary, fund_summary)
        rows.append([symbol, decision])
        print(f"[✓] Combined decision for {symbol} - {month_str}")

    df = pd.DataFrame(rows, columns=["Symbol", "LLM_Final_Decision"])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[✓] Final combined LLM signals saved to {out_path}")

def run_llm_combined_signals_all_months():
    from datetime import datetime, timedelta
    start_date = datetime(2023, 3, 1)
    months = [(start_date + timedelta(days=30 * i)).strftime("%Y-%m") for i in range(15)]
    for month in months:
        run_llm_combined_signals_for_month(month)

# To run for a single month:
# run_llm_combined_signals_for_month("2025-06")

# To run for all 15 months:
# run_llm_combined_signals_all_months()
