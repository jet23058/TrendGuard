# Changelog

All notable changes to this project will be documented in this file.

## [2026-01-04]

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
- [Feat] OCR Image upload for auto-filling portfolio from screenshots (frontend/src/App.jsx)
- [Feat] Firebase integration: Google Sign-in and Firestore Cloud Sync (frontend/src/App.jsx)
- [Feat] Manual sync button with save status indicator (frontend/src/App.jsx)
- [Security] Moved Firebase credentials to .env file (frontend/src/firebase.js, frontend/.env)
- [Fix] Resolved duplicated component definition and runtime error in App.jsx (frontend/src/App.jsx)
- [Feat] Enhanced portfolio visibility: Show holdings count in industry headers and details in stock cards (frontend/src/App.jsx)

### Legacy (Streamlit - deprecated)
- [Feat] Initial project setup with Streamlit framework (app.py)
- [Feat] Stock data fetcher module using yfinance (src/data_fetcher.py)
- [Feat] Watchlist manager for daily stock list tracking (src/watchlist_manager.py)
- [Feat] Technical analysis module with KD indicator calculation (src/technical_analysis.py)
- [Feat] Strategy advisor implementing Livermore trading rules (src/strategy_advisor.py)
