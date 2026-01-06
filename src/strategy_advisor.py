"""
Strategy Advisor Module - 利弗摩爾規則策略建議
"""
from typing import Optional


def check_risk_status(
    current_price: float,
    cost: float,
    k_value: float,
    volume_ratio: float,
    is_kd_golden_cross: bool,
    is_breakout: bool,
    breakout_type: Optional[str] = None
) -> dict:
    """
    根據利弗摩爾規則生成分析結果 (僅陳述事實，不提供投資建議)
    
    Args:
        current_price: 現價
        cost: 買入成本
        k_value: KD 指標 K 值
        volume_ratio: 量能比率 (相對於5日均量)
        is_kd_golden_cross: 是否 KD 金叉
        is_breakout: 是否突破
        breakout_type: 突破類型 ('upward' or 'downward')
    
    Returns:
        dict with status text and signal type
    """
    if cost <= 0:
        return {
            "text": "⚠️ 請輸入正確的成本價",
            "type": "warning",
            "priority": 0
        }
    
    price_change_pct = (current_price - cost) / cost
    
    # 1. 硬性停損
    if price_change_pct <= -0.10:
        return {
            "text": "⚠️ 跌幅達 10%，已觸發策略預設之停損門檻。",
            "type": "danger",
            "priority": 100,
            "action": "STOP_LOSS_ALERT"
        }
    
    # 2. 獲利超過 20%
    if price_change_pct >= 0.20:
        return {
            "text": "🚀 帳面獲利超過 20%，趨勢強勁。",
            "type": "success",
            "priority": 90,
            "action": "PROFIT_ALERT"
        }
    
    # 3. 關鍵點突破
    if is_kd_golden_cross and is_breakout and breakout_type == "upward":
        return {
            "text": "🔥 價格突破前高，且 KD 指標呈現黃金交叉。",
            "type": "success",
            "priority": 85,
            "action": "BREAKOUT_ALERT"
        }
    
    # 4. 單純 KD 金叉
    if is_kd_golden_cross:
        return {
            "text": "📈 KD 指標出現黃金交叉訊號。",
            "type": "info",
            "priority": 60,
            "action": "TECHNICAL_SIGNAL"
        }
    
    # 5. 突破前高但無金叉
    if is_breakout and breakout_type == "upward":
        return {
            "text": "📊 價格創下波段新高。",
            "type": "info",
            "priority": 55,
            "action": "price_update"
        }
    
    # 6. 跌破前低
    if is_breakout and breakout_type == "downward":
        return {
            "text": "⚠️ 價格跌破波段前低。",
            "type": "warning",
            "priority": 75,
            "action": "price_update"
        }
    
    # 7. 動能消失
    if volume_ratio < 0.5 and abs(price_change_pct) < 0.02:
        return {
            "text": "💤 價格波動收斂，成交量縮減。",
            "type": "neutral",
            "priority": 40,
            "action": "low_volatility"
        }
    
    # 8. KD 過熱
    if k_value >= 80:
        if price_change_pct > 0:
            return {
                "text": "🌡️ KD 指標進入高檔區 (K > 80)。",
                "type": "warning",
                "priority": 50,
                "action": "overbought"
            }
        else:
            return {
                "text": "⚠️ KD 指標高檔但價格未創高 (背離疑慮)。",
                "type": "warning",
                "priority": 55,
                "action": "divergence"
            }
    
    # 9. KD 超賣
    if k_value <= 20:
        return {
            "text": "🔍 KD 指標進入低檔區 (K < 20)。",
            "type": "info",
            "priority": 45,
            "action": "oversold"
        }
    
    # 10. 小幅虧損 (5-10%)
    if -0.10 < price_change_pct <= -0.05:
        return {
            "text": "📉 帳面虧損介於 5-10% 之間。",
            "type": "warning",
            "priority": 70,
            "action": "drawdown"
        }
    
    # 11. 小幅獲利中
    if 0.05 <= price_change_pct < 0.20:
        return {
            "text": f"📈 目前帳面獲利 {price_change_pct*100:.1f}%。",
            "type": "success",
            "priority": 30,
            "action": "profit"
        }
    
    # 12. 默認
    return {
        "text": "👀 目前無特殊技術訊號。",
        "type": "neutral",
        "priority": 20,
        "action": "none"
    }


def get_position_suggestion(stock_count: int) -> dict:
    """
    持股檔數建議
    
    Args:
        stock_count: 目前持股檔數
    
    Returns:
        dict with suggestion
    """
    if stock_count == 0:
        return {
            "text": "目前空手，尋找符合條件的標的進場",
            "type": "neutral",
            "ideal": False
        }
    elif stock_count <= 3:
        return {
            "text": f"目前持有 {stock_count} 檔，符合利弗摩爾建議的集中持股原則",
            "type": "success",
            "ideal": True
        }
    elif stock_count <= 5:
        return {
            "text": f"目前持有 {stock_count} 檔，略多。考慮汰弱留強，集中火力在最強標的",
            "type": "warning",
            "ideal": False
        }
    else:
        return {
            "text": f"持有 {stock_count} 檔過於分散！利弗摩爾強調集中持股，建議減少至 3 檔以內",
            "type": "danger",
            "ideal": False
        }


ADVICE_COLORS = {
    "danger": "#FF6B6B",
    "warning": "#FFD93D",
    "success": "#00D4AA",
    "info": "#6366F1",
    "neutral": "#6C7A89"
}
