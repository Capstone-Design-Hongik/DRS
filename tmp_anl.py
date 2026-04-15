import yfinance as yf
import pandas as pd

# 3월 27일까지의 차트 데이터
df = yf.Ticker('ANL').history(start='2025-01-01', end='2026-03-29')
close = df['Close']
high = df['High']

print(f'ANL 3월 27일 장마감 종가: ${close.iloc[-1]:.2f}\n')

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

# 실제 다음 1주일(4월 첫째 주) 동안 실제로 7% 올랐는지 정답 확인
next_week = yf.Ticker('ANL').history(start='2026-03-30', end='2026-04-04')
future_max = next_week['High'].max()
future_return = (future_max / close.iloc[-1] - 1) * 100

print(f'\n==================================================')
print(f'🎯 [블라인드 테스트 검증: ANL의 실제 4월 첫째 주 성적표]')
print(f'실제 다음 주 장중 최고 주가: ${future_max:.2f}')
print(f'실제 최고점 도달 수익률: {future_return:+.2f}%')
print(f'AI 예측 (7% 이상 승리) => {"✅ 실전 승리!!" if future_return >= 7 else "❌ 실패 (7% 도달 못함)"}')
print(f'==================================================')
