import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import App from './App';
import { onAuthStateChanged } from 'firebase/auth';

// Mock Firebase relative import
vi.mock('./firebase', () => ({
    auth: {},
    db: {},
    googleProvider: {},
}));

// Mock Firebase SDK
vi.mock('firebase/auth', () => ({
    signInWithPopup: vi.fn(),
    signOut: vi.fn(),
    onAuthStateChanged: vi.fn(),
    getAuth: vi.fn(),
}));

vi.mock('firebase/firestore', () => ({
    doc: vi.fn(),
    getDoc: vi.fn(() => Promise.resolve({
        exists: () => false,
        data: () => ({ portfolio: [] })
    })),
    setDoc: vi.fn(),
    collection: vi.fn(),
    onSnapshot: vi.fn(() => vi.fn()),
}));

// Mock child components
vi.mock('./components/Header', () => ({
    default: ({ user, onLogin }) => (
        <div data-testid="header">
            {user ? 'Logged In' : <button onClick={onLogin}>Login</button>}
        </div>
    ),
}));

vi.mock('./components/StockCardMini', () => ({ default: () => <div>StockCardMock</div> }));
vi.mock('./components/SimpleMarkdown', () => ({ default: () => <div>MarkdownMock</div> }));
vi.mock('./components/IndustryGroup', () => ({ default: () => <div>IndustryGroupMock</div> }));

vi.mock('lucide-react', () => ({
    Briefcase: () => <span>Briefcase</span>,
    PlusCircle: () => <span>PlusCircle</span>,
    Activity: () => <span>Activity</span>,
    Factory: () => <span>Factory</span>,
    Zap: () => <span>Zap</span>,
    AlertCircle: () => <span>AlertCircle</span>,
    Sparkles: () => <span>Sparkles</span>,
    TrendingUp: () => <span>TrendingUp</span>,
    MinusCircle: () => <span>MinusCircle</span>,
    RefreshCw: () => <span>RefreshCw</span>,
    Loader2: () => <span>Loader2</span>,
    AlertTriangle: () => <span>AlertTriangle</span>,
    FileText: () => <span>FileText</span>,
    Image: () => <span>Image</span>,
    Search: () => <span>Search</span>,
    Trash2: () => <span>Trash2</span>,
    Check: () => <span>Check</span>,
    X: () => <span>X</span>,
    Upload: () => <span>Upload</span>,
    ChevronRight: () => <span>ChevronRight</span>,
    TrendingDown: () => <span>TrendingDown</span>,
    BarChart2: () => <span>BarChart2</span>,
    PieChart: () => <span>PieChart</span>,
    LogOut: () => <span>LogOut</span>,
    User: () => <span>User</span>,
    Info: () => <span>Info</span>,
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

vi.mock('tesseract.js', () => ({}));

// Mock fetch
global.fetch = vi.fn((url) => {
    if (url && url.includes('tw_stocks.json')) {
        return Promise.resolve({
            ok: true,
            json: () => Promise.resolve([]),
        });
    }
    return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
            date: '2025-01-01',
            stocks: [],
            criteria: { description: 'Test Criteria' },
            changes: { new: [], continued: [], removed: [] }
        }),
    });
});

describe('App Component - Portfolio Import', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
    });

    it('does not load portfolio from localStorage for guest', async () => {
        const fakePortfolio = [{ ticker: '2330', name: 'TSMC', cost: 500, shares: 1000 }];
        localStorage.setItem('trendguard_portfolio', JSON.stringify(fakePortfolio));

        onAuthStateChanged.mockImplementation((auth, callback) => {
            callback(null);
            return vi.fn();
        });

        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>
        );

        await waitFor(() => expect(screen.getByText('符合條件')).toBeInTheDocument());

        const portfolioCountSection = screen.getByText('我的庫存').closest('div').parentElement;
        expect(portfolioCountSection).toHaveTextContent('0 檔');
    });

    it('guest cannot see import button', async () => {
        onAuthStateChanged.mockImplementation((auth, callback) => {
            callback(null);
            return vi.fn();
        });

        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>
        );
        await waitFor(() => expect(screen.getByText('符合條件')).toBeInTheDocument());

        // Guest should NOT see the import button
        expect(screen.queryByText('匯入')).not.toBeInTheDocument();
    });

    it('logged-in user can see import button and open modal', async () => {
        const mockUser = { uid: '123', displayName: 'Test User' };
        onAuthStateChanged.mockImplementation((auth, callback) => {
            callback(mockUser);
            return vi.fn();
        });

        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>
        );
        await waitFor(() => expect(screen.getByText('符合條件')).toBeInTheDocument());

        // User should see the import button
        const importButton = screen.getByText('匯入');
        expect(importButton).toBeInTheDocument();

        // Click should open the modal
        fireEvent.click(importButton);
        expect(screen.getByText(/匯入我的庫存/)).toBeInTheDocument();
    });
});
