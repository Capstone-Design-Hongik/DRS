#!/usr/bin/env python3
import os
import sys
import yfinance as yf
import pandas as pd
import numpy as np
from tqdm import tqdm
import warnings

# pandas의 SettingWithCopy 버그 경고 무시
warnings.simplefilter(action='ignore', category=FutureWarning)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def get_all_tickers():
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'ma20.parquet')
        df = pd.read_parquet(data_path)
        # Parquet 파일이 ticker, vector 포맷인지 혹은 컬럼명 포맷인지 판별
        if 'ticker' in df.columns:
            return df['ticker'].unique().tolist()
        else:
            return [str(c) for c in df.columns if c != 'Date']
    except Exception as e:
        print(f"티커 목록 가져오기 실패: {e}")
        sys.exit(1)

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'momentum_training_data.parquet')

# --- 하이퍼파라미터 설정 ---
TARGET_RETURN = 0.07  # "다음 주에 7% 오르는지" 판별
NUM_TICKERS = 3000    # 상위 3,000개 주식만 연산 (시가총액/거래량 상위 우선)
PERIOD = "2y"         # 과거 2년치 데이터 (약 100주간의 금요일 생성)

def generate_data():
    print(f"🚀 데이터를 다운로드하고 학습용 [기출문제집]을 조립합니다...")
    print(f"   => 목표: 매주 금요일 종가 기준, 다음주 내내 누적 +7% 오르는 패턴 찾기")
    
    tickers = get_all_tickers()[:NUM_TICKERS]
    print(f"✅ 추출 대상 종목: {len(tickers)}개")
    
    all_chunks = []
    
    # 병렬 다운로드 시 yfinance 에러가 종종 나므로, chunk로 쪼개어 pandas-datareader처럼 한꺼번에 다운로드 후 분리
    chunk_size = 500
    for i in range(0, len(tickers), chunk_size):
        chunk_tickers = tickers[i:min(i+chunk_size, len(tickers))]
        print(f"📥 다운로드 중... ({(i//chunk_size)+1} / {(len(tickers)//chunk_size)+1} 묶음)")
        
        # progress=False로 두어 출력 줄임, multi-level columns 형태로 리턴됨
        data = yf.download(chunk_tickers, period=PERIOD, interval="1d", progress=False)
        
        if data.empty:
            continue
            
        for t in tqdm(chunk_tickers, desc="데이터 가공 중", leave=False):
            try:
                # yfinance >= 0.2 구문 처리 (Multi-Index Column 분리)
                if isinstance(data.columns, pd.MultiIndex):
                    try:
                        df = data.xs(t, level=1, axis=1).copy()
                    except KeyError:
                        continue
                else:
                    df = data.copy() if len(chunk_tickers) == 1 else pd.DataFrame()
                    
                df = df.dropna(subset=['Close'])
                if len(df) < 100: continue  # 상장한 지 얼마 안 된 종목 제외
                
                close = df['Close']
                vol = df['Volume']
                
                # --- 1단계: 일봉(Daily) 기준 피쳐 생성 ---
                df['ROC_5'] = close.pct_change(5)
                df['ROC_20'] = close.pct_change(20)
                df['ROC_60'] = close.pct_change(60)
                
                sma10 = close.rolling(10).mean()
                sma20 = close.rolling(20).mean()
                sma50 = close.rolling(50).mean()
                
                df['Dist_SMA10'] = (close - sma10) / sma10
                df['Dist_SMA20'] = (close - sma20) / sma20
                df['Dist_SMA50'] = (close - sma50) / sma50
                
                # 거래량 비율 (최근 5일평균 / 장기 50일평균)
                vol_sma5 = vol.rolling(5).mean()
                vol_sma50 = vol.rolling(50).mean()
                df['Vol_Ratio'] = vol_sma5 / vol_sma50.replace(0, np.nan)
                
                # 최근 52주 최고가 대비 하락률 (고점 대비 얼마나 열려있는가)
                high_252 = df['High'].rolling(252).max()
                df['Dist_High52'] = (close - high_252) / high_252
                
                # RSI_14
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss.replace(0, np.nan)
                df['RSI_14'] = 100 - (100 / (1 + rs))
                
                # --- 2단계: 미래 5영업일(다음 주 금요일) 수익률 및 Target 정답지 만들기 ---
                df['Future_Return'] = close.shift(-5) / close - 1
                df['Target'] = (df['Future_Return'] >= TARGET_RETURN).astype(int)
                
                df['Ticker'] = t
                df['Date'] = df.index
                
                # --- 3단계: 매주 "금요일" 데이터만 핀포인트 추출! ---
                # 주말 추천 모델이므로 월~목 장중 데이터는 정답지에서 제외시켜 과적합 방지
                friday_df = df[df.index.dayofweek == 4].copy()
                
                # 과거 데이터가 충분하지 않아 NaN인 앞부분, 그리고 아직 5일이 지나지 않아 Future_Return이 없는 맨 끝부분 날림
                friday_df = friday_df.dropna()
                
                if not friday_df.empty:
                    # 필요한 특성들만 모아서 저장
                    features = [
                        'Ticker', 'Date', 
                        'ROC_5', 'ROC_20', 'ROC_60', 
                        'Dist_SMA10', 'Dist_SMA20', 'Dist_SMA50', 'Dist_High52',
                        'Vol_Ratio', 'RSI_14', 
                        'Future_Return', 'Target'
                    ]
                    all_chunks.append(friday_df[features])
            except Exception as e:
                # 상장 폐지나 데이터 손상 건너뛰기
                continue

    if all_chunks:
        final_df = pd.concat(all_chunks, ignore_index=True)
        print("\n" + "=" * 50)
        print(f"📊 총 학습용 기출문제(Rows): {len(final_df):,} 장")
        print(f"   => 이 중 다음 주 7% 상승 성공(Target=1) 비율: {(final_df['Target'].mean() * 100):.1f}%")
        print("=" * 50)
        
        final_df.to_parquet(OUTPUT_FILE, index=False)
        print(f"💾 데이터 추출 완료! Parquet 파일 저장: {OUTPUT_FILE}")
    else:
        print("❌ 유효한 데이터를 추출하지 못했습니다.")

if __name__ == "__main__":
    generate_data()
