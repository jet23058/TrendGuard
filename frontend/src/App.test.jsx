import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import App, { normalizeSyncedStockData } from './App';
import { BrowserRouter } from 'react-router-dom';

// --- Mocks ---

// Mock child components that might render complex charts or cause issues
vi.mock('./components/Header', () => ({
  default: () => <div data-testid="mock-header">Header</div>
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  ComposedChart: () => <div>Chart</div>,
  Line: () => null,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ReferenceLine: () => null,
}));

// Mock Firebase functions to avoid auth issues during test
vi.mock('./firebase', () => ({
  auth: { currentUser: null },
  db: {},
  googleProvider: {},
}));
vi.mock('firebase/auth', () => ({
  signInWithPopup: vi.fn(),
  signOut: vi.fn(),
  onAuthStateChanged: vi.fn((auth, callback) => {
    callback(null); // Simulate no user logged in
    return () => {}; // Unsubscribe function
  })
}));
vi.mock('firebase/firestore', () => ({
  doc: vi.fn(),
  getDoc: vi.fn(),
  setDoc: vi.fn(),
  collection: vi.fn(),
  onSnapshot: vi.fn(),
}));

// Mock Data
const MOCK_DATA = {
  date: "2026-01-21",
  updatedAt: "2026-01-21T18:00:00Z",
  quoteTime: "2026-01-21T18:00:00Z",
  criteria: { description: "Test Criteria" },
  stocks: [
    { 
      ticker: "1101", name: "台泥", sector: "水泥工業", 
      consecutiveRed: 2, changePct: 1.5, currentPrice: 30,
      rsi: 85.2, rsiStatus: "overbought",
      volume: 2500, avgVolume30d: 1000, volumeRatio30d: 2.5, volumeStatus: "high", volumeAnomaly: true,
      price30dAgo: 24, price30dDate: "2025-12-22", changeFrom30dPct: 25,
      capitalText: "369.2億"
    },
    { 
      ticker: "2330", name: "台積電", sector: "半導體業", 
      consecutiveRed: 3, changePct: 6.5, currentPrice: 600,
      rsi: 55.1, rsiStatus: "neutral",
      volume: 1800, avgVolume30d: 1600, volumeRatio30d: 1.13, volumeStatus: "normal", volumeAnomaly: false,
      price30dAgo: 550, price30dDate: "2025-12-22", changeFrom30dPct: 9.09,
      capitalText: "2,593.0億"
    },
    { 
      ticker: "2603", name: "長榮", sector: "航運業", 
      consecutiveRed: 3, changePct: 2.0, currentPrice: 150,
      rsi: 18.4, rsiStatus: "oversold",
      volume: 450, avgVolume30d: 1000, volumeRatio30d: 0.45, volumeStatus: "low", volumeAnomaly: true,
      price30dAgo: 140, price30dDate: "2025-12-22", changeFrom30dPct: 7.14,
      capitalText: "529.0億"
    },
    { 
      ticker: "9999", name: "飆股", sector: "其他", 
      consecutiveRed: 5, changePct: 9.9, currentPrice: 100,
      rsi: 82.0, rsiStatus: "overbought",
      volume: 5000, avgVolume30d: 2000, volumeRatio30d: 2.5, volumeStatus: "high", volumeAnomaly: true,
      price30dAgo: 80, price30dDate: "2025-12-22", changeFrom30dPct: 25,
      capitalText: "50.0億"
    }
  ],
  changes: { new: [], continued: [], removed: [] }
};

const MOCK_RANKS = {
  ranks: {
    "1101": 100,
    "2330": 1,
    "2603": 200,
    "9999": 300
  }
};

describe('Synced stock data normalization', () => {
  it('uses the portfolio stock name when the API falls back to ticker as name', () => {
    const result = normalizeSyncedStockData(
      { ticker: '2330', name: '2330', currentPrice: 600 },
      { ticker: '2330', name: '台積電' }
    );

    expect(result.name).toBe('台積電');
  });

  it('keeps the API stock name when it returns a real name', () => {
    const result = normalizeSyncedStockData(
      { ticker: '3289', name: '宜特', currentPrice: 120 },
      { ticker: '3289', name: '舊名稱' }
    );

    expect(result.name).toBe('宜特');
  });
});

