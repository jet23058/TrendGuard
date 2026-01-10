# Changelog

All notable changes to this project will be documented in this file.

## [2026-01-10]

### Added
- [Feat] **Daily Articles Waterfall View**: New `/articles` page with a masonry-style waterfall layout for browsing historical reports (`frontend/src/pages/ArticleList.jsx`).
- [Feat] **AI-Powered Market Analysis**: Integrated Google Gemini API to generate daily market commentary and summaries (`scripts/article_generator.py`).
- [Feat] **Automatic Article Indexing**: Backend now generates `articles_index.json` for fast frontend retrieval (`scripts/update_daily.py`).
- [Feat] **Rich Article Page**: New `/report/:date` page displaying markdown content alongside interactive stock cards (`frontend/src/pages/DailyReport.jsx`).
- [UI] **Shared Header Component**: Extracted navigation and auth controls to a reusable `Header` component with active state indication (`frontend/src/components/Header.jsx`).
- [UI] **Interactive Charts Restored**: Restored MA/KD toggle and detailed tooltips in `StockCardMini` component (`frontend/src/components/StockCardMini.jsx`).

### Changed
- [Refactor] **Navigation Architecture**: Implemented `react-router-dom` for multi-page navigation (Dashboard / Daily Articles).
- [Refactor] **Home Page Layout**: Removed the inline article banner from the dashboard to focus on stock data.
- [Refactor] **Component Extraction**: Refactored `App.jsx` by extracting `IndustryGroup`, `StockCardMini`, and `Header` into separate files.
- [Data] **Data Structure Separation**: Separated `history/` (snapshot data) and `articles/` (AI text content) in `public/data` for cleaner data management.



### Added
- [Feat] React frontend with Vite + TailwindCSS (frontend/)
- [Feat] Candlestick charts with KD indicator overlay using Recharts (frontend/src/App.jsx)
- [Feat] Portfolio import modal with stock search dropdown (frontend/src/App.jsx)
- [Feat] Mock data generation for Taiwan stocks with realistic prices (frontend/src/App.jsx)
- [Feat] Livermore AI advisor with strategy recommendations (frontend/src/App.jsx)
- [Feat] Change log section showing new entries (green) and exits (gray) (frontend/src/App.jsx)
- [Feat] Stock cards with real-time price display and P&L calculation (frontend/src/App.jsx)
- [Feat] Daily update script for GitHub Actions (scripts/update_daily.py)
- [Feat] GitHub Actions workflow with tests and verification (.github/workflows/daily-update.yml)
- [Test] Unit tests for update_daily.py covering KD calculation and recommendation logic (tests/test_update_daily.py)

### Changed
- [Refactor] Switched from Streamlit (Python) to React (JavaScript) frontend
- [Refactor] App.jsx now fetches real data from daily_recommendations.json instead of mock data (frontend/src/App.jsx)
- [Refactor] update_daily.py now uses Livermore breakout criteria: MA突破 + 連紅K + N日新高 (scripts/update_daily.py)
- [Feat] Added twstock for Chinese stock names (scripts/update_daily.py)
- [Feat] Industry grouping UI with horizontal scroll and count display (frontend/src/App.jsx)
- [Feat] Import portfolio modal with searchable dropdown by code/name, free input for shares/cost (frontend/src/App.jsx)
- [Refactor] Removed refresh button, added full datetime with timezone to scan time display (frontend/src/App.jsx)
- [Feat] Added disclaimer banner at top of page (frontend/src/App.jsx)
- [Feat] Portfolio-based sorting: industries and stocks with holdings appear first (frontend/src/App.jsx)
- [Feat] Unlisted portfolio stocks section for holdings not in recommendations (frontend/src/App.jsx)
- [Refactor] Updated HTML title to project name (frontend/index.html)
- [Feat] LocalStorage persistence for portfolio data (frontend/src/App.jsx)
- [Feat] On-demand Chart Sync for unlisted portfolio stocks via Vercel Serverless Function (frontend/src/App.jsx, api/stock.py)
- [Feat] Highlight held stocks with "持" tag in Daily Change Summary (frontend/src/App.jsx)
- [Feat] CSV/Text Paste Import for Portfolio: Support copying from Excel/CSV with auto-parsing (frontend/src/App.jsx)
- [Feat] Portfolio Overwrite Option: Added "Overwrite Existing Portfolio" checkbox in Import Modal for CSV imports (frontend/src/App.jsx)
- [UI] Share Count Formatting: Added comma separators (1,000) for share counts (frontend/src/App.jsx)
- [Fix] Stock Card Layout: Fixed bottom content cutoff issue by setting explicit card height (frontend/src/App.jsx)
- [UI] Daily Summary: Added portfolio hold counts to "New", "Continued", and "Removed" sections (frontend/src/App.jsx)
- [UI] Chart: Improved tooltip alignment with dashed cursor line (frontend/src/App.jsx)
- [UI] Unlisted Portfolio: Ticker symbols are now clickable links to Yahoo Finance (frontend/src/App.jsx)
- [Feat] Unified Workflow: Added `npm run dev:all` to start both frontend and backend concurrently (frontend/package.json)
- [Fix] API 403 Forbidden: Added User-Agent headers to request session in both local and production APIs (backend/server.py, api/stock.py)
- [Feat] Local Python Server: Added Flask backend for local API development without Vercel CLI (backend/server.py)
- [Refactor] Unlisted Portfolio: Implemented manual sync with Firestore persistence for on-demand stock data (frontend/src/App.jsx)
- [Feat] OCR Image upload for auto-filling portfolio from screenshots (frontend/src/App.jsx)
- [Feat] Firebase integration: Google Sign-in and Firestore Cloud Sync (frontend/src/App.jsx)
- [Feat] Manual sync button with save status indicator (frontend/src/App.jsx)
- [Security] Moved Firebase credentials to .env file (frontend/src/firebase.js, frontend/.env)
- [Fix] Resolved duplicated component definition and runtime error in App.jsx (frontend/src/App.jsx)
- [Feat] Enhanced portfolio visibility: Show holdings count in industry headers and details in stock cards (frontend/src/App.jsx)
- [Feat] Daily Change Summary: New, Continued, Removed stocks analysis (scripts/update_daily.py, frontend/src/App.jsx)
- [Test] Unit tests for daily diff logic (tests/test_daily_diff.py)

### Legacy (Streamlit - deprecated)
- [Feat] Initial project setup with Streamlit framework (app.py)
- [Feat] Stock data fetcher module using yfinance (src/data_fetcher.py)
- [Feat] Watchlist manager for daily stock list tracking (src/watchlist_manager.py)
- [Feat] Technical analysis module with KD indicator calculation (src/technical_analysis.py)
- [Feat] Strategy advisor implementing Livermore trading rules (src/strategy_advisor.py)
