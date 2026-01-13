import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Calendar, TrendingUp, Activity, AlertTriangle, ChevronRight, Share2, Loader2, Factory } from 'lucide-react';
import StockCardMini from '../components/StockCardMini';
import SimpleMarkdown from '../components/SimpleMarkdown';
import IndustryGroup from '../components/IndustryGroup';

const DailyReport = () => {
    const { date } = useParams();
    const [data, setData] = useState(null);
    const [article, setArticle] = useState(null); // AI/Generated Article Content
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchReport = async () => {
            setLoading(true);
            // 依據你的環境設定 BASE_URL
            const BASE_URL = import.meta.env.PROD
                ? 'https://raw.githubusercontent.com/jet23058/TrendGuard/data'
                : '/data';

            try {
                // 1. Fetch Core Data (Scan Results)
                const histRes = await fetch(`${BASE_URL}/history/${date}.json`);
                if (histRes.ok) {
                    const scanData = await histRes.json();
                    setData(scanData);
                }

                // 2. Fetch Rich Article (AI Content)
                const articleRes = await fetch(`${BASE_URL}/articles/${date}.json`);
                if (articleRes.ok) {
                    const articleData = await articleRes.json();
                    setArticle(articleData);
                }
            } catch (err) {
                console.error("Error fetching report:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchReport();
    }, [date]);

    // Group stocks by industry for display
    const groupedStocks = React.useMemo(() => {
        if (!data?.stocks) return {};
        return data.stocks.reduce((acc, stock) => {
            const sector = stock.sector || '其他';
            if (!acc[sector]) acc[sector] = [];
            acc[sector].push(stock);
            return acc;
        }, {});
    }, [data]);

    // Helper to sort industries by count
    const sortedIndustries = React.useMemo(() => {
        return Object.entries(groupedStocks).sort((a, b) => b[1].length - a[1].length);
    }, [groupedStocks]);

    if (loading) return (
        <div className="min-h-screen bg-gray-950 flex items-center justify-center text-white">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500 mr-2" />
            讀取分析報告...
        </div>
    );

    if (!data || !data.stocks) return <div className="min-h-screen bg-gray-950 flex items-center justify-center text-white">找不到該日資料</div>;

    // Data Preparation
    const topStock = data.stocks[0];
    const bullCount = data.summary?.buySignals || data.stocks.length;
    const newCount = data.changes?.new?.length || 0;

    // 優先使用 AI 生成的標題，否則使用動態標題
    const marketSentiment = bullCount > 20 ? "極度火熱" : bullCount > 10 ? "多方強勢" : "震盪整理";
    const displayTitle = article?.title || `台股${marketSentiment}！${newCount} 檔新黑馬突圍`;

    // 優先使用 AI 生成的內容，否則使用預設模板
    const displayContent = article?.content || `
## 昨日盤勢小結

今日台股收盤，TrendGuard 系統透過全市場掃描，篩選出 **${bullCount}** 檔符合「突破關鍵點 + 均線多頭」的強勢標的。
目前的市場氣氛呈現 **${marketSentiment}** 格局。
${newCount > 0 ? `值得注意的是，今日有 **${newCount}** 檔個股新進榜單，顯示資金正在尋找新的攻擊發起點。` : '今日無新進榜個股，顯示市場處於既有趨勢的延續期。'}
  `;



    return (
        <div className="min-h-screen bg-gray-950 text-gray-300 font-sans selection:bg-blue-500/30">
            {/* 頂部導航 */}
            <nav className="border-b border-gray-800 bg-gray-900/50 backdrop-blur sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
                        <ArrowLeft size={20} /> <span className="font-bold">返回</span>
                    </Link>
                    <div className="text-sm text-gray-500 font-mono">{date}</div>
                </div>
            </nav>

            <main className="max-w-5xl mx-auto px-4 py-12">
                {/* === 1. 標題區 (Hero Section) === */}
                <header className="mb-12 text-center max-w-3xl mx-auto">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-900/30 text-blue-400 text-xs font-bold mb-4 border border-blue-800">
                        <Activity size={14} /> 利弗摩爾動能掃描
                        {article?.isAiGenerated && <span className="ml-2 px-1 bg-purple-900/50 text-purple-300 rounded text-[10px]">AI Analysis</span>}
                    </div>
                    <h1 className="text-3xl md:text-5xl font-bold text-white mb-8 leading-tight">
                        {displayTitle}
                    </h1>
                    <div className="flex items-center justify-center gap-6 text-sm text-gray-400">
                        <span className="flex items-center gap-2"><Calendar size={16} /> {date}</span>
                        <span className="flex items-center gap-2"><TrendingUp size={16} /> 多頭標的：<b className="text-white">{bullCount}</b> 檔</span>
                    </div>
                </header>

                {/* === 2. 深度分析文章 (AI Generated) === */}
                <article className="prose prose-invert max-w-3xl mx-auto mb-20 bg-gray-900/30 p-8 rounded-2xl border border-gray-800 shadow-xl">
                    <SimpleMarkdown content={displayContent} />
                </article>


                {/* === 3. 完整突破清單 (Grouped by Sector) === */}
                <section className="mb-20">
                    <div className="flex items-center gap-3 mb-8 border-b border-gray-800 pb-4">
                        <div className="bg-blue-600 w-1 h-8 rounded-full"></div>
                        <h3 className="text-2xl font-bold text-white">今日突破型態個股 ({data.stocks.length}檔)</h3>
                    </div>

                    <div className="space-y-2">
                        {sortedIndustries.map(([sector, stocks]) => (
                            <IndustryGroup
                                key={sector}
                                sector={sector}
                                stocks={stocks}
                                portfolioTickers={[]}
                                portfolio={[]}
                                stockHistoryMap={{}}
                            />
                        ))}
                    </div>
                </section>

            </main>

            {/* Footer */}
            <footer className="border-t border-gray-800 bg-gray-900 py-12 text-center text-gray-600 text-xs">
                <div className="max-w-2xl mx-auto px-4 space-y-4">
                    <p className="leading-relaxed">
                        本報告內容（包括但不限於 AI 生成之分析文字）僅供技術研究參考，<br />
                        並不保證精確性或完整性。投資人應獨立判斷。
                    </p>
                    <p>&copy; {new Date().getFullYear()} TrendGuard. All market data is for reference only.</p>
                </div>
            </footer>
        </div>
    );
};

export default DailyReport;
