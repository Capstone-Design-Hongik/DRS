import pandas as pd
import numpy as np

def generate_tabular_data(filepath='stock_features.csv', rows=1000):
    """
    주식의 가상 기술적/수학적 지표(Feature) 데이터와 
    내일 가격 상승 여부(Target)를 담은 표(Tabular) 데이터를 생성합니다.
    """
    np.random.seed(42)
    
    # 여러가지 기술적 보조 지표들을 랜덤하게 생성합니다 (RSI, MACD, 거래량변화, 가격변화)
    rsi = np.random.uniform(20, 80, rows)             # 20~80 사이 RSI
    macd = np.random.normal(0, 1, rows)               # 평균 0, 표준편차 1인 MACD
    volume_change = np.random.normal(0, 5, rows)      # 전일대비 거래량 변화율
    price_change = np.random.normal(0, 2, rows)       # 전일대비 가격 변화율
    
    # 모델이 학습할 수 있도록, 지표와 상승여부(Target)간에 약한 상관관계를 인위적으로 부여합니다.
    # 예: RSI가 낮을수록(과매도), MACD가 높을수록 내일 오를 확률이 높아지게 임의 세팅
    logit = -0.05 * (rsi - 50) + 0.5 * macd + 0.1 * volume_change + np.random.normal(0, 1, rows)
    prob = 1 / (1 + np.exp(-logit))
    
    # 확률이 50%를 넘으면 1 (상승), 미만이면 0 (하락)
    target = (prob > 0.5).astype(int)
    
    # 엑셀과 같은 행렬 형태의 데이터 프레임 생성
    df = pd.DataFrame({
        'RSI_14': rsi,
        'MACD': macd,
        'Volume_Change_Pct': volume_change,
        'Price_Change_Pct': price_change,
        'Target_Up_Tomorrow': target
    })
    
    df.to_csv(filepath, index=False)
    print(f"{filepath} 파일에 {rows}개의 행(Row)을 가진 테이블(Tabular) 데이터를 생성했습니다.")

if __name__ == '__main__':
    generate_tabular_data()
