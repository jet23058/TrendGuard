import React, { useState, useEffect, useMemo, useRef } from 'react';
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

// --- 1. K線圖繪製元件 ---
const CandleStickShape = (props) => {
  const { x, y, width, height, payload } = props;
  const { open, close, high, low } = payload;

  if (!high || !low || !open || !close) return null;

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

// --- 4. 精簡版股票卡片 ---
const StockCardMini = ({ stock, isInPortfolio, portfolioItem }) => {
  const { ticker, name, currentPrice, changePct, consecutiveRed, stopLoss, ohlc } = stock;
  const isUp = changePct >= 0;
  const yahooUrl = `https://tw.stock.yahoo.com/quote/${ticker}.TW/technical-analysis`;
  const [chartMode, setChartMode] = useState('ma'); // 'ma' or 'kd'

  const chartData = useMemo(() => {
    if (!ohlc || ohlc.length === 0) return [];
    return ohlc.slice(-20).map(item => ({ ...item, priceRange: [item.low, item.high] }));
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
    <div className={`bg-gray-800 rounded-xl border overflow-hidden shadow-lg flex-shrink-0 w-72 h-[450px] flex flex-col ${isInPortfolio ? 'border-yellow-500/50 ring-1 ring-yellow-500/30' : 'border-gray-700'}`}>
      <div className="p-3 border-b border-gray-700 bg-gray-900/50">
        <div className="flex justify-between items-center mb-1">
          <div className="flex items-center gap-2">
            <a href={yahooUrl} target="_blank" rel="noopener noreferrer" className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-2 py-0.5 rounded transition-colors cursor-pointer">
              {ticker} ↗
            </a>
            <h3 className="text-sm font-bold text-white truncate max-w-[80px]">{name}</h3>
            {isInPortfolio && <span className="text-[10px] bg-yellow-600 text-yellow-100 px-1.5 py-0.5 rounded">持有</span>}
          </div>
          <div className={`text-right ${isUp ? 'text-red-400' : 'text-green-400'}`}>
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
          <div className="text-xs text-gray-400">停損</div>
          <div className="font-mono text-sm font-bold text-white">{stopLoss?.toFixed(1)}</div>
        </div>
      </div>

      {chartData.length > 0 && (
        <div className="flex-1 w-full px-2 pb-2 min-h-0 relative">
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
          {/* 圖例 */}
          <div className="flex justify-center gap-3 text-[10px] mt-1">
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
      )}
    </div>
  );
};

// --- 5. 產業群組 ---
const IndustryGroup = ({ sector, stocks, portfolioTickers, portfolio }) => {
  // 排序：庫存優先
  const sortedStocks = useMemo(() => {
    return [...stocks].sort((a, b) => {
      const aInPortfolio = portfolioTickers.includes(a.ticker);
      const bInPortfolio = portfolioTickers.includes(b.ticker);
      if (aInPortfolio && !bInPortfolio) return -1;
      if (!aInPortfolio && bInPortfolio) return 1;
      return 0;
    });
  }, [stocks, portfolioTickers]);

  // 計算該產業中的庫存數量
  const portfolioCount = useMemo(() => {
    return stocks.filter(s => portfolioTickers.includes(s.ticker)).length;
  }, [stocks, portfolioTickers]);

  return (
    <div className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        <Factory className="w-5 h-5 text-blue-500" />
        <h3 className="text-lg font-bold text-white">
          {sector}
          <span className="text-blue-400 ml-2">({stocks.length})</span>
          {portfolioCount > 0 && (
            <span className="text-yellow-400 ml-2 text-sm">
              (庫存: {portfolioCount})
            </span>
          )}
        </h3>
        <ChevronRight className="w-5 h-5 text-gray-500" />
      </div>
      <div className="overflow-x-auto pb-4 -mx-4 px-4">
        <div className="flex gap-3" style={{ minWidth: 'max-content' }}>
          {sortedStocks.map(stock => {
            const portfolioItem = portfolio.find(p => p.ticker === stock.ticker);
            return (
              <StockCardMini
                key={stock.ticker}
                stock={stock}
                isInPortfolio={portfolioTickers.includes(stock.ticker)}
                portfolioItem={portfolioItem}
              />
            );
          })}
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

// --- 6. 不在推薦但在庫存的股票 (簡化版：不使用即時 API) ---
// --- 6. 不在推薦但在庫存的股票 (手動同步 + Firestore 持久化) ---
const UnlistedPortfolioSection = ({ portfolio, recommendedTickers, user }) => {
  const [syncedData, setSyncedData] = useState({});
  const [loading, setLoading] = useState(false);
  const unlistedStocks = portfolio.filter(p => !recommendedTickers.includes(p.ticker));

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
              // 簡易策略建議 logic
              let advice = "資料已同步，請自行判斷。";
              let adviceType = "hold";

              const currentPrice = apiData.currentPrice;
              const cost = stock.cost || 0;

              if (cost > 0) {
                if (currentPrice < cost * 0.9) {
                  advice = "⚠️ 觸發 10% 停損警告！離場觀望。";
                  adviceType = "sell";
                } else if (currentPrice > cost * 1.2) {
                  advice = "🚀 獲利 > 20%，可考慮加碼。";
                  adviceType = "buy";
                } else if (apiData.ma20 && currentPrice < apiData.ma20) {
                  advice = "跌破月線，請留意風險。";
                  adviceType = "neutral";
                } else if (apiData.ma5 && currentPrice > apiData.ma5 && currentPrice > apiData.ma20) {
                  advice = "均線之上，續抱觀察。";
                  adviceType = "hold";
                }
              }

              // 構造相容的物件
              const fullData = {
                ...apiData,
                ticker: stock.ticker,
                recommendation: {
                  text: advice,
                  type: adviceType
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
          <p className="opacity-80">注意：若在本地開發環境 (localhost) 且未啟動 API，同步可能會失敗。</p>
        </div>
      </div>
    </div>
  );
};

// --- 7. 主程式 ---
export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [portfolio, setPortfolio] = useState(() => {
    // 預設從 localStorage 載入 (未登入時)
    try {
      const saved = localStorage.getItem('tw_stock_portfolio');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

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
      }
    });
    return () => unsubscribe();
  }, []);

  const [saveStatus, setSaveStatus] = useState('saved'); // 'saved', 'saving', 'error'

  // 儲存庫存 (同時寫入 LocalStorage 與 Firestore)
  useEffect(() => {
    localStorage.setItem('tw_stock_portfolio', JSON.stringify(portfolio));

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

  // 手動同步功能
  const handleManualSync = async () => {
    if (!user) return;
    setSaveStatus('saving');
    try {
      await setDoc(doc(db, "users", user.uid), {
        portfolio: portfolio,
        updatedAt: new Date().toISOString()
      }, { merge: true });
      setSaveStatus('saved');
      alert('同步成功！已儲存到雲端。');
    } catch (err) {
      console.error("Manual sync failed:", err);
      setSaveStatus('error');
      alert('同步失敗，請檢查網路或權限設定。');
    }
  };

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
      // 登出後選擇保留當前畫面上的庫存，還是清空？
      // 為了體驗，保留當前狀態，直到下次重新整理或登入
      alert("已登出");
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await fetch('/data/daily_recommendations.json');
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      setData(await response.json());
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
  const recommendedTickers = useMemo(() => data?.stocks?.map(s => s.ticker) || [], [data]);

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
    buySignals: data?.stocks?.filter(s => s.recommendation?.type === 'buy').length || 0,
    portfolioCount: portfolio.length
  }), [data, groupedByIndustry, portfolio]);

  const scanTime = useMemo(() => {
    if (!data?.updatedAt) return 'N/A';
    // GitHub Actions 產生的時間是 UTC (無後綴)，需視為 UTC 處理
    const dateStr = data.updatedAt.endsWith('Z') ? data.updatedAt : `${data.updatedAt}Z`;

    return new Date(dateStr).toLocaleString('zh-TW', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      timeZoneName: 'short',
      timeZone: 'Asia/Taipei'
    });
  }, [data]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">載入每日推薦資料中...</p>
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
      <ImportModal isOpen={isImportModalOpen} onClose={() => setIsImportModalOpen(false)} onImport={handleImport} recommendedStocks={data?.stocks || []} />

      <header className="bg-gray-900 border-b border-gray-800 sticky top-0 z-10 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <BarChart2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white">利弗摩爾台股戰情室</h1>

                {/* 懸浮說明 Tooltip */}
                <div className="group relative flex items-center">
                  <Info className="w-5 h-5 text-gray-400 hover:text-yellow-400 cursor-help transition-colors" />

                  {/* Tooltip 本體 */}
                  <div className="absolute left-1/2 -translate-x-1/2 top-full mt-3 w-80 p-4 bg-[#FEFCE8] border-2 border-yellow-400 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50 transform translate-y-2 group-hover:translate-y-0">
                    {/* 小三角形箭頭 */}
                    <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-[#FEFCE8] border-t-2 border-l-2 border-yellow-400 transform rotate-45"></div>

                    {/* 內容 */}
                    <div className="relative z-10 text-left">
                      <h4 className="text-[#854D0E] font-bold text-base mb-2 border-b border-yellow-300 pb-2">
                        📖 關於傑西·利弗摩爾
                      </h4>
                      <p className="text-[#A16207] text-xs mb-2 leading-relaxed">
                        被譽為「投機之王」，本系統基於其《股票作手回憶錄》之核心哲學設計：
                      </p>
                      <ul className="text-[#713F12] text-xs space-y-1.5 list-disc pl-4">
                        <li><strong className="text-[#854D0E]">順勢而為：</strong>不猜頭摸底，沿著最小阻力線操作。</li>
                        <li><strong className="text-[#854D0E]">關鍵點 (Pivot)：</strong>耐心等待股價突破關鍵價位再進場。</li>
                        <li><strong className="text-[#854D0E]">資金管理：</strong>虧損絕不超過本金 10%，嚴格執行停損。</li>
                        <li><strong className="text-[#854D0E]">試單與加碼：</strong>分批進場，只有在賺錢時才加碼。</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 mt-0.5">
                <p className="text-xs text-gray-400">Livermore Breakout Scanner</p>
                <span className="bg-green-900/40 text-green-500 text-[10px] px-1.5 py-0.5 rounded border border-green-800/50">真實數據</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-3">
                <button
                  onClick={handleManualSync}
                  title="手動同步 (點擊強制儲存)"
                  className="p-1.5 rounded-full hover:bg-gray-800 text-gray-400 transition-colors relative"
                >
                  <RefreshCw size={16} className={saveStatus === 'saving' ? 'animate-spin text-blue-400' : saveStatus === 'error' ? 'text-red-400' : ''} />
                  {saveStatus === 'error' && <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>}
                </button>
                <div className="flex items-center gap-2 bg-gray-800 py-1.5 px-3 rounded-full border border-gray-700">
                  <img src={user.photoURL} alt={user.displayName} className="w-6 h-6 rounded-full" />
                  <span className="text-sm text-gray-300 hidden md:block">{user.displayName}</span>
                  <button onClick={handleLogout} className="text-gray-400 hover:text-red-400 p-1 rounded-full hover:bg-gray-700 transition-colors" title="登出">
                    <LogOut size={16} />
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={handleLogin}
                className="flex items-center gap-2 text-gray-300 hover:text-white px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
              >
                <UserIcon size={16} />
                <span className="text-sm font-medium">登入 Google</span>
              </button>
            )}

            <button onClick={() => setIsImportModalOpen(true)} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors flex items-center gap-2">
              <Upload size={16} /> 匯入庫存 {portfolio.length > 0 && <span className="bg-yellow-500 text-yellow-900 text-xs px-1.5 py-0.5 rounded-full font-bold">{portfolio.length}</span>}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* 免責聲明 */}
        <Disclaimer />

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
          <div className="bg-gray-900 p-4 rounded-xl border border-yellow-900/50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">我的庫存</span>
              <Briefcase className="w-4 h-4 text-yellow-500" />
            </div>
            <div className="text-2xl font-bold text-yellow-400 font-mono">{stats.portfolioCount} <span className="text-sm text-gray-500 font-normal">檔</span></div>
          </div>
          <div className="bg-gray-900 p-4 rounded-xl border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">掃描時間</span>
              <Zap className="w-4 h-4 text-yellow-500" />
            </div>
            <div className="text-xs font-mono text-gray-300 leading-relaxed">{scanTime}</div>
          </div>
        </div>

        {/* 篩選條件 */}
        <div className="bg-blue-900/20 border border-blue-900/50 p-4 rounded-lg">
          <p className="text-blue-200 text-sm">📊 <strong>篩選條件：</strong>{data?.criteria?.description}</p>
        </div>

        {/* Daily Changes Summary */}
        <DailyChangesSection changes={data?.changes} portfolio={portfolio} />

        {/* 不在推薦但在庫存的股票 */}
        <UnlistedPortfolioSection portfolio={portfolio} recommendedTickers={recommendedTickers} user={user} />

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

      <footer className="text-center py-6 border-t border-gray-800 mt-10">
        <p className="text-gray-500 text-xs">🎯 利弗摩爾台股戰情室 | 基於 Jesse Livermore 交易哲學設計</p>
        <p className="text-gray-600 text-xs mt-1">⚠️ 本系統僅供參考，不構成投資建議。投資有風險，請謹慎評估。</p>
      </footer>
    </div>
  );
}
