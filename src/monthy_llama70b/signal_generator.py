import os, csv

def generate_signals(month_str):
    path = f"results/summaries/{month_str}"
    signals = []
    for fname in os.listdir(path):
        sym = fname.split("_")[0]
        with open(os.path.join(path, fname)) as f:
            explanation = f.read()
            decision = "HOLD"
            if "BUY" in explanation.upper(): decision = "BUY"
            elif "SELL" in explanation.upper(): decision = "SELL"
            signals.append([sym, month_str, decision, explanation])
    os.makedirs("results/signals", exist_ok=True)
    with open(f"results/signals/signals_{month_str}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Symbol", "Month", "Signal", "Explanation"])
        writer.writerows(signals)
    print(f"[✓] Signals saved for {month_str}")
