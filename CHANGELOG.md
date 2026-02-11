# Changelog

All notable changes to this project will be documented in this file.

## [2026-02-11] - Performance Optimization

### Changed
- [Perf] **Optimized TWSE Provider**: Reduced historical data lookback from 180 days to 30 days when using TWSE provider, decreasing API requests by 71.4% (567 → 162 requests for 81 stocks)
- [Perf] **Rate Limiting**: Added 0.1 second delay between TWSE API requests to avoid rate limiting
- [Feat] **Smart Data Range**: Dynamically adjust historical data range based on provider type (30 days for TWSE, 180 days for FinMind)

### Technical Details
- TWSE API requires monthly requests (2 months instead of 7)
- Estimated scan time reduced from ~5 minutes to ~1.4 minutes
- 30 days of data is sufficient for technical analysis (MA20, KD, breakout detection)

## [2026-02-11]

### Added
- [Feat] **Stock Data Facade Pattern**: Implemented Facade Design Pattern to abstract stock data sources, allowing flexible switching between TWSE API and FinMind API (`stock_data_facade.py`)
- [Feat] **TWSE API Provider**: Added native TWSE (Taiwan Stock Exchange) API support as alternative data source with no rate limits (`stock_data_facade.py:TWSEProvider`)
- [Feat] **Provider Adapter Layer**: Created adapter module to seamlessly integrate facade with existing FinMind-based code (`stock_facade_adapter.py`)
- [Test] **Comprehensive Test Suite**: Added 10 unit tests covering facade initialization, provider switching, data fetching, and error handling (`tests/test_stock_data_facade.py`)

### Changed
- [Refactor] **Environment Configuration**: Added `STOCK_DATA_PROVIDER` environment variable to select data source (default: 'twse') (`.env.example`)
- [Refactor] **Backward Compatibility**: Updated `api/stock.py` and `scripts/update_daily.py` to use facade while maintaining backward compatibility with existing code
- [Security] **No Hardcoded Secrets**: All API tokens are loaded from environment variables following security best practices

### Fixed
- [Fix] **Import Path**: Fixed ModuleNotFoundError in GitHub Actions by adding parent directory to sys.path in `scripts/update_daily.py`

### Technical Details
- Provider Pattern: Abstract base class `StockDataProvider` with concrete implementations for TWSE and FinMind
- Default Provider: TWSE (no API limits, suitable for production)
- Fallback Provider: FinMind (feature-rich, requires token for higher limits)
- Data Format: Unified output format across both providers for consistency

## [2026-02-06]

### Added
- [Feat] **Market Rank Filter**: Added a frontend filter to view Top 100/500/1000 market cap stocks (`frontend/src/App.jsx`).
- [Feat] **Market Cap Data Source**: Added scheduled crawler for TAIFEX market cap ranking (`scripts/fetch_market_cap_rank.py`, `.github/workflows/update-market-rank.yml`).
- [Feat] **Parallel Scanning**: Implemented multi-threaded scanning in daily update script for 10x speedup (`scripts/update_daily.py`).
- [Feat] **Anonymous Optimization**: Daily script now intelligently prioritizes top market cap stocks when running without a FinMind token to maximize utility within rate limits.

### Fixed
- [Fix] **Vercel Deployment**: Resolved 250MB size limit by rewriting `api/stock.py` to use lightweight `requests` instead of heavy data libraries.
- [Fix] **CI/CD Pipeline**: Enabled tests on Pull Requests and fixed circular dependencies causing import errors.

### Changed
- [Refactor] **Data Source Migration**: Fully migrated from `yfinance` to `FinMind` for better data reliability.
- [Refactor] **Market Rank Architecture**: Moved ranking logic to frontend to decouple data fetching from presentation.

## [2026-02-02]

