import pandas as pd
from pycaret.classification import setup, compare_models, tune_model, finalize_model, save_model

def train_automl(csv_path: str):
    """
    PyCaret 분류(Classification) 모듈을 사용하여 
    내일 가격이 오를지(1) 내릴지(0)를 예측하는 AutoML 파이프라인을 실행합니다.
    """
    print(f"[{csv_path}] 테이블 데이터를 판다스(Pandas)로 불러옵니다...")
    df = pd.read_csv(csv_path)
    
    print("\n1. PyCaret Setup 시작 (전처리 자동화)")
    # setup() 함수 한 번으로 수많은 전처리가 완료됩니다.
    # 결측치 채우기, 정규화, Train/Test 분할 등이 백그라운드에서 진행됩니다.
    clf_setup = setup(
        data=df, 
        target='Target_Up_Tomorrow', # 예측해야 할 정답 컬럼 명시
        session_id=123,              # 재현성을 위한 시드 번호
        train_size=0.8,
        normalize=True,              # 모델들이 각기 다른 feature 스케일에 영향을 덜 받도록 정규화
        transformation=True,         # 비대칭적인 데이터 분포를 정규분포에 가깝게 변환
        verbose=False                # 콘솔 출력량이 너무 많아지는 것을 방지
    )
    
    print("\n2. 수많은 머신러닝 알고리즘 자동 비교 시작 (Compare Models)")
    print("RandomForest, XGBoost, LightGBM, LogisticRegression 등을 비교 중입니다...")
    print("(각 모델별로 교차검증을 수행하므로 다소 시간이 걸릴 수 있습니다.)")
    
    # 가용한 모든 모델을 돌려 성능(기본적으로 Accuracy)이 높은 상위 1개 모델 선택
    best_model = compare_models(n_select=1, sort='Accuracy')
    print(f"\n최적의 베이스라인 모델 선정 완료: {best_model}")
    
    print("\n3. 하이퍼파라미터 튜닝 (Tune Model)")
    # 선정된 1등 모델의 세부 옵션(Hyper-parameters)을 자동으로 튜닝해 성능을 끌어올립니다.
    tuned_model = tune_model(best_model, optimize='Accuracy', n_iter=10)
    
    print("\n4. 최종 파이프라인 확정 및 저장 (Finalize & Save)")
    # 나누어둔 검증용 테스트 데이터까지 전부 끌어와 최종적으로 학습을 확정합니다.
    final_model = finalize_model(tuned_model)
    
    # 전처리 과정(스케일러 등)과 확정된 머신러닝 모델을 한 데 묶어(Pipeline) 저장합니다.
    # 나중에 새 데이터가 들어왔을 때 전처리부터 예측까지 원스톱으로 가능해집니다.
    save_model(final_model, 'best_stock_prediction_pipeline')
    print("전처리+예측 과정이 합쳐진 최종 파이프라인이 'best_stock_prediction_pipeline.pkl' 파일로 저장되었습니다.")

if __name__ == '__main__':
    csv_file = 'stock_features.csv'
    import os
    if os.path.exists(csv_file):
        train_automl(csv_file)
    else:
        print(f"에러: '{csv_file}'가 없습니다. 먼저 `generate_tabular_data.py`를 실행하세요.")
