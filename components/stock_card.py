"""
Stock Card Component - 個股詳情卡片
"""
import streamlit as st
from config import COLORS
from src.strategy_advisor import ADVICE_COLORS


def render_stock_card(
    symbol: str,
    name: str,
    current_price: float,
    change_pct: float,
    cost: float,
    shares: int,
    advice: dict,
    kd_status: dict,
    volume_analysis: dict,
    chart_fig,
    is_new_entry: bool = False
):
    """
    渲染個股詳情卡片
    
    Args:
        symbol: 股票代碼
        name: 股票名稱
        current_price: 現價
        change_pct: 漲跌幅
        cost: 成本價
        shares: 股數(張)
        advice: Strategy advice dict
        kd_status: KD indicator status
        volume_analysis: Volume analysis dict
        chart_fig: Plotly figure
        is_new_entry: 是否為新進場
    """
    # Calculate P&L
    pnl_pct = (current_price - cost) / cost * 100 if cost > 0 else 0
    pnl_value = (current_price - cost) * shares
    market_value = current_price * shares
    
    # Colors
    price_change_color = COLORS["success"] if change_pct >= 0 else COLORS["danger"]
    pnl_color = COLORS["success"] if pnl_pct >= 0 else COLORS["danger"]
    advice_color = ADVICE_COLORS.get(advice.get("type", "neutral"), COLORS["neutral"])
    
    # Badge for new entry
    badge_html = ""
    if is_new_entry:
        badge_html = f"""
        <span style="
            background: {COLORS['success']};
            color: #000;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
        ">✨ 新進場</span>
        """
    
    # Title with price info
    title = f"{symbol} {name} | ${current_price:.2f} ({change_pct:+.2f}%)"
    
    with st.expander(title, expanded=True):
        # Advice alert box
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {advice_color}20 0%, {advice_color}10 100%);
            border-left: 4px solid {advice_color};
            border-radius: 0 8px 8px 0;
            padding: 16px;
            margin-bottom: 16px;
        ">
            <p style="margin: 0; color: #FFFFFF; font-size: 14px; line-height: 1.6;">
                {advice.get('text', '')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Info cards row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="
                background: rgba(30, 33, 48, 0.8);
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                border: 1px solid rgba(255,255,255,0.1);
            ">
                <p style="margin: 0; color: #9CA3AF; font-size: 11px;">成本價</p>
                <p style="margin: 4px 0 0 0; color: #FFFFFF; font-size: 18px; font-weight: 600;">
                    ${cost:.2f}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="
                background: rgba(30, 33, 48, 0.8);
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                border: 1px solid rgba(255,255,255,0.1);
            ">
                <p style="margin: 0; color: #9CA3AF; font-size: 11px;">持有張數</p>
                <p style="margin: 4px 0 0 0; color: #FFFFFF; font-size: 18px; font-weight: 600;">
                    {shares // 1000} 張
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {pnl_color}20 0%, {pnl_color}10 100%);
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                border: 1px solid {pnl_color}40;
            ">
                <p style="margin: 0; color: #9CA3AF; font-size: 11px;">損益</p>
                <p style="margin: 4px 0 0 0; color: {pnl_color}; font-size: 18px; font-weight: 600;">
                    {pnl_pct:+.2f}%
                </p>
                <p style="margin: 2px 0 0 0; color: {pnl_color}; font-size: 11px;">
                    ${pnl_value:+,.0f}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            kd_color = kd_status.get("color", COLORS["neutral"])
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {kd_color}20 0%, {kd_color}10 100%);
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                border: 1px solid {kd_color}40;
            ">
                <p style="margin: 0; color: #9CA3AF; font-size: 11px;">KD 狀態</p>
                <p style="margin: 4px 0 0 0; color: {kd_color}; font-size: 16px; font-weight: 600;">
                    {kd_status.get('status', 'N/A')}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Volume status
        vol_ratio = volume_analysis.get("ratio", 0)
        vol_status = volume_analysis.get("status", "N/A")
        vol_desc = volume_analysis.get("description", "")
        
        if vol_ratio >= 1.5:
            vol_color = COLORS["success"]
        elif vol_ratio <= 0.5:
            vol_color = COLORS["warning"]
        else:
            vol_color = COLORS["neutral"]
        
        st.markdown(f"""
        <div style="
            background: rgba(30, 33, 48, 0.6);
            border-radius: 8px;
            padding: 10px 16px;
            margin: 12px 0;
            display: flex;
            align-items: center;
            gap: 12px;
            border: 1px solid rgba(255,255,255,0.05);
        ">
            <span style="color: {vol_color}; font-size: 14px;">📊 {vol_status}</span>
            <span style="color: #6C7A89; font-size: 12px;">|</span>
            <span style="color: #9CA3AF; font-size: 12px;">{vol_desc}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Chart
        st.plotly_chart(chart_fig, use_container_width=True, config={'displayModeBar': False})


def render_empty_state():
    """渲染空狀態"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1E2130 0%, #252A40 100%);
        border-radius: 16px;
        padding: 60px 40px;
        text-align: center;
        border: 2px dashed rgba(99, 102, 241, 0.3);
        margin: 24px 0;
    ">
        <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
        <h3 style="color: #FFFFFF; margin: 0 0 8px 0;">尚無持股資料</h3>
        <p style="color: #9CA3AF; margin: 0; font-size: 14px;">
            請使用左側選單新增持股，開始您的交易追蹤之旅
        </p>
    </div>
    """, unsafe_allow_html=True)
