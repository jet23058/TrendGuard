import React, { useState, useEffect } from 'react';
import { BookOpen, AlertTriangle, Info, Clock, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import Header from '../components/Header';
import { auth, googleProvider } from '../firebase';
import { signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';

const KnowledgeCard = ({ title, icon: Icon, children, color = "blue" }) => {
    const colorClasses = {
        blue: "border-l-4 border-blue-500 bg-gray-800",
        yellow: "border-l-4 border-yellow-500 bg-gray-800",
        red: "border-l-4 border-red-500 bg-gray-800",
        green: "border-l-4 border-green-500 bg-gray-800",
        purple: "border-l-4 border-purple-500 bg-gray-800",
    };

    return (
        <div className={`p-6 rounded-lg shadow-lg ${colorClasses[color]} mb-6`}>
            <div className="flex items-center gap-3 mb-4">
                <div className={`p-2 rounded-full bg-gray-700`}>
                    <Icon size={24} className={`text-${color}-400`} />
                </div>
                <h3 className="text-xl font-bold text-white">{title}</h3>
            </div>
            <div className="text-gray-300 space-y-2 leading-relaxed">
                {children}
            </div>
        </div>
    );
};

const KnowledgeHub = () => {
    const [user, setUser] = useState(null);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
        });
        return () => unsubscribe();
    }, []);

    const handleLogin = async () => {
        try {
            await signInWithPopup(auth, googleProvider);
        } catch (err) {
            console.error("Login failed:", err);
            alert("登入失敗");
        }
    };

    const handleLogout = async () => {
        try {
            await signOut(auth);
        } catch (err) {
            console.error("Logout failed:", err);
        }
    };

    return (
        <div className="min-h-screen bg-gray-950 text-white pb-10">
            <Header 
                user={user} 
                onLogin={handleLogin} 
                onLogout={handleLogout} 
                onImport={() => {}} // 知識頁面暫不支援匯入操作，傳空函式
            />
            <div className="max-w-4xl mx-auto p-4 md:p-8">
                <header className="mb-8">
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <BookOpen className="text-blue-400" />
                        股市知識小站
                    </h1>
                    <p className="text-gray-400 mt-2">彙整台股常見術語、符號與交易規則，助您更了解市場運作。</p>
                </header>

                <div className="grid md:grid-cols-1 gap-6">
                    {/* 股票符號解密 */}
                    <KnowledgeCard title="股票名稱旁的符號是什麼意思？" icon={Info} color="yellow">
                        <ul className="space-y-4">
                            <li className="flex items-start gap-3">
                                <span className="bg-yellow-900 text-yellow-200 px-2 py-0.5 rounded text-sm font-mono font-bold shrink-0">*</span>
                                <div>
                                    <strong className="text-yellow-400">連 30 分鐘無成交</strong>
                                    <p className="text-sm text-gray-400 mt-1">代表該股票流動性較低，最近 30 分鐘內沒有任何一筆撮合成功。</p>
                                </div>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="bg-red-900 text-red-200 px-2 py-0.5 rounded text-sm font-mono font-bold shrink-0">!</span>
                                <div>
                                    <strong className="text-red-400">處置股票 / 注意股票</strong>
                                    <p className="text-sm text-gray-400 mt-1">
                                        代表該股近期漲跌幅過大、週轉率過高，被證交所列為注意或處置對象。可能會有撮合時間限制（如 5 分鐘或 20 分鐘一盤）。
                                    </p>
                                </div>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="bg-blue-900 text-blue-200 px-2 py-0.5 rounded text-sm font-mono font-bold shrink-0">#</span>
                                <div>
                                    <strong className="text-blue-400">處置股票 (全額交割/分盤交易)</strong>
                                    <p className="text-sm text-gray-400 mt-1">
                                        通常指已被列為處置股票，需要預收款券才能交易，且撮合時間延長。
                                    </p>
                                </div>
                            </li>
                        </ul>
                    </KnowledgeCard>

                    {/* 顏色代表意義 */}
                    <KnowledgeCard title="紅色與綠色的意義" icon={TrendingUp} color="red">
                        <div className="grid md:grid-cols-2 gap-4">
                            <div className="bg-gray-700/50 p-4 rounded border border-red-500/30">
                                <h4 className="font-bold text-red-400 mb-2 flex items-center gap-2">
                                    <TrendingUp size={16} /> 上漲 (紅色)
                                </h4>
                                <p className="text-sm">
                                    在台灣股市，<span className="text-red-400 font-bold">紅色</span>代表股價上漲。這與美股（綠漲紅跌）相反。
                                    <br />
                                    漲停板：當日漲幅達到 10%。
                                </p>
                            </div>
                            <div className="bg-gray-700/50 p-4 rounded border border-green-500/30">
                                <h4 className="font-bold text-green-400 mb-2 flex items-center gap-2">
                                    <TrendingDown size={16} /> 下跌 (綠色)
                                </h4>
                                <p className="text-sm">
                                    <span className="text-green-400 font-bold">綠色</span>代表股價下跌。
                                    <br />
                                    跌停板：當日跌幅達到 10%。
                                </p>
                            </div>
                        </div>
                    </KnowledgeCard>

                    {/* 交易時間 */}
                    <KnowledgeCard title="交易時間與盤別" icon={Clock} color="purple">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-gray-700 text-gray-200">
                                    <tr>
                                        <th className="p-3">盤別</th>
                                        <th className="p-3">時間</th>
                                        <th className="p-3">說明</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-700">
                                    <tr>
                                        <td className="p-3 font-bold text-purple-300">盤前試撮</td>
                                        <td className="p-3">08:30 - 09:00</td>
                                        <td className="p-3 text-gray-400">可掛單，模擬撮合價格，09:00 正式開盤。</td>
                                    </tr>
                                    <tr>
                                        <td className="p-3 font-bold text-blue-300">普通交易 (盤中)</td>
                                        <td className="p-3">09:00 - 13:30</td>
                                        <td className="p-3 text-gray-400">主要交易時段，逐筆撮合。</td>
                                    </tr>
                                    <tr>
                                        <td className="p-3 font-bold text-yellow-300">盤後定價</td>
                                        <td className="p-3">14:00 - 14:30</td>
                                        <td className="p-3 text-gray-400">以當日收盤價進行交易，電腦隨機撮合。</td>
                                    </tr>
                                    <tr>
                                        <td className="p-3 font-bold text-gray-300">零股交易</td>
                                        <td className="p-3">盤中 / 盤後</td>
                                        <td className="p-3 text-gray-400">盤中 09:10 起每 1 分鐘撮合；盤後 13:40 - 14:30 僅撮合一次。</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </KnowledgeCard>

                     {/* 處置股票與注意股票詳解 */}
                     <KnowledgeCard title="什麼是注意股票與處置股票？" icon={AlertTriangle} color="blue">
                         <div className="space-y-4">
                             <div>
                                 <h4 className="text-orange-400 font-bold mb-1">⚠️ 注意股票 (Warning)</h4>
                                 <p className="text-sm">
                                     當股票漲跌幅、週轉率或成交量異常時，證交所會列為「注意股票」。
                                     此時交易規則<strong>尚未改變</strong>，僅作為提醒投資人風險。
                                 </p>
                             </div>
                             <div>
                                 <h4 className="text-red-400 font-bold mb-1">🚫 處置股票 (Disposition)</h4>
                                 <p className="text-sm">
                                     若連續多日被列為注意股票，就會進入「處置」階段，也就是俗稱的「關廁所」。
                                 </p>
                                 <ul className="list-disc list-inside text-sm text-gray-400 mt-2 ml-2 space-y-1">
                                     <li><strong>第一次處置：</strong>通常改為 5 分鐘撮合一次。</li>
                                     <li><strong>第二次處置：</strong>通常改為 20 分鐘撮合一次，且需「預收款券」（圈存），要先存錢/存股才能下單。</li>
                                 </ul>
                             </div>
                         </div>
                    </KnowledgeCard>

                </div>
            </div>
        </div>
    );
};

export default KnowledgeHub;
