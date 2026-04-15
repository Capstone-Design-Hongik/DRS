#!/usr/bin/env python3
import sys
import os
import warnings
warnings.simplefilter(action='ignore')

try:
    import pandas as pd
    from pycaret.classification import setup, compare_models, finalize_model, save_model
except ImportError:
    print("❌ 모듈 로드 실패! 'pip install pycaret pandas' 명령어를 실행해주세요.")
    sys.exit(1)

OUTPUT_MODEL = 'weekly_momentum_model'
DATA_FILE = 'momentum_training_data.parquet'

def main():
    print("="*60)
    print("🤖 PyCaret AutoML: 이번 주(단서) 기반 다음 주 7% 급등 종목 예측 모델 학습")
    print("="*60)
    
    file_path = os.path.join(os.path.dirname(__file__), DATA_FILE)
    if not os.path.exists(file_path):
        print(f"❌ 데이터 파일이 없습니다. 먼저 데이터를 생성해주세요: {file_path}")
        return
        
    print(f"📦 데이터 로드 중: {file_path}")
    df = pd.read_parquet(file_path)
    print(f"✅ 기출문제 총 {len(df):,} 장 로드 완료!")
    
    # 💥 가장 중요한 부분 💥
    # AI가 꼼수를 부리거나 커닝하지 못하게 만들기:
    # 1. Ticker와 Date는 지운다 (과거에 애플이 많이 올랐다는 이유만으로 현재 애플을 추천하는 과적합 방지, 오직 '순수 차트 상황'만 본다)
    # 2. Future_Return은 정답(Target)을 만드는 원본이므로 반드시 삭제! (넣으면 100% 예측하는 커닝 모델이 됨)
    features = df.drop(columns=['Ticker', 'Date', 'Future_Return'])
    
    print("\n🛠️ PyCaret 학습 환경 세팅 중... (데이터 정규화, 결측치 보정 등 자동화)")
    clf_setup = setup(
        data=features, 
        target='Target', 
        session_id=42,
        normalize=True,             # 크기가 각기 다른 지표(1%, 200배 등)를 비슷한 척도로 맞춰줌 (성능 극대화)
        transformation=True,        # 데이터가 한쪽으로 쏠린 것을 예쁘게 펴줌
        fold=5,                     # 신뢰도를 높이기 위해 5번 시험(교차 검증)을 봄
        train_size=0.8,             # 데이터의 80%는 훈련, 20%는 혼자 몰래 테스트용으로 빼둠
        verbose=False               # 화면 렌더링이 깨지는 것 방지
    )
    
    print("\n🏎️ 트리 기반 일타 머신러닝 알고리즘 5개(LightGBM, XGBoost 등) 대결 시작!")
    print("   => 데이터가 방대하여 수 분이 소요될 수 있습니다. 커피 한 잔 하고 오세요 ☕")
    # 빠르고 가장 정확한 앙상블/트리 계열만 한정해서 배틀을 시킵니다 (F1-score 기준)
    best_model = compare_models(
        include=['lightgbm', 'xgboost', 'rf', 'et', 'gbc'], 
        sort='F1', 
        verbose=True
    )
    
    print("\n🏆 최종 1위 알고리즘:")
    print(best_model)
    
    # 1등으로 뽑힌 모델을 전체 데이터로 최종 완성(Finalize)
    print("\n💪 최고 모델 최종 최적화(Finalize) 중...")
    final_model = finalize_model(best_model)
    
    # 모델 파일(.pkl) 저장
    save_path = os.path.join(os.path.dirname(__file__), OUTPUT_MODEL)
    save_model(final_model, save_path)
    
    print("\n✅ 모든 과정 완료! 최종 뇌(모델)가 성공적으로 컴퓨터에 저장되었습니다.")
    print(f"📁 뇌 파일 저장 위치: {save_path}.pkl")

if __name__ == "__main__":
    main()
