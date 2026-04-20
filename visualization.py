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

def plot_sparkline_grid(period: str = "1mo"):
    """
    주요 섹터의 미니 차트 그리드 (Tiles with Charts)
    각 섹터를 '카드' 형태로 표현하고, 배경색으로 등락을 표현합니다.
    """
    sectors = {
        'XLK': '기술', 'XLV': '헬스케어', 'XLF': '금융',
        'XLY': '임의소비재', 'XLP': '필수소비재', 'XLE': '에너지',
        'XLI': '산업재', 'XLC': '커뮤니케이션', 'XLB': '소재',
        'XLRE': '부동산', 'XLU': '유틸리티'
    }
    tickers = list(sectors.keys())
    
    # Period Mapping
    yf_p = "3mo"
    if period == "1d": yf_p = "5d" 
    elif period == "1w": yf_p = "1mo"
    elif period == "1mo": yf_p = "3mo"
    elif period == "1y" or period == "ytd": yf_p = "1y"

    try:
        df = yf.download(tickers, period=yf_p, progress=False)['Close']
        if df.empty: return go.Figure()
        
        # Subplots (Grid 4x3)
        fig = make_subplots(
            rows=4, cols=3, 
            subplot_titles=[f"{t} ({sectors[t]})" for t in tickers],
            vertical_spacing=0.1,
            horizontal_spacing=0.05
        )
        
        row, col = 1, 1
        for ticker in tickers:
            if ticker in df.columns:
                series = df[ticker].dropna()
                if series.empty: continue

                # 등락률 계산
                start_val = series.iloc[0]
                end_val = series.iloc[-1]
                pct_change = ((end_val - start_val) / start_val) * 100
                
                # 색상 결정 (배경색 스타일링을 위해 Annotation 활용 예정)
                # 차트 선 색상: 상승=진한 초록, 하락=진한 빨강
                # 배경: 상승=연한 초록, 하락=연한 빨강 (Plotly shape로 구현)
                
                line_color = '#006400' if pct_change >= 0 else '#8B0000' # Dark Green / Dark Red
                bg_color = 'rgba(144, 238, 144, 0.3)' if pct_change >= 0 else 'rgba(255, 182, 193, 0.3)' # Light Green / Light Red
                
                # 1. 배경 사각형 추가 (Shape)
                # Subplot의 Domain을 정확히 알기 어려우므로, 전체 영역에 shape를 추가하는 방식 대신
                # 차트 영역의 배경색(plot_bgcolor)을 개별 제어하기는 어려움.
                # 대안: Filled Area Chart로 하단을 채우거나, Annotation으로 박스 그리기.
                # 여기서는 가독성을 위해 '선 차트 + 영역 채우기'로 타일 느낌 강조.
                
                fig.add_trace(
                    go.Scatter(
                        x=series.index, y=series.values, 
                        mode='lines', 
                        line=dict(color=line_color, width=2),
                        fill='tozeroy', # 바닥까지 채우기
                        fillcolor=bg_color, # 연한 배경색
                        name=ticker
                    ),
                    row=row, col=col
                )
                
                # 2. 수치 텍스트 (우측 상단)
                fig.add_annotation(
                    x=series.index[-1], y=end_val,
                    text=f"{end_val:.1f}<br>({pct_change:+.1f}%)",
                    showarrow=False,
                    font=dict(color=line_color, size=12, family="Arial Black"),
                    xanchor="left", yanchor="bottom",
                    row=row, col=col
                )

                # Y축 범위 조정 (여백 확보)
                min_y, max_y = series.min(), series.max()
                margin = (max_y - min_y) * 0.2
                fig.update_yaxes(range=[min_y - margin, max_y + margin], row=row, col=col, showticklabels=False, visible=False)
                fig.update_xaxes(showticklabels=False, visible=False, row=row, col=col)

            col += 1
            if col > 3:
                col = 1
                row += 1
        
        fig.update_layout(
            height=900, 
            title_text=f"섹터별 상세 트렌드 카드 ({yf_p}) - 배경색: 등락 방향",
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)', # 투명 배경
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig

    except Exception as e:
        print(f"Sparkline error: {e}")
        return go.Figure()

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
