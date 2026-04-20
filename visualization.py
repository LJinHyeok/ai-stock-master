import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import yfinance as yf

def plot_candlestick(df: pd.DataFrame, title: str = "Stock Price"):
    """
    캔들스틱 차트와 거래량, 주요 이동평균선(SMA), 볼린저 밴드를 시각화합니다.
    """
    # 서브플롯 생성 (상단: 캔들스틱, 하단: 거래량)
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        subplot_titles=(f"{title}", "Volume"),
        row_heights=[0.7, 0.3]
    )

    # 1. 캔들스틱
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="OHLC"
    ), row=1, col=1)

    # 2. 이동평균선 (SMA 20, 50)
    if 'SMA_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='orange', width=1), name='SMA 20'), row=1, col=1)
    if 'SMA_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='blue', width=1), name='SMA 50'), row=1, col=1)

    # 3. 볼린저 밴드
    bbu = [c for c in df.columns if 'BBU' in c]
    bbl = [c for c in df.columns if 'BBL' in c]
    if bbu and bbl:
        fig.add_trace(go.Scatter(x=df.index, y=df[bbu[0]], line=dict(color='gray', width=1, dash='dot'), name='Upper Band'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df[bbl[0]], line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(128,128,128,0.1)', name='Lower Band'), row=1, col=1)

    # 4. 일목균형표
    span_a = [c for c in df.columns if 'ISA' in c]
    span_b = [c for c in df.columns if 'ISB' in c]
    if span_a and span_b:
         fig.add_trace(go.Scatter(x=df.index, y=df[span_a[0]], line=dict(width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
         fig.add_trace(go.Scatter(x=df.index, y=df[span_b[0]], line=dict(width=0), fill='tonexty', fillcolor='rgba(0, 250, 154, 0.1)', name='Ichimoku Cloud'), row=1, col=1)

    # 5. 거래량
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='rgba(100, 100, 100, 0.5)'), row=2, col=1)

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=600,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def plot_rsi(df: pd.DataFrame):
    if 'RSI_14' not in df.columns: return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI_14'], name='RSI 14', line=dict(color='purple')))
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
    fig.update_layout(title="RSI (14)", height=300, yaxis_range=[0, 100])
    return fig

def plot_macd(df: pd.DataFrame):
    macd_col = 'MACD_12_26_9'
    signal_col = 'MACDs_12_26_9'
    hist_col = 'MACDh_12_26_9'
    if macd_col not in df.columns: return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[macd_col], name='MACD', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df.index, y=df[signal_col], name='Signal', line=dict(color='orange')))
    fig.add_trace(go.Bar(x=df.index, y=df[hist_col], name='Histogram', marker_color='gray'))
    fig.update_layout(title="MACD", height=300)
    return fig

def plot_heatmap(corr_matrix: pd.DataFrame, title: str = "Correlation Heatmap"):
    fig = px.imshow(
        corr_matrix, 
        text_auto=".2f", 
        aspect="auto",
        title=title,
        color_continuous_scale='RdBu_r',
        zmin=-1, zmax=1
    )
    return fig

def plot_sector_treemap(period: str = "5d"):
    """
    S&P 500 주요 섹터 ETF 데이터를 가져와 Treemap을 그립니다.
    일간(1d), 주간(5d), 월간(1mo), 연간(1y), 연중(ytd) 등 기간별 등락률을 시각화합니다.
    """
    sectors = {
        'XLK': '기술 (Technology)',
        'XLV': '헬스케어 (Healthcare)',
        'XLF': '금융 (Financials)',
        'XLY': '임의소비재 (Cons. Disc.)',
        'XLP': '필수소비재 (Cons. Staples)',
        'XLE': '에너지 (Energy)',
        'XLI': '산업재 (Industrials)',
        'XLC': '커뮤니케이션 (Comm. Svcs)',
        'XLB': '소재 (Materials)',
        'XLRE': '부동산 (Real Estate)',
        'XLU': '유틸리티 (Utilities)'
    }
    
    tickers = list(sectors.keys())
    data_list = []
    
    # yfinance period mapping
    yf_period = "1mo" 
    if period == "1d": yf_period = "5d"
    elif period == "1w": yf_period = "1mo"
    elif period == "1mo": yf_period = "3mo"
    elif period == "1y" or period == "ytd": yf_period = "2y" # 넉넉히
    
    try:
        # 데이터 일괄 다운로드
        df = yf.download(tickers, period=yf_period, progress=False)['Close']
        
        if df.empty:
            return go.Figure()

        # 기간별 등락률 계산 로직
        if len(df) < 2: return go.Figure()

        current = df.iloc[-1]
        
        # 비교 시점 결정
        if period == "1d":
            prev = df.iloc[-2]
        elif period == "1w":
            idx = -6 if len(df) >= 6 else 0
            prev = df.iloc[idx]
        elif period == "1mo":
            idx = -21 if len(df) >= 21 else 0
            prev = df.iloc[idx]
        elif period == "1y":
            idx = -252 if len(df) >= 252 else 0
            prev = df.iloc[idx]
        elif period == "ytd":
            # 연초 대비
            current_year = df.index[-1].year
            start_of_year = df[df.index.year == current_year]
            if not start_of_year.empty:
                prev = start_of_year.iloc[0]
            else:
                prev = df.iloc[0] # Fallback
        else:
             prev = df.iloc[-2]

        for ticker in tickers:
            if ticker in current.index:
                # 등락률 계산
                pct_change = ((current[ticker] - prev[ticker]) / prev[ticker]) * 100
                data_list.append({
                    'Ticker': ticker,
                    'Sector': sectors[ticker],
                    'Change(%)': pct_change,
                    'Value': 1 
                })

        treemap_df = pd.DataFrame(data_list)
        
        title_map = {"1d": "일간", "1w": "주간", "1mo": "월간", "1y": "연간(1 Year)", "ytd": "연중(YTD)"}
        p_title = title_map.get(period, period)
        
        fig = px.treemap(
            treemap_df, 
            path=['Sector', 'Ticker'], 
            values='Value',
            color='Change(%)',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0,
            title=f"S&P 500 섹터별 등락률 ({p_title} 기준)"
        )
        
        fig.update_layout(height=600)
        fig.data[0].texttemplate = "<b>%{label}</b><br>%{color:.2f}%"
        
        return fig
        
    except Exception as e:
        print(f"Treemap error: {e}")
        return go.Figure()

def plot_theme_sparklines(period: str = "1mo"):
    """
    주요 테마별 ETF의 미니 스파크라인 차트트
    섹터, 가치/성장, 성장(테마), 배당, 혁신 그룹으로 분리하여 각각 Subplot Figure 생성성
    """
    themes = {
        "섹터 (Sectors)": {
            'XLK': '정보기술', 'XLV': '헬스케어', 'XLF': '금융',
            'XLC': '커뮤니케이션', 'XLY': '소비순환재', 'XLP': '경기방어주',
            'XLI': '산업재', 'XLU': '유틸리티', 'XLE': '에너지',
            'XLRE': '부동산(리츠)', 'XLB': '소재'
        },
        "가치/성장 (Value & Growth)": {
            'VUG': '대형성장', 'IWP': '중형성장', 'VTV': '대형가치', 'VOE': '중형가치'
        },
        "성장 (Tech Themes)": {
            'SOXX': '반도체', 'SKYY': '클라우드', 'AIQ': '인공지능', 'CIBR': '사이버보안'
        },
        "배당 (Dividends)": {
            'VIG': '기술배당', 'SCHD': '배당성장', 'VNQ': '리츠', 'JEPQ': '커버드콜'
        },
        "혁신 (Innovation)": {
            'BOTZ': '로봇', 'URA': '원전', 'IBIT': '비트코인', 'ARKK': '혁신'
        }
    }
    
    # Collect all tickers
    all_tickers = []
    for t_dict in themes.values():
        all_tickers.extend(list(t_dict.keys()))
        
    all_tickers = list(set(all_tickers))
    
    # Period Mapping
    yf_p = "3mo"
    if period == "1d": yf_p = "5d" 
    elif period == "1w": yf_p = "1mo"
    elif period == "1mo": yf_p = "3mo"
    elif period == "1y" or period == "ytd": yf_p = "1y"

    try:
        df = yf.download(all_tickers, period=yf_p, progress=False)['Close']
        if df.empty: return {}
        
        figs = {}
        for theme_name, tickers_dict in themes.items():
            tickers = list(tickers_dict.keys())
            rows = len(tickers)
            
            fig = make_subplots(
                rows=rows, cols=1,
                vertical_spacing=0.03
            )
            
            row = 1
            for ticker in tickers:
                if ticker in df.columns:
                    series = df[ticker].dropna()
                    if series.empty: continue
                    
                    start_val = series.iloc[0]
                    end_val = series.iloc[-1]
                    pct_change = ((end_val - start_val) / start_val) * 100
                    
                    line_color = '#d62728' if pct_change < 0 else '#2ca02c' 
                    bg_color = 'rgba(214, 39, 40, 0.2)' if pct_change < 0 else 'rgba(44, 160, 44, 0.2)'
                    
                    fig.add_trace(
                        go.Scatter(
                            x=series.index, y=series.values,
                            mode='lines',
                            line=dict(color=line_color, width=1.5),
                            fill='tozeroy',
                            fillcolor=bg_color,
                            name=ticker
                        ),
                        row=row, col=1
                    )
                    
                    # Annotations Using Plotly Subplot Domain Coordinates
                    x_domain_ref = "x domain" if row == 1 else f"x{row} domain"
                    y_domain_ref = "y domain" if row == 1 else f"y{row} domain"

                    name_ko = tickers_dict[ticker]
                    
                    fig.add_annotation(
                        x=0.01, y=0.5, xref=x_domain_ref, yref=y_domain_ref,
                        text=f"<b>{name_ko}</b> <span style='font-size:10px; color:gray;'>{ticker}</span>",
                        showarrow=False, xanchor="left", yanchor="middle",
                        font=dict(size=13)
                    )
                    
                    fig.add_annotation(
                        x=0.99, y=0.5, xref=x_domain_ref, yref=y_domain_ref,
                        text=f"<b>${end_val:.2f}</b>  <span style='color:{line_color};'><b>{pct_change:+.1f}%</b></span>",
                        showarrow=False, xanchor="right", yanchor="middle",
                        font=dict(size=13)
                    )
                    
                    min_y, max_y = series.min(), series.max()
                    margin = (max_y - min_y) * 0.4
                    # Handle flat charts (e.g. constant price)
                    if margin == 0: margin = end_val * 0.01
                        
                    fig.update_yaxes(range=[min_y - margin, max_y + margin], showgrid=False, showticklabels=False, zeroline=False, row=row, col=1)
                    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False, row=row, col=1)
                
                row += 1
            
            height = rows * 45 + 50 # Calculate responsive height
            fig.update_layout(
                height=height,
                title=dict(text=f"<b>■ {theme_name}</b>", font=dict(size=16)),
                margin=dict(l=5, r=5, t=40, b=5),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            figs[theme_name] = fig
            
        return figs

    except Exception as e:
        print(f"Theme sparkline error: {e}")
        return {}

def plot_macro_chart(df: pd.DataFrame, columns: list, title: str, colors: list = None):
    """
    매크로 지표용 Plotly Line Chart
    마우스 오버 시 수치 확인 가능하도록 개선
    """
    if df.empty: return go.Figure()
    
    fig = go.Figure()
    
    # 색상 팔레트
    default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    if not colors: colors = default_colors
    
    for i, col in enumerate(columns):
        if col in df.columns:
            # 결측치 제거 후 플롯
            series = df[col].dropna()
            color = colors[i % len(colors)]
            
            fig.add_trace(go.Scatter(
                x=series.index, 
                y=series.values,
                mode='lines',
                name=col,
                line=dict(width=2, color=color)
            ))
            
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, weight="bold")), # Title Font Size Up
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=12)),
        hovermode="x unified",
        font=dict(size=14) # Global Font Size Up
    )
    
    fig.update_xaxes(tickfont=dict(size=12))
    fig.update_yaxes(tickfont=dict(size=12))
    
    return fig
