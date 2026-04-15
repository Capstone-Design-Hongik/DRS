import pandas as pd
import numpy as np

def generate_stock_data(filepath='mock_stock_data.csv', days=500):
    """
    일정 수준의 추세(Trend)와 주기(Seasonality), 그리고 노이즈(Noise)를 가지는 
    가상의 시계열 주가 데이터를 생성합니다.
    """
    np.random.seed(42)
    
    # 임의의 기준일 설정
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    
    # 요소 생성
    time = np.arange(days)
    trend = time * 0.1                             # 우상향하는 추세
    seasonality = 10 * np.sin(2 * np.pi * time / 30) # 30일 순환 주기
    noise = np.random.normal(0, 2, size=days)        # 무작위 노이즈
    
    base_price = 100 # 시작 기준가
    
    # 실제 주가와 비슷하게 3개 요소 합산
    close_prices = base_price + trend + seasonality + noise
    # 주가가 마이너스가 되지 않도록 최소 1 달러로 방어
    close_prices = np.maximum(close_prices, 1.0)
    
    # 데이터 프레임 구성
    df = pd.DataFrame({
        'Date': dates,
        'Close': close_prices
    })
    
    df.to_csv(filepath, index=False)
    print(f"가상의 주가 시계열 데이터 {days}일치가 성공적으로 생성되었습니다: {filepath}")

if __name__ == '__main__':
    # 스크립트 실행 시 CSV 파일 생성
    generate_stock_data()
