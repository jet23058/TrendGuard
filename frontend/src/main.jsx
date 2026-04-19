import { StrictMode, Suspense, lazy } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'

const App = lazy(() => import('./App.jsx'))
const DailyReport = lazy(() => import('./pages/DailyReport.jsx'))
const ArticleList = lazy(() => import('./pages/ArticleList.jsx'))
const KnowledgeHub = lazy(() => import('./pages/KnowledgeHub.jsx'))
const PrivacyPolicy = lazy(() => import('./pages/PrivacyPolicy.jsx'))
const TermsOfService = lazy(() => import('./pages/TermsOfService.jsx'))

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
      <Suspense fallback={null}>
        <Routes>
          <Route path="/" element={<ArticleList />} />
          <Route path="/dashboard" element={<App />} />
          <Route path="/report/:date" element={<DailyReport />} />
          <Route path="/knowledge" element={<KnowledgeHub />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/terms" element={<TermsOfService />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  </StrictMode>,
)
