import os
import pandas as pd

def preprocess_news(file_path, output_dir="C:/Users/mayur/MarketSenseAI/data/news"):
    df = pd.read_csv(file_path)
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    df["Month"] = df["Date"].dt.strftime("%Y-%m")

    for (month, symbol), group in df.groupby(["Month", "Symbol"]):
        out_dir = os.path.join(output_dir, month)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{symbol}.csv")
        group.to_csv(out_path, index=False)
        print(f"[OK] Saved: {out_path}")  # replaced ✓ with [OK]

# Example usage
preprocess_news("C:/Users/mayur/MarketSenseAI/src/all_nifty_news_updated.csv")
