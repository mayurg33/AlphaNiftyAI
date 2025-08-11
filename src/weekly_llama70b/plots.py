import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# === CONFIG ===
strategy_files = {
    'MS-Top10-Cap-GPT': 'results/backtests/topn_cap_gpt_weekly.csv',
    'MS-Top10-LLM': 'results/backtests/topn_gpt.csv',
    'MS-L': 'results/backtests/buy_only_ms_l.csv',
    'MS-High-LLM': 'results/backtests/high_gpt.csv',
    'MS': 'results/backtests/ms.csv',
    'Nifty50 Index Fund': 'results/backtests/benchmark_weekly.csv',
    'NIFTY++': 'results/backtests/nifty_plus_simple.csv',
    'MS-Cap-Top10-LLM-NIFTY++': 'results/backtests/top10_cap_gpt_stoploss.csv',
    'MS-Cap-Top5-LLM-NIFTY++': 'results/backtests/top5_cap_gpt_stoploss.csv'
}

# === PLOTTING ===
plt.figure(figsize=(9, 5.5))

for strategy, filepath in strategy_files.items():
    df = pd.read_csv(filepath, parse_dates=['week'])
    df = df.sort_values('week')
    
    # Multiply cumulative return by 100000 to get dollar value
    investment_value = df['cumulative_strategy'] * 100000
    plt.plot(df['week'], investment_value, label=strategy)

# === FORMATTING ===
plt.title('Value of 1 Lakh Rs. Investment Over Time')
plt.ylabel('Value of 1 Lakh Rs. Investment')
plt.xlabel('Date')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()

# Improve x-axis date formatting
plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

# === SAVE / SHOW ===
plt.xticks(rotation=45)
plt.savefig("results/everything_plot.png", dpi=300)
plt.show()
