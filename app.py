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
    tab1, tab2 = st.tabs(["📊 글로벌 거시경제 및 자산 지표 (Macro Expert View)", "🎯 주요 테마 ETF"])

    # 1. 매크로 인텔리전스
    with tab1:
        
        # 글로벌 거시경제 및 자산 지표 대시보드
        st.markdown("### 📊 글로벌 거시경제 및 자산 지표 (Macro Expert View)")
        st.caption("실시간 데이터를 기반으로 한 총 20종 이상의 핵심 거시경제 지표 시각화 대시보드입니다.")
        
        # 데이터 로드
        fred_df = macro_news.get_fred_data()
        comm_df = macro_news.get_commodities_data()
        
        # 탭으로 카테고리 구분 (제거 -> 대시보드 형태)
        # m_tab1, m_tab2, m_tab3, m_tab4 = st.tabs(["💰 금리/유동성", "🏭 경기/고용/물가", "🛢️ 원자재/자산", "😱 심리/공포"])

        # 3열 그리드 생성 (Dashboard Layout)
        
        # --- Row 1: 금리 & 채권 & 리스크 ---
        st.markdown("#### 1. 금리 & 채권 & 리스크 (Rates & Bonds)")
        r1c1, r1c2, r1c3 = st.columns(3)
        
        with r1c1: # 장단기 금리차
            if '장단기 금리차 (10Y-2Y)' in fred_df.columns:
                fig = visualization.plot_macro_chart(fred_df, ['장단기 금리차 (10Y-2Y)'], "장단기 금리차 (10Y-2Y)", ['#1f77b4'])
                st.plotly_chart(fig, use_container_width=True)
                g = macro_news.get_macro_interpretation('장단기 금리차 (10Y-2Y)')
                st.info(f"**{g['meaning']}**\n\n{g['action']}", icon="💡")
        
        with r1c2: # 국채 & 기준금리
             cols_rate = []
             if '미국채 10년물 수익률' in fred_df.columns: cols_rate.append('미국채 10년물 수익률')
             if '기준금리 (Fed Funds)' in fred_df.columns: cols_rate.append('기준금리 (Fed Funds)')
             
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


    # 2. 시장 지도
    with tab2:
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
        
        # B. 스파크라인 테마 (Barometer)
        st.markdown(f"## 🎯 <b>주요 테마 ETF 역학 지도</b> <span style='font-size:18px; color:gray;'>({period_opt})</span>", unsafe_allow_html=True)
        st.caption("5대 핵심 테마별 시장 트렌드와 수익률을 직관적으로 보여주는 ETF 바로미터입니다.")
        st.write("") # 여백 추가
        with st.spinner("테마별 데이터 분석 및 차트 생성 중..."):
            theme_figs = visualization.plot_theme_sparklines(period=period_val)
            
            if theme_figs:
                # 스크린샷과 유사한 분할 레이아웃
                # Left: 섹터 (11개) | Right: 나머지 테마 (4개씩 2x2 배열)
                col_left, col_right = st.columns([1.2, 2.0])
                
                with col_left:
                    # 좌측 전체 (섹터)
                    if "섹터 (Sectors)" in theme_figs:
                        st.plotly_chart(theme_figs["섹터 (Sectors)"], use_container_width=True, config={'displayModeBar': False})
                
                with col_right:
                    # 우측 상단 (가치/성장, 성장)
                    r1c1, r1c2 = st.columns(2)
                    with r1c1:
                        if "가치/성장 (Value & Growth)" in theme_figs:
                            st.plotly_chart(theme_figs["가치/성장 (Value & Growth)"], use_container_width=True, config={'displayModeBar': False})
                    with r1c2:
                        if "성장 (Tech Themes)" in theme_figs:
                            st.plotly_chart(theme_figs["성장 (Tech Themes)"], use_container_width=True, config={'displayModeBar': False})
                    
                    st.divider() # 살짝 구분선
                    
                    # 우측 하단 (배당, 혁신)
                    r2c1, r2c2 = st.columns(2)
                    with r2c1:
                        if "배당 (Dividends)" in theme_figs:
                            st.plotly_chart(theme_figs["배당 (Dividends)"], use_container_width=True, config={'displayModeBar': False})
                    with r2c2:
                        if "혁신 (Innovation)" in theme_figs:
                            st.plotly_chart(theme_figs["혁신 (Innovation)"], use_container_width=True, config={'displayModeBar': False})

if __name__ == "__main__":
    main()
