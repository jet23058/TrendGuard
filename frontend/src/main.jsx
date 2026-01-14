import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import DailyReport from './pages/DailyReport.jsx'
import ArticleList from './pages/ArticleList.jsx'

// AdSense Injection
const adSenseId = import.meta.env.VITE_ADSENSE_ID;
if (adSenseId) {
  // Script
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${adSenseId}`;
  script.crossOrigin = "anonymous";
  document.head.appendChild(script);

  // Meta
  const meta = document.createElement('meta');
  meta.name = "google-adsense-account";
  meta.content = adSenseId;
  document.head.appendChild(meta);
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ArticleList />} />
        <Route path="/dashboard" element={<App />} />
        <Route path="/report/:date" element={<DailyReport />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
