# src/summarize_news_loop.py
import os
import pandas as pd
from groq import Groq
from datetime import datetime, timedelta

NEWS_BASE_DIR = "data/news"
SUMMARY_BASE_DIR = "results/summaries_news"
os.makedirs(SUMMARY_BASE_DIR, exist_ok=True)

client = Groq(api_key="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")

def summarize_news_for_month(month_str):
    month_dir = os.path.join(NEWS_BASE_DIR, month_str)
    output_dir = os.path.join(SUMMARY_BASE_DIR, month_str)
    os.makedirs(output_dir, exist_ok=True)

    for file in os.listdir(month_dir):
        if not file.endswith(".csv"):
            continue
        symbol = file.replace(".csv", "")
        df = pd.read_csv(os.path.join(month_dir, file))

        if df.empty:
            print(f"[SKIP] No news for {symbol} in {month_str}")
            continue

        # Combine top 10 headlines with sources
        top_news = df.head(10).apply(lambda row: f"- {row['Heading']} ({row['Source']})", axis=1)
        text = "\n".join(top_news)

        prompt = f"""
You are a financial analyst. Given these recent headlines about {symbol}, summarize the overall news sentiment and suggest whether to BUY, SELL or HOLD this stock.

{text}

Respond in the format:
Final Decision: <BUY/SELL/HOLD>
Reason: <short 1-2 sentence justification>
"""
        try:
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content.strip()
            out_path = os.path.join(output_dir, f"{symbol}_news.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[OK] News summarized for {symbol} - {month_str}")
        except Exception as e:
            print(f"[ERROR] {symbol} - {e}")

def summarize_news_all_months():
    start_date = datetime(2024, 12, 1)
    months = [(start_date + timedelta(days=30 * i)).strftime("%Y-%m") for i in range(15)]
    for month in months:
        summarize_news_for_month(month)

# To run:
summarize_news_all_months()
