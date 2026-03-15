import React from 'react';

export const AnimatedBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none w-full h-full bg-transparent flex justify-center items-center">
      {/* Top Left Blob */}
      <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-indigo-500/40 dark:bg-indigo-500/20 rounded-full dark:mix-blend-overlay filter blur-[100px] opacity-90 dark:opacity-70 animate-blob scale-150" />
      
      {/* Top Right Blob */}
      <div className="absolute top-[10%] right-[-10%] w-[500px] h-[500px] bg-purple-500/40 dark:bg-purple-500/20 rounded-full dark:mix-blend-overlay filter blur-[100px] opacity-80 dark:opacity-60 animate-blob scale-125" style={{ animationDelay: '2s' }} />
      
      {/* Middle Right Blob */}
      <div className="absolute top-[40%] right-[10%] w-[400px] h-[400px] bg-blue-500/30 dark:bg-blue-500/10 rounded-full dark:mix-blend-overlay filter blur-[80px] opacity-70 dark:opacity-50 animate-blob" style={{ animationDelay: '3s' }} />

      {/* Bottom Left Blob */}
      <div className="absolute bottom-[-10%] left-[10%] w-[700px] h-[700px] bg-pink-500/40 dark:bg-pink-500/20 rounded-full dark:mix-blend-overlay filter blur-[120px] opacity-90 dark:opacity-70 animate-blob scale-150" style={{ animationDelay: '4s' }} />
    </div>
  );
};
