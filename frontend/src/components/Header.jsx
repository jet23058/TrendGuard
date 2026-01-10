import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BarChart2, Info, LogOut, User as UserIcon } from 'lucide-react';

const Header = ({ user, onLogin, onLogout }) => {
    const location = useLocation();

    // Helper to determine if link is active
    const getLinkClass = (path) => {
        const isActive = location.pathname === path;
        return isActive
            ? "px-3 py-2 text-sm font-bold text-white bg-blue-600 rounded-md shadow-md shadow-blue-900/50 transition-all border border-blue-500"
            : "px-3 py-2 text-sm font-medium text-gray-400 hover:text-white hover:bg-gray-800 rounded-md transition-colors";
    };

    return (
        <header className="bg-gray-900 border-b border-gray-800 sticky top-0 z-10 shadow-lg">
            <div className="max-w-7xl mx-auto px-4 py-3">
                <div className="flex justify-between items-center mb-0">
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-3">
                            <div className="bg-blue-600 p-2 rounded-lg">
                                <BarChart2 className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <h1 className="text-xl font-bold tracking-tight text-white hidden md:block">利弗摩爾台股戰情室</h1>
                                    <h1 className="text-xl font-bold tracking-tight text-white md:hidden">戰情室</h1>

                                    {/* Tooltip */}
                                    <div className="group relative flex items-center">
                                        <Info className="w-5 h-5 text-gray-400 hover:text-yellow-400 cursor-help transition-colors" />
                                        <div className="absolute left-1/2 -translate-x-1/2 top-full mt-3 w-80 p-4 bg-[#FEFCE8] border-2 border-yellow-400 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50 transform translate-y-2 group-hover:translate-y-0">
                                            <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-[#FEFCE8] border-t-2 border-l-2 border-yellow-400 transform rotate-45"></div>
                                            <div className="relative z-10 text-left">
                                                <h4 className="text-[#854D0E] font-bold text-base mb-2 border-b border-yellow-300 pb-2">
                                                    📖 關於傑西·利弗摩爾
                                                </h4>
                                                <p className="text-[#A16207] text-xs mb-2 leading-relaxed">
                                                    被譽為「投機之王」，以其對於價格波動的敏銳觀察與「關鍵點」理論聞名。
                                                </p>
                                                <ul className="text-[#713F12] text-xs space-y-1.5 list-disc pl-4">
                                                    <li><strong className="text-[#854D0E]">順勢而為：</strong>不猜頭摸底，沿著最小阻力線操作。</li>
                                                    <li><strong className="text-[#854D0E]">關鍵點 (Pivot)：</strong>耐心等待股價突破關鍵價位再進場。</li>
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Primary Nav */}
                        <nav className="hidden md:flex items-center gap-2">
                            <Link to="/" className={getLinkClass('/')}>戰情室</Link>
                            <Link to="/articles" className={getLinkClass('/articles')}>每日文章</Link>
                        </nav>
                    </div>

                    {/* User Controls */}
                    <div className="flex items-center gap-4">
                        {user ? (
                            <div className="flex items-center gap-3">
                                <div className="flex items-center gap-2 bg-gray-800 py-1.5 px-3 rounded-full border border-gray-700">
                                    <img src={user.photoURL} alt={user.displayName} className="w-6 h-6 rounded-full" />
                                    <span className="text-sm text-gray-300 hidden md:block">{user.displayName}</span>
                                    <button onClick={onLogout} className="text-gray-400 hover:text-red-400 p-1 rounded-full hover:bg-gray-700 transition-colors" title="登出">
                                        <LogOut size={16} />
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <button
                                onClick={onLogin}
                                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all shadow-lg hover:shadow-blue-900/50 flex items-center gap-2"
                            >
                                <UserIcon size={16} />
                                <span className="hidden md:inline">登入 / 註冊</span>
                                <span className="md:hidden">登入</span>
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
