# PyCaret AutoML Example

이 폴더는 **AutoML (Automated Machine Learning)** 도구인 **PyCaret**을 활용하여 **형식이 있는 표(Tabular) 데이터**를 다루는 가장 효율적이고 대중적인 방법을 보여줍니다.

## 3가지 라이브러리 접근 방식 비교
- **`fastai` (Vision)**: 인간의 눈처럼 2D 차트 형태(그림)를 보고 무슨 '패턴'인지 분류.
- **`Darts` (Time-Series)**: 시계열 날짜에 따른 한 줄짜리 숫자의 흐름(예: 종가 500일치)을 읽고 단기 미래의 가격 폭을 수치적으로 '예측'.
- **`PyCaret` (Tabular)**: 행(Row)과 열(Column)로 구성된 엑셀과 같은 데이터 프레임을 다룹니다.
  - 수학적 보조지표(RSI, MACD, 볼린저밴드 등)나 펀더멘털 데이터를 독립변수(Feature) 열로 깔아 두고, 
  - 내일 오를지/내릴지(1 or 0의 **분류/Classification**) 혹은
  - 내일 종가가 얼마일지(**회귀/Regression**)를 
  - 수십 개의 머신러닝 알고리즘(XGBoost, Random Forest, LightGBM 등)을 통해 코딩 몇 줄 만에 한꺼번에 비교 평가합니다.

본 예제는 기술적 지표들을 보고 내일 주가가 오를지(1), 내릴지(0)를 예측해보는 `PyCaret 분류(Classification)`의 기초 예시입니다.

## 실행 방법

1. **가상의 기술적 지표 표 데이터(CSV) 생성**
   ```bash
   python generate_tabular_data.py
   ```
   RSI, MACD, 거래량변화율 등의 무작위 기술적 지표 Feature들과 내일 상승 여부(Target_Up_Tomorrow) 컬럼을 가진 1,000행짜리의 정형표 데이터 `stock_features.csv` 파일을 생성합니다.

2. **PyCaret AutoML 파이프라인 구동 및 모델 저장**
   ```bash
   python train_pycaret.py
   ```
   다음 4단계의 AutoML 과정을 스크립트 실행 한 번으로 모두 처리합니다:
   1. `setup()`: 결측치 보정, 파생 변수 처리, 데이터 규모(Scale)를 맞추는 스케일링 등 전처리를 완전 자동화합니다.
   2. `compare_models()`: Scikit-learn의 기본 모델부터 강력한 트리 기반 모델들까지 순식간에 여러 알고리즘 성과를 교차 검증으로 비교하고 1등 모델을 찾아냅니다.
   3. `tune_model()`: 찾아낸 1등 모델의 내부 설정값(Hyperparameters)을 조정하여 성능 한계치까지 돌파합니다.
   4. `save_model()`: 확정된 머신러닝 모델과 앞단의 전처리 과정 도구들을 하나로 합쳐서 `.pkl` 파이프라인 파일로 저장합니다. 

## 요구사항 (Dependencies)
- `pandas`
- `numpy`
- `pycaret`
