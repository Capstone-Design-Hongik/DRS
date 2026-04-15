from fastai.vision.all import *
from pathlib import Path

def train_chart_pattern_model(data_path: str, epochs: int = 5):
    """
    CNN을 이용하여 차트 이미지를 학습하고 패턴을 분류하는 함수입니다.
    data_path: 데이터를 포함하는 최상위 디렉토리. 내부에 각 클래스명(예: uptrend, downtrend)으로 된 폴더가 있어야 합니다.
    """
    path = Path(data_path)
    
    # 1. DataBlock 정의
    # 차트 이미지를 시각적 패턴(ImageBlock)으로 인식하고, 상위 폴더명을 카테고리(CategoryBlock)로 사용
    dblock = DataBlock(
        blocks=(ImageBlock, CategoryBlock), 
        get_items=get_image_files,           # 데이터셋 폴더 내의 모든 이미지 파일 가져오기
        splitter=RandomSplitter(valid_pct=0.2, seed=42), # 20%를 검증 데이터로 분리
        get_y=parent_label,                  # 상위 폴더 이름(ex. uptrend)을 레이블(정답)으로 사용
        item_tfms=Resize(224)                # ResNet 학습을 위해 이미지를 224x224로 리사이징
    )
    
    # 데이터 로더 생성
    dls = dblock.dataloaders(path, bs=32)
    print("클래스 목록:", dls.vocab)
    
    # 2. 모델 생성 (Vision Learner)
    # 이미지 분류에 성능이 좋은 사전 학습된 ResNet18을 베이스 모델로 사용
    learn = vision_learner(dls, resnet18, metrics=accuracy)
    
    # 3. 전이 학습 (Fine Tuning)
    print(f"모델 학습을 시작합니다. (Epochs: {epochs})")
    learn.fine_tune(epochs)
    
    # 4. 학습된 모델 저장
    learn.export('chart_pattern_model.pkl')
    print("학습된 모델이 'chart_pattern_model.pkl'로 저장되었습니다.")
    
    return learn

def predict_pattern(model_path: str, image_path: str):
    """
    저장된 모델을 불러와서 새로운 차트 이미지의 패턴을 예측합니다.
    """
    print(f"\n[{image_path}] 이미지 예측 중...")
    learn = load_learner(model_path)
    pred_class, pred_idx, outputs = learn.predict(image_path)
    
    print(f"예측된 패턴: {pred_class}")
    print(f"클래스별 확률: {outputs}")
    return pred_class

if __name__ == '__main__':
    # 목업 데이터가 담긴 폴더 경로
    data_dir = 'dataset'
    
    if Path(data_dir).exists():
        # 폴더가 존재하면 학습을 스크립트로 진행합니다.
        learn = train_chart_pattern_model(data_dir, epochs=3)
        
        # 예측 테스트 (생성된 이미지 중 하나로 테스트)
        # test_image = Path(data_dir)/'uptrend'/'up_0.png'
        # if test_image.exists():
        #     predict_pattern('chart_pattern_model.pkl', test_image)
    else:
        print(f"디렉토리 '{data_dir}'를 찾을 수 없습니다. 먼저 generate_mock_data.py를 실행하여 데이터를 생성해주세요.")
