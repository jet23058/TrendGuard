import React, { useState, useMemo, useRef, useEffect } from 'react';
import { TrendingUp, TrendingDown, BarChart2 } from 'lucide-react';
import {
    ComposedChart,
    Line,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine
} from 'recharts';
import StockHistoryCalendar from './StockHistoryCalendar';

// --- Hook: 監聽元素是否進入視窗 ---
const useInView = (options = {}) => {
    const [isInView, setIsInView] = useState(false);
    const ref = useRef(null);

    useEffect(() => {
        const observer = new IntersectionObserver(([entry]) => {
            if (entry.isIntersecting) {
                setIsInView(true);
                if (options.triggerOnce) {
                    observer.disconnect();
                }
            }
        }, {
            rootMargin: '100px', // 預設提早 100px 觸發
            ...options
        });

        if (ref.current) {
            observer.observe(ref.current);
        }

        return () => {
            observer.disconnect();
        };
    }, []); // Empty dependency array for stability

    return [ref, isInView];
};

// --- 1. K線圖繪製元件 ---
const CandleStickShape = (props) => {
    const { x, y, width, height, payload } = props;
    const { open, close, high, low } = payload;

    if (high === undefined || low === undefined || open === undefined || close === undefined) return null;

    const isUp = close >= open;
    const color = isUp ? '#ef4444' : '#22c55e'; // 紅漲綠跌

    // 確保有足夠的寬度
    const candleWidth = Math.max(width * 0.8, 6);
    const wickWidth = 1.5;
    const centerX = x + width / 2;

    const range = high - low;
    if (range === 0) {
        return <line x1={x} y1={y} x2={x + width} y2={y} stroke={color} strokeWidth={2} />;
    }

    const ratio = height / range;

    // 計算各點位置
    const yHigh = y;
    const yLow = y + height;
    const yOpen = y + (high - open) * ratio;
    const yClose = y + (high - close) * ratio;

    const bodyTop = Math.min(yOpen, yClose);
    const bodyHeight = Math.max(Math.abs(yOpen - yClose), 2); // 最小高度 2px

    return (
        <g>
            {/* 上影線 */}
            <line
                x1={centerX}
                y1={yHigh}
                x2={centerX}
                y2={bodyTop}
                stroke={color}
                strokeWidth={wickWidth}
            />
            {/* 下影線 */}
            <line
                x1={centerX}
                y1={bodyTop + bodyHeight}
                x2={centerX}
                y2={yLow}
                stroke={color}
                strokeWidth={wickWidth}
            />
            {/* 蠟燭體 */}
            <rect
                x={centerX - candleWidth / 2}
                y={bodyTop}
                width={candleWidth}
                height={bodyHeight}
                fill={color}
                stroke={color}
                strokeWidth={1}
            />
        </g>
    );
};

const CustomCursor = (props) => {
    const { x, y, width, height, points } = props;

    // 處理不同類型的游標屬性
    let centerX;
    let startY = y || 0;
    let endY = (y || 0) + (height || 200);

    if (points && points.length > 0) {
        // 線圖模式：使用 points 的 x
        centerX = points[0].x;
    } else if (x !== undefined) {
        // Bar 圖模式：加上固定偏移量來對齊 K 棒中心
        centerX = x + 15;
    } else {
        return null;
    }

    return (
        <line
            x1={centerX}
            y1={startY}
            x2={centerX}
            y2={endY}
            stroke="#ffffff"
            strokeWidth={1.5}
            strokeOpacity={0.8}
        />
    );
};

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;
        const isUp = data.close >= data.open;
        return (
            <div className="bg-gray-800 border border-gray-700 p-3 rounded shadow-lg text-xs z-50">
                <p className="text-gray-400 mb-2 font-mono border-b border-gray-700 pb-1">{label}</p>
                <div className="grid grid-cols-2 gap-x-6 gap-y-1">
                    <span className="text-gray-400">開盤</span>
                    <span className="font-mono text-right text-white">{data.open?.toFixed(1)}</span>
                    <span className="text-gray-400">最高</span>
                    <span className="font-mono text-right text-red-400">{data.high?.toFixed(1)}</span>
                    <span className="text-gray-400">最低</span>
                    <span className="font-mono text-right text-green-400">{data.low?.toFixed(1)}</span>
                    <span className="text-gray-400">收盤</span>
                    <span className={`font-mono text-right ${isUp ? 'text-red-400' : 'text-green-400'}`}>{data.close?.toFixed(1)}</span>
                </div>
                {data.k && (
                    <div className="mt-2 pt-2 border-t border-gray-700 grid grid-cols-2 gap-x-6">
                        <span className="text-orange-400">K: {data.k?.toFixed(1)}</span>
                        <span className="text-cyan-400 text-right">D: {data.d?.toFixed(1)}</span>
                    </div>
                )}
            </div>
        );
    }
    return null;
};

