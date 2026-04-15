import pandas as pd
import matplotlib.pyplot as plt
from darts import TimeSeries
from darts.models import NBEATSModel
from darts.dataprocessing.transformers import Scaler

def train_and_forecast(csv_path: str):
    """
    Darts를 사용하여 시계열 데이터를 학습하고 미래를 예측합니다.
    """
    print(f"[{csv_path}] 데이터를 로컬에서 불러옵니다...")
    df = pd.read_csv(csv_path)
    
    # 1. Darts TimeSeries 객체로 변환
    # 시간축이 되는 'Date' 컬럼과 예측하려는 타겟인 'Close' 컬럼을 지정합니다.
    series = TimeSeries.from_dataframe(df, time_col='Date', value_cols='Close')
    
    # 2. 데이터 전처리 (스케일링)
    # 신경망 모델들은 0~1 사이의 값으로 스케일링이 되어야 학습이 잘 됩니다.
    scaler = Scaler()
    series_scaled = scaler.fit_transform(series)
    
    # Train / Validation 세트 분리 (마지막 30일을 검증용으로 사용)
    train_scaled, val_scaled = series_scaled[:-30], series_scaled[-30:]
    print(f"데이터 분리 완료 - Train: {len(train_scaled)}일, Validation: {len(val_scaled)}일")
    
    # 3. 딥러닝 예측 모델 선언 (N-BEATS)
    print("N-BEATS 딥러닝 모델을 초기화합니다.")
    model = NBEATSModel(
        input_chunk_length=30,  # 과거 30일의 데이터를 참고하여
        output_chunk_length=7,  # 향후 7일치 데이터를 한번에 예측하는 윈도우 설정
        n_epochs=20,            # 전체 데이터셋을 20번 반복 학습
        random_state=42,
        batch_size=32
    )
    
    # 4. 모델 학습 (Fit)
    print("데이터를 바탕으로 모델 학습을 시작합니다... (이 작업은 다소 시간이 걸릴 수 있습니다)")
    model.fit(train_scaled, verbose=True)
    
    # 5. 미래 데이터 예측 (Predict)
    print("\n학습된 모델을 기반으로 향후 30일을 예측합니다.")
    # 입력된 시계열(train_scaled)의 끝지점으로부터 미래 30스텝을 예측
    pred_scaled = model.predict(n=30, series=train_scaled)
    
    # 비교를 위해 스케일링된 데이터를 다시 원래 가격 단위로 복구(역변환)
    pred_actual = scaler.inverse_transform(pred_scaled)
    val_actual = scaler.inverse_transform(val_scaled)
    
    # 6. 결과 시각화
    plt.figure(figsize=(10, 5))
    val_actual.plot(label='Actual Data (Validation)')
    pred_actual.plot(label='N-BEATS Forecast Prediction', color='red')
    plt.title('Darts N-BEATS Future Price Concept Forecast')
    plt.legend()
    plt.savefig('forecast_result.png')
    print("\n예측 결과 차트가 'forecast_result.png' 파일로 저장되었습니다.")

if __name__ == '__main__':
    csv_file = 'mock_stock_data.csv'
    import os
    if os.path.exists(csv_file):
        train_and_forecast(csv_file)
    else:
        print(f"'{csv_file}' 에러: 데이터가 없습니다. 먼저 `generate_ts_data.py`를 실행해주세요.")
