import yfinance as yf
import pandas as pd
df = yf.Ticker('LTRN').history(start='2025-01-01', end='2026-03-29')
close = df['Close']
high = df['High']
print(f'LTRN 3월 27일 종가: ${close.iloc[-1]:.2f}')
dist_high52 = (close.iloc[-1] - high.rolling(252).max().iloc[-1]) / high.rolling(252).max().iloc[-1]
roc_60 = close.pct_change(60).iloc[-1]
dist_sma50 = (close.iloc[-1] - close.rolling(50).mean().iloc[-1]) / close.rolling(50).mean().iloc[-1]
dist_sma20 = (close.iloc[-1] - close.rolling(20).mean().iloc[-1]) / close.rolling(20).mean().iloc[-1]
delta = close.diff()
gain = delta.where(delta > 0, 0).rolling(14).mean().iloc[-1]
loss = -delta.where(delta < 0, 0).rolling(14).mean().iloc[-1]
rsi = 100 - (100 / (1 + gain/loss))

print(f'1. Dist_High52 (중요도 1위): {dist_high52*100:.2f}%')
print(f'2. ROC_60 (중요도 2위): {roc_60*100:.2f}%')
print(f'3. Dist_SMA50 (중요도 3위): {dist_sma50*100:.2f}%')
print(f'4. Dist_SMA20 (중요도 4위): {dist_sma20*100:.2f}%')
print(f'5. RSI_14 (중요도 7위): {rsi:.2f}')
