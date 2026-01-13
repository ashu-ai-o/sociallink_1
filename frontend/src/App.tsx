import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { MobileNav } from './components/MobileNav';
import { OfflineNotice } from './components/OfflineNotice';
import { Routes } from 'react-router-dom';



function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <OfflineNotice />
      <MobileNav />
            {/* Add padding for mobile nav */}
      <div className="lg:pb-0 pb-20 pt-[57px] lg:pt-0">
        <Routes>
         
        </Routes>
      </div>
    </div>
  );
}
export default App
