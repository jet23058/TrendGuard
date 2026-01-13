import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import IndustryGroup from './IndustryGroup';

// Mock StockCardMini to capture props
const mockStockCardMini = vi.fn();
vi.mock('./StockCardMini', () => ({
    default: (props) => {
        mockStockCardMini(props);
        return <div data-testid="stock-card">{props.stock.ticker}</div>;
    }
}));

// Mock lucide-react
vi.mock('lucide-react', () => ({
    Factory: () => <span>Factory</span>,
}));

describe('IndustryGroup Component', () => {
    const sampleStocks = [
        { ticker: '2330', name: 'TSMC', currentPrice: 600 },
        { ticker: '2317', name: 'Foxconn', currentPrice: 150 },
    ];

    const sampleHistoryMap = {
        '2330': ['2025-01-01', '2025-01-02'],
        '2317': ['2025-01-03'],
    };

    beforeEach(() => {
        mockStockCardMini.mockClear();
    });

    it('renders without crashing when stockHistoryMap is provided', () => {
        render(
            <IndustryGroup
                sector="電子"
                stocks={sampleStocks}
                portfolioTickers={[]}
                portfolio={[]}
                stockHistoryMap={sampleHistoryMap}
            />
        );

        expect(screen.getByText('電子')).toBeInTheDocument();
        expect(screen.getAllByTestId('stock-card')).toHaveLength(2);
    });

    it('renders without crashing when stockHistoryMap is NOT provided (default empty object)', () => {
        render(
            <IndustryGroup
                sector="電子"
                stocks={sampleStocks}
                portfolioTickers={[]}
                portfolio={[]}
            />
        );

        expect(screen.getByText('電子')).toBeInTheDocument();
        expect(screen.getAllByTestId('stock-card')).toHaveLength(2);
    });

    it('passes historyDates correctly to StockCardMini', () => {
        render(
            <IndustryGroup
                sector="電子"
                stocks={sampleStocks}
                portfolioTickers={[]}
                portfolio={[]}
                stockHistoryMap={sampleHistoryMap}
            />
        );

        // Verify StockCardMini was called with correct historyDates
        const tsmcCall = mockStockCardMini.mock.calls.find(
            call => call[0].stock.ticker === '2330'
        );
        expect(tsmcCall[0].historyDates).toEqual(['2025-01-01', '2025-01-02']);

        const foxconnCall = mockStockCardMini.mock.calls.find(
            call => call[0].stock.ticker === '2317'
        );
        expect(foxconnCall[0].historyDates).toEqual(['2025-01-03']);
    });

    it('passes empty array for stocks not in historyMap', () => {
        render(
            <IndustryGroup
                sector="電子"
                stocks={[{ ticker: '9999', name: 'Unknown', currentPrice: 100 }]}
                portfolioTickers={[]}
                portfolio={[]}
                stockHistoryMap={sampleHistoryMap}
            />
        );

        const unknownCall = mockStockCardMini.mock.calls.find(
            call => call[0].stock.ticker === '9999'
        );
        expect(unknownCall[0].historyDates).toEqual([]);
    });
});
