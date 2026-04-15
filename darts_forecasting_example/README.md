# Darts Time-Series Forecasting Example

이 폴더는 시계열 분석 및 예측에 특화된 라이브러리인 **Darts (Unit8)** 를 활용하여, 주가 데이터의 미래 흐름을 딥러닝 모델로 직접적으로 예측(Forecasting)하는 방법을 보여줍니다.

## 차트 패턴(fastai) vs 시계열 데이터 예측(Darts)의 차이점
- `fastai` (Vision): "현재 차트 형태를 캡처한 이미지"가 **어떤 패턴 이름(헤드앤숄더, 이중바닥 등)인지 분류**하는 데 특화되었습니다.
- `Darts`: 과거부터 현재까지 누적된 **"가격 숫자들의 나열" (e.g. 100->102->98)을 그대로 입력**받아, 숨겨진 주기와 패턴을 모델이 파악한 후, **"앞으로 7일 동안의 가격 수치" 자체를 결과물로 예측(Forecasting)** 해냅니다.

본 예제에서는 Darts에서 가장 성능이 뛰어난 시계열 특화 딥러닝 모델 중 하나인 **N-BEATS**를 사용하여 예측을 수행합니다.

## 실행 방법

1. **가상의 주가 숫자 데이터(CSV) 생성**
   ```bash
   python generate_ts_data.py
   ```
   이 스크립트는 적당한 상승 추세와 주기가 섞인 500일치의 가상 주가 데이터를 생성해 `mock_stock_data.csv` 로 만듭니다.

2. **Darts 시계열 모델 훈련 및 예측**
   ```bash
   python train_darts.py
   ```
   - 데이터를 DataFrame에서 불러와 Darts 전용 규격인 `TimeSeries` 로 변환합니다.
   - 값의 폭발적인 증가를 막기 위해 데이터를 `Scaler()` 로 0~1 사이로 정규화합니다.
   - 과거 30일을 보고 미래 7일을 예측하는 윈도우 규칙으로 `N-BEATS` 모델을 훈련시킵니다.
   - 학습이 끝난 뒤 마지막 검증 구간을 예측하여, 실제 정답값과 예측결과가 들어있는 `forecast_result.png` 이미지가 저장됩니다.

## 요구사항 (Dependencies)
- `darts`
- `pandas`
- `numpy`
- `matplotlib`
