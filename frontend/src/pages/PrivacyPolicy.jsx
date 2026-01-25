import React from 'react';
import Header from '../components/Header';
import { auth, googleProvider } from '../firebase';
import { signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';

const PrivacyPolicy = () => {
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
                <h1 className="text-3xl font-bold text-white mb-8">隱私權政策 (Privacy Policy)</h1>
                
                <div className="space-y-6 text-gray-400 leading-relaxed">
                    <p>最後更新日期：2026年1月25日</p>
                    
                    <p>
                        歡迎使用 TrendGuard（以下簡稱「本服務」）。我們非常重視您的隱私權，本政策旨在說明我們如何收集、使用及保護您的個人資訊。
                    </p>

                    <h2 className="text-xl font-bold text-white mt-8 mb-4">1. 資料收集</h2>
                    <p>
                        當您使用本服務時，我們可能會收集以下類型的資訊：
                    </p>
                    <ul className="list-disc pl-6 space-y-2">
                        <li><strong>帳戶資訊：</strong>當您使用 Google 帳戶登入時，我們會接收您的 Email 地址、姓名與頭像資訊，僅用於身份驗證與個人化設定。</li>
                        <li><strong>使用數據：</strong>您在本平台上的操作紀錄，例如追蹤的股票清單、筆記內容等。這些資料會儲存於雲端資料庫 (Firebase Firestore) 以提供跨裝置同步功能。</li>
                    </ul>

                    <h2 className="text-xl font-bold text-white mt-8 mb-4">2. 資料使用方式</h2>
                    <p>我們收集的資料僅用於：</p>
                    <ul className="list-disc pl-6 space-y-2">
                        <li>提供並維護本服務的功能。</li>
                        <li>記住您的偏好設定（如關注清單）。</li>
                        <li>改善使用者體驗與系統效能。</li>
                    </ul>

                    <h2 className="text-xl font-bold text-white mt-8 mb-4">3. 資料分享與揭露</h2>
                    <p>
                        除法律規定或為了保護本服務權利外，我們<strong>絕對不會</strong>將您的個人資訊出售、出租或分享給任何第三方。
                    </p>

                    <h2 className="text-xl font-bold text-white mt-8 mb-4">4. 資料安全</h2>
                    <p>
                        我們使用業界標準的安全措施（如 Firebase Authentication 與 Firestore Security Rules）來保護您的資料。但請注意，網際網路傳輸無法保證 100% 安全。
                    </p>

                    <h2 className="text-xl font-bold text-white mt-8 mb-4">5. 聯絡我們</h2>
                    <p>
                        如果您對本隱私權政策有任何疑問，請透過 GitHub Issues 或 Email 聯絡我們。
                    </p>
                </div>
            </div>
        </div>
    );
};

export default PrivacyPolicy;
