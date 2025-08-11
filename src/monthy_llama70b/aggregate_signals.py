# src/aggregate_signals.py
import os
import pandas as pd

PRICE_DIR = "results/signals"
FUND_DIR = "results/summaries_fundamentals"
AGG_DIR = "results/aggregated_signals"
os.makedirs(AGG_DIR, exist_ok=True)

def extract_decision(text):
    text = text.upper()
    if "BUY" in text:
        return "BUY"
    elif "SELL" in text:
        return "SELL"
    else:
        return "HOLD"

def aggregate_signals(month_str):
    price_signal_path = os.path.join(PRICE_DIR, f"signals_{month_str}.csv")
    if not os.path.exists(price_signal_path):
        print(f"[ERROR] Missing price signal file: {price_signal_path}")
        return

    price_df = pd.read_csv(price_signal_path)
    price_df = price_df.set_index("Symbol")

    aggregated_data = []

    for symbol in price_df.index:
        price_signal = price_df.loc[symbol, "Signal"]

        fund_file = os.path.join(FUND_DIR, f"{symbol}_fundamentals.txt")
        if os.path.exists(fund_file):
            with open(fund_file, "r") as f:
                fund_summary = f.read()
            fund_signal = extract_decision(fund_summary)
        else:
            fund_signal = "HOLD"
            fund_summary = "N/A"

        # Simple logic: Final = BUY only if both say BUY, else HOLD unless one says SELL
        if price_signal == "BUY" and fund_signal == "BUY":
            final_signal = "BUY"
        elif price_signal == "SELL" or fund_signal == "SELL":
            final_signal = "SELL"
        else:
            final_signal = "HOLD"

        aggregated_data.append([symbol, price_signal, fund_signal, final_signal])

    df = pd.DataFrame(aggregated_data, columns=["Symbol", "PriceSignal", "FundSignal", "FinalSignal"])
    df.to_csv(os.path.join(AGG_DIR, f"aggregated_signals_{month_str}.csv"), index=False)
    print(f"[✓] Aggregated signals saved: aggregated_signals_{month_str}.csv")
