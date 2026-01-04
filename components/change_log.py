"""
Change Log Component - 異動快報
"""
import streamlit as st
from config import COLORS


def render_change_log(changes: dict):
    """
    渲染異動快報區塊
    
    Args:
        changes: Dict with new_entries, exits, holdings
    """
    new_entries = changes.get("new_entries", [])
    exits = changes.get("exits", [])
    
    # Only show if there are changes
    if not new_entries and not exits:
        return
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1E2130 0%, #252A40 100%);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
        border: 1px solid rgba(99, 102, 241, 0.2);
    ">
        <h3 style="margin: 0 0 16px 0; color: #FFFFFF; font-size: 18px;">
            📋 異動快報
        </h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: rgba(0, 212, 170, 0.1);
            border-radius: 8px;
            padding: 16px;
            border: 1px solid rgba(0, 212, 170, 0.3);
            min-height: 100px;
        ">
            <h4 style="margin: 0 0 12px 0; color: {COLORS['success']}; font-size: 14px;">
                ✨ 新進場
            </h4>
        """, unsafe_allow_html=True)
        
        if new_entries:
            for stock in new_entries:
                st.markdown(f"""
                <div style="
                    background: rgba(0, 212, 170, 0.15);
                    border-radius: 6px;
                    padding: 10px 12px;
                    margin-bottom: 8px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <div>
                        <span style="color: #FFFFFF; font-weight: 600;">{stock['symbol']}</span>
                        <span style="color: #9CA3AF; font-size: 12px; margin-left: 8px;">{stock['name']}</span>
                    </div>
                    <span style="color: {COLORS['success']}; font-size: 12px;">
                        成本 ${stock['cost']:.2f}
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <p style="color: #6C7A89; font-size: 13px; margin: 0; text-align: center;">
                今日無新進場
            </p>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: rgba(108, 122, 137, 0.1);
            border-radius: 8px;
            padding: 16px;
            border: 1px solid rgba(108, 122, 137, 0.3);
            min-height: 100px;
        ">
            <h4 style="margin: 0 0 12px 0; color: {COLORS['neutral']}; font-size: 14px;">
                🗑️ 已離場
            </h4>
        """, unsafe_allow_html=True)
        
        if exits:
            for stock in exits:
                st.markdown(f"""
                <div style="
                    background: rgba(108, 122, 137, 0.15);
                    border-radius: 6px;
                    padding: 10px 12px;
                    margin-bottom: 8px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <div>
                        <span style="color: #9CA3AF; font-weight: 600; text-decoration: line-through;">{stock['symbol']}</span>
                        <span style="color: #6C7A89; font-size: 12px; margin-left: 8px;">{stock['name']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <p style="color: #6C7A89; font-size: 13px; margin: 0; text-align: center;">
                今日無離場
            </p>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
