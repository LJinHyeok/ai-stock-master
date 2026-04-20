import yfinance as yf
import pandas as pd
import ta
import numpy as np

def calculate_all_indicators(ticker: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """
    야후 파이낸스 데이터 다운로드 후 보고서 기반의 모든 기술적 지표 계산.
    """
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty: return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

    import ta

    # 1. 추세 지표 (Trend)
    # SMA: 5, 20, 50, 60, 120, 200
    for length in [5, 20, 50, 60, 120, 200]:
        try:
            df[f'SMA_{length}'] = ta.trend.sma_indicator(df['Close'], window=length)
        except Exception: pass
    
    # EMA: 12, 26 (MACD용)
    try:
        df['EMA_12'] = ta.trend.ema_indicator(df['Close'], window=12)
        df['EMA_26'] = ta.trend.ema_indicator(df['Close'], window=26)
    except Exception: pass
    
    # MACD
    try:
        df['MACD_12_26_9'] = ta.trend.macd(df['Close'], window_slow=26, window_fast=12)
        df['MACDs_12_26_9'] = ta.trend.macd_signal(df['Close'], window_slow=26, window_fast=12, window_sign=9)
        df['MACDh_12_26_9'] = ta.trend.macd_diff(df['Close'], window_slow=26, window_fast=12, window_sign=9)
    except Exception: pass

    # ADX (추세 강도)
    try:
        adx = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
        df['ADX'] = adx.adx()
    except Exception: pass

    # Ichimoku Cloud
    try:
        ichimoku = ta.trend.IchimokuIndicator(df['High'], df['Low'], window1=9, window2=26, window3=52)
        df['ISA_9'] = ichimoku.ichimoku_a()
        df['ISB_26'] = ichimoku.ichimoku_b()
    except Exception: pass

    # ** Parabolic SAR **
    try:
        psar = ta.trend.PSARIndicator(df['High'], df['Low'], df['Close'], step=0.02, max_step=0.2)
        df['PSARl'] = psar.psar_up()
        df['PSARs'] = psar.psar_down()
    except Exception: pass

    # 2. 모멘텀 지표 (Momentum)
    # RSI
    try:
        df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)
    except Exception: pass
    
    # Stochastic
    try:
        df['STOCHk'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
    except Exception: pass

    # CCI
    try:
        df['CCI_14'] = ta.trend.cci(df['High'], df['Low'], df['Close'], window=14)
    except Exception: pass
    
    # Williams %R
    try:
        df['WillR_14'] = ta.momentum.williams_r(df['High'], df['Low'], df['Close'], lbp=14)
    except Exception: pass

    # 3. 변동성 지표 (Volatility)
    # Bollinger Bands
    try:
        bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BBL_20'] = bb.bollinger_lband()
        df['BBU_20'] = bb.bollinger_hband()
    except Exception: pass
    
    # ATR
    try:
        df['ATR_14'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    except Exception: pass

    # 4. 거래량 지표 (Volume)
    # OBV
    try:
        df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
    except Exception: pass
    # MFI
    try:
        df['MFI_14'] = ta.volume.money_flow_index(df['High'], df['Low'], df['Close'], df['Volume'], window=14)
    except Exception: pass

    return df

def generate_signal(df: pd.DataFrame) -> dict:
    """
    종합 예측 스코어링 시스템 (Advanced Scoring System).
    각 지표의 매수/매도 시그널을 합산하여 최종 투자의견을 도출합니다.
    """
    if df.empty: return {"action": "Neutral", "score": 0, "reasons": []}

    last = df.iloc[-1]
    prev = df.iloc[-2]
    score = 0
    reasons = []

    def check(col): return col in df.columns and not pd.isna(last[col])

    # 1. 추세 (Trend) - 비중 높음
    # SMA 정배열 (Strong Uptrend)
    if check('SMA_20') and check('SMA_50') and check('SMA_200'):
        if last['SMA_20'] > last['SMA_50'] > last['SMA_200']:
            score += 2
            reasons.append("이동평균선 정배열 (20 > 50 > 200) : 강력한 상승 추세")
        elif last['SMA_20'] < last['SMA_50'] < last['SMA_200']:
            score -= 2
            reasons.append("이동평균선 역배열 (20 < 50 < 200) : 강력한 하락 추세")

    # 골든/데드 크로스 (20 vs 60) - 신규 추가
    if check('SMA_20') and check('SMA_60'):
         if prev['SMA_20'] < prev['SMA_60'] and last['SMA_20'] > last['SMA_60']:
             score += 2
             reasons.append("골든 크로스 (20일선이 60일선 상향 돌파)")
         elif prev['SMA_20'] > prev['SMA_60'] and last['SMA_20'] < last['SMA_60']:
             score -= 2
             reasons.append("데드 크로스 (20일선이 60일선 하향 이탈)")

    # MACD
    if check('MACD_12_26_9') and check('MACDs_12_26_9'):
        if last['MACD_12_26_9'] > last['MACDs_12_26_9']:
            score += 1
            reasons.append("MACD > Signal (매수 우위)")
        else:
            score -= 1 # 매도 우위

    # Parabolic SAR - 신규 추가
    # 컬럼명이 PSARl (Long - 매수포지션, 점이 아래), PSARs (Short - 매도포지션, 점이 위) 형태로 생성됨
    # 하나는 NaN이고 하나는 값이 있음
    psar_long = [c for c in df.columns if 'PSARl' in c]
    psar_short = [c for c in df.columns if 'PSARs' in c]
    
    if psar_long and not pd.isna(last[psar_long[0]]):
        score += 1
        reasons.append("Parabolic SAR 매수 시그널 (주가 아래 점)")
    elif psar_short and not pd.isna(last[psar_short[0]]):
        score -= 1
        reasons.append("Parabolic SAR 매도 시그널 (주가 위 점)")

    # 2. 모멘텀 (Momentum)
    # RSI
    if check('RSI_14'):
        rsi = last['RSI_14']
        if rsi < 30: 
            score += 2
            reasons.append(f"RSI 과매도 ({rsi:.1f}) : 반등 기대")
        elif rsi > 70:
            score -= 2
            reasons.append(f"RSI 과매수 ({rsi:.1f}) : 조정 주의")
        elif 50 < rsi < 70:
            score += 0.5
        elif 30 < rsi < 50:
            score -= 0.5

    # Stochastic
    stoch_k = [c for c in df.columns if 'STOCHk' in c]
    if stoch_k:
        k_val = last[stoch_k[0]]
        if k_val < 20: score += 1; reasons.append("Stochastic 과매도 구간")
        elif k_val > 80: score -= 1; reasons.append("Stochastic 과매수 구간")

    # CCI
    if check('CCI_14'):
        cci = last['CCI_14']
        if cci < -100: score += 1; reasons.append("CCI 과매도 구간")
        elif cci > 100: score -= 1; reasons.append("CCI 과매수 구간")

    # 3. 변동성 (Volatility)
    # Bollinger Bands
    bbl = [c for c in df.columns if 'BBL' in c]
    bbu = [c for c in df.columns if 'BBU' in c]
    if bbl and bbu:
        if last['Close'] <= last[bbl[0]]:
            score += 2
            reasons.append("볼린저 밴드 하단 터치 (과매도)")
        elif last['Close'] >= last[bbu[0]]:
            score -= 2
            reasons.append("볼린저 밴드 상단 터치 (과매수)")

    # 4. 거래량 (MFI)
    if check('MFI_14'):
        mfi = last['MFI_14']
        if mfi < 20: score += 1; reasons.append("MFI 자금 유입 기대 (과매도)")
        elif mfi > 80: score -= 1; reasons.append("MFI 자금 유출 주의 (과매수)")

    # 최종판단
    # 점수 범위 예상: -10 ~ +10 -> 정규화 필요 없이 구간으로 판단
    if score >= 6: action = "Strong Buy (강력 매수)"
    elif score >= 2: action = "Buy (매수)"
    elif score <= -6: action = "Strong Sell (강력 매도)"
    elif score <= -2: action = "Sell (매도)"
    else: action = "Neutral (중립)"

    return {
        "action": action,
        "score": score,
        "reasons": reasons
    }
