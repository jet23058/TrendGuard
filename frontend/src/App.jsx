import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Activity,
  PieChart,
  Zap,
  BarChart2,
  Loader2,
  ChevronRight,
  Factory,
  Upload,
  X,
  Search,
  PlusCircle,
  Trash2,
  Check,
  AlertCircle,
  Briefcase,
  Image,
  FileText,
  LogOut,
  User as UserIcon,
  RefreshCw,
  Sparkles,
  MinusCircle,
  Info // 新增 Info 圖示
} from 'lucide-react';
import Tesseract from 'tesseract.js';

import StockCardMini from './components/StockCardMini';
import SimpleMarkdown from './components/SimpleMarkdown';
import IndustryGroup from './components/IndustryGroup';
import Header from './components/Header';
import { auth, db, googleProvider } from './firebase';
import { signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';
import { doc, getDoc, setDoc, collection, onSnapshot } from 'firebase/firestore';
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

// --- 台股代碼表 (擴大範圍) ---
const TAIWAN_STOCKS = [
  // 權值股
  { ticker: '2330', name: '台積電' },
  { ticker: '2317', name: '鴻海' },
  { ticker: '2454', name: '聯發科' },
  { ticker: '2303', name: '聯電' },
  { ticker: '2308', name: '台達電' },
  { ticker: '2412', name: '中華電' },
  { ticker: '2891', name: '中信金' },
  { ticker: '2882', name: '國泰金' },
  { ticker: '2881', name: '富邦金' },
  { ticker: '2886', name: '兆豐金' },
  { ticker: '2884', name: '玉山金' },
  { ticker: '2885', name: '元大金' },
  { ticker: '2887', name: '台新金' },
  { ticker: '2880', name: '華南金' },
  { ticker: '2883', name: '開發金' },
  // 航運
  { ticker: '2603', name: '長榮' },
  { ticker: '2609', name: '陽明' },
  { ticker: '2615', name: '萬海' },
  { ticker: '2618', name: '長榮航' },
  // AI/半導體
  { ticker: '3035', name: '智原' },
  { ticker: '6770', name: '力積電' },
  { ticker: '6443', name: '元晶' },
  { ticker: '3037', name: '欣興' },
  { ticker: '3008', name: '大立光' },
  { ticker: '3034', name: '聯詠' },
  { ticker: '2379', name: '瑞昱' },
  { ticker: '3443', name: '創意' },
  { ticker: '6669', name: '緯穎' },
  { ticker: '3661', name: '世芯-KY' },
  { ticker: '2449', name: '京元電子' },
  { ticker: '3711', name: '日月光投控' },
  { ticker: '2337', name: '旺宏' },
  { ticker: '3006', name: '晶豪科' },
  // 電子代工
  { ticker: '3231', name: '緯創' },
  { ticker: '2382', name: '廣達' },
  { ticker: '2356', name: '英業達' },
  { ticker: '4938', name: '和碩' },
  { ticker: '2324', name: '仁寶' },
  { ticker: '2353', name: '宏碁' },
  { ticker: '2357', name: '華碩' },
  // 面板/顯示
  { ticker: '3481', name: '群創' },
  { ticker: '2409', name: '友達' },
  { ticker: '8069', name: '元太' },
  // 傳產/其他
  { ticker: '2002', name: '中鋼' },
  { ticker: '1301', name: '台塑' },
  { ticker: '1303', name: '南亞' },
  { ticker: '1326', name: '台化' },
  { ticker: '2912', name: '統一超' },
  { ticker: '9910', name: '豐泰' },
  { ticker: '2377', name: '微星' },
  { ticker: '3017', name: '奇鋐' },
  { ticker: '2327', name: '國巨' },
  { ticker: '2474', name: '可成' },
  { ticker: '2301', name: '光寶科' },
  { ticker: '2345', name: '智邦' },
  { ticker: '2395', name: '研華' },
  { ticker: '2408', name: '南亞科' },
  { ticker: '3023', name: '信邦' },
  { ticker: '6239', name: '力成' },
  { ticker: '2207', name: '和泰車' },
  { ticker: '1216', name: '統一' },
  { ticker: '2105', name: '正新' },
  { ticker: '8438', name: '昶昕' },
  { ticker: '5351', name: '鈺創' },
  { ticker: '6284', name: '佳邦' },
  { ticker: '3092', name: '鴻碩' },
  { ticker: '3516', name: '亞帝歐' },
  { ticker: '3308', name: '聯德' },
  { ticker: '6937', name: '天虹' },
  { ticker: '5289', name: '宜鼎' },
  { ticker: '2467', name: '志聖' },
  { ticker: '4967', name: '十銓' },
  { ticker: '3131', name: '弘塑' },
  { ticker: '3289', name: '宜特' },
  { ticker: '2472', name: '立隆電' },
  // ETF
  { ticker: '0050', name: '元大台灣50' },
  { ticker: '0056', name: '元大高股息' },
  { ticker: '00878', name: '國泰永續高股息' },
  { ticker: '00919', name: '群益台灣精選高息' },
  { ticker: '00929', name: '復華台灣科技優息' }
];



// --- 2. 免責聲明 ---
const Disclaimer = () => (
  <div className="bg-yellow-900/20 border border-yellow-800/50 p-4 rounded-lg mb-6">
    <div className="flex items-start gap-3">
      <AlertCircle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
      <div className="text-sm text-yellow-200/80">
        <strong className="text-yellow-400">免責聲明：</strong>
        本系統提供之資訊僅供參考，不構成任何投資建議或買賣邀約。投資人應自行判斷並承擔投資風險，本系統不對任何因使用本資訊所造成之損失負責。過去績效不代表未來表現。
      </div>
    </div>
  </div>
);

// --- 2.0 輔助函式：移除 Markdown 符號取得純文字 (用於預覽) ---
const stripMarkdown = (md) => {
  if (!md) return '';
  return md
    .replace(/#{1,6} /g, '') // Remove Headers
    .replace(/\*\*/g, '')    // Remove Bold
    .replace(/- /g, '')      // Remove List bullets
    .replace(/---/g, '')     // Remove HR
    .replace(/\n+/g, ' ')    // Collapse newlines
    .trim();
};



// --- 3. 匯入庫存 Modal ---
const ImportModal = ({ isOpen, onClose, onImport, recommendedStocks = [] }) => {
  const [importList, setImportList] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStock, setSelectedStock] = useState(null);
  const [cost, setCost] = useState('');
  const [shares, setShares] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [allTwStocks, setAllTwStocks] = useState([]);
  const dropdownRef = useRef(null);

  // 載入完整台股清單
  useEffect(() => {
    fetch('/data/tw_stocks.json')
      .then(res => res.json())
      .then(data => setAllTwStocks(data))
      .catch(err => console.error('Failed to load stock list:', err));
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // 使用完整清單搜尋
  const filteredStocks = useMemo(() => {
    if (allTwStocks.length === 0) return [];
    if (!searchQuery) return allTwStocks.slice(0, 30); // 空白時顯示前 30 個
    const query = searchQuery.toLowerCase();
    return allTwStocks.filter(stock =>
      stock.ticker.toLowerCase().includes(query) || stock.name.toLowerCase().includes(query)
    ).slice(0, 30);
  }, [searchQuery, allTwStocks]);

  const handleSelectStock = (stock) => {
    setSelectedStock(stock);
    setSearchQuery(`${stock.ticker} ${stock.name}`);
    setIsDropdownOpen(false);
  };

  const handleAddToList = () => {
    if (!searchQuery || !cost || !shares) return;
    let stockToAdd = selectedStock;
    if (!stockToAdd) {
      const parts = searchQuery.split(' ');
      stockToAdd = { ticker: parts[0], name: parts[1] || parts[0] };
    }
    setImportList([...importList, {
      ticker: stockToAdd.ticker,
      name: stockToAdd.name,
      cost: parseFloat(cost),
      shares: parseInt(shares)
    }]);
    setSearchQuery('');
    setSelectedStock(null);
    setCost('');
    setShares('');
  };

  const handleRemoveItem = (index) => {
    setImportList(importList.filter((_, i) => i !== index));
  };

  // 新增覆蓋選項
  const [shouldOverwrite, setShouldOverwrite] = useState(false);

  const handleConfirm = () => {
    onImport(importList, shouldOverwrite);
    onClose();
  };

  // OCR 圖片處理
  const [isProcessing, setIsProcessing] = useState(false);
  const [ocrProgress, setOcrProgress] = useState(0);
  const fileInputRef = useRef(null);

  const handleImageUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsProcessing(true);
    setOcrProgress(0);

    const foundStocks = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const result = await Tesseract.recognize(file, 'chi_tra+eng', {
          logger: m => {
            if (m.status === 'recognizing text') {
              setOcrProgress(Math.round((i / files.length + m.progress / files.length) * 100));
            }
          }
        });

        const text = result.data.text;
        console.log('OCR Result:', text);

        // 清理文字並分割成行
        const lines = text.split('\n').map(l => l.replace(/\s+/g, ' ').trim()).filter(l => l);
        console.log('Lines:', lines);

        // 搜尋股票代碼 (4-6位數字)
        const codeMatches = text.match(/\b\d{4,6}\b/g) || [];
        codeMatches.forEach(code => {
          const stock = allTwStocks.find(s => s.ticker === code);
          if (stock && !foundStocks.find(f => f.ticker === code)) {
            foundStocks.push({ ...stock, cost: 0, shares: 0 });
          }
        });

        // 搜尋股票名稱 - 使用模糊匹配
        allTwStocks.forEach(stock => {
          // 完整名稱匹配
          if (text.includes(stock.name)) {
            if (!foundStocks.find(f => f.ticker === stock.ticker)) {
              foundStocks.push({ ...stock, cost: 0, shares: 0 });
            }
          }
          // 部分名稱匹配 (至少2個字)
          else if (stock.name.length >= 2) {
            const shortName = stock.name.substring(0, 2);
            if (text.includes(shortName)) {
              // 驗證後面沒有其他文字干擾
              const regex = new RegExp(shortName + '[電科金]?');
              if (regex.test(text) && !foundStocks.find(f => f.ticker === stock.ticker)) {
                foundStocks.push({ ...stock, cost: 0, shares: 0 });
              }
            }
          }
        });

        // 嘗試提取數字來猜測成本和股數
        // 券商 APP 格式通常是：股票名 價格 股數 獲利
        const numberPattern = /(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)/g;
        const numbers = text.match(numberPattern) || [];
        console.log('Numbers found:', numbers);

      } catch (err) {
        console.error('OCR Error:', err);
      }
    }

    if (foundStocks.length > 0) {
      setImportList(prev => {
        const existingTickers = new Set(prev.map(p => p.ticker));
        const newItems = foundStocks.filter(f => !existingTickers.has(f.ticker));
        return [...prev, ...newItems];
      });
      alert(`成功辨識 ${foundStocks.length} 檔股票！\n\n${foundStocks.map(s => `${s.ticker} ${s.name}`).join('\n')}\n\n請手動填入成本和股數。`);
    } else {
      alert('未能辨識出任何股票代碼。\n\n提示：請確保圖片清晰，或嘗試手動輸入。');
    }

    setIsProcessing(false);
    setOcrProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // CSV 文字貼上處理
  const [csvText, setCsvText] = useState('');

  const handleCsvParse = () => {
    if (!csvText.trim()) return;

    try {
      const rows = csvText.split('\n').filter(r => r.trim());
      const parsedItems = [];

      rows.forEach(row => {
        // 簡單的 CSV 解析，處理引號內的逗號
        // Regex: 匹配 (引號包圍的內容) 或 (非逗號內容)
        const regex = /"([^"]+)"|([^,]+)/g;
        let matches = [];
        let match;
        while ((match = regex.exec(row)) !== null) {
          matches.push(match[1] || match[2]); // match[1] 是引號內容，match[2] 是非引號內容
        }

        // 確保欄位足夠 (至少 4 欄: 代號, 名稱, 成本, 股數)
        if (matches.length >= 4) {
          let ticker = matches[0].trim();
          // 跳過標題列
          if (ticker === '股號' || ticker === '股票代號' || ticker === '代號') return;

          let name = matches[1].trim();
          let costStr = matches[2].trim().replace(/,/g, '');
          let sharesStr = matches[3].trim().replace(/,/g, '');

          let cost = parseFloat(costStr);
          let shares = parseInt(sharesStr);

          if (ticker && !isNaN(cost) && !isNaN(shares)) {
            // 檢查是否已存在
            parsedItems.push({ ticker, name, cost, shares });
          }
        }
      });

      if (parsedItems.length > 0) {
        // 如果是 CSV 匯入，預設建議覆蓋
        setShouldOverwrite(true);

        setImportList(prev => {
          const existingTickers = new Set(prev.map(p => p.ticker));
          const newItems = parsedItems.filter(p => !existingTickers.has(p.ticker));
          return [...prev, ...newItems];
        });
        setCsvText('');
        alert(`成功解析 ${parsedItems.length} 筆資料！\n\n注意：已自動勾選「覆蓋現有庫存」選項。`);
      } else {
        alert('解析失敗：未找到有效資料，請檢查格式。');
      }

    } catch (e) {
      console.error("CSV Parse Error", e);
      alert('解析發生錯誤，請檢查文字格式。');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl border border-gray-700 w-full max-w-2xl shadow-2xl flex flex-col max-h-[90vh]">
        <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-800 rounded-t-xl">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Upload size={18} /> 匯入我的庫存
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 flex-1 overflow-y-auto">
          {/* 圖片上傳區塊 */}
          <div className="mb-6 p-4 bg-purple-900/20 border border-purple-800/50 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <Image className="w-5 h-5 text-purple-400" />
              <h4 className="text-sm font-bold text-purple-300">截圖自動辨識</h4>
            </div>
            <p className="text-xs text-gray-400 mb-3">上傳券商 APP 的持股截圖，系統會自動辨識股票代碼</p>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageUpload}
              accept="image/*"
              multiple
              className="hidden"
              id="ocr-upload"
            />
            <label
              htmlFor="ocr-upload"
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer transition-colors ${isProcessing
                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                : 'bg-purple-600 hover:bg-purple-700 text-white'
                }`}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  辨識中 {ocrProgress}%
                </>
              ) : (
                <>
                  <Image size={16} />
                  選擇截圖
                </>
              )}
            </label>
          </div>

          {/* CSV 匯入區塊 */}
          <div className="mb-6 p-4 bg-blue-900/20 border border-blue-800/50 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5 text-blue-400" />
              <h4 className="text-sm font-bold text-blue-300">CSV / 文字貼上</h4>
            </div>
            <p className="text-xs text-gray-400 mb-3">支援格式：股號,名稱,成本,股數 (Excel 複製亦可)</p>

            <textarea
              value={csvText}
              onChange={(e) => setCsvText(e.target.value)}
              placeholder={`範例：\n2330,台積電,500,1000\n0050,元大台灣50,120,500`}
              className="w-full h-24 bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-blue-500 mb-3 font-mono"
            />

            <button
              onClick={handleCsvParse}
              disabled={!csvText.trim()}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${!csvText.trim()
                ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
            >
              解析內容
            </button>
          </div>

          {/* 手動輸入區塊標題 */}
          <div className="flex items-center gap-2 mb-3">
            <FileText className="w-4 h-4 text-gray-400" />
            <h4 className="text-sm font-bold text-gray-300">手動輸入</h4>
          </div>

          <div className="grid grid-cols-12 gap-3 mb-6 items-end bg-gray-800/50 p-4 rounded-lg border border-gray-700">
            <div className="col-span-12 md:col-span-5 relative" ref={dropdownRef}>
              <label className="block text-xs text-gray-400 mb-1 ml-1">股票代碼或名稱</label>
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => { setSearchQuery(e.target.value); setIsDropdownOpen(true); setSelectedStock(null); }}
                  onFocus={() => setIsDropdownOpen(true)}
                  placeholder="輸入 2330 或 台積電..."
                  className="w-full bg-gray-950 border border-gray-600 rounded-lg py-2 pl-3 pr-8 text-sm text-white focus:border-blue-500 focus:outline-none placeholder-gray-600"
                />
                <Search className="absolute right-2 top-2.5 text-gray-500 w-4 h-4" />
              </div>
              {isDropdownOpen && searchQuery && (
                <ul className="absolute z-50 w-full mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl max-h-48 overflow-auto">
                  {filteredStocks.length > 0 ? filteredStocks.map((stock) => (
                    <li key={stock.ticker} onClick={() => handleSelectStock(stock)} className="px-3 py-2 hover:bg-gray-700 cursor-pointer text-sm flex justify-between">
                      <span className="text-white font-mono">{stock.ticker}</span>
                      <span className="text-gray-300">{stock.name}</span>
                    </li>
                  )) : <li className="px-3 py-2 text-gray-500 text-sm">無相符結果 (可直接輸入)</li>}
                </ul>
              )}
            </div>
            <div className="col-span-6 md:col-span-3">
              <label className="block text-xs text-gray-400 mb-1 ml-1">平均成本 (元)</label>
              <input type="number" value={cost} onChange={(e) => setCost(e.target.value)} placeholder="例如 580" className="w-full bg-gray-950 border border-gray-600 rounded-lg py-2 px-3 text-sm text-white focus:border-blue-500 focus:outline-none" />
            </div>
            <div className="col-span-6 md:col-span-2">
              <label className="block text-xs text-gray-400 mb-1 ml-1">股數</label>
              <input type="number" value={shares} onChange={(e) => setShares(e.target.value)} placeholder="1000" className="w-full bg-gray-950 border border-gray-600 rounded-lg py-2 px-3 text-sm text-white focus:border-blue-500 focus:outline-none" />
            </div>
            <div className="col-span-12 md:col-span-2">
              <button onClick={handleAddToList} disabled={!searchQuery || !cost || !shares} className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-1">
                <PlusCircle size={16} /> 加入
              </button>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-bold text-gray-300 mb-2">待匯入清單 ({importList.length})</h4>
            <div className="bg-gray-950 border border-gray-800 rounded-lg overflow-hidden min-h-[120px]">
              {importList.length > 0 ? (
                <div className="divide-y divide-gray-800">
                  {importList.map((item, index) => (
                    <div key={index} className="grid grid-cols-12 p-3 items-center">
                      <div className="col-span-5">
                        <div className="font-bold text-white text-sm">{item.name}</div>
                        <div className="text-xs text-gray-500 font-mono">{item.ticker}</div>
                      </div>
                      <div className="col-span-3 text-right text-gray-300 font-mono text-sm">${item.cost.toLocaleString()}</div>
                      <div className="col-span-3 text-right text-gray-300 font-mono text-sm">{item.shares.toLocaleString()} 股</div>
                      <div className="col-span-1 flex justify-end">
                        <button onClick={() => handleRemoveItem(index)} className="text-gray-500 hover:text-red-400 p-1"><Trash2 size={16} /></button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : <div className="flex items-center justify-center h-24 text-gray-600 text-sm">尚未加入任何持股</div>}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-gray-700 bg-gray-800 rounded-b-xl flex justify-between items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer select-none hover:text-white transition-colors">
            <input
              type="checkbox"
              checked={shouldOverwrite}
              onChange={(e) => setShouldOverwrite(e.target.checked)}
              className="w-4 h-4 rounded border-gray-600 text-blue-600 focus:ring-blue-500 bg-gray-700"
            />
            <span className={shouldOverwrite ? "text-red-400 font-bold" : ""}>覆蓋現有庫存 (將刪除舊資料！)</span>
          </label>

          <div className="flex gap-3">
            <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">取消</button>
            <button onClick={handleConfirm} disabled={importList.length === 0} className="bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 text-white px-6 py-2 rounded-md text-sm font-bold flex items-center gap-2">
              <Check size={16} /> 確認匯入
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};





// --- 5.1 每日異動摘要組件 ---
const DailyChangesSection = ({ changes, portfolio }) => {
  if (!changes) return null;

  // 建立持有股票集合 (Set 查詢較快)
  const heldTickers = new Set(portfolio.map(p => p.ticker));

  const ChangeCard = ({ title, icon: Icon, colorClass, items, bgColor, badgeColor }) => {
    // 計算此分類中的庫存數量
    const heldCount = items.filter(i => heldTickers.has(i.ticker)).length;

    return (
      <div className={`rounded-xl border border-gray-800 ${bgColor} p-4 flex-1`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Icon className={`w-5 h-5 ${colorClass}`} />
            <h3 className="text-white font-bold">{title}</h3>
            {heldCount > 0 && (
              <span className="text-yellow-400 text-xs font-bold bg-yellow-900/30 px-1.5 py-0.5 rounded border border-yellow-700/30">
                持有: {heldCount}
              </span>
            )}
          </div>
          <span className={`text-xs px-2 py-0.5 rounded-full ${badgeColor} text-white font-mono`}>
            {items.length}
          </span>
        </div>
        <div className="space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
          {items.length > 0 ? (
            items.map(item => {
              const isHeld = heldTickers.has(item.ticker);
              return (
                <div key={item.ticker} className={`flex justify-between items-center text-sm p-2 rounded transition-colors ${isHeld ? 'bg-orange-900/40 border border-orange-700/50' : 'bg-gray-900/50 hover:bg-gray-800'}`}>
                  <div className="flex items-center gap-2">
                    <span className={`font-mono font-bold ${colorClass}`}>{item.ticker}</span>
                    <span className="text-gray-300 truncate max-w-[80px]">{item.name}</span>
                    {isHeld && (
                      <span className="px-1.5 py-0.5 bg-orange-600 text-white text-[10px] rounded font-bold">
                        持
                      </span>
                    )}
                  </div>
                  <div className="font-mono text-gray-400">
                    {item.currentPrice || item.close || '-'}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-gray-500 text-xs text-center py-4">無資料</div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <ChangeCard
        title="✨ 新進榜"
        icon={Sparkles}
        colorClass="text-green-400"
        items={changes.new}
        bgColor="bg-green-900/20"
        badgeColor="bg-green-600"
      />
      <ChangeCard
        title="🔥 續漲榜"
        icon={TrendingUp}
        colorClass="text-blue-400"
        items={changes.continued}
        bgColor="bg-blue-900/20"
        badgeColor="bg-blue-600"
      />
      <ChangeCard
        title="📉 被剔除"
        icon={MinusCircle}
        colorClass="text-gray-400"
        items={changes.removed}
        bgColor="bg-gray-900"
        badgeColor="bg-gray-600"
      />
    </div>
  );
};

// --- 6. 不在掃描結果但在庫存的股票 (簡化版：不使用即時 API) ---
// --- 6. 不在掃描結果但在庫存的股票 (手動同步 + Firestore 持久化) ---
const UnlistedPortfolioSection = ({ portfolio, scanResultTickers, user }) => {
  const [syncedData, setSyncedData] = useState({});
  const [loading, setLoading] = useState(false);
  const unlistedStocks = portfolio.filter(p => !scanResultTickers.includes(p.ticker));

  // 監聽 Firestore 資料
  useEffect(() => {
    if (!user) return;

    // 訂閱 users/{uid}/portfolioAnalysis 集合
    const unsubscribe = onSnapshot(collection(db, "users", user.uid, "portfolioAnalysis"), (snapshot) => {
      const data = {};
      snapshot.forEach(doc => {
        data[doc.id] = doc.data().data; // 結構: { data: fullJsonData, lastUpdated: ... }
      });
      setSyncedData(data);
    });

    return () => unsubscribe();
  }, [user]);

  const handleSync = async () => {
    if (!user) {
      alert("請先登入以使用同步功能");
      return;
    }
    setLoading(true);

    // 改為序列執行 (Sequential) 以避免觸發 API Rate Limit (403 Forbidden)
    for (const stock of unlistedStocks) {
      try {
        // Add cache-busting timestamp
        const res = await fetch(`/api/stock?ticker=${stock.ticker}&t=${new Date().getTime()}`);
        const text = await res.text(); // 先讀取文字，避免 JSON 解析錯誤

        try {
          if (!res.ok) {
            console.error(`API Error Status: ${res.status} ${res.statusText}`);
            try {
              const errorJson = JSON.parse(text);
              throw new Error(errorJson.error || 'API Error');
            } catch (e) {
              // If text is not JSON (e.g. empty or HTML), throw original text or status
              throw new Error(`API Error: ${res.status} ${res.statusText}`);
            }
          }
          const apiData = JSON.parse(text);

          // 寫入 Firestore
          await setDoc(doc(db, "users", user.uid, "portfolioAnalysis", stock.ticker), {
            ticker: stock.ticker,
            data: apiData,
            lastUpdated: new Date().toISOString()
          });

          // 成功後稍微暫停，避免太快
          await new Promise(resolve => setTimeout(resolve, 1000));

        } catch (jsonError) {
          console.error(`Sync failed for ${stock.ticker}: Not valid JSON`, text.substring(0, 100)); // 只顯示前100字
          // 如果是 HTML (通常是 404/500), 提示可能是環境問題
          if (text.trim().startsWith('<')) {
            throw new Error("API 回傳異常 (HTML)。請確認 Python Server (backend/server.py) 是否已啟動。");
          }
          throw jsonError;
        }
      } catch (err) {
        console.error(`Sync failed for ${stock.ticker}`, err);
        // 累積錯誤最後顯示，或顯示在 console
        if (err.code === 'permission-denied') {
          alert("權限不足：請檢查 Firebase Firestore Rules 設定。");
        }
        // 若遇到 403，顯示提示並中斷後續
        if (err.message.includes('403') || err.message.includes('Forbidden')) {
          alert(`同步失敗 (${stock.ticker})：請求過於頻繁被拒 (403)。請稍後再試。`);
          break;
        }
      }
    }

    setLoading(false);
  };

  if (unlistedStocks.length === 0) return null;

  return (
    <div className="mb-12">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Factory className="w-5 h-5 text-gray-400" />
          <h2 className="text-xl font-bold text-gray-300">庫存追蹤 (未入選)</h2>
          <span className="bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full text-sm">
            {unlistedStocks.length}
          </span>
        </div>
        <button
          onClick={handleSync}
          disabled={loading || !user}
          className="flex items-center gap-2 bg-blue-900/40 hover:bg-blue-800 text-blue-300 px-3 py-1.5 rounded-lg text-sm transition-colors disabled:opacity-50 border border-blue-700/50"
          title={!user ? "請先登入" : "同步最新股價"}
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {loading ? '同步中...' : '同步圖表'}
        </button>
      </div>

      <div className="overflow-x-auto pb-4 -mx-4 px-4">
        <div className="flex gap-3" style={{ minWidth: 'max-content' }}>
          {unlistedStocks.map(stock => {
            const apiData = syncedData[stock.ticker];

            // 如果已同步資料，使用完整 StockCardMini 顯示
            if (apiData) {
              // 簡易策略分析 logic (僅分析事實，非投資建議)
              let analysisText = "資料已同步，尚未出現明確訊號。";
              let analysisType = "neutral";

              const currentPrice = apiData.currentPrice;
              const cost = stock.cost || 0;

              if (cost > 0) {
                if (currentPrice < cost * 0.9) {
                  analysisText = "⚠️ 觸發策略設定之 10% 支撐門檻。";
                  analysisType = "danger";
                } else if (currentPrice > cost * 1.2) {
                  analysisText = "🚀 帳面獲利超過 20%，趨勢強勁。";
                  analysisType = "success";
                } else if (apiData.ma20 && currentPrice < apiData.ma20) {
                  analysisText = "股價跌破 20 日均線。";
                  analysisType = "warning";
                } else if (apiData.ma5 && currentPrice > apiData.ma5 && currentPrice > apiData.ma20) {
                  analysisText = "股價位於均線之上。";
                  analysisType = "info";
                }
              }

              // 構造相容的物件
              const fullData = {
                ...apiData,
                ticker: stock.ticker,
                analysis_result: {
                  text: analysisText,
                  type: analysisType
                }
              };

              return (
                <StockCardMini
                  key={stock.ticker}
                  stock={fullData}
                  portfolioItem={stock}
                  isInPortfolio={true}
                />
              );
            }

            // 未同步前顯示簡易卡片
            return (
              <div key={stock.ticker} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50 flex flex-col justify-between w-72 h-[450px] flex-shrink-0">
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <a
                        href={`https://tw.stock.yahoo.com/quote/${stock.ticker}.TW/technical-analysis`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xl font-bold font-mono text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        {stock.ticker} ↗
                      </a>
                      <div className="text-gray-500 text-sm mt-1">{stock.name}</div>
                    </div>
                    <span className="bg-yellow-900/30 text-yellow-400 text-xs px-2 py-1 rounded border border-yellow-700/50">
                      持有中
                    </span>
                  </div>

                  {(stock.cost > 0 && stock.shares > 0) && (
                    <div className="mt-4 bg-gray-900/50 rounded-lg p-3 space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">成本</span>
                        <span className="text-gray-300 font-mono">${stock.cost.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">庫存</span>
                        <span className="text-gray-300 font-mono">{stock.shares.toLocaleString()}股</span>
                      </div>
                      <div className="flex justify-between text-sm pt-1 border-t border-gray-800">
                        <span className="text-gray-500">市值</span>
                        <span className="text-gray-400 font-mono">
                          {(stock.cost * stock.shares).toLocaleString()} (預估)
                        </span>
                      </div>
                    </div>
                  )}
                </div>
                <div className="text-center text-gray-500 text-xs mt-auto">
                  尚未同步資料
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 提示訊息 */}
      <div className="mt-4 p-3 bg-blue-900/10 border border-blue-900/30 rounded-lg text-xs text-gray-400 flex items-start gap-2">
        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-blue-500" />
        <div className="space-y-1">
          <p>「同步圖表」使用即時 API 並將資料儲存至雲端，之後重新整理即可直接讀取。</p>
        </div>
      </div>
    </div>
  );
};

