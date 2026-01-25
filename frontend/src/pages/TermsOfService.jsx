import React from 'react';
import Header from '../components/Header';
import { auth, googleProvider } from '../firebase';
import { signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';

const TermsOfService = () => {
    const [user, setUser] = React.useState(null);

    React.useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
        });
        return () => unsubscribe();
    }, []);

    const handleLogin = async () => {
        try {
            await signInWithPopup(auth, googleProvider);
        } catch (error) {
            console.error("Login failed:", error);
        }
    };

    const handleLogout = async () => {
        try {
            await signOut(auth);
        } catch (error) {
            console.error("Logout failed:", error);
        }
    };

    return (
        <div className="min-h-screen bg-gray-950 text-gray-300 font-sans">
            <Header user={user} onLogin={handleLogin} onLogout={handleLogout} />
            
            <div className="max-w-4xl mx-auto px-4 py-16">
                <h1 className="text-3xl font-bold text-white mb-8">使用條款 (Terms of Service)</h1>
                
                <div className="space-y-6 text-gray-400 leading-relaxed">
                    <p>最後更新日期：2026年1月25日</p>
                    
                    <p>
                        請在使用 TrendGuard（以下簡稱「本服務」）前仔細閱讀本使用條款。使用本服務即表示您同意受本條款之約束。
                    </p>

                    <h2 className="text-xl font-bold text-white mt-8 mb-4">1. 服務性質與免責聲明</h2>
                    <ul className="list-disc pl-6 space-y-2">
                        <li><strong>非投資建議：</strong>本服務提供的所有數據、圖表、分析與文章僅供技術研究與參考，<strong>不構成任何買賣建議或投資邀約</strong>。</li>
                        <li><strong>風險自負：</strong>股票交易涉及高風險，投資人應獨立判斷並自行承擔交易風險。對於使用本服務資訊而導致的任何投資損益，本服務不負任何責任。</li>
                        <li><strong>資料準確性：</strong>我們致力於提供準確的市場數據，但無法保證所有資訊（如股價、技術指標）均為即時或完全無誤。</li>
                    </ul>

                    <h2 className="text-xl font-bold text-white mt-8 mb-4">2. 使用規範</h2>
                    <p>您同意在使用本服務時：</p>
                    <ul className="list-disc pl-6 space-y-2">
                        <li>不利用本服務進行任何非法活動。</li>
                        <li>不嘗試破壞、干擾或攻擊本服務的伺服器與網路。</li>
                        <li>不使用自動化程式（如爬蟲）過度頻繁地存取本服務 API，以免影響其他使用者。</li>
                    </ul>

                    <h2 className="text-xl font-bold text-white mt-8 mb-4">3. 服務變更與終止</h2>
                    <p>
                        我們保留隨時修改、暫停或終止本服務部分或全部功能的權利，恕不另行通知。
                    </p>

                    <h2 className="text-xl font-bold text-white mt-8 mb-4">4. 智慧財產權</h2>
                    <p>
                        本服務之原始碼、演算法、視覺設計與內容（除公開市場數據外）均受著作權法保護，未經授權不得轉載或用於商業用途。
                    </p>
                </div>
            </div>
        </div>
    );
};

export default TermsOfService;
