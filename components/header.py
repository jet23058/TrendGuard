"""
Header Component - 戰情總覽
"""
import streamlit as st
from datetime import datetime
from config import COLORS


def render_header(portfolio_stats: dict, date_str: str = None):
    """
    渲染戰情總覽區塊
    
    Args:
        portfolio_stats: Portfolio statistics dict
        date_str: Display date string
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y年%m月%d日")
    
    # Header container
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1E2130 0%, #2D3250 100%);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        border: 1px solid rgba(99, 102, 241, 0.3);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div>
                <h1 style="
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                    background: linear-gradient(90deg, #6366F1, #A78BFA);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                ">🎯 利弗摩爾台股戰情室</h1>
                <p style="margin: 8px 0 0 0; color: #9CA3AF; font-size: 14px;">
                    📅 {date_str} | Livermore Trader Dashboard
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats cards
    total_value = portfolio_stats.get("total_value", 0)
    total_pnl = portfolio_stats.get("total_pnl", 0)
    total_pnl_pct = portfolio_stats.get("total_pnl_pct", 0)
    stock_count = portfolio_stats.get("stock_count", 0)
    
    pnl_color = COLORS["success"] if total_pnl >= 0 else COLORS["danger"]
    pnl_icon = "📈" if total_pnl >= 0 else "📉"
    
    # Position status
    if stock_count == 0:
        position_status = "空手等待"
        position_color = COLORS["neutral"]
    elif stock_count <= 3:
        position_status = "理想持股"
        position_color = COLORS["success"]
    else:
        position_status = "過度分散"
        position_color = COLORS["warning"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(99, 102, 241, 0.05) 100%);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(99, 102, 241, 0.3);
            text-align: center;
        ">
            <p style="margin: 0; color: #9CA3AF; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">總市值</p>
            <h2 style="margin: 8px 0; color: #FFFFFF; font-size: 28px; font-weight: 700;">
                ${total_value:,.0f}
            </h2>
            <p style="margin: 0; color: #6366F1; font-size: 12px;">💰 Total Value</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba({int(pnl_color[1:3], 16)}, {int(pnl_color[3:5], 16)}, {int(pnl_color[5:7], 16)}, 0.2) 0%, rgba({int(pnl_color[1:3], 16)}, {int(pnl_color[3:5], 16)}, {int(pnl_color[5:7], 16)}, 0.05) 100%);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid {pnl_color}40;
            text-align: center;
        ">
            <p style="margin: 0; color: #9CA3AF; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">總損益</p>
            <h2 style="margin: 8px 0; color: {pnl_color}; font-size: 28px; font-weight: 700;">
                {pnl_icon} {total_pnl:+,.0f}
            </h2>
            <p style="margin: 0; color: {pnl_color}; font-size: 12px;">({total_pnl_pct:+.2f}%)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba({int(position_color[1:3], 16)}, {int(position_color[3:5], 16)}, {int(position_color[5:7], 16)}, 0.2) 0%, rgba({int(position_color[1:3], 16)}, {int(position_color[3:5], 16)}, {int(position_color[5:7], 16)}, 0.05) 100%);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid {position_color}40;
            text-align: center;
        ">
            <p style="margin: 0; color: #9CA3AF; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">持股檔數</p>
            <h2 style="margin: 8px 0; color: #FFFFFF; font-size: 28px; font-weight: 700;">
                {stock_count} 檔
            </h2>
            <p style="margin: 0; color: {position_color}; font-size: 12px;">{position_status} (建議 ≤3)</p>
        </div>
        """, unsafe_allow_html=True)
