import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import App from './App';
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
      consecutiveRed: 2, changePct: 1.5, currentPrice: 30 
    },
    { 
      ticker: "2330", name: "台積電", sector: "半導體業", 
      consecutiveRed: 3, changePct: 6.5, currentPrice: 600 
    },
    { 
      ticker: "2603", name: "長榮", sector: "航運業", 
      consecutiveRed: 3, changePct: 2.0, currentPrice: 150 
    },
    { 
      ticker: "9999", name: "飆股", sector: "其他", 
      consecutiveRed: 5, changePct: 9.9, currentPrice: 100 
    }
  ],
  changes: { new: [], continued: [], removed: [] }
};

describe('App Filter Logic Tests', () => {
  // Setup fetch mock
  beforeEach(() => {
    global.fetch = vi.fn((url) => {
      if (url && url.includes('daily_scan_results.json')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(MOCK_DATA),
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
    expect(screen.getByText('台泥')).toBeInTheDocument();
    expect(screen.getByText('台積電')).toBeInTheDocument();
    expect(screen.getByText('長榮')).toBeInTheDocument();
    expect(screen.getByText('飆股')).toBeInTheDocument();
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
