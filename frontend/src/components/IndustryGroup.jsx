import React, { useMemo } from 'react';
import { Factory } from 'lucide-react';
import StockCardMini from './StockCardMini';

// --- 5. 產業群組 ---
const IndustryGroup = ({ sector, stocks, portfolioTickers = [], portfolio = [], stockHistoryMap = {} }) => {
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
        <div className="mb-8 pl-2">
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
            </div>
            <div className="flex overflow-x-auto overflow-y-hidden pb-4 gap-4 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                {sortedStocks.map(stock => {
                    // 找出該股票的庫存資訊
                    const item = portfolio.find(p => p.ticker === stock.ticker);
                    const isInPortfolio = !!item;

                    return (
                        <StockCardMini
                            key={stock.ticker}
                            stock={stock}
                            isInPortfolio={isInPortfolio}
                            portfolioItem={item}
                            historyDates={stockHistoryMap[stock.ticker] || []}
                        />
                    );
                })}
            </div>
        </div>
    );
};

export default IndustryGroup;