// --- 6. 文章 Banner 組件 ---
const ArticleBanner = ({ article }) => {
  const summary = stripMarkdown(article.content).substring(0, 100) + '...';

  return (
    <Link to={`/report/${article.date}`} className="block group cursor-pointer no-underline">
      <div className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border border-gray-700 hover:border-blue-500/50 rounded-xl p-6 shadow-lg transition-all duration-300 hover:shadow-blue-900/20 relative overflow-hidden">
        {/* 背景裝飾 */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl -mr-32 -mt-32 transition-opacity group-hover:opacity-100"></div>

        <div className="flex flex-col md:flex-row items-start md:items-center gap-6 relative z-10">
          {/* 左側：日期與標題 */}
          <div className="flex-shrink-0 min-w-[200px]">
            <span className="inline-flex items-center gap-1.5 text-blue-400 text-xs font-bold bg-blue-900/30 px-2 py-1 rounded mb-2 border border-blue-800/50">
              <Activity size={12} /> {article.date} 盤勢分析
            </span>
            <h3 className="text-xl font-bold text-white group-hover:text-blue-300 transition-colors">
              {article.title || '今日大盤重點速覽'}
            </h3>
          </div>

          {/* 中間：摘要 */}
          <div className="hidden md:block flex-1 border-l border-gray-700 pl-6">
            <p className="text-gray-400 text-sm leading-relaxed line-clamp-2 group-hover:text-gray-300 transition-colors">
              {summary}
            </p>
          </div>

          {/* 右側：Call to Action */}
          <div className="flex items-center text-gray-500 group-hover:text-white transition-colors">
            <span className="text-sm font-medium mr-2 hidden sm:block">閱讀全文</span>
            <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center group-hover:bg-blue-600 transition-all">
              <ChevronRight size={18} />
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
};



// --- 7. 主程式 ---
export default function App() {
  const [data, setData] = useState(null);
  const [article, setArticle] = useState(null); // 新增文章狀態
  // Removed selectedArticle state
  // 用於控制 Modal 顯示
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [portfolio, setPortfolio] = useState([]); // 僅允許登入後讀取，預設為空

  const [isDataLoaded, setIsDataLoaded] = useState(false);

  // 監聽登入狀態與資料同步
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      if (currentUser) {
        setIsDataLoaded(false); // 登入時先暫停同步寫入
        try {
          const docRef = doc(db, "users", currentUser.uid);
          const docSnap = await getDoc(docRef);

          if (docSnap.exists()) {
            const data = docSnap.data();
            if (data.portfolio && Array.isArray(data.portfolio)) {
              // 策略：簡單聯集，保留任一邊有的資料
              setPortfolio(local => {
                const cloudStocks = data.portfolio;
                const cloudTickers = new Set(cloudStocks.map(s => s.ticker));
                const merged = [...cloudStocks];

                local.forEach(item => {
                  if (!cloudTickers.has(item.ticker)) {
                    merged.push(item);
                  }
                });
                return merged;
              });
            }
          }
          // 若雲端無資料，setIsDataLoaded(true) 後會由下一個 effect 自動寫入本地資料
        } catch (err) {
          console.error("Error fetching portfolio:", err);
        } finally {
          setIsDataLoaded(true);
        }
      } else {
        setIsDataLoaded(false);
        setPortfolio([]); // 未登入狀態下清空庫存
      }
    });
    return () => unsubscribe();
  }, []);

  const [saveStatus, setSaveStatus] = useState('saved'); // 'saved', 'saving', 'error'

  // 儲存庫存 (僅寫入 Firestore)
  useEffect(() => {
    // 移除 LocalStorage 寫入，確保資料安全性與隱私 (未登入即清空)
    if (user && isDataLoaded) { // 只有在登入且完成初始載入後才寫入雲端
      const saveToFirestore = async () => {
        setSaveStatus('saving');
        try {
          await setDoc(doc(db, "users", user.uid), {
            portfolio: portfolio,
            updatedAt: new Date().toISOString()
          }, { merge: true });
          setSaveStatus('saved');
        } catch (err) {
          console.error("Error saving to Firestore:", err);
          setSaveStatus('error');
        }
      };
      // Debounce saving if needed, but for now direct call
      const timeoutId = setTimeout(saveToFirestore, 500);
      return () => clearTimeout(timeoutId);
    }
  }, [portfolio, user, isDataLoaded]);



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
      setPortfolio([]); // 登出後立即清空
      // alert("已登出"); // 可選：不打擾使用者
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const DATA_BASE_URL = import.meta.env.DEV
        ? '/data'
        : 'https://raw.githubusercontent.com/jet23058/TrendGuard/data';

      const response = await fetch(`${DATA_BASE_URL}/daily_scan_results.json`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const result = await response.json();
      setData(result);

      // Fetch Article if date exists
      if (result.date) {
        try {
          const articleRes = await fetch(`${DATA_BASE_URL}/articles/${result.date}.json`);
          if (articleRes.ok) {
            setArticle(await articleRes.json());
          }
        } catch (err) {
          console.warn("No article found for today");
        }
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleImport = (list, shouldOverwrite = false) => {
    // 如果是覆蓋模式，直接取代
    if (shouldOverwrite) {
      setPortfolio(list);
      return;
    }

    // 合併新匯入的股票，避免重複
    setPortfolio(prev => {
      const existingTickers = new Set(prev.map(p => p.ticker));
      const newItems = list.filter(item => !existingTickers.has(item.ticker));
      return [...prev, ...newItems];
    });
  };

  const handleClearPortfolio = () => {
    if (window.confirm('確定要清空所有庫存嗎？')) {
      setPortfolio([]);
    }
  };

  const portfolioTickers = useMemo(() => portfolio.map(p => p.ticker), [portfolio]);
  const scanResultTickers = useMemo(() => data?.stocks?.map(s => s.ticker) || [], [data]);

  // 按產業分組，庫存所在產業優先
  const groupedByIndustry = useMemo(() => {
    if (!data?.stocks) return {};
    const groups = {};
    data.stocks.forEach(stock => {
      const sector = stock.sector || '其他';
      if (!groups[sector]) groups[sector] = [];
      groups[sector].push(stock);
    });

    // 產業排序：有庫存股票的產業優先，再按數量排序
    const entries = Object.entries(groups);
    entries.sort((a, b) => {
      const aHasPortfolio = a[1].some(s => portfolioTickers.includes(s.ticker));
      const bHasPortfolio = b[1].some(s => portfolioTickers.includes(s.ticker));
      if (aHasPortfolio && !bHasPortfolio) return -1;
      if (!aHasPortfolio && bHasPortfolio) return 1;
      return b[1].length - a[1].length;
    });

    return entries.reduce((acc, [k, v]) => { acc[k] = v; return acc; }, {});
  }, [data, portfolioTickers]);

  const stats = useMemo(() => ({
    total: data?.stocks?.length || 0,
    industries: Object.keys(groupedByIndustry).length,
    buySignals: data?.stocks?.filter(s => s.signal?.type === 'breakout').length || 0,
    portfolioCount: portfolio.length
  }), [data, groupedByIndustry, portfolio]);

  const [displayTimes, setDisplayTimes] = useState({ scan: 'N/A', alert: 'N/A' });

  useEffect(() => {
    if (!data) return;

    const fmt = (iso) => {
      if (!iso) return 'N/A';
      const d = iso.endsWith('Z') ? iso : `${iso}Z`;
      return new Date(d).toLocaleString('zh-TW', {
        month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
        timeZone: 'Asia/Taipei'
      });
    };

    setDisplayTimes({
      scan: fmt(data.quoteTime || data.updatedAt),
      alert: fmt(data.alertUpdateTime || data.updatedAt)
    });
  }, [data]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">載入每日掃描結果中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-400 mb-2">載入失敗</p>
          <p className="text-gray-500 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-sans pb-10">
      {user && <ImportModal isOpen={isImportModalOpen} onClose={() => setIsImportModalOpen(false)} onImport={handleImport} recommendedStocks={data?.stocks || []} />}

      <Header
        user={user}
        onLogin={handleLogin}
        onLogout={handleLogout}
        onImport={() => setIsImportModalOpen(true)}
      />

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* 免責聲明 */}
        <Disclaimer />

        {/* 文章區塊 (已移除：首頁不顯示文章) */}

        {/* 統計卡片 */}

        {/* 文章閱讀 Modal Removed */}


        {/* 統計卡片 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-900 p-4 rounded-xl border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">符合條件</span>
              <Activity className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-2xl font-bold text-white font-mono">{stats.total} <span className="text-sm text-gray-500 font-normal">檔</span></div>
          </div>
          <div className="bg-gray-900 p-4 rounded-xl border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">產業分佈</span>
              <Factory className="w-4 h-4 text-purple-500" />
            </div>
            <div className="text-2xl font-bold text-purple-400 font-mono">{stats.industries} <span className="text-sm text-gray-500 font-normal">類</span></div>
          </div>
          <div
            onClick={() => user && setIsImportModalOpen(true)}
            className={`bg-gray-900 p-4 rounded-xl border border-yellow-900/50 ${user ? 'cursor-pointer hover:bg-gray-800 transition-colors' : ''}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">我的庫存</span>
              {user ? (
                <button className="flex items-center gap-1 bg-yellow-600/20 hover:bg-yellow-600/40 text-yellow-500 px-2 py-1 rounded text-xs transition-colors">
                  <PlusCircle className="w-3 h-3" />
                  匯入
                </button>
              ) : (
                <Briefcase className="w-4 h-4 text-yellow-500" />
              )}
            </div>
            <div className="text-2xl font-bold text-yellow-400 font-mono">{stats.portfolioCount} <span className="text-sm text-gray-500 font-normal">檔</span></div>
          </div>
          <div className="bg-gray-900 p-4 rounded-xl border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">更新時間</span>
              <Zap className="w-4 h-4 text-yellow-500" />
            </div>
            <div className="flex flex-col gap-1">
              <div className="text-xs text-gray-400 flex justify-between">
                <span>掃描:</span>
                <span className="font-mono text-white">{displayTimes.scan}</span>
              </div>
              <div className="text-xs text-gray-400 flex justify-between">
                <span>警示:</span>
                <span className="font-mono text-yellow-500">{displayTimes.alert}</span>
              </div>
            </div>
          </div>
        </div>

        {/* 篩選條件 */}
        <div className="bg-blue-900/20 border border-blue-900/50 p-4 rounded-lg">
          <p className="text-blue-200 text-sm">📊 <strong>篩選條件：</strong>{data?.criteria?.description}</p>
        </div>

        {/* Daily Changes Summary */}
        <DailyChangesSection changes={data?.changes} portfolio={portfolio} />

        {/* 不在掃描結果但在庫存的股票 */}
        <UnlistedPortfolioSection portfolio={portfolio} scanResultTickers={scanResultTickers} user={user} />

        <div className="border-t border-gray-800 my-4"></div>

        {/* 產業分組 */}
        {Object.entries(groupedByIndustry).map(([sector, stocks]) => (
          <IndustryGroup
            key={sector}
            sector={sector}
            stocks={stocks}
            portfolioTickers={portfolioTickers}
            portfolio={portfolio}
          />
        ))}
      </main>

      <section className="bg-gray-900 border border-gray-800 rounded-xl p-8 mt-12 mb-12">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-800">
          <Briefcase className="w-8 h-8 text-yellow-500" />
          <h2 className="text-2xl font-bold text-white">深度解析：傑西·利弗摩爾 (Jesse Livermore) 的交易心法</h2>
        </div>

        <div className="space-y-8 text-gray-300 leading-relaxed">

          {/* 第一段：策略核心 */}
          <div>
            <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <span className="bg-blue-600 w-1 h-6 block rounded-full"></span>
              什麼是「關鍵點 (Pivot Point)」理論？
            </h3>
            <p className="mb-4">
              傑西·利弗摩爾被譽為華爾街史上最偉大的投機客，他的核心哲學並非頻繁交易，而是「耐心等待」。他認為市場大部分時間都是雜亂無章的，只有當價格來到某個心理關卡——即他所謂的<strong>「關鍵點」</strong>時，真正的行情才會啟動。
            </p>
            <p>
              本系統透過演算法模擬此一邏輯：我們不預測底部，而是等待股價<strong>「帶量突破」</strong>長期的盤整區間。當價格創下近期新高，且均線呈現多頭排列時，往往代表市場上的「最小阻力線 (Line of Least Resistance)」已經轉向早方。
            </p>
          </div>

          {/* 第二段：資金管理 */}
          <div>
            <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <span className="bg-red-600 w-1 h-6 block rounded-full"></span>
              風險控管：保本是第一要務
            </h3>
            <p className="mb-4">
              利弗摩爾曾說：「賺大錢的不是依靠買進或賣出，而是依靠『等待』。」但在等待的過程中，保護本金至關重要。本系統內建嚴格的風險監控指標：
            </p>
            <ul className="list-disc pl-6 space-y-2 bg-gray-950/50 p-4 rounded-lg border border-gray-800">
              <li><strong>硬性停損機制：</strong>建議投資人將單筆虧損嚴格控制在總資金的 10% 以內。系統會自動標示跌破支撐的警示，避免人性的猶豫導致虧損擴大。</li>
              <li><strong>汰弱留強：</strong>不要在虧損的部位攤平。如果一檔股票買進後沒有如預期上漲，反而跌破關鍵點，代表判斷錯誤，應立即出場。</li>
            </ul>
          </div>

          {/* 第三段：加碼哲學 */}
          <div>
            <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <span className="bg-green-600 w-1 h-6 block rounded-full"></span>
              金字塔式加碼法 (Pyramiding)
            </h3>
            <p>
              真正的暴利來自於大波段趨勢。利弗摩爾強調<strong>「只有在賺錢的時候才加碼」</strong>。當第一筆試單部位出現獲利，且股價回測支撐不破、再次過高時，才是安全的加碼點。本系統的「連紅K」與「續漲榜」功能，即是為了輔助投資人判斷趨勢是否延續，以決定是否進行順勢加碼。
            </p>
          </div>

          <div className="bg-blue-900/20 border border-blue-800 p-4 rounded text-sm text-blue-200 mt-4">
            <strong>系統使用指南：</strong> 請利用上方的「市場掃描」功能查看今日符合突破條件的標的，並搭配「我的庫存」功能追蹤持股狀態。所有數據僅供技術分析研究，不作為直接的買賣建議。
          </div>
        </div>
      </section>

      <footer className="py-8 border-t border-gray-800 mt-12 bg-gray-900/50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="md:flex md:justify-between mb-8">
            <div className="mb-6 md:mb-0">
              <p className="text-gray-400 font-bold mb-2">利弗摩爾台股戰情室 TrendGuard</p>
              <p className="text-gray-500 text-xs mb-4">
                本系統基於 Jesse Livermore 交易哲學設計，提供台股技術分析數據。
                <br />
                資料來源：台灣證券交易所 (TWSE) 與 Yahoo Finance。
              </p>
            </div>

            {/* 歷史報告連結 */}
            <div>
              <h3 className="text-white font-bold mb-4 text-sm">📊 歷史市場分析報告</h3>
              <div className="flex flex-wrap gap-3">
                <Link to="/report/2026-01-10" className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm text-blue-400 transition-colors border border-gray-700">
                  2026-01-10 盤後分析
                </Link>
                <Link to="/report/2026-01-09" className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm text-gray-400 transition-colors border border-gray-700">
                  2026-01-09 盤後分析
                </Link>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-800 pt-8 text-center">
            <div className="flex justify-center gap-6 text-xs text-gray-500 mb-4">
              <a href="#" className="hover:text-gray-300">隱私權政策 (Privacy Policy)</a>
              <a href="#" className="hover:text-gray-300">使用條款 (Terms of Service)</a>
              <a href="#" className="hover:text-gray-300">免責聲明</a>
              <a href="#" className="hover:text-gray-300">聯絡我們</a>
            </div>

            <p className="text-gray-600 text-[10px]">
              ⚠️ 投資有風險，本站資訊僅供參考，不構成任何投資建議。使用者應自行承擔交易風險。
              <br />
              Copyright © {new Date().getFullYear()} TrendGuard. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div >
  );
}
