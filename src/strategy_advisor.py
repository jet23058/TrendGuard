"""
Strategy Advisor Module - 利弗摩爾規則策略建議
"""
from typing import Optional


def get_advice(
    current_price: float,
    cost: float,
    k_value: float,
    volume_ratio: float,
    is_kd_golden_cross: bool,
    is_breakout: bool,
    breakout_type: Optional[str] = None
) -> dict:
    """
    根據利弗摩爾規則生成交易建議
    
    Args:
        current_price: 現價
        cost: 買入成本
        k_value: KD 指標 K 值
        volume_ratio: 量能比率 (相對於5日均量)
        is_kd_golden_cross: 是否 KD 金叉
        is_breakout: 是否突破
        breakout_type: 突破類型 ('upward' or 'downward')
    
    Returns:
        dict with advice, type, and priority
    """
    if cost <= 0:
        return {
            "text": "⚠️ 請輸入正確的成本價",
            "type": "warning",
            "priority": 0
        }
    
    price_change_pct = (current_price - cost) / cost
    
    # 1. 硬性停損 - 最高優先級
    if price_change_pct <= -0.10:
        return {
            "text": "⚠️ 觸發 10% 硬性停損！請立即市價賣出，不要猶豫。利弗摩爾法則：控制虧損是交易的第一要務。",
            "type": "danger",
            "priority": 100,
            "action": "SELL"
        }
    
    # 2. 獲利超過 20%
    if price_change_pct >= 0.20:
        return {
            "text": "🚀 獲利拉開 20%！建議進行金字塔式加碼，或設定移動停利保護獲利。這是強勢股的標誌！",
            "type": "success",
            "priority": 90,
            "action": "HOLD_OR_ADD"
        }
    
    # 3. 關鍵點突破 (金叉 + 突破前高)
    if is_kd_golden_cross and is_breakout and breakout_type == "upward":
        return {
            "text": "🔥 關鍵點突破！KD 金叉搭配價格突破前高，這是利弗摩爾最重視的買點。考慮加碼！",
            "type": "success",
            "priority": 85,
            "action": "BUY"
        }
    
    # 4. 單純 KD 金叉
    if is_kd_golden_cross:
        return {
            "text": "📈 KD 金叉出現！短線可能有反彈機會，但需搭配量能確認。",
            "type": "info",
            "priority": 60,
            "action": "WATCH"
        }
    
    # 5. 突破前高但無金叉
    if is_breakout and breakout_type == "upward":
        return {
            "text": "📊 價格突破前高！觀察是否有量能配合，若量增則是好訊號。",
            "type": "info",
            "priority": 55,
            "action": "WATCH"
        }
    
    # 6. 跌破前低
    if is_breakout and breakout_type == "downward":
        return {
            "text": "⚠️ 價格跌破前低！趨勢轉弱，考慮減碼或停損。",
            "type": "warning",
            "priority": 75,
            "action": "REDUCE"
        }
    
    # 7. 動能消失 (量縮 + 盤整)
    if volume_ratio < 0.5 and abs(price_change_pct) < 0.02:
        return {
            "text": "💤 動能消失，進入無聊盤整區間。考慮換股操作或等待突破方向。",
            "type": "neutral",
            "priority": 40,
            "action": "WAIT"
        }
    
    # 8. KD 過熱
    if k_value >= 80:
        if price_change_pct > 0:
            return {
                "text": "🌡️ KD 指標進入過熱區 (K > 80)，但趨勢仍屬強勢。可持有，但注意設好停利。",
                "type": "warning",
                "priority": 50,
                "action": "HOLD_TRAILING"
            }
        else:
            return {
                "text": "⚠️ KD 過熱但未獲利，可能是假突破或鈍化。密切觀察。",
                "type": "warning",
                "priority": 55,
                "action": "WATCH"
            }
    
    # 9. KD 超賣
    if k_value <= 20:
        return {
            "text": "🔍 KD 進入超賣區 (K < 20)，可能有反彈機會。觀察是否出現金叉。",
            "type": "info",
            "priority": 45,
            "action": "WATCH_FOR_ENTRY"
        }
    
    # 10. 小幅虧損 (5-10%)
    if -0.10 < price_change_pct <= -0.05:
        return {
            "text": "📉 帳面虧損 5-10%，接近停損線。密切關注，若持續走弱應果斷停損。",
            "type": "warning",
            "priority": 70,
            "action": "MONITOR"
        }
    
    # 11. 小幅獲利中
    if 0.05 <= price_change_pct < 0.20:
        return {
            "text": f"📈 目前獲利 {price_change_pct*100:.1f}%，持續往好的方向發展。考慮設移動停利保護獲利。",
            "type": "success",
            "priority": 30,
            "action": "HOLD"
        }
    
    # 12. 默認 - 續抱觀察
    return {
        "text": "👀 續抱觀察，等待關鍵點出現。記住：沒有明確訊號時，耐心是最好的策略。",
        "type": "neutral",
        "priority": 20,
        "action": "HOLD"
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