// --- 精簡版股票卡片 (Rich Version Restored) ---
const StockCardMini = ({ stock, isInPortfolio, portfolioItem, historyDates = [] }) => {
    const { ticker, name, currentPrice, changePct, consecutiveRed, stopLoss, ohlc, alert, market, tags } = stock;
    const isUp = changePct >= 0;
    const yahooUrl = `https://tw.stock.yahoo.com/quote/${ticker}.TW/technical-analysis`;
    const [chartMode, setChartMode] = useState('ma'); // 'ma' or 'kd'
    const [isCalendarOpen, setIsCalendarOpen] = useState(false);
    
    // Lazy Load Chart: 提早 200px 載入，只觸發一次
    const [chartRef, chartInView] = useInView({ triggerOnce: true, rootMargin: '200px' });

    const chartData = useMemo(() => {
        if (!ohlc || ohlc.length === 0) return [];
        // Restore full logic: slice 20, normalize structure
        return ohlc.slice(-20).map(item => ({
            ...item,
            // Ensure numbers
            open: Number(item.open),
            close: Number(item.close),
            high: Number(item.high),
            low: Number(item.low),
            priceRange: [Number(item.low), Number(item.high)]
        }));
    }, [ohlc]);

    // 計算成交量最大值用於正規化
    const maxVolume = useMemo(() => {
        if (!chartData.length) return 1;
        return Math.max(...chartData.map(d => d.volume || 0));
    }, [chartData]);

    // 計算未實現損益 (如果有庫存資訊)
    const unrealizedPL = useMemo(() => {
        if (!portfolioItem || !portfolioItem.cost || !currentPrice) return null;
        const diff = currentPrice - portfolioItem.cost;
        const pl = diff * (portfolioItem.shares || 1000); // 預設 1000 股如果沒填
        const plPct = (diff / portfolioItem.cost) * 100;
        return { val: pl, pct: plPct };
    }, [currentPrice, portfolioItem]);

    return (
        <div className={`bg-gray-800 rounded-xl border shadow-lg flex-shrink-0 w-72 h-[460px] flex flex-col relative ${isInPortfolio ? 'border-yellow-500/50 ring-1 ring-yellow-500/30' : 'border-gray-700'}`}>
            <div className="p-3 border-b border-gray-700 bg-gray-900/50 rounded-t-xl">
                <div className="flex justify-between items-start gap-2">
                    <div className="flex flex-col gap-1 min-w-0">
                        <div className="flex items-center gap-2">
                            <a href={yahooUrl} target="_blank" rel="noopener noreferrer" className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-2 py-0.5 rounded transition-colors cursor-pointer no-underline flex-shrink-0">
                                {ticker} ↗
                            </a>
                            <h3 className="text-sm font-bold text-white truncate max-w-[80px]">{name}</h3>
                            <button
                                onClick={() => setIsCalendarOpen(true)}
                                className="p-1 hover:bg-gray-700 rounded transition-colors flex-shrink-0"
                                title="查看上榜紀錄"
                            >
                                <BarChart2 size={14} className="text-gray-400 hover:text-blue-400" />
                            </button>
                        </div>
                        {/* 標籤區：處置/警示 + 持有 + 禁當沖 + 市場 + Tags */}
                        <div className="flex flex-wrap items-center gap-2">
                            {/* Market Badge (上市/上櫃) */}
                            {market && (
                                <span className="text-[10px] bg-gray-700 text-gray-300 border border-gray-600 px-1.5 py-0.5 rounded">
                                    {market}
                                </span>
                            )}
                            
                            {/* Alert Badge */}
                            {alert && (
                                <div className="group relative z-10">
                                    <div className="flex items-center gap-1">
                                        <span className={`text-[10px] px-1.5 py-0.5 rounded cursor-help ${alert.color === 'red' ? 'bg-red-900 text-red-200 border border-red-700' : 'bg-yellow-900 text-yellow-200 border border-yellow-700'}`}>
                                            {alert.badge}
                                        </span>
                                        {alert.risk && alert.risk.level !== 'low' && (
                                            <span className={`text-[9px] px-1 rounded-sm ${alert.risk.level === 'high' ? 'bg-red-500 text-white animate-pulse' : 'bg-orange-500 text-white'}`}>
                                                風險 {alert.risk.level === 'high' ? '高' : '中'}
                                            </span>
                                        )}
                                    </div>
                                    {/* Tooltip */}
                                    <div className="absolute left-0 top-full mt-1 w-56 p-2 bg-gray-950 border border-gray-700 rounded shadow-xl text-xs z-50 invisible group-hover:visible whitespace-pre-wrap text-left">
                                        <div className={`font-bold mb-1 ${alert.color === 'red' ? 'text-red-400' : 'text-yellow-400'}`}>
                                            {alert.info}
                                        </div>
                                        {alert.risk && alert.risk.message && (
                                            <div className="mb-2 p-1.5 bg-gray-900 rounded border border-gray-800 text-orange-300 font-bold">
                                                ⚠️ {alert.risk.message}
                                            </div>
                                        )}
                                        <div className="text-gray-400 leading-relaxed mb-2">{alert.detail}</div>
                                        {alert.history && alert.history.length > 0 && (
                                            <div className="border-t border-gray-800 pt-1 mt-1">
                                                <div className="text-[10px] text-gray-500 mb-1">近期注意紀錄：</div>
                                                <div className="flex flex-wrap gap-1">
                                                    {alert.history.slice(0, 5).map(h => (
                                                        <span key={h} className="text-[9px] bg-gray-800 px-1 rounded text-gray-400">{h}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                            
                            {/* Can Day Trade */}
                            {stock.canDayTrade === false && (
                                <span className="text-[10px] bg-red-900 text-red-200 border border-red-700 px-1.5 py-0.5 rounded cursor-help" title="此股票不在當沖標的清單中，或正處於處置狀態">
                                    🚫 禁當沖
                                </span>
                            )}

                            {/* Portfolio */}
                            {isInPortfolio && <span className="text-[10px] bg-yellow-600 text-yellow-100 px-1.5 py-0.5 rounded">持有</span>}
                            
                            {/* Special Tags (e.g. Box Breakout) */}
                            {tags && tags.map(tag => (
                                <span key={tag} className="text-[10px] bg-indigo-900 text-indigo-200 border border-indigo-700 px-1.5 py-0.5 rounded">
                                    {tag}
                                </span>
                            ))}
                        </div>
                    </div>
                    <div className={`text-right flex-shrink-0 ${isUp ? 'text-red-400' : 'text-green-400'}`}>
                        <div className="text-lg font-bold font-mono">{currentPrice?.toFixed(2)}</div>
                        <div className="text-xs font-medium flex items-center justify-end gap-1">
                            {isUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                            {changePct > 0 ? '+' : ''}{changePct?.toFixed(2)}%
                        </div>
                    </div>
                </div>

                {/* 庫存資訊顯示區 */}
                {portfolioItem && (
                    <div className="flex justify-between items-center text-[10px] bg-gray-800/50 rounded px-2 py-1 mt-1 border border-gray-700/50">
                        <div className="text-gray-400 flex gap-2">
                            <span>{portfolioItem.shares.toLocaleString()} 股</span>
                            <span>均價 {portfolioItem.cost}</span>
                        </div>
                        {unrealizedPL && (
                            <div className={`font-mono font-bold ${unrealizedPL.val >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                                {unrealizedPL.val >= 0 ? '+' : ''}{Math.round(unrealizedPL.val).toLocaleString()} ({unrealizedPL.val >= 0 ? '+' : ''}{unrealizedPL.pct.toFixed(1)}%)
                            </div>
                        )}
                    </div>
                )}
            </div>

            <div className="grid grid-cols-3 gap-2 p-3 text-center">
                <div className="bg-gray-700/30 rounded p-2">
                    <div className="text-xs text-gray-400">連紅K</div>
                    <div className="font-mono text-lg font-bold text-red-400">{consecutiveRed}</div>
                </div>
                {/* KD 可點擊切換圖表模式 */}
                <button
                    onClick={() => setChartMode(m => m === 'kd' ? 'ma' : 'kd')}
                    className={`rounded p-2 transition-colors ${chartMode === 'kd' ? 'bg-purple-900/50 ring-1 ring-purple-500' : 'bg-gray-700/30 hover:bg-gray-600/30'}`}
                >
                    <div className="text-xs text-gray-400">KD {chartMode === 'kd' && '✓'}</div>
                    <div className="font-mono text-sm font-bold">
                        <span className="text-orange-400">{stock.k}</span>/<span className="text-cyan-400">{stock.d}</span>
                    </div>
                </button>
                <div className="bg-gray-700/30 rounded p-2">
                    <div className="text-xs text-gray-400">支撐</div>
                    <div className="font-mono text-sm font-bold text-white">{stopLoss?.toFixed(1)}</div>
                </div>
            </div>

            {
                chartData.length > 0 && (
                    <div className="flex-1 w-full px-2 pb-2 min-h-0 relative flex flex-col">
                        <div ref={chartRef} className="flex-1 w-full min-h-0">
                            {chartInView ? (
                                <ResponsiveContainer width="100%" height="100%">
                                <ComposedChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                                    <CartesianGrid stroke="#374151" strokeDasharray="3 3" vertical={false} />
                                    <XAxis dataKey="date" hide />
                                    <YAxis yAxisId="price" orientation="right" domain={['auto', 'auto']} tick={{ fontSize: 9, fill: '#9ca3af' }} axisLine={false} tickLine={false} width={35} />
                                    <YAxis yAxisId="volume" orientation="left" domain={[0, maxVolume * 3]} hide />
                                    {chartMode === 'kd' && <YAxis yAxisId="kd" orientation="left" domain={[0, 100]} hide />}
                                    <Tooltip content={<CustomTooltip />} cursor={<CustomCursor />} />

                                    {/* 成交量柱狀圖 (底層) */}
                                    <Bar
                                        yAxisId="volume"
                                        dataKey="volume"
                                        fill="#3b82f6"
                                        fillOpacity={0.2}
                                        isAnimationActive={false}
                                    />

                                    {/* K線蠟燭圖 (上層) */}
                                    <Bar
                                        yAxisId="price"
                                        dataKey="priceRange"
                                        shape={<CandleStickShape />}
                                        isAnimationActive={false}
                                        barSize={8}
                                    />

                                    {chartMode === 'ma' ? (
                                        <>
                                            {/* 均線模式 */}
                                            <Line yAxisId="price" type="monotone" dataKey="ma5" stroke="#f59e0b" dot={false} strokeWidth={1} name="MA5" />
                                            <Line yAxisId="price" type="monotone" dataKey="ma10" stroke="#10b981" dot={false} strokeWidth={1} name="MA10" />
                                            <Line yAxisId="price" type="monotone" dataKey="ma20" stroke="#ec4899" dot={false} strokeWidth={1} name="MA20" />
                                        </>
                                    ) : (
                                        <>
                                            {/* KD模式 */}
                                            <Line yAxisId="kd" type="monotone" dataKey="k" stroke="#fb923c" dot={false} strokeWidth={1.5} name="K" />
                                            <Line yAxisId="kd" type="monotone" dataKey="d" stroke="#22d3ee" dot={false} strokeWidth={1.5} name="D" />
                                            <ReferenceLine yAxisId="kd" y={80} stroke="rgba(239, 68, 68, 0.3)" strokeDasharray="3 3" />
                                            <ReferenceLine yAxisId="kd" y={20} stroke="rgba(34, 197, 94, 0.3)" strokeDasharray="3 3" />
                                        </>
                                    )}
                                </ComposedChart>
                            </ResponsiveContainer>
                            ) : (
                                <div className="w-full h-full bg-gray-700/10 animate-pulse rounded flex items-center justify-center">
                                    <BarChart2 className="text-gray-700 w-8 h-8 opacity-20" />
                                </div>
                            )}
                        </div>
                        {/* 圖例 */}
                        <div className="flex justify-center gap-3 text-[10px] mt-1 shrink-0">
                            {chartMode === 'ma' ? (
                                <>
                                    <span className="text-amber-500">● MA5</span>
                                    <span className="text-emerald-500">● MA10</span>
                                    <span className="text-pink-500">● MA20</span>
                                </>
                            ) : (
                                <>
                                    <span className="text-orange-400">● K</span>
                                    <span className="text-cyan-400">● D</span>
                                </>
                            )}
                            <span className="text-blue-400/50">■ 成交量</span>
                        </div>
                    </div>
                )
            }

            {/* Stock History Calendar Popup */}
            <StockHistoryCalendar
                isOpen={isCalendarOpen}
                onClose={() => setIsCalendarOpen(false)}
                stockName={name}
                ticker={ticker}
                historyDates={historyDates}
            />
        </div>
    );
};

export default StockCardMini;
