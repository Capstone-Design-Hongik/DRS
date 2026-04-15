import os
import sys
import yfinance as yf
import pandas as pd
import numpy as np
from tqdm import tqdm
import warnings
from pycaret.classification import load_model, predict_model

warnings.simplefilter(action='ignore')

TARGET_DATE = "2026-04-03"  # 사용자가 요청한 예측 기준일
MODEL_FILE = os.path.join(os.path.dirname(__file__), 'weekly_momentum_model')

def get_all_tickers():
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'ma20.parquet')
        df = pd.read_parquet(data_path)
        if 'ticker' in df.columns:
            return df['ticker'].unique().tolist()
        else:
            return [str(c) for c in df.columns if c != 'Date']
    except Exception as e:
        print(f"티커 목록 가져오기 실패: {e}")
        sys.exit(1)

def main():
    print("="*60)
    print(f"🔮 AI 실시간 추론기: {TARGET_DATE} 종가 기준 다음 주 7% 상승 예측")
    print("="*60)
    
    try:
        model = load_model(MODEL_FILE)
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return

    tickers = get_all_tickers()[:3000]
    print(f"✅ 추출 대상 종목: {len(tickers)}개")
    
    all_rows = []
    chunk_size = 500
    
    for i in range(0, len(tickers), chunk_size):
        chunk_tickers = tickers[i:min(i+chunk_size, len(tickers))]
        print(f"📥 데이터 실시간 패치 중... ({(i//chunk_size)+1} / {(len(tickers)//chunk_size)+1} 묶음)")
        
        # 기준일을 계산해야 하므로 2년치(여유있게) 다운로드
        data = yf.download(chunk_tickers, period="2y", interval="1d", progress=False)
        if data.empty: continue
            
        for t in tqdm(chunk_tickers, desc="AI 지표 연산 중", leave=False):
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    try:
                        df = data.xs(t, level=1, axis=1).copy()
                    except KeyError: continue
                else:
                    df = data.copy() if len(chunk_tickers) == 1 else pd.DataFrame()
                    
                df = df.dropna(subset=['Close'])
                if len(df) < 100: continue
                
                # --- 지표 계산 (과거부터 쭉) ---
                close = df['Close']
                vol = df['Volume']
                
                df['ROC_5'] = close.pct_change(5)
                df['ROC_20'] = close.pct_change(20)
                df['ROC_60'] = close.pct_change(60)
                
                sma10 = close.rolling(10).mean()
                sma20 = close.rolling(20).mean()
                sma50 = close.rolling(50).mean()
                
                df['Dist_SMA10'] = (close - sma10) / sma10
                df['Dist_SMA20'] = (close - sma20) / sma20
                df['Dist_SMA50'] = (close - sma50) / sma50
                
                vol_sma5 = vol.rolling(5).mean()
                vol_sma50 = vol.rolling(50).mean()
                df['Vol_Ratio'] = vol_sma5 / vol_sma50.replace(0, np.nan)
                
                high_252 = df['High'].rolling(252).max()
                df['Dist_High52'] = (close - high_252) / high_252
                
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss.replace(0, np.nan)
                df['RSI_14'] = 100 - (100 / (1 + rs))
                
                df['Ticker'] = t
                df['Date'] = df.index
                
                # --- 타겟 날짜(4월 3일) 시점까지만 데이터를 자름 ---
                sub_df = df.loc[:TARGET_DATE].copy()
                if sub_df.empty: continue
                
                # 4월 3일 혹은 그 이전 가장 최신 영업일의 데이터 1줄 추출
                last_row = sub_df.iloc[-1:].copy()
                
                features = [
                    'Ticker', 'Date', 
                    'ROC_5', 'ROC_20', 'ROC_60', 
                    'Dist_SMA10', 'Dist_SMA20', 'Dist_SMA50', 'Dist_High52',
                    'Vol_Ratio', 'RSI_14'
                ]
                all_rows.append(last_row[features])
            except Exception:
                continue

    if not all_rows:
        print("❌ 유효한 데이터를 추출하지 못했습니다.")
        return
        
    final_df = pd.concat(all_rows, ignore_index=True)
    features_only = final_df.drop(columns=['Ticker', 'Date'], errors='ignore')
    
    print("\n🧠 AI 예측 엔진 가동 중...")
    predictions = predict_model(model, data=features_only, raw_score=True)
    
    prob_col = 'prediction_score_1'
    if prob_col not in predictions.columns:
        prob_col = 'prediction_score'
        
    predictions['Ticker'] = final_df['Ticker']
    
    bulls = predictions.sort_values(by=prob_col, ascending=False)
    top_10 = bulls.head(10)
    
    print(f"\n🏆 [기준일: {TARGET_DATE}] AI 추천 다음 주 상승 유망 종목 TOP 10 🏆")
    print("-" * 60)
    for i, (_, row) in enumerate(top_10.iterrows(), 1):
        prob = row[prob_col] * 100
        print(f"{i:2d}위. {row['Ticker']:<5s} (상승 확률: {prob:.1f}%)")
    print("-" * 60)

if __name__ == "__main__":
    main()
