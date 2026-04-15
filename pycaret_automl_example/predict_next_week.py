import pandas as pd
from pycaret.classification import load_model, predict_model
import os

MODEL_FILE = 'weekly_momentum_model'
DATA_FILE = 'momentum_training_data.parquet'

def main():
    print("="*60)
    print("🔮 XGBoost AI 모델 기반: 다음 주 상승 유망 종목 TOP 10 예측")
    print("="*60)
    
    # 1. 모델 로드
    model_path = os.path.join(os.path.dirname(__file__), MODEL_FILE)
    try:
        model = load_model(model_path)
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return
        
    # 2. 데이터 로드
    data_path = os.path.join(os.path.dirname(__file__), DATA_FILE)
    if not os.path.exists(data_path):
        print("❌ 데이터 파일이 없습니다.")
        return
    df = pd.read_parquet(data_path)
    
    # 3. 최신 데이터(가장 최근 날짜)만 필터링
    latest_date = df['Date'].max()
    latest_df = df[df['Date'] == latest_date].copy()
    
    print(f"📅 기준일 (최근 금요일): {latest_date.date()}")
    print(f"🔍 전체 대상 종목 수: {len(latest_df):,} 개")
    
    # 4. 예측 수행
    # 정답(Target)은 지우고 문제(Features)만 AI에게 풀게 함
    features_only = latest_df.drop(columns=['Target', 'Future_Return'], errors='ignore')
    
    # 예측 수행!
    predictions = predict_model(model, data=features_only, raw_score=True)
    
    # PyCaret 3.x에서는 확률이 'prediction_score_1' (Target이 1일 확률) 형식으로 나옵니다.
    prob_col = 'prediction_score_1'
    if prob_col not in predictions.columns:
        print(f"⚠️ 예측 결과 형태 변경 안내: {predictions.columns}")
        # fallback
        pred_col = 'prediction_label'
        score_col = 'prediction_score'
        
        # 1로 예측원 것만 추출
        bulls = predictions[predictions[pred_col] == 1]
        bulls = bulls.sort_values(by=score_col, ascending=False)
        top_10 = bulls.head(10)
        
        print("\n🏆 AI 추천 다음 주 상승 유망 종목 TOP 10 🏆")
        for i, (_, row) in enumerate(top_10.iterrows(), 1):
            print(f"{i:2d}위. {row['Ticker']:<5s} (AI 상승 확신도: {row[score_col]*100:.1f}%)")
    else:
        # 확률 기준 정렬 (무조건 1이 될 확률 기준!!)
        predictions = predictions.sort_values(by=prob_col, ascending=False)
        top_10 = predictions.head(10)
        
        print("\n🏆 AI 추천 다음 주 상승 유망 종목 TOP 10 🏆")
        print("-" * 60)
        for i, (_, row) in enumerate(top_10.iterrows(), 1):
            prob = row[prob_col] * 100
            print(f"{i:2d}위. {row['Ticker']:<5s} (상승 확률: {prob:.1f}%)")
        print("-" * 60)
    print("\n* 본 예측 결과는 머신러닝의 통계적 확률일 뿐이며, 투자 보조 지표로만 활용해 주십시오.")

if __name__ == "__main__":
    main()
