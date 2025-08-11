import pandas as pd
import numpy as np

# Load your monthly returns
df = pd.read_csv("results/portfolio/monthly_returns_vs_benchmark.csv")

# Drop months with missing data
df = df.dropna(subset=["Strategy Return (%)"])

# Convert percentage to decimal returns
returns = df["Strategy Return (%)"] / 100
returns2=df["Benchmark Return (%)"] /100

# Compute cumulative returns
cumulative = (1 + returns).cumprod()
cumulative2 = (1 + returns2).cumprod()

# Total return (%)
total_return = (cumulative.iloc[-1] - 1) * 100
total_return_nse = (cumulative2.iloc[-1] - 1) * 100
# Annualized volatility (%)
volatility = returns.std() * np.sqrt(12) * 100

# Sharpe Ratio (assuming risk-free rate = 0)
sharpe = returns.mean() / returns.std()

# Sortino Ratio (downside std dev)
negative_returns = returns[returns < 0]
sortino = returns.mean() / negative_returns.std() if len(negative_returns) > 0 else np.nan

# Win Rate (%)
win_rate = (returns > 0).sum() / len(returns) * 100

# Max Drawdown (%)
rolling_max = cumulative.cummax()
drawdown = (cumulative - rolling_max) / rolling_max
max_dd = drawdown.min() * 100

# Print results
print(cumulative)
print(f" Total Return (%):     {total_return:.2f}")
print(f" Total Return benchmark(%):     {total_return_nse:.2f}")
print(f" Sharpe Ratio:         {sharpe:.2f}")
print(f" Sortino Ratio:        {sortino:.2f}")
print(f" Volatility (%):       {volatility:.2f}")
print(f" Win Rate (%):         {win_rate:.2f}")
print(f" Max Drawdown (%):     {max_dd:.2f}")