describe('App Filter Logic Tests', () => {
  // Setup fetch mock
  beforeEach(() => {
    localStorage.clear();
    global.fetch = vi.fn((url) => {
      if (url && url.includes('daily_scan_results.json')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(MOCK_DATA),
        });
      }
      if (url && url.includes('market_cap_rank.json')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(MOCK_RANKS),
        });
      }
      if (url && url.includes(`/articles/${MOCK_DATA.date}.json`)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ date: MOCK_DATA.date, title: '測試文章' }),
        });
      }
      // Mock other fetches to avoid errors
      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({}),
      });
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  // Helper to render App with Router
  const renderApp = () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
  };

  it('renders all stocks by default (Red K >= 2)', async () => {
    renderApp();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('符合條件')).toBeInTheDocument();
    });

    // Check if stocks are in the document
    expect(await screen.findByText('台泥')).toBeInTheDocument();
    expect(screen.getByText('台積電')).toBeInTheDocument();
    expect(screen.getByText('長榮')).toBeInTheDocument();
    expect(screen.getByText('飆股')).toBeInTheDocument();
  });

  it('renders the added daily scan fields on stock cards', async () => {
    renderApp();
    await waitFor(() => expect(screen.getByText('台泥')).toBeInTheDocument());

    expect(screen.getAllByText('RSI 14').length).toBeGreaterThan(0);
    expect(screen.getByText('369.2億')).toBeInTheDocument();
    expect(screen.getAllByText('量 / 30日均量').length).toBeGreaterThan(0);
    expect(screen.getAllByText('2.50x 異常').length).toBeGreaterThan(0);
  });

  it('filters by RSI overbought quick filter', async () => {
    renderApp();
    await waitFor(() => expect(screen.getByText('長榮')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'RSI > 80' }));

    expect(screen.getByText('台泥')).toBeInTheDocument();
    expect(screen.getByText('飆股')).toBeInTheDocument();
    expect(screen.queryByText('台積電')).not.toBeInTheDocument();
    expect(screen.queryByText('長榮')).not.toBeInTheDocument();
  });

  it('filters by the new dashboard search text', async () => {
    renderApp();
    await waitFor(() => expect(screen.getByText('台積電')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('搜尋每日掃描結果'), { target: { value: 'RSI>80' } });

    expect(screen.getByText('台泥')).toBeInTheDocument();
    expect(screen.getByText('飆股')).toBeInTheDocument();
    expect(screen.queryByText('台積電')).not.toBeInTheDocument();
    expect(screen.queryByText('長榮')).not.toBeInTheDocument();
  });

  it('filters by common combo for oversold rebound', async () => {
    renderApp();
    await waitFor(() => expect(screen.getByText('台泥')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: '超跌回拉' }));

    expect(screen.getByText('長榮')).toBeInTheDocument();
    expect(screen.queryByText('台泥')).not.toBeInTheDocument();
    expect(screen.queryByText('台積電')).not.toBeInTheDocument();
    expect(screen.queryByText('飆股')).not.toBeInTheDocument();
  });

  it('allows selecting multiple quick filters at the same time', async () => {
    renderApp();
    await waitFor(() => expect(screen.getByText('台積電')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'RSI > 80' }));
    fireEvent.click(screen.getByRole('button', { name: '量能異常' }));

    expect(screen.getByText('台泥')).toBeInTheDocument();
    expect(screen.getByText('飆股')).toBeInTheDocument();
    expect(screen.queryByText('台積電')).not.toBeInTheDocument();
    expect(screen.queryByText('長榮')).not.toBeInTheDocument();

    fireEvent.click(screen.getAllByRole('button', { name: '全部' }).find(button => button.getAttribute('aria-pressed') === 'false'));

    expect(screen.getByText('台積電')).toBeInTheDocument();
    expect(screen.getByText('長榮')).toBeInTheDocument();
  });

  it('does not show the full-page daily loading screen while fetching data', () => {
    global.fetch = vi.fn(() => new Promise(() => {}));

    renderApp();

    expect(screen.queryByText('載入每日掃描結果中...')).not.toBeInTheDocument();
    expect(screen.getByText('符合條件')).toBeInTheDocument();
  });

  it('hydrates from dashboard cache before the network refresh completes', async () => {
    localStorage.setItem('trendguard_dashboard_cache_v2', JSON.stringify({
      savedAt: Date.now(),
      value: {
        data: MOCK_DATA,
        marketRanks: MOCK_RANKS.ranks,
        article: { date: MOCK_DATA.date, title: '快取文章' },
        stockHistoryMap: {}
      }
    }));
    global.fetch = vi.fn(() => new Promise(() => {}));

    renderApp();

    expect(await screen.findByText('台泥')).toBeInTheDocument();
    expect(screen.queryByText('載入每日掃描結果中...')).not.toBeInTheDocument();
  });

  it('does not fetch the daily history index or per-day history files on entry', async () => {
    renderApp();

    await waitFor(() => expect(screen.getByText('台泥')).toBeInTheDocument());

    const fetchedUrls = global.fetch.mock.calls.map(([url]) => String(url));
    expect(fetchedUrls.some(url => url.includes('articles_index.json'))).toBe(false);
    expect(fetchedUrls.some(url => url.includes('/history/'))).toBe(false);
  });

  it('filters by Red K days (>= 3)', async () => {
    renderApp();
    await waitFor(() => expect(screen.getByText('台泥')).toBeInTheDocument());

    // Find the button for "3+"
    // The buttons contain text "3" and a span with "+".
    // We can find it by looking for the button that contains "3"
    const buttons = screen.getAllByRole('button');
    const button3 = buttons.find(btn => btn.textContent.includes('3') && btn.textContent.includes('檔'));

    if (!button3) throw new Error('Button 3+ not found');
    fireEvent.click(button3);

    // Verify results
    // 台泥 (2 days) should disappear
    expect(screen.queryByText('台泥')).not.toBeInTheDocument();
    
    // Others (>= 3 days) should stay
    expect(screen.getByText('台積電')).toBeInTheDocument(); // 3 days
    expect(screen.getByText('長榮')).toBeInTheDocument();   // 3 days
    expect(screen.getByText('飆股')).toBeInTheDocument();   // 5 days
  });

  it('toggles Exact Match mode (== 3)', async () => {
    renderApp();
    await waitFor(() => expect(screen.getByText('飆股')).toBeInTheDocument());

    // 1. Select 3 days first
    const buttons = screen.getAllByRole('button');
    const button3 = buttons.find(btn => btn.textContent.includes('3') && btn.textContent.includes('檔'));
    fireEvent.click(button3);

    // 2. Click "剛好 (==)" toggle
    const exactModeBtn = screen.getByText((content) => content.includes('剛好'));
    fireEvent.click(exactModeBtn);

    // 3. Verify results
    // 台泥 (2) -> Gone
    // 飆股 (5) -> Gone (because now it's exactly 3)
    // 台積電 (3) -> Keep
    // 長榮 (3) -> Keep
    expect(screen.queryByText('台泥')).not.toBeInTheDocument();
    expect(screen.queryByText('飆股')).not.toBeInTheDocument();
    expect(screen.getByText('台積電')).toBeInTheDocument();
    expect(screen.getByText('長榮')).toBeInTheDocument();
  });

  it('filters by Strong Stock percentage (> 5%)', async () => {
    renderApp();
    await waitFor(() => expect(screen.getByText('長榮')).toBeInTheDocument());

    // Find the input for percentage
    const input = screen.getByPlaceholderText('0');
    
    // Type '5'
    fireEvent.change(input, { target: { value: '5' } });

    // Verify results
    // 台泥 (1.5%) -> Gone
    // 長榮 (2.0%) -> Gone
    // 台積電 (6.5%) -> Keep
    // 飆股 (9.9%) -> Keep
    expect(screen.queryByText('台泥')).not.toBeInTheDocument();
    expect(screen.queryByText('長榮')).not.toBeInTheDocument();
    expect(screen.getByText('台積電')).toBeInTheDocument();
    expect(screen.getByText('飆股')).toBeInTheDocument();
  });

  it('combines Red K (>=3) and Strong Filter (>5%)', async () => {
    renderApp();
    await waitFor(() => expect(screen.getByText('長榮')).toBeInTheDocument());

    // 1. Set Red K >= 3
    const buttons = screen.getAllByRole('button');
    const button3 = buttons.find(btn => btn.textContent.includes('3') && btn.textContent.includes('檔'));
    fireEvent.click(button3);

    // 2. Set Strong Filter > 5
    const input = screen.getByPlaceholderText('0');
    fireEvent.change(input, { target: { value: '5' } });

    // Verify results
    // 台泥 (2 days, 1.5%) -> Gone (both fail)
    // 長榮 (3 days, 2.0%) -> Gone (fails pct)
    // 台積電 (3 days, 6.5%) -> Keep (pass both)
    // 飆股 (5 days, 9.9%) -> Keep (pass both)
    
    expect(screen.queryByText('台泥')).not.toBeInTheDocument();
    expect(screen.queryByText('長榮')).not.toBeInTheDocument();
    expect(screen.getByText('台積電')).toBeInTheDocument();
    expect(screen.getByText('飆股')).toBeInTheDocument();
  });

  it('restores list when clearing input', async () => {
    renderApp();
    await waitFor(() => expect(screen.getByText('長榮')).toBeInTheDocument());

    // 1. Filter to remove something
    const input = screen.getByPlaceholderText('0');
    fireEvent.change(input, { target: { value: '5' } });
    expect(screen.queryByText('長榮')).not.toBeInTheDocument();

    // 2. Clear input (set to empty string, simulates deleting)
    fireEvent.change(input, { target: { value: '' } });

    // 3. Verify logic handles empty string -> 0 -> restore list
    expect(screen.getByText('長榮')).toBeInTheDocument();
  });
  
  it('updates stats count dynamically when filtering', async () => {
    renderApp();
    await waitFor(() => expect(screen.getByText('符合條件')).toBeInTheDocument());
    
    // Default (>=2): 2(1), 3(2), 5(1) -> Total 4 stocks.
    // Button "3+" should represent: 3(2) + 5(1) = 3 stocks (B, C, D)
    
    const buttons = screen.getAllByRole('button');
    const button3 = buttons.find(btn => btn.textContent.includes('3') && btn.textContent.includes('檔'));
    
    // Check initial count inside the button text (e.g. "3+ 3 檔")
    // Note: depends on exact rendering structure, usually checking textContent is safest
    expect(button3).toHaveTextContent('3 檔');
    
    // Now apply Strong Filter > 5%
    // Stock B (6.5%) -> Keep
    // Stock C (2.0%) -> Remove
    // Stock D (9.9%) -> Keep
    // New count for "3+" should be 2
    
    const input = screen.getByPlaceholderText('0');
    fireEvent.change(input, { target: { value: '5' } });
    
    // Re-check the button count
    expect(button3).toHaveTextContent('2 檔');
  });
});
