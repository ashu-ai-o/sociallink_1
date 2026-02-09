import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import './styles/global.css'


createRoot(document.getElementById('root')!).render(
  
  <StrictMode>
    <App />
  </StrictMode>,
)

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('✓ Service Worker registered:', registration);
      })
      .catch(error => {
        console.log('✗ Service Worker registration failed:', error);
      });
  });
}