"""
Charts Module - Plotly 圖表生成
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from config import CHART_COLORS


def create_candlestick_chart(
    df: pd.DataFrame,
    symbol: str,
    name: str = "",
    show_volume: bool = True,
    show_kd: bool = True
) -> go.Figure:
    """
    創建 K 線圖 + 成交量 + KD 指標
    
    Args:
        df: OHLCV DataFrame with K, D columns
        symbol: 股票代碼
        name: 股票名稱
        show_volume: 是否顯示成交量
        show_kd: 是否顯示 KD 指標
    
    Returns:
        Plotly Figure
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="無資料可顯示",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="#9CA3AF")
        )
        return fig
    
    # Determine number of rows
    rows = 1
    row_heights = [0.6]
    if show_volume:
        rows += 1
        row_heights.append(0.2)
    if show_kd:
        rows += 1
        row_heights.append(0.2)
    
    # Create subplots
    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=None
    )
    
    # Colors for candlestick
    colors = [CHART_COLORS['up'] if close >= open_ else CHART_COLORS['down'] 
              for open_, close in zip(df['Open'], df['Close'])]
    
    # 1. Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='K線',
            increasing_line_color=CHART_COLORS['up'],
            decreasing_line_color=CHART_COLORS['down'],
            increasing_fillcolor=CHART_COLORS['up'],
            decreasing_fillcolor=CHART_COLORS['down'],
        ),
        row=1, col=1
    )
    
    current_row = 2
    
    # 2. Volume chart
    if show_volume and 'Volume' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='成交量',
                marker_color=colors,
                opacity=0.7
            ),
            row=current_row, col=1
        )
        fig.update_yaxes(title_text="成交量", row=current_row, col=1)
        current_row += 1
    
    # 3. KD indicator
    if show_kd and 'K' in df.columns and 'D' in df.columns:
        # K line
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['K'],
                name='K',
                line=dict(color=CHART_COLORS['k_line'], width=2),
                mode='lines'
            ),
            row=current_row, col=1
        )
        # D line
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['D'],
                name='D',
                line=dict(color=CHART_COLORS['d_line'], width=2),
                mode='lines'
            ),
            row=current_row, col=1
        )
        
        # Overbought/Oversold lines
        fig.add_hline(y=80, line_dash="dash", line_color="#FF6B6B", 
                      opacity=0.5, row=current_row, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="#00D4AA", 
                      opacity=0.5, row=current_row, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#6C7A89", 
                      opacity=0.3, row=current_row, col=1)
        
        fig.update_yaxes(title_text="KD", range=[0, 100], row=current_row, col=1)
    
    # Update layout
    title_text = f"{symbol} {name}" if name else symbol
    
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=16, color='#FFFFFF'),
            x=0.5
        ),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30, 33, 48, 0.8)',
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10)
        ),
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode='x unified'
    )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        showline=True,
        linewidth=1,
        linecolor='rgba(128, 128, 128, 0.3)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        showline=True,
        linewidth=1,
        linecolor='rgba(128, 128, 128, 0.3)'
    )
    
    return fig


def create_mini_chart(df: pd.DataFrame, color: str = "#6366F1") -> go.Figure:
    """
    創建迷你走勢圖 (用於卡片)
    
    Args:
        df: OHLCV DataFrame
        color: 線條顏色
    
    Returns:
        Plotly Figure
    """
    if df.empty:
        fig = go.Figure()
        return fig
    
    is_positive = df['Close'].iloc[-1] >= df['Close'].iloc[0]
    line_color = CHART_COLORS['up'] if is_positive else CHART_COLORS['down']
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['Close'],
            mode='lines',
            line=dict(color=line_color, width=2),
            fill='tozeroy',
            fillcolor=f'rgba({int(line_color[1:3], 16)}, {int(line_color[3:5], 16)}, {int(line_color[5:7], 16)}, 0.1)'
        )
    )
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        height=100,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    
    return fig


def create_kd_gauge(k_value: float, d_value: float) -> go.Figure:
    """
    創建 KD 儀表盤
    
    Args:
        k_value: K 值
        d_value: D 值
    
    Returns:
        Plotly Figure
    """
    # Determine color based on K value
    if k_value >= 80:
        color = CHART_COLORS['down']  # Overbought - red
    elif k_value <= 20:
        color = CHART_COLORS['up']    # Oversold - green
    else:
        color = CHART_COLORS['k_line']  # Normal - yellow
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=k_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"K值<br><span style='font-size:0.8em;color:#9CA3AF'>D值: {d_value:.1f}</span>"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#6C7A89"},
            'bar': {'color': color},
            'bgcolor': "rgba(30, 33, 48, 0.8)",
            'borderwidth': 2,
            'bordercolor': "#6C7A89",
            'steps': [
                {'range': [0, 20], 'color': 'rgba(0, 212, 170, 0.3)'},
                {'range': [20, 80], 'color': 'rgba(108, 122, 137, 0.2)'},
                {'range': [80, 100], 'color': 'rgba(255, 107, 107, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "#FFFFFF", 'width': 4},
                'thickness': 0.75,
                'value': k_value
            }
        }
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        height=200,
        margin=dict(l=20, r=20, t=50, b=20),
        font={'color': "#FFFFFF", 'family': "Arial"}
    )
    
    return fig
