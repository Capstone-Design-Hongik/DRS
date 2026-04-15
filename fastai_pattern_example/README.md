# Fastai Chart Pattern Example

이 폴더는 `fastai`를 활용하여 시계열 금융 데이터(차트 패턴)를 **컴퓨터 비전(Computer Vision)** 문제로 치환하여 학습시키는 가장 직관적이고 널리 쓰이는 방식을 보여줍니다.

## 패턴 인식 접근 방식
1. **시각적 접근(Vision Approach)** - *본 예제에서 사용됨*
   - 주가 데이터를 실제 인간이 보는 것과 동일하게 **이미지(차트 캡처본)** 로 변환합니다.
   - 변환된 이미지를 `fastai.vision`의 CNN(Convolutional Neural Network, 예: ResNet)을 사용해 분류합니다.
   - **장점**: 직관적임. 인간 눈에 띄는 기술적 분석 패턴(헤드앤숄더, 이중바닥 등)을 형태 자체로 잡아냅니다.
2. **시계열/정형 데이터 접근(Tabular/Time-Series Approach)**
   - 가격(Open, High, Low, Close) 배열 자체를 `tsai`(fastai 타임시리즈 확장 라이브러리)나 LSTM/Transformer 모델에 바로 입력합니다.

## 실행 방법
본 예제는 `matplotlib`을 이용해 가상의 차트 이미지를 그리고 폴더에 저장한 뒤, 이를 이미지 분류 문제로 학습시키는 과정을 따릅니다.

1. **가상의 학습용 이미지 파일 생성**
   ```bash
   python generate_mock_data.py
   ```
   이 스크립트를 실행하면 현재 폴더 내에 `dataset/` 폴더가 생성되며 그 아래 `uptrend`, `downtrend`, `ranging` 이름의 폴더들에 차트 이미지가 50장씩 만들어집니다.

2. **모델 학습 및 저장**
   ```bash
   python train_vision.py
   ```
   폴더 구조를 읽고 DataLoaders를 생성한 후, ResNet18을 기반으로 미세조정(fine-tuning) 학습을 진행합니다. 학습이 끝나면 모델은 `chart_pattern_model.pkl`로 저장됩니다.

## 요구사항 (Dependencies)
- `fastai`
- `matplotlib`
- `numpy`
- `Pillow` (fastai 이미지 처리에 사용)
