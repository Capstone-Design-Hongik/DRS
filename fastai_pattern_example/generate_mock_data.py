import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def generate_random_walk(length=100):
    """랜덤 워크(Random Walk)를 사용하여 임의의 주가 흐름과 비슷한 데이터를 생성합니다."""
    return np.cumsum(np.random.normal(0, 1, length))

def save_plot(data, filename):
    """데이터를 흑백 라인 차트로 변환하여 이미지로 저장합니다."""
    plt.figure(figsize=(3, 3))
    plt.plot(data, color='black', linewidth=2)
    
    # 딥러닝 모델이 차트의 '형태(Shape)'에만 집중할 수 있도록 x, y축 라벨 및 눈금을 모두 제거
    plt.axis('off') 
    plt.tight_layout()
    
    # 여백 없이 저장
    plt.savefig(filename, bbox_inches='tight', pad_inches=0)
    plt.close()

def create_dataset(base_dir='dataset', samples_per_class=50):
    """
    가상의 차트 이미지 데이터셋을 생성합니다.
    클래스: uptrend(상승장), downtrend(하락장), ranging(횡보장)
    """
    classes = ['uptrend', 'downtrend', 'ranging']
    base_path = Path(base_dir)
    
    for cls in classes:
        (base_path / cls).mkdir(parents=True, exist_ok=True)
    
    print(f"가상의 차트 이미지 데이터를 생성합니다. (각 클래스당 {samples_per_class}개)")
    
    for i in range(samples_per_class):
        # 1. 상승장 (Uptrend): 랜덤 워크에 양의 기울기를 더함
        up = generate_random_walk() + np.linspace(0, 20, 100)
        save_plot(up, base_path / 'uptrend' / f'up_{i}.png')
        
        # 2. 하락장 (Downtrend): 랜덤 워크에 음의 기울기를 더함
        down = generate_random_walk() - np.linspace(0, 20, 100)
        save_plot(down, base_path / 'downtrend' / f'down_{i}.png')
        
        # 3. 횡보장 (Ranging): 뚜렷한 추세가 없는 일반 랜덤 워크
        range_data = generate_random_walk()
        save_plot(range_data, base_path / 'ranging' / f'range_{i}.png')
        
    print(f"데이터 생성이 완료되었습니다. 위치: {base_path.absolute()}")

if __name__ == '__main__':
    create_dataset()
