# src/summarize_fundamentals.py
import os
import json
from groq import Groq

FUNDAMENTALS_DIR = "data/fundamentals"
SUMMARY_DIR = "results/summaries_fundamentals"
os.makedirs(SUMMARY_DIR, exist_ok=True)

client = Groq(api_key=os.getenv("GROQ_KEYS"))

def extract_summary_text(fund):
    m = fund.get("metrics", {})
    fields = [
        f"Company: {m.get('companyName')}",
        f"Sector: {m.get('sector')}",
        f"Industry: {m.get('industry')}",
        f"Market Cap: {m.get('marketCap')}",
        f"Trailing PE: {m.get('trailingPE')}",
        f"Forward PE: {m.get('forwardPE')}",
        f"ROE: {m.get('returnOnEquity')}",
        f"Profit Margin: {m.get('profitMargins')}",
        f"Revenue Growth: {m.get('revenueGrowth')}",
        f"Earnings Growth: {m.get('earningsGrowth')}",
        f"Debt/Equity: {m.get('debtToEquity')}"
    ]
    return "\n".join(fields)

def summarize_fundamentals(month_str):
    for file in os.listdir(FUNDAMENTALS_DIR):
        if not file.endswith(f"_{month_str}.json"):
            continue
        try:
            with open(os.path.join(FUNDAMENTALS_DIR, file)) as f:
                data = json.load(f)
            text = extract_summary_text(data)
            symbol = data['metrics'].get("symbol", file.split("_")[0])
            prompt = f"You are a financial analyst. Based on the following data, would you recommend BUY, HOLD, or SELL for the stock? Justify briefly.\n\n{text}"
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            summary = response.choices[0].message.content.strip()
            with open(os.path.join(SUMMARY_DIR, f"{symbol}_fundamentals.txt"), "w") as out:
                out.write(summary)
            print(f"[✓] Summarized fundamentals for {symbol}")
        except Exception as e:
            print(f"[ERROR] Summarizing {file}: {e}")