### Fixed
- [Fix] **Missing Dependency**: Added `tqdm` to GitHub Actions dependencies. FinMind requires tqdm but it wasn't explicitly installed, causing test failures (`.github/workflows/daily-update.yml`).
- [Fix] **Switch Data Source from yfinance to FinMind**: Replaced yfinance with FinMind API for Taiwan stock data. yfinance was missing data for certain trading days (e.g., 1/30), causing incomplete OHLC data in scan results. FinMind provides more reliable and complete Taiwan stock data (`scripts/update_daily.py`, `.github/workflows/daily-update.yml`).
- [Refactor] **Backend API Migration**: Updated `backend/server.py` to use FinMind instead of yfinance for the `/api/stock` endpoint, ensuring consistent data source for manual portfolio synchronization and chart viewing. Also simplified suffix handling logic.
- [Fix] **Cache-busting for Data Fetching**: Added cache-busting parameter (`?v=timestamp`) to frontend fetch requests for `daily_scan_results.json`, `articles_index.json`, and article files. This resolves the issue where GitHub Raw CDN caching caused stale data to be displayed, making users see outdated scan results even though the backend updates were running correctly (`frontend/src/App.jsx`).
- [Fix] **Delayed Schedule for Data Availability**: Changed GitHub Actions cron schedule from 15:30 to 17:00 Taiwan time (UTC 07:30 → 09:00). This ensures FinMind has enough time to update with the latest closing prices (`.github/workflows/daily-update.yml`).

## [2026-01-24]

### Added
- [Feat] **Day Trade Restriction Check**: Backend now fetches the official day trading allowlist from TWSE/TPEX APIs. Stocks not on the list or under disposition are marked with a red "🚫 禁當沖" label in the dashboard (`scripts/update_daily.py`, `frontend/src/components/StockCardMini.jsx`).
- [Docs] **Project Plan**: Added `PROJECT_PLAN.md` detailing system architecture, current features, and roadmap.

### Fixed
- [Fix] **CI/CD Data Continuity**: Fixed issue where "Continued" and "Removed" lists were empty by ensuring the workflow fetches the previous day's data from the `data` branch before scanning (`.github/workflows/daily-update.yml`).

### Performance
- [Perf] **Lazy Chart Rendering**: Implemented `IntersectionObserver` in `StockCardMini` to only render Recharts components when they enter the viewport, significantly improving scroll performance (`frontend/src/components/StockCardMini.jsx`).

### Changed
- [Assets] **Favicon Update**: Updated website favicon and added `apple-touch-icon` for better mobile experience (`frontend/public/`).

## [2026-01-22]

### Added
- [Feat] **Strong Stock Filter**: Added a numeric input field to filter stocks by daily gain percentage (e.g. > 5%) in the dashboard (`frontend/src/App.jsx`).
- [Feat] **Exact Red-K Mode**: Added toggle switch to filter stocks by exact consecutive red days (== N) vs minimum (>= N) (`frontend/src/App.jsx`).
- [Feat] **Market Breadth Stats**: Backend now calculates total market rising/falling/flat counts during scanning and injects this data into AI-generated articles for broader market context (`scripts/update_daily.py`, `scripts/article_generator.py`).

### Fixed
- [Fix] **Filter Logic Bug**: Fixed React `useMemo` dependency issue where filtering by percentage didn't trigger a re-render (`frontend/src/App.jsx`).
- [Test] **Filter Logic Tests**: Added comprehensive integration tests for all filtering scenarios using Vitest and React Testing Library (`frontend/src/App.test.jsx`).

## [2026-01-21]

### Added
- [Feat] **AI-Generated Daily Market Article**: Integrated Google Gemini 2.0 Flash to automatically generate comprehensive daily market analysis articles after scanning completes.
- [Feat] **Article Page with History Navigation**: New dedicated page to view AI-generated articles with date picker for browsing historical articles.
- [Feat] **Stock History Tracking**: Added stock history indicators showing consecutive days a stock appeared in the scan results.

### Changed
- [Refactor] **Data Branch Restructure**: Changed from nested folder structure to flat file structure in the `data` branch for better compatibility with raw.githubusercontent.com URLs.
