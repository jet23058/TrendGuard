"""
趨勢守衛者 (Livermore Trader Dashboard)
Main Application - Watchlist Mode
"""
import streamlit as st
from datetime import datetime
from pathlib import Path

# Local imports
from config import COLORS, DATA_PERIOD
from src.data_fetcher import get_stock_data, get_current_price, get_stock_info
from src.watchlist_manager import (
    load_watchlist, save_watchlist, detect_watchlist_changes,
    add_to_watchlist, remove_from_watchlist,
    get_previous_trading_date, get_sample_stocks
)
from src.technical_analysis import (
    calculate_kd, detect_kd_cross, get_kd_status,
    get_volume_analysis, detect_breakout
)
from src.strategy_advisor import check_risk_status
from src.charts import create_candlestick_chart


# Page config
st.set_page_config(
    page_title="趨勢守衛者",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_path = Path("styles/custom.css")
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = load_watchlist()
    if 'yesterday_watchlist' not in st.session_state:
        yesterday_date = get_previous_trading_date()
        st.session_state.yesterday_watchlist = load_watchlist(yesterday_date)
    if 'refresh_trigger' not in st.session_state:
        st.session_state.refresh_trigger = 0


def refresh_data():
    """Refresh all data"""
    st.session_state.refresh_trigger += 1
    st.session_state.watchlist = load_watchlist()
    yesterday_date = get_previous_trading_date()
    st.session_state.yesterday_watchlist = load_watchlist(yesterday_date)


def render_header():
    """Render header section"""
    today_str = datetime.now().strftime("%Y年%m月%d日")
    
    # 定義 Tooltip 的 CSS 樣式
    tooltip_style = """
    <style>
        /* Tooltip 容器 */
        .livermore-tooltip {
            position: relative;
            display: inline-block;
            margin-left: 12px;
            vertical-align: middle;
            cursor: pointer;
        }

        /* i 圖示樣式 */
        .livermore-tooltip .info-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 1px solid #6366F1;
            color: #A78BFA;
            font-size: 14px;
            font-weight: bold;
            font-family: serif;
            font-style: italic;
            transition: all 0.2s ease;
        }

        /* 滑鼠移上去時圖示變色 */
        .livermore-tooltip:hover .info-icon {
            background: #6366F1;
            color: #FFFFFF;
        }

        /* 彈出說明框樣式 (黃色底) */
        .livermore-tooltip .tooltip-content {
            visibility: hidden;
            width: 340px;
            background-color: #FEFCE8; /* 淺黃色背景 */
            color: #854D0E;            /* 深褐色文字 */
            text-align: left;
            border-radius: 12px;
            padding: 16px;
            
            /* 定位 */
            position: absolute;
            z-index: 999;
            top: 135%;
            left: 50%;
            transform: translateX(-50%);
            
            /* 特效 */
            opacity: 0;
            transition: opacity 0.3s, top 0.3s;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid #FDE047; /* 黃色邊框 */
            
            /* 文字設定 */
            font-size: 14px;
            line-height: 1.6;
            font-weight: normal;
            white-space: normal;
        }

        /* 小三角形箭頭 */
        .livermore-tooltip .tooltip-content::after {
            content: "";
            position: absolute;
            bottom: 100%;
            left: 50%;
            margin-left: -8px;
            border-width: 8px;
            border-style: solid;
            border-color: transparent transparent #FEFCE8 transparent;
        }

        /* Hover 時顯示說明框 */
        .livermore-tooltip:hover .tooltip-content {
            visibility: visible;
            opacity: 1;
            top: 125%;
        }
    </style>
    """
    
    st.markdown(f"""
    {tooltip_style}
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
                <div style="display: flex; align-items: center;">
                    <h1 style="
                        margin: 0;
                        font-size: 28px;
                        font-weight: 700;
                        background: linear-gradient(90deg, #6366F1, #A78BFA);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                    ">🎯 趨勢守衛者</h1>
                    
                    <div class="livermore-tooltip">
                        <span class="info-icon">i</span>
                        <div class="tooltip-content">
                            <strong style="font-size: 16px; display: block; margin-bottom: 8px; color: #713F12; border-bottom: 1px solid #FDE047; padding-bottom: 4px;">
                                📖 關於傑西·利弗摩爾 (Jesse Livermore)
                            </strong>
                            <span style="font-size: 13px;">被譽為「投機之王」，本系統基於其《股票作手回憶錄》之核心哲學設計：</span>
                            <ul style="margin: 8px 0 0 16px; padding: 0; list-style-type: circle;">
                                <li><strong>順勢而為：</strong>不猜頭摸底，沿著最小阻力線操作。</li>
                                <li><strong>關鍵點 (Pivot Points)：</strong>耐心等待股價突破關鍵價位再進場。</li>
                                <li><strong>資金管理：</strong>虧損絕不超過本金 10%，嚴格執行停損。</li>
                                <li><strong>試單與加碼：</strong>分批進場，只有在賺錢時才加碼 (Add up)。</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <p style="margin: 8px 0 0 0; color: #9CA3AF; font-size: 14px;">
                    📅 {today_str} | 每日觀察清單報告
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_change_log(changes: dict):
    """Render change log showing new entries and exits"""
    new_entries = changes.get("new_entries", [])
    exits = changes.get("exits", [])
    
    st.markdown("""
    <h3 style="color: #FFFFFF; margin: 24px 0 16px 0; border-bottom: 1px solid rgba(99, 102, 241, 0.3); padding-bottom: 8px;">
        📋 異動快報（相較於前一個交易日）
    </h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: rgba(0, 212, 170, 0.1);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(0, 212, 170, 0.3);
            min-height: 120px;
        ">
            <h4 style="margin: 0 0 16px 0; color: {COLORS['success']}; font-size: 16px;">
                ✨ 今日新加入
            </h4>
        """, unsafe_allow_html=True)
        
        if new_entries:
            for symbol in new_entries:
                info = get_stock_info(symbol)
                name = info.get('name', symbol)
                st.markdown(f"""
                <div style="
                    background: rgba(0, 212, 170, 0.2);
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-bottom: 10px;
                    border-left: 4px solid {COLORS['success']};
                ">
                    <span style="color: #FFFFFF; font-weight: 700; font-size: 16px;">{symbol}</span>
                    <span style="color: #00D4AA; font-size: 13px; margin-left: 8px;">{name}</span>
                    <span style="
                        background: {COLORS['success']};
                        color: #000;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 600;
                        margin-left: 8px;
                    ">NEW</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <p style="color: #6C7A89; font-size: 14px; margin: 0; text-align: center; padding: 20px 0;">
                今日無新加入標的
            </p>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: rgba(108, 122, 137, 0.1);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(108, 122, 137, 0.3);
            min-height: 120px;
        ">
            <h4 style="margin: 0 0 16px 0; color: {COLORS['neutral']}; font-size: 16px;">
                🗑️ 今日被去除
            </h4>
        """, unsafe_allow_html=True)
        
        if exits:
            for symbol in exits:
                info = get_stock_info(symbol)
                name = info.get('name', symbol)
                st.markdown(f"""
                <div style="
                    background: rgba(108, 122, 137, 0.2);
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-bottom: 10px;
                    border-left: 4px solid {COLORS['neutral']};
                ">
                    <span style="color: #9CA3AF; font-weight: 600; font-size: 16px; text-decoration: line-through;">{symbol}</span>
                    <span style="color: #6C7A89; font-size: 13px; margin-left: 8px;">{name}</span>
                    <span style="
                        background: {COLORS['neutral']};
                        color: #FFF;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 600;
                        margin-left: 8px;
                    ">OUT</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <p style="color: #6C7A89; font-size: 14px; margin: 0; text-align: center; padding: 20px 0;">
                今日無被去除標的
            </p>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


def render_stock_analysis_content(symbol: str, is_new: bool = False):
    """Render individual stock analysis content (inside a tab)"""
    # Get stock info
    info = get_stock_info(symbol)
    name = info.get('name', symbol)
    
    # Get price data
    price_data = get_current_price(symbol)
    current_price = price_data.get('current', 0)
    change_pct = price_data.get('change_pct', 0)
    
    # Get historical data
    df = get_stock_data(symbol, DATA_PERIOD)
    
    if df.empty:
        st.warning(f"無法取得 {symbol} {name} 的資料")
        return
    
    # Calculate indicators
    df = calculate_kd(df)
    
    # Get KD info
    k_value = df['K'].iloc[-1] if 'K' in df.columns and not df['K'].isna().all() else 50
    d_value = df['D'].iloc[-1] if 'D' in df.columns and not df['D'].isna().all() else 50
    kd_status = get_kd_status(k_value)
    kd_cross = detect_kd_cross(df)
    
    # Volume analysis
    volume_analysis = get_volume_analysis(df)
    
    # Breakout detection
    breakout = detect_breakout(df)
    
    # Get advice (using current price as "cost" for recommendation purposes)
    advice = check_risk_status(
        current_price=current_price,
        cost=current_price * 0.95,  # Assume hypothetical 5% gain for analysis
        k_value=k_value,
        volume_ratio=volume_analysis.get('ratio', 1),
        is_kd_golden_cross=(kd_cross.get('type') == 'golden'),
        is_breakout=breakout.get('is_breakout', False),
        breakout_type=breakout.get('type')
    )
    
    # Colors
    price_color = COLORS["success"] if change_pct >= 0 else COLORS["danger"]
    kd_color = kd_status.get("color", COLORS["neutral"])
    advice_color = COLORS.get(advice.get("type", "neutral"), COLORS["neutral"])
    
    # New entry badge
    if is_new:
        st.markdown(f"""
        <div style="margin-bottom: 12px;">
            <span style="background: {COLORS['success']}; color: #000; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 600;">
                ✨ 今日新加入觀察
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    # Advice box
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {advice_color}25 0%, {advice_color}10 100%);
        border-left: 4px solid {advice_color};
        border-radius: 0 12px 12px 0;
        padding: 16px 20px;
        margin-bottom: 20px;
    ">
        <p style="margin: 0 0 4px 0; color: #9CA3AF; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">
            📌 利弗摩爾建議
        </p>
        <p style="margin: 0; color: #FFFFFF; font-size: 15px; line-height: 1.6;">
            {advice.get('text', '')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        price_str = f"${current_price:.2f}" if current_price else "N/A"
        st.markdown(f"""
        <div style="background: rgba(30, 33, 48, 0.8); border-radius: 10px; padding: 14px; text-align: center; border: 1px solid rgba(255,255,255,0.1);">
            <p style="margin: 0; color: #9CA3AF; font-size: 11px; text-transform: uppercase;">現價</p>
            <p style="margin: 6px 0 0 0; color: {price_color}; font-size: 20px; font-weight: 700;">{price_str}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: rgba(30, 33, 48, 0.8); border-radius: 10px; padding: 14px; text-align: center; border: 1px solid rgba(255,255,255,0.1);">
            <p style="margin: 0; color: #9CA3AF; font-size: 11px; text-transform: uppercase;">漲跌幅</p>
            <p style="margin: 6px 0 0 0; color: {price_color}; font-size: 20px; font-weight: 700;">{change_pct:+.2f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {kd_color}20 0%, {kd_color}10 100%); border-radius: 10px; padding: 14px; text-align: center; border: 1px solid {kd_color}40;">
            <p style="margin: 0; color: #9CA3AF; font-size: 11px; text-transform: uppercase;">KD 狀態</p>
            <p style="margin: 6px 0 0 0; color: {kd_color}; font-size: 18px; font-weight: 700;">{kd_status.get('status', 'N/A')}</p>
            <p style="margin: 2px 0 0 0; color: #9CA3AF; font-size: 11px;">K:{k_value:.1f} D:{d_value:.1f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        vol_ratio = volume_analysis.get('ratio', 0)
        vol_status = volume_analysis.get('status', 'N/A')
        vol_color = COLORS["success"] if vol_ratio >= 1.5 else (COLORS["warning"] if vol_ratio <= 0.5 else COLORS["neutral"])
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {vol_color}20 0%, {vol_color}10 100%); border-radius: 10px; padding: 14px; text-align: center; border: 1px solid {vol_color}40;">
            <p style="margin: 0; color: #9CA3AF; font-size: 11px; text-transform: uppercase;">量能</p>
            <p style="margin: 6px 0 0 0; color: {vol_color}; font-size: 18px; font-weight: 700;">{vol_status}</p>
            <p style="margin: 2px 0 0 0; color: #9CA3AF; font-size: 11px;">{vol_ratio:.1f}x 均量</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Chart
    chart_fig = create_candlestick_chart(
        df=df,
        symbol=symbol,
        name=name,
        show_volume=True,
        show_kd=True
    )
    st.plotly_chart(chart_fig, use_container_width=True, config={'displayModeBar': False})


def render_sidebar():
    """Render sidebar for watchlist management"""
    with st.sidebar:
        st.markdown("""
        <h2 style="
            color: #FFFFFF;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(99, 102, 241, 0.3);
        ">📊 觀察清單管理</h2>
        """, unsafe_allow_html=True)
        
        # Add stock form
        with st.form("add_stock_form", clear_on_submit=True):
            st.markdown("### ➕ 新增觀察標的")
            
            symbol = st.text_input(
                "股票代碼",
                placeholder="例如: 2330",
                help="輸入台股代碼（不含 .TW）"
            )
            
            submitted = st.form_submit_button("🚀 新增", use_container_width=True)
            
            if submitted and symbol:
                symbol = symbol.strip().upper()
                add_to_watchlist(symbol)
                st.success(f"✅ 已新增 {symbol}")
                refresh_data()
                st.rerun()
        
        st.markdown("---")
        
        # Load sample stocks
        if st.button("📈 載入熱門範例", use_container_width=True, help="載入台股熱門標的"):
            sample_stocks = get_sample_stocks()
            save_watchlist(sample_stocks)
            st.success("已載入 10 檔熱門台股")
            refresh_data()
            st.rerun()
        
        st.markdown("---")
        
        # Current watchlist
        st.markdown("### 📋 目前觀察清單")
        
        watchlist = st.session_state.watchlist
        stocks = watchlist.get("stocks", [])
        
        if stocks:
            st.markdown(f"<p style='color: #9CA3AF; font-size: 12px;'>共 {len(stocks)} 檔</p>", unsafe_allow_html=True)
            
            for symbol in stocks:
                col1, col2 = st.columns([3, 1])
                with col1:
                    info = get_stock_info(symbol)
                    name = info.get('name', symbol)
                    st.markdown(f"""
                    <div style="
                        background: rgba(30, 33, 48, 0.8);
                        padding: 8px 12px;
                        border-radius: 6px;
                        margin-bottom: 4px;
                    ">
                        <span style="color: #FFFFFF; font-weight: 600;">{symbol}</span>
                        <span style="color: #9CA3AF; font-size: 11px; display: block;">{name}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"remove_{symbol}", help="移除"):
                        remove_from_watchlist(symbol)
                        refresh_data()
                        st.rerun()
        else:
            st.info("尚無觀察標的，請新增或載入範例")
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 重新整理資料", use_container_width=True):
            refresh_data()
            st.rerun()
        
        # Last update
        st.markdown(f"""
        <p style="color: #6C7A89; font-size: 11px; text-align: center; margin-top: 16px;">
            最後更新：{datetime.now().strftime('%H:%M:%S')}
        </p>
        """, unsafe_allow_html=True)


def main():
    """Main application"""
    init_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render header
    render_header()
    
    # Get watchlist data
    today_stocks = st.session_state.watchlist.get("stocks", [])
    yesterday_stocks = st.session_state.yesterday_watchlist.get("stocks", [])
    
    # Detect changes
    changes = detect_watchlist_changes(today_stocks, yesterday_stocks)
    new_entry_set = set(changes.get("new_entries", []))
    
    # Render change log
    render_change_log(changes)
    
    # Render stock analysis section
    if today_stocks:
        st.markdown("""
        <h3 style="color: #FFFFFF; margin: 32px 0 16px 0; border-bottom: 1px solid rgba(99, 102, 241, 0.3); padding-bottom: 8px;">
            📈 個股分析報告
        </h3>
        <p style="color: #9CA3AF; font-size: 13px; margin-bottom: 20px;">
            點選股票標籤查看 K 線圖、成交量、KD 指標及利弗摩爾交易建議
        </p>
        """, unsafe_allow_html=True)
        
        # Create tab labels with stock info
        tab_labels = []
        for symbol in today_stocks:
            info = get_stock_info(symbol)
            name = info.get('name', symbol)
            is_new = symbol in new_entry_set
            label = f"{'✨ ' if is_new else ''}{symbol} {name}"
            tab_labels.append(label)
        
        # Create tabs
        tabs = st.tabs(tab_labels)
        
        # Render content for each tab
        for idx, (tab, symbol) in enumerate(zip(tabs, today_stocks)):
            with tab:
                is_new = symbol in new_entry_set
                render_stock_analysis_content(symbol, is_new=is_new)
    else:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1E2130 0%, #252A40 100%);
            border-radius: 16px;
            padding: 60px 40px;
            text-align: center;
            border: 2px dashed rgba(99, 102, 241, 0.3);
            margin: 32px 0;
        ">
            <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
            <h3 style="color: #FFFFFF; margin: 0 0 8px 0;">尚無觀察標的</h3>
            <p style="color: #9CA3AF; margin: 0; font-size: 14px;">
                請使用左側選單新增股票，或點擊「載入熱門範例」快速開始
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="
        text-align: center;
        padding: 24px;
        margin-top: 40px;
        border-top: 1px solid rgba(99, 102, 241, 0.2);
    ">
        <p style="color: #6C7A89; font-size: 12px; margin: 0;">
            🎯 趨勢守衛者 | 基於 Jesse Livermore 交易哲學設計
        </p>
        <p style="color: #4B5563; font-size: 11px; margin: 8px 0 0 0;">
            ⚠️ 本系統僅供參考，不構成投資建議。投資有風險，請謹慎評估。
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
