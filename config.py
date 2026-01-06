"""
Configuration settings for Livermore Trader Dashboard
"""

# Color Theme
COLORS = {
    "primary": "#6366F1",       # Indigo
    "success": "#00D4AA",       # Green (上漲/新進場)
    "danger": "#FF6B6B",        # Red (下跌/支撐)
    "warning": "#FFD93D",       # Yellow (警戒/過熱)
    "neutral": "#6C7A89",       # Gray (中性/續抱)
    "background": "#0F1117",    # Dark background
    "card_bg": "#1E2130",       # Card background
    "text": "#FFFFFF",          # Primary text
    "text_muted": "#9CA3AF",    # Muted text
}

# Chart Colors
CHART_COLORS = {
    "up": "#00D4AA",
    "down": "#FF6B6B",
    "volume": "#6366F1",
    "k_line": "#FFD93D",
    "d_line": "#00D4AA",
}

# KD Parameters
KD_PARAMS = {
    "k_period": 9,
    "d_period": 3,
    "smooth_k": 3,
    "overbought": 80,
    "oversold": 20,
}

# Trading Rules (Livermore)
TRADING_RULES = {
    "stop_loss_pct": 0.10,      # 10% 支撐
    "profit_target_pct": 0.20,  # 20% 獲利目標
    "volume_threshold": 0.5,    # 量能閾值 (5日均量的 50%)
    "price_change_threshold": 0.02,  # 價格變動閾值
}

# Data Settings
DATA_PERIOD = "1mo"  # 近一個月資料
PORTFOLIO_DIR = "data/portfolios"
