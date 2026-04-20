# AI Stock Master

주식 분석 전문가용 프로그램입니다. Python과 Streamlit을 기반으로 구축되었습니다.

## 특징

- **실시간 데이터**: Yahoo Finance API를 통한 주식 데이터 수집
- **전문가 분석**: 다양한 기술적 보조지표 (MA, RSI, MACD 등) 제공
- **시각화**: Plotly를 이용한 인터랙티브 차트

## 설치 방법

1. 가상환경 생성 및 활성화 (권장):

    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

2. 의존성 설치:

    ```bash
    pip install -r requirements.txt
    ```

## 실행 방법

```bash
streamlit run app.py
```
