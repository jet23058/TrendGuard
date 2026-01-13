import React, { useState } from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';

const StockHistoryCalendar = ({ isOpen, onClose, stockName, ticker, historyDates = [] }) => {
    const [currentDate, setCurrentDate] = useState(new Date());

    if (!isOpen) return null;

    // Convert historyDates to Set for O(1) lookup
    const historySet = new Set(historyDates);

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    // Get first day of month and total days
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    // Navigation handlers
    const prevMonth = () => setCurrentDate(new Date(year, month - 1, 1));
    const nextMonth = () => setCurrentDate(new Date(year, month + 1, 1));

    // Generate calendar days
    const days = [];
    const weekDays = ['日', '一', '二', '三', '四', '五', '六'];

    // Empty cells before first day
    for (let i = 0; i < firstDay; i++) {
        days.push(<div key={`empty-${i}`} className="h-8"></div>);
    }

    // Actual days
    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const isOnList = historySet.has(dateStr);
        const isToday = new Date().toISOString().slice(0, 10) === dateStr;

        days.push(
            <div
                key={day}
                className={`h-8 w-8 flex items-center justify-center text-sm rounded-full transition-colors
          ${isOnList ? 'bg-blue-600 text-white font-bold' : 'text-gray-400'}
          ${isToday && !isOnList ? 'ring-1 ring-blue-500' : ''}
        `}
                title={isOnList ? `${dateStr} 在榜` : dateStr}
            >
                {day}
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
            <div
                className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl p-4 w-80"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h3 className="text-lg font-bold text-white">{stockName}</h3>
                        <p className="text-xs text-gray-500 font-mono">{ticker} 上榜紀錄</p>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white p-1">
                        <X size={20} />
                    </button>
                </div>

                {/* Month Navigation */}
                <div className="flex items-center justify-between mb-4">
                    <button onClick={prevMonth} className="p-1 hover:bg-gray-800 rounded">
                        <ChevronLeft size={20} className="text-gray-400" />
                    </button>
                    <span className="text-white font-medium">
                        {year} 年 {month + 1} 月
                    </span>
                    <button onClick={nextMonth} className="p-1 hover:bg-gray-800 rounded">
                        <ChevronRight size={20} className="text-gray-400" />
                    </button>
                </div>

                {/* Week Day Headers */}
                <div className="grid grid-cols-7 gap-1 mb-2">
                    {weekDays.map(d => (
                        <div key={d} className="h-8 flex items-center justify-center text-xs text-gray-500 font-medium">
                            {d}
                        </div>
                    ))}
                </div>

                {/* Calendar Grid */}
                <div className="grid grid-cols-7 gap-1">
                    {days}
                </div>

                {/* Legend */}
                <div className="mt-4 pt-3 border-t border-gray-800 flex items-center gap-4 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full bg-blue-600"></div>
                        <span>在榜日</span>
                    </div>
                    <span>共 {historyDates.length} 次上榜</span>
                </div>
            </div>
        </div>
    );
};

export default StockHistoryCalendar;
