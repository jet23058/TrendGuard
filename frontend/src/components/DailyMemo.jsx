import React, { useState, useEffect, useMemo } from 'react';
import { doc, getDoc, setDoc, deleteDoc, collection, getDocs, query, where } from 'firebase/firestore';
import { db } from '../firebase';
import { Save, Calendar as CalendarIcon, ChevronLeft, ChevronRight, X, Loader2, Trash2 } from 'lucide-react';

const DailyMemo = ({ user, isOpen, onClose }) => {
    const [currentDate, setCurrentDate] = useState(new Date()); // 當前檢視的月份/日期
    const [selectedDate, setSelectedDate] = useState(new Date()); // 當前選中的日期
    const [memoContent, setMemoContent] = useState('');
    const [existingMemos, setExistingMemos] = useState(new Set()); // 儲存有 Memo 的日期字串集合
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [loadingMonth, setLoadingMonth] = useState(false);

    // Helper: 格式化日期 YYYY-MM-DD
    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    // 載入該月份所有有 Memo 的日期 (用於日曆標記)
    useEffect(() => {
        if (!user || !isOpen) return;

        const fetchMonthMemos = async () => {
            setLoadingMonth(true);
            try {
                // 這裡簡化處理：讀取該使用者所有的 memos (如果量大未來可優化為 query by month)
                // 目前假設使用者筆記不會多到爆掉
                const memosRef = collection(db, "users", user.uid, "memos");
                const q = query(memosRef);
                const querySnapshot = await getDocs(q);
                
                const dates = new Set();
                querySnapshot.forEach((doc) => {
                    dates.add(doc.id);
                });
                setExistingMemos(dates);
            } catch (err) {
                console.error("Error fetching memo list:", err);
            } finally {
                setLoadingMonth(false);
            }
        };

        fetchMonthMemos();
    }, [user, isOpen, currentDate.getMonth()]); // 當月份改變或打開時重新讀取

    // 當選中日期改變時，讀取該日的 Memo
    useEffect(() => {
        if (!user || !selectedDate) return;

        const loadMemo = async () => {
            setLoading(true);
            const dateStr = formatDate(selectedDate);
            try {
                const docRef = doc(db, "users", user.uid, "memos", dateStr);
                const docSnap = await getDoc(docRef);

                if (docSnap.exists()) {
                    setMemoContent(docSnap.data().content || '');
                } else {
                    setMemoContent('');
                }
            } catch (err) {
                console.error("Error loading specific memo:", err);
                setMemoContent('');
            } finally {
                setLoading(false);
            }
        };

        loadMemo();
    }, [user, selectedDate]);

    const handleSave = async () => {
        if (!user) return;
        setSaving(true);
        const dateStr = formatDate(selectedDate);
        const docRef = doc(db, "users", user.uid, "memos", dateStr);

        try {
            if (!memoContent.trim()) {
                // 如果內容為空，則刪除該文件
                await deleteDoc(docRef);
                setExistingMemos(prev => {
                    const next = new Set(prev);
                    next.delete(dateStr);
                    return next;
                });
            } else {
                // 寫入/更新
                await setDoc(docRef, {
                    content: memoContent,
                    updatedAt: new Date().toISOString()
                }, { merge: true });
                
                setExistingMemos(prev => new Set(prev).add(dateStr));
            }
            // 成功提示可選，目前僅按鈕狀態變化
        } catch (err) {
            console.error("Error saving memo:", err);
            alert("儲存失敗，請檢查網路或權限設定");
        } finally {
            setSaving(false);
        }
    };

    // 日曆邏輯
    const getDaysInMonth = (year, month) => new Date(year, month + 1, 0).getDate();
    const getFirstDayOfMonth = (year, month) => new Date(year, month, 1).getDay(); // 0 = Sunday

    const renderCalendar = () => {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        const daysInMonth = getDaysInMonth(year, month);
        const firstDay = getFirstDayOfMonth(year, month);
        
        const days = [];
        // 空白填充
        for (let i = 0; i < firstDay; i++) {
            days.push(<div key={`empty-${i}`} className="h-8 w-8" />);
        }

        // 日期
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month, day);
            const dateStr = formatDate(date);
            const hasMemo = existingMemos.has(dateStr);
            const isSelected = formatDate(selectedDate) === dateStr;
            const isToday = formatDate(new Date()) === dateStr;

            days.push(
                <button
                    key={day}
                    onClick={() => setSelectedDate(date)}
                    className={`h-8 w-8 rounded-full flex items-center justify-center text-sm relative transition-all
                        ${isSelected ? 'bg-blue-600 text-white font-bold shadow-lg shadow-blue-900/50' : 'hover:bg-gray-700 text-gray-300'}
                        ${isToday && !isSelected ? 'border border-blue-500 text-blue-400' : ''}
                    `}
                >
                    {day}
                    {hasMemo && (
                        <span className={`absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full ${isSelected ? 'bg-white' : 'bg-yellow-500'}`}></span>
                    )}
                </button>
            );
        }

        return days;
    };

    const prevMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    const nextMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
            <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-4xl shadow-2xl flex flex-col md:flex-row overflow-hidden max-h-[90vh]">
                
                {/* 左側：日曆區 */}
                <div className="p-6 bg-gray-800/50 border-b md:border-b-0 md:border-r border-gray-700 w-full md:w-80 flex-shrink-0">
                    <div className="flex justify-between items-center mb-6">
                        <button onClick={prevMonth} className="p-1 hover:bg-gray-700 rounded-full text-gray-400 hover:text-white">
                            <ChevronLeft size={20} />
                        </button>
                        <h3 className="font-bold text-white text-lg">
                            {currentDate.getFullYear()}年 {currentDate.getMonth() + 1}月
                        </h3>
                        <button onClick={nextMonth} className="p-1 hover:bg-gray-700 rounded-full text-gray-400 hover:text-white">
                            <ChevronRight size={20} />
                        </button>
                    </div>

                    <div className="grid grid-cols-7 gap-1 text-center mb-2">
                        {['日', '一', '二', '三', '四', '五', '六'].map(d => (
                            <div key={d} className="text-xs text-gray-500 font-bold h-8 flex items-center justify-center">{d}</div>
                        ))}
                        {renderCalendar()}
                    </div>

                    <div className="mt-6 flex items-center gap-4 justify-center text-xs text-gray-400">
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                            <span>有筆記</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                            <span>目前選取</span>
                        </div>
                    </div>
                </div>

                {/* 右側：編輯區 */}
                <div className="flex-1 flex flex-col min-h-[400px]">
                    <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-800/30">
                        <div>
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <CalendarIcon className="text-blue-400" size={20} />
                                {formatDate(selectedDate)}
                            </h2>
                            <p className="text-xs text-gray-500 mt-0.5">我的交易筆記</p>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-full text-gray-400 hover:text-white transition-colors">
                            <X size={20} />
                        </button>
                    </div>

                    <div className="flex-1 p-6 relative">
                        {loading ? (
                            <div className="absolute inset-0 flex items-center justify-center bg-gray-900/50 z-10">
                                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
                            </div>
                        ) : (
                            <textarea
                                value={memoContent}
                                onChange={(e) => setMemoContent(e.target.value)}
                                placeholder="在此輸入筆記... (清空並儲存即可刪除)"
                                className="w-full h-full bg-transparent text-gray-300 text-base leading-relaxed placeholder-gray-600 focus:outline-none resize-none"
                                spellCheck={false}
                            />
                        )}
                    </div>

                    <div className="p-4 border-t border-gray-700 bg-gray-800/30 flex justify-between items-center">
                        <div className="text-xs text-gray-500">
                            {saving ? '儲存中...' : (memoContent ? '記得按下儲存按鈕' : '內容為空將自動刪除')}
                        </div>
                        <button 
                            onClick={handleSave}
                            disabled={saving || loading}
                            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white px-6 py-2 rounded-lg text-sm font-bold transition-all shadow-lg shadow-blue-900/20"
                        >
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            儲存筆記
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DailyMemo;
