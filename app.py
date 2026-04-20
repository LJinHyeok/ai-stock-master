import streamlit as st
import pandas as pd
import datetime

# 모듈 임포트
import indicators
import macro_news
import visualization

st.set_page_config(
    page_title="AI Stock Master Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

def main():
    st.title("📈 AI Stock Master Pro - 전문가용 시스템")
    st.caption("Powered by Vibe Coding & Gemini 3 Pro Agent")
    st.markdown("---")

    # 사이드바 설정
    st.sidebar.header("글로벌 설정 (Global Settings)")
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except FileNotFoundError:
        api_key = None
    except Exception:
        api_key = None

    if not api_key:
        api_key = st.sidebar.text_input("Gemini API Key 입력", type="password")
        if api_key: 
            # 임시로 session_state에 저장하거나 환경변수로 활용
            st.session_state["GEMINI_API_KEY"] = api_key
            # st.secrets["GEMINI_API_KEY"] = api_key # Caution: This depends on streamlit version if writeable

    st.sidebar.info("분석할 모듈을 선택하세요.")
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 종목 정밀 분석", "🌍 매크로 인텔리전스", "🗺️ 시장 역학 지도"])

    # 1. 종목 분석
    with tab1:
        col_in, col_act = st.columns([3, 1])
        with col_in:
            ticker = st.text_input("종목 코드 (Ticker)", value="AAPL", help="분석할 미국 주식 티커를 입력하세요 (예: AAPL, TSLA, NVDA)")
        with col_act:
            btn_run = st.button("AI 정밀 분석 실행", use_container_width=True)

        if btn_run or ticker:
            with st.spinner("퀀트 알고리즘 및 AI 분석 수행 중..."):
                df = indicators.calculate_all_indicators(ticker, period="2y")
                
                if not df.empty:
                    # 신호 생성
                    sig = indicators.generate_signal(df)
                    
                    # AI Opinion UI
                    action_map = {"BUY": "매수 (BUY)", "SELL": "매도 (SELL)", "HOLD": "관망 (HOLD)"}
                    korean_action = action_map.get(sig['action'], sig['action'])
                    
                    st.markdown(f"### 🧠 AI 투자 의견: **{korean_action}**")
                    
                    # Score Normalize (-10 ~ 10 -> 0 ~ 1.0)
                    norm_score = (sig['score'] + 10) / 20
                    norm_score = max(0.0, min(1.0, norm_score))
                    
                    st.progress(norm_score)
                    st.caption(f"퀀트 점수 (Quant Score): {sig['score']} / 10 (높을수록 매수 우위)")
                    
                    with st.expander("🔍 상세 분석 근거 (Logic Trace)", expanded=True):
                        for r in sig['reasons']:
                            # 간단한 한글 번역 매핑 (필요시 더 정교하게)
                            trans_r = r.replace("Bullish", "강세").replace("Bearish", "약세").replace("oversold", "과매도").replace("overbought", "과매수")
                            st.write(f"- {trans_r}")
                    
                    st.divider()

                    # Main Chart
                    st.subheader("기술적 분석 차트 (Technical Analysis)")
                    fig = visualization.plot_candlestick(df, title=f"{ticker} 주가 움직임")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 보조 지표 차트
                    c1, c2 = st.columns(2)
                    with c1: st.plotly_chart(visualization.plot_rsi(df), use_container_width=True)
                    with c2: st.plotly_chart(visualization.plot_macd(df), use_container_width=True)
                
                else:
                    st.error("데이터 로드 실패. 티커를 확인해주세요.")

    # 2. 매크로 인텔리전스
    with tab2:
        st.header("매크로 인텔리전스 & AI 뉴스 분석")
        
        # 글로벌 거시경제 및 자산 지표 섹션
        st.subheader("📈 글로벌 거시경제 및 자산 지표 (Macro Expert View)")
        st.caption("실시간 데이터를 기반으로 한 10대 핵심 지표 대시보드입니다.")

        # 데이터 로드
        fred_df = macro_news.get_fred_data()
        comm_df = macro_news.get_commodities_data()
        
        # 탭으로 카테고리 구분 (제거 -> 대시보드 형태)
        # m_tab1, m_tab2, m_tab3, m_tab4 = st.tabs(["💰 금리/유동성", "🏭 경기/고용/물가", "🛢️ 원자재/자산", "😱 심리/공포"])

        # 3열 그리드 생성 (Dashboard Layout)
        st.markdown("### 📊 매크로 경제 지표 대시보드 (Global Macro Intelligence)")
        st.caption("실시간 데이터를 기반으로 한 20대 핵심 지표 대시보드입니다.")
        
        # --- Row 1: 금리 & 채권 & 리스크 ---
        st.markdown("#### 1. 금리 & 채권 & 리스크 (Rates & Bonds)")
        r1c1, r1c2, r1c3 = st.columns(3)
        
        with r1c1: # 장단기 금리차
            if '10Y-2Y Spread' in fred_df.columns:
                fig = visualization.plot_macro_chart(fred_df, ['10Y-2Y Spread'], "장단기 금리차 (10Y-2Y)", ['#1f77b4'])
                st.plotly_chart(fig, use_container_width=True)
                g = macro_news.get_macro_interpretation('장단기 금리차 (10Y-2Y)')
                st.info(f"**{g['meaning']}**\n\n{g['action']}", icon="💡")
        
        with r1c2: # 국채 & 기준금리
             cols_rate = []
             if '10Y Yield' in fred_df.columns: cols_rate.append('10Y Yield')
             if 'Fed Funds' in fred_df.columns: cols_rate.append('Fed Funds')
             
             if cols_rate:
                fig_rate = visualization.plot_macro_chart(fred_df, cols_rate, "국채 10년물 & 기준금리", ['#ff7f0e', '#d62728'])
                st.plotly_chart(fig_rate, use_container_width=True)
                g = macro_news.get_macro_interpretation('미국채 10년물 수익률')
                st.info(f"**{g['meaning']}**", icon="💡")
        
        with r1c3: # 하이일드 스프레드
            if '하이일드 스프레드 (Credit Risk)' in fred_df.columns:
                fig_risk = visualization.plot_macro_chart(fred_df, ['하이일드 스프레드 (Credit Risk)'], "하이일드 스프레드 (Risk)", ['#d62728'])
                st.plotly_chart(fig_risk, use_container_width=True)
                g = macro_news.get_macro_interpretation('하이일드 스프레드 (Credit Risk)')
                st.info(f"**{g['meaning']}**\n\n{g['action']}", icon="💡")

        st.divider()

        # --- Row 2: 유동성 & 인플레이션 ---
        st.markdown("#### 2. 유동성 & 물가 (Liquidity & Inflation)")
        r2c1, r2c2, r2c3 = st.columns(3)

        with r2c1: # M2 & 유통속도
            cols_m2 = []
            if 'M2 통화량' in fred_df.columns: cols_m2.append('M2 통화량')
            if 'M2 통화유통속도' in fred_df.columns: cols_m2.append('M2 통화유통속도') # Scale diff process needed ideally, keeping simple
            
            if 'M2 통화량' in fred_df.columns:
                fig_m2 = visualization.plot_macro_chart(fred_df, ['M2 통화량'], "M2 통화량", ['#2ca02c'])
                st.plotly_chart(fig_m2, use_container_width=True)
                g = macro_news.get_macro_interpretation('M2 통화량')
                st.info(f"**{g['meaning']}**", icon="💡")

        with r2c2: # CPI & PCE
            cols_inf = []
            if '소비자물가지수 (CPI)' in fred_df.columns: cols_inf.append('소비자물가지수 (CPI)')
            elif 'CPI' in fred_df.columns: cols_inf.append('CPI')
            if '개인소비지출 (PCE)' in fred_df.columns: cols_inf.append('개인소비지출 (PCE)')
            elif 'PCE' in fred_df.columns: cols_inf.append('PCE')

            if cols_inf:
                fig_inf = visualization.plot_macro_chart(fred_df, cols_inf, "소비자물가(CPI) & PCE", ['#9467bd', '#8c564b'])
                st.plotly_chart(fig_inf, use_container_width=True)
                g = macro_news.get_macro_interpretation('소비자물가지수 (CPI)')
                st.info(f"**{g['meaning']}**", icon="💡")

        with r2c3: # PPI & 기대인플레
            cols_ppi = []
            if '생산자물가지수 (PPI)' in fred_df.columns: cols_ppi.append('생산자물가지수 (PPI)')
            if '5년 기대인플레이션 (BEI)' in fred_df.columns: cols_ppi.append('5년 기대인플레이션 (BEI)')
            
            if cols_ppi:
                 fig_ppi = visualization.plot_macro_chart(fred_df, cols_ppi, "생산자물가(PPI) & 기대인플레", ['#e377c2', '#7f7f7f'])
                 st.plotly_chart(fig_ppi, use_container_width=True)
                 g = macro_news.get_macro_interpretation('생산자물가지수 (PPI)')
                 st.info(f"**{g['meaning']}**", icon="💡")

        st.divider()

        # --- Row 3: 고용 & 경기 ---
        st.markdown("#### 3. 고용 & 경기 (Labor & Economy)")
        r3c1, r3c2, r3c3 = st.columns(3)

        with r3c1: # 실업률 & 샴의 법칙
             cols_un = []
             if '실업률 (Unemployment)' in fred_df.columns: cols_un.append('실업률 (Unemployment)')
             if '샴의 법칙 (불황지표)' in fred_df.columns: cols_un.append('샴의 법칙 (불황지표)')
             
             if cols_un:
                 fig_un = visualization.plot_macro_chart(fred_df, cols_un, "실업률 & 샴의 법칙(불황)", ['#bcbd22', '#17becf'])
                 st.plotly_chart(fig_un, use_container_width=True)
                 g = macro_news.get_macro_interpretation('샴의 법칙 (불황지표)')
                 st.info(f"**{g['meaning']}**", icon="💡")
        
        with r3c2: # 신규 실업수당 & 경제활동참가율
             if '신규 실업수당 청구건수' in fred_df.columns:
                 fig_job = visualization.plot_macro_chart(fred_df, ['신규 실업수당 청구건수'], "신규 실업수당 청구건수", ['#9edae5'])
                 st.plotly_chart(fig_job, use_container_width=True)
                 g = macro_news.get_macro_interpretation('신규 실업수당 청구건수')
                 st.info(f"**{g['meaning']}**", icon="💡")

        with r3c3: # GDP (Real)
            # GDP fetch might be slow or fail, ensure checks
            cols_gdp = []
            if '실질 GDP (Real GDP)' in fred_df.columns: cols_gdp.append('실질 GDP (Real GDP)')
            elif '미국 GDP' in fred_df.columns: cols_gdp.append('미국 GDP')
            
            if cols_gdp:
                fig_gdp = visualization.plot_macro_chart(fred_df, cols_gdp, "미국 GDP 성장", ['#dbdb8d'])
                st.plotly_chart(fig_gdp, use_container_width=True)
                g = macro_news.get_macro_interpretation('미국 GDP')
                st.info(f"**{g['meaning']}**", icon="💡")

        st.divider()

        # --- Row 4: 소비 & 심리 ---
        st.markdown("#### 4. 소비 & 심리 (Consumption & Sentiment)")
        r4c1, r4c2, r4c3 = st.columns(3)

        with r4c1: # 소매판매
             if '소매판매 (Retail Sales)' in fred_df.columns: 
                 fig_ret = visualization.plot_macro_chart(fred_df, ['소매판매 (Retail Sales)'], "소매판매 (Retail Sales)", ['#c5b0d5'])
                 st.plotly_chart(fig_ret, use_container_width=True)
                 g = macro_news.get_macro_interpretation('소매판매 (Retail Sales)')
                 st.info(f"**{g['meaning']}**", icon="💡")

        with r4c2: # 소비자심리지수
             if '소비자심리지수' in fred_df.columns:
                 fig_sent = visualization.plot_macro_chart(fred_df, ['소비자심리지수'], "소비자심리지수", ['#98df8a'])
                 st.plotly_chart(fig_sent, use_container_width=True)
                 g = macro_news.get_macro_interpretation('소비자심리지수')
                 st.info(f"**{g['meaning']}**", icon="💡")

        with r4c3: # VIX
             if '공포지수 (VIX)' in fred_df.columns:
                fig_vix = visualization.plot_macro_chart(fred_df, ['공포지수 (VIX)'], "공포지수 (VIX)", ['#c49c94'])
                st.plotly_chart(fig_vix, use_container_width=True)
                g = macro_news.get_macro_interpretation('공포지수 (VIX)')
                st.info(f"**{g['meaning']}**", icon="💡")

        st.divider()

        # --- Row 5: 자산 클래스 (Assets) ---
        st.markdown("#### 5. 주요 자산 시장 (Key Assets)")
        r5c1, r5c2, r5c3 = st.columns(3)

        with r5c1: # 달러 & 금
             cols_safe = [c for c in ['Dollar Index (DXY)', 'Gold (COMEX)'] if c in comm_df.columns]
             if cols_safe:
                 # 정규화하여 추세 비교
                 norm_safe = (comm_df[cols_safe] - comm_df[cols_safe].mean()) / comm_df[cols_safe].std()
                 fig_safe = visualization.plot_macro_chart(norm_safe, cols_safe, "달러 & 금 (Normalized)", ['#7f7f7f', '#ffd700'])
                 st.plotly_chart(fig_safe, use_container_width=True)
                 g = macro_news.get_macro_interpretation('Dollar Index (DXY)')
                 st.info(f"**달러/금:** 안전자산 선호 심리 및 역상관성 체크", icon="💡")

        with r5c2: # 비트코인
             if 'Bitcoin' in comm_df.columns:
                 fig_btc = visualization.plot_macro_chart(comm_df, ['Bitcoin'], "비트코인 (BTC)", ['#f7931a'])
                 st.plotly_chart(fig_btc, use_container_width=True)
                 g = macro_news.get_macro_interpretation('Bitcoin')
                 st.info(f"**{g['meaning']}**\n\n{g['action']}", icon="💡")

        with r5c3: # 유가 & 구리
             cols_ind = [c for c in ['Crude Oil (WTI)', 'Copper'] if c in comm_df.columns]
             if cols_ind:
                 norm_ind = (comm_df[cols_ind] - comm_df[cols_ind].mean()) / comm_df[cols_ind].std()
                 fig_ind = visualization.plot_macro_chart(norm_ind, cols_ind, "유가 & 구리 (경기민감)", ['#bcbd22', '#d62728'])
                 st.plotly_chart(fig_ind, use_container_width=True)
                 g = macro_news.get_macro_interpretation('Crude Oil (WTI)')
                 st.info(f"**에너지/산업재:** 경기 회복 시 상승 탄력 (닥터 코퍼)", icon="💡")


    # 3. 시장 지도
    with tab3:
        st.header("S&P 500 섹터 순환매 지도 & 트렌드 (Sector Rotation)")
        
        col_opt, col_refresh = st.columns([4, 1])
        with col_opt:
            period_opt = st.radio(
                "분석 기간 선택", 
                ["1d (일간)", "1w (주간)", "1mo (월간)", "1y (연간)", "ytd (연중)"], 
                horizontal=True,
                index=2
            )
            # 매핑
            period_val = period_opt.split(" ")[0]
        
        with col_refresh:
            if st.button("새로고침"): st.cache_data.clear()
        
        # A. 트리맵
        st.subheader("1. 섹터 등락률 지도 (Market Map)")
        with st.spinner(f"S&P 500 섹터별 {period_opt} 데이터 분석 중..."):
            fig_map = visualization.plot_sector_treemap(period=period_val)
            st.plotly_chart(fig_map, use_container_width=True)
            
        st.info("💡 팁: 초록색은 상승, 빨간색은 하락을 의미합니다. 영역 크기는 동일하게 설정되어 있습니다.")

        st.divider()

        # B. 스파크라인 그리드
        st.subheader(f"2. 섹터별 상세 트렌드 차트 ({period_opt})")
        with st.spinner("트렌드 차트 생성 중..."):
            fig_grid = visualization.plot_sparkline_grid(period=period_val)
            st.plotly_chart(fig_grid, use_container_width=True)

if __name__ == "__main__":
    main()
