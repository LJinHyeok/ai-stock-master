from GoogleNews import GoogleNews
import yfinance as yf
import datetime
import pandas as pd
import google.generativeai as genai
import streamlit as st

def get_market_news(keyword: str = "Stock Market OR Economy OR Fed", period: str = "1d", max_results: int = 10) -> pd.DataFrame:
    """Google News 스크래핑"""
    try:
        googlenews = GoogleNews(lang='en', period=period)
        googlenews.search(keyword)
        result = googlenews.result()
        if not result: return pd.DataFrame()
        df = pd.DataFrame(result)
        # Try sorting
        try:
            df['datetime'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.sort_values(by='datetime', ascending=False)
        except: pass
        return df.head(max_results)
    except Exception as e:
        print(f"News error: {e}")
        return pd.DataFrame()

def analyze_sentiment_with_ai(news_list: list) -> dict:
    """
    [보고서 기반] 월스트리트 수석 애널리스트 페르소나를 적용한 심층 분석 (한국어 출력)
    """
    api_key = st.secrets.get("GEMINI_API_KEY") or st.session_state.get("GEMINI_API_KEY")
    if not api_key:
        return {"score": 50, "summary": "API Key Missing", "reason": "Please set GEMINI_API_KEY"}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # 프롬프트 엔지니어링 (Persona + Logic + Korean)
        prompt = f"""
        당신은 월스트리트(Wall Street)의 수석 시장 전략가(Chief Market Strategist)입니다.
        당신의 임무는 아래 제공된 뉴스 헤드라인들을 심층 분석하여 현재 시장의 분위기와 거시경제적 함의를 도출하는 것입니다.
        모든 분석 결과는 전문가 수준의 **한국어**로 작성되어야 합니다.

        **분석 대상 뉴스 헤드라인:**
        {news_list}
        
        **지시사항:**
        1. 뉴스들의 전반적인 톤(Tone)과 잠재적인 시장 영향력을 종합적으로 분석하십시오.
        2. 시장 심리(Market Sentiment)를 '강세(Bullish)', '약세(Bearish)', '중립(Neutral)' 중 하나로 판단하십시오.
        3. '시장 공포/탐욕 지수(Market Fear/Greed Score)'를 0에서 100 사이의 숫자로 산출하십시오.
           - 0-20: 극도의 공포 (Strong Bearish)
           - 40-60: 중립 (Neutral)
           - 80-100: 극도의 탐욕 (Strong Bullish)
        4. 다음 항목을 포함하여 전문가 리포트를 작성하십시오:
           - **핵심 동인 (Key Drivers)**: 시장을 움직이는 주된 요인 3가지.
           - **리스크 요인 (Risk Factors)**: 투자자가 유의해야 할 잠재적 위험.
           - **전망 (Outlook)**: 단기 및 중기 시장 전망.

        **출력 형식 (JSON):**
        {{
            "sentiment": "강세/약세/중립",
            "score": 55,
            "summary": "핵심 동인 및 시장 상황 요약 (3문장 이내)",
            "reason": "점수 산정 근거 및 상세 분석 리포트 (핵심 동인, 리스크, 전망 포함하여 마크다운 형식으로 작성)"
        }}
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        
        import json
        return json.loads(text)

    except Exception as e:
        return {"score": 50, "summary": f"AI 분석 오류: {str(e)}", "reason": "분석 중 문제가 발생했습니다."}

def get_fred_data() -> pd.DataFrame:
    """
    확장된 FRED 거시경제 데이터 (총 20종 이상)
    에러 핸들링을 강화하여 가능한 많은 데이터를 가져옵니다.
    """
    indicators = {
        # 1. 금리 & 채권 & 리스크
        'T10Y2Y': '장단기 금리차 (10Y-2Y)', 
        'DGS10': '미국채 10년물 수익률', 
        'FEDFUNDS': '기준금리 (Fed Funds)',
        'BAMLH0A0HYM2': '하이일드 스프레드 (Credit Risk)', # NEW
        
        # 2. 물가 (Inflation)
        'CPIAUCSL': '소비자물가지수 (CPI)',
        'PCEPI': '개인소비지출 (PCE)',
        'PPIACO': '생산자물가지수 (PPI)', # NEW
        'M2SL': 'M2 통화량',
        'M2V': 'M2 통화유통속도', # NEW
        'T5YIE': '5년 기대인플레이션 (BEI)', # NEW

        # 3. 고용 (Labor)
        'UNRATE': '실업률 (Unemployment)',
        'ICSA': '신규 실업수당 청구건수', # NEW
        'CIVPART': '경제활동 참가율', # NEW
        'SAHMREALTIME': '샴의 법칙 (불황지표)', # NEW

        # 4. 경기 & 소비 (Economy)
        'GDP': '미국 GDP',
        'GDPC1': '실질 GDP (Real GDP)', # NEW
        'INDPRO': '산업생산지수', # NEW
        'RSXFS': '소매판매 (Retail Sales)', # NEW
        'HOUST': '주택 착공 건수', # NEW
        'PSAVERT': '개인 저축률', # NEW

        # 5. 심리
        'VIXCLS': '공포지수 (VIX)', 
        'UMCSENT': '소비자심리지수'
    }
    
    start = (datetime.datetime.now() - datetime.timedelta(days=365*5)).strftime('%Y-%m-%d')
    end = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 데이터 수집 (안정성 강화)
    data_frames = []
    
    for code, name in indicators.items():
        try:
            # 개별 시도: FRED public API csv
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={code}"
            d = pd.read_csv(url, na_values=['.']) 
            # Convert 'observation_date' to datetime
            d['observation_date'] = pd.to_datetime(d['observation_date'], errors='coerce')
            d.set_index('observation_date', inplace=True)
            d.index.name = 'Date'
            
            # Numeric conversion and dropnas
            d[code] = pd.to_numeric(d[code], errors='coerce')
            d = d.dropna(subset=[code])
            
            # 기간 필터링
            d = d.loc[start:end]
            
            # 컬럼명 변경
            d.columns = [name]
            
            if not d.empty:
                data_frames.append(d)
        except Exception as e:
            # print(f"Failed to fetch {name} ({code}): {e}") # 로그 과다 방지
            continue
            
    if not data_frames:
        return pd.DataFrame()
        
    # 날짜 기준 통합 (Outer Join)
    df_result = pd.concat(data_frames, axis=1, join='outer')
    return df_result

def get_commodities_data() -> pd.DataFrame:
    """[확장] 달러, 원유, 금, 구리, 비트코인"""
    tickers = {
        'DX-Y.NYB': 'Dollar Index (DXY)',
        'CL=F': 'Crude Oil (WTI)',
        'GC=F': 'Gold (COMEX)',
        'HG=F': 'Copper',
        'BTC-USD': 'Bitcoin'
    }
    try:
        # yfinance는 리스트로 줘도 부분 성공 가능
        data = yf.download(list(tickers.keys()), period="5y", progress=False)['Close']
        
        # 컬럼 이름 매핑 (MultiIndex 처리)
        if isinstance(data.columns, pd.MultiIndex): 
            data.columns = data.columns.get_level_values(0)
            
        # 존재하는 컬럼만 rename
        rename_map = {k: v for k, v in tickers.items() if k in data.columns}
        return data.rename(columns=rename_map)
    except Exception as e:
        print(f"Comm. Error: {e}")
        return pd.DataFrame()

def get_macro_interpretation(indicator_name: str) -> dict:
    """
    각 지표에 대한 상세 해석 가이드 (Korean)
    """
    map_dict = {
        '장단기 금리차 (10Y-2Y)': {
            'desc': '장기 금리(10년)와 단기 금리(2년)의 차이입니다.',
            'meaning': '경기 침체의 가장 강력한 선행 지표입니다. 0 이하(역전)로 떨어지면 침체 경고, 다시 급등하면 불황 시작을 알립니다.',
            'action': '역전 후 정상화 시점에 주식 비중 축소 및 채권/방어주 비중 확대 고려.'
        },
        '미국채 10년물 수익률': {
            'desc': '미국 정부가 발행한 10년 만기 채권의 금리입니다.',
            'meaning': '글로벌 자산 가격의 벤치마크입니다. 금리 상승은 기술주/성장주에 악재, 하락은 호재로 작용합니다.',
            'action': '4.0% 이상 급등 시 주식 시장 조정 가능성 주의.'
        },
        '하이일드 스프레드 (Credit Risk)': {
            'desc': '투기등급(BB 이하) 회사채와 국채 간 금리 차이입니다.',
            'meaning': '기업 부도 위험을 나타냅니다. 스프레드가 치솟으면 신용 경색(자금줄 막힘) 위기가 온다는 뜻입니다.',
            'action': '급등 시 현금 비중 확대 필수.'
        },
        'M2 통화량': {
            'desc': '시중에 풀린 현금, 예금 등 유동성의 총량입니다.',
            'meaning': '유동성은 자산 시장의 연료입니다. M2 증가율이 꺾이면 증시 상승 동력이 약해질 수 있습니다.',
            'action': '전년 대비 증감률(YoY) 추세 확인.'
        },
        'M2 통화유통속도': {
            'desc': 'M2 통화가 경제 내에서 얼마나 빠르게 순환하는지를 나타내는 지표입니다.',
            'meaning': '통화유통속도가 낮으면 돈이 돌지 않아 경제 활동이 위축될 수 있음을 시사합니다.',
            'action': '장기적인 하락 추세는 저성장/저물가 압력을 의미할 수 있습니다.'
        },
        '소비자물가지수 (CPI)': {
            'desc': '소비자가 구입하는 상품/서비스의 가격 변동입니다.',
            'meaning': '연준(Fed)의 금리 정책을 결정하는 핵심 지표입니다. 예상보다 높으면 금리 인상(긴축) 우려로 증시에 악재입니다.',
            'action': '발표일 전후 변동성 확대 주의.'
        },
        '개인소비지출 (PCE)': {
            'desc': '가계가 실제 지출한 금액을 집계한 지표로, 연준이 가장 선호하는 물가 지표입니다.',
            'meaning': 'CPI보다 실제 소비 패턴을 더 잘 반영합니다.',
            'action': 'Core PCE(근원물가) 추세가 꺾이는지가 금리 인하의 열쇠입니다.'
        },
        '생산자물가지수 (PPI)': {
            'desc': '기업 간 거래되는 원자재/중간재 가격 변동입니다.',
            'meaning': 'CPI의 선행 지표 역할을 합니다. 기업 마진 압박 요인이 됩니다.',
            'action': 'PPI 상승은 곧 CPI 상승으로 이어질 수 있음.'
        },
        '5년 기대인플레이션 (BEI)': {
            'desc': '시장 참여자들이 예상하는 향후 5년 평균 물가 상승률입니다.',
            'meaning': '장기적인 인플레이션 심리를 보여줍니다. 높으면 고금리 장기화 우려가 있습니다.',
            'action': '2.5% 상회 여부 모니터링.'
        },
        '실업률 (Unemployment)': {
            'desc': '경제활동인구 중 실업자의 비율입니다.',
            'meaning': '경기의 후행 지표지만, 급격한 상승은 경기 침체(Recession)를 의미합니다. 너무 낮으면 긴축, 너무 높으면 침체 우려.',
            'action': '역사적 저점에서 반등하기 시작할 때가 위험 신호.'
        },
        '신규 실업수당 청구건수': {
            'desc': '매주 실업수당을 새로 신청한 사람의 수입니다.',
            'meaning': '고용 시장의 가장 빠른 선행 지표입니다. 수치가 급증하면 고용 둔화 신호입니다.',
            'action': '예상치 상회 시 경기 둔화 우려 반영.'
        },
        '경제활동 참가율': {
            'desc': '생산가능인구 중 경제활동에 참여하는 인구의 비율입니다.',
            'meaning': '고용 시장의 건전성을 나타냅니다. 참가율이 낮으면 잠재 성장률 하락 요인이 됩니다.',
            'action': '장기적인 추세 변화를 통해 노동 시장의 구조적 변화를 파악.'
        },
        '샴의 법칙 (불황지표)': {
            'desc': '실업률의 3개월 이동평균이 지난 12개월 최저치보다 0.5%p 이상 상승했는지 여부입니다.',
            'meaning': '경기 침체 시작을 알리는 매우 정확한 지표로 알려져 있습니다.',
            'action': '지표 급등 시 적극적 리스크 관리 필요.'
        },
        '미국 GDP': {
            'desc': '국내총생산, 국가 경제 규모의 성장률입니다.',
            'meaning': '경제가 성장하고 있는지 후퇴하고 있는지 보여주는 가장 기본적인 성적표입니다.',
            'action': '2분기 연속 마이너스 성장 시 기술적 경기 침체로 간주합니다.'
        },
        '실질 GDP (Real GDP)': {
            'desc': '물가 상승분을 제외한 실제 경제 성장률입니다.',
            'meaning': '명목 GDP보다 실제 경제의 생산량 변화를 더 정확하게 보여줍니다.',
            'action': '실질 GDP 성장률 둔화는 경기 침체 가능성을 시사합니다.'
        },
        '산업생산지수': {
            'desc': '제조업, 광업, 유틸리티 부문의 생산량 변화를 측정합니다.',
            'meaning': '경기 동행 지표로, 경제의 생산 활동 수준을 나타냅니다.',
            'action': '지속적인 하락은 경기 둔화의 신호입니다.'
        },
        '소매판매 (Retail Sales)': {
            'desc': '백화점, 마트 등 소매점 매출액 총합입니다.',
            'meaning': '미국 경제의 70%인 소비의 건전성을 보여줍니다. 예상 밖 감소는 경기 둔화 우려를 낳습니다.',
            'action': '소비 위축 시 경기민감주 주의.'
        },
        '주택 착공 건수': {
            'desc': '새로 짓기 시작한 주택의 수입니다.',
            'meaning': '부동산 경기는 경제의 선행 지표입니다. 착공 감소는 향후 가전, 가구 등 소비 감소로 이어집니다.',
            'action': '건설/자재 섹터와 연동.'
        },
        '개인 저축률': {
            'desc': '개인의 가처분 소득 중 저축하는 비율입니다.',
            'meaning': '소비 여력과 경제의 안정성을 나타냅니다. 저축률 하락은 미래 소비 둔화로 이어질 수 있습니다.',
            'action': '저축률 급락 시 소비 위축 가능성 경계.'
        },
        '공포지수 (VIX)': {
            'desc': 'S&P 500 옵션 가격에 반영된 향후 변동성 기대치입니다.',
            'meaning': '시장의 불안감을 나타냅니다. 20 이하는 평온, 30 이상은 극도의 공포(패닉) 상태입니다.',
            'action': '역설적으로 VIX 급등(40 근접) 시가 매수 기회일 수 있음.'
        },
        '소비자심리지수': {
            'desc': '미시간대학교에서 발표하는 소비자의 체감 경기 설문 결과입니다.',
            'meaning': '미국 경제의 70%를 차지하는 소비의 선행 지표입니다.',
            'action': '심리가 바닥을 치고 턴어라운드할 때가 주가 반등 시점과 겹치는 경향이 있습니다.'
        },
        '기준금리 (Fed Funds)': {
            'desc': '미국 중앙은행(Fed)이 설정하는 초단기 목표 금리입니다.',
            'meaning': '모든 돈의 가격을 결정합니다. 긴축 사이클(인상)과 완화 사이클(인하) 어디에 있는지 파악해야 합니다.',
            'action': '금리 인하 사이클 초입에는 채권과 주식이 보통 강세를 보입니다.'
        },
        'Dollar Index (DXY)': {
            'desc': '주요 6개국 통화 대비 미국 달러의 가치입니다.',
            'meaning': '달러 강세는 미국 외 기업 실적 악화 및 신흥국 자금 이탈을 유발하여 증시에 부담을 줍니다.',
            'action': '달러 꺾일 때 신흥국/성장주 유리.'
        },
         'Crude Oil (WTI)': {
            'desc': '서부 텍사스산 원유 가격입니다.',
            'meaning': '에너지 비용이자 인플레이션의 주요 원인입니다. 너무 오르면 소비 위축, 너무 내리면 경기 침체를 의미합니다.',
            'action': '70~80불 밴드 이탈 여부 주목.'
        },
        'Gold (COMEX)': {
            'desc': '대표적인 안전 자산이자 인플레이션 헤지 수단입니다.',
            'meaning': '화폐 가치 하락이나 지정학적 위기 시 돋보입니다.',
            'action': '실질 금리가 하락할 때 금 가격이 오르는 경향이 강합니다.'
        },
        'Copper': {
            'desc': '구리, 산업 전반에 쓰여 "닥터 코퍼"라 불리는 경기 선행 지표입니다.',
            'meaning': '구리 가격 상승은 제조업 경기 회복을 시사합니다.',
            'action': '경기가 좋아질 때 가장 먼저 반응하는 원자재 중 하나입니다.'
        },
        'Bitcoin': {
            'desc': '대표적인 암호화폐이자 디지털 금입니다.',
            'meaning': '가장 민감한 위험 자산(Risk On) 성격을 가집니다.',
            'action': '유동성이 풍부할 때 가장 탄력적으로 상승합니다.'
        }
    }
    return map_dict.get(indicator_name, {
        'desc': '주요 거시경제 지표입니다.', 
        'meaning': '시장의 흐름을 읽는 중요한 단서가 됩니다.', 
        'action': '추세적 변화에 주목하세요.'
    })

def get_commodities_data() -> pd.DataFrame:
    """[확장] 달러, 원유, 금, 구리, 비트코인"""
    tickers = {
        'DX-Y.NYB': 'Dollar Index (DXY)',
        'CL=F': 'Crude Oil (WTI)',
        'GC=F': 'Gold (COMEX)',
        'HG=F': 'Copper',
        'BTC-USD': 'Bitcoin'
    }
    try:
        # 데이터가 없는 경우를 대비해 yfinance의 경우 에러 핸들링 강화
        data = yf.download(list(tickers.keys()), period="5y", progress=False)['Close']
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        return data.rename(columns=tickers)
    except Exception as e:
        print(f"Comm. Error: {e}")
        return pd.DataFrame()
