# Changelog

All notable changes to this project will be documented in this file.

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
