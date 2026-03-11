import React from 'react';

export const AnimatedBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none w-full h-full bg-transparent flex justify-center items-center">
      {/* Top Left Blob */}
      <div className="absolute top-[-10%] left-[-10%] w-[400px] h-[400px] sm:w-[500px] sm:h-[500px] bg-indigo-500/20 rounded-full mix-blend-multiply dark:mix-blend-overlay filter blur-[100px] opacity-70 animate-blob" />
      
      {/* Top Right Blob */}
      <div className="absolute top-[10%] right-[-10%] w-[350px] h-[350px] sm:w-[450px] sm:h-[450px] bg-purple-500/20 rounded-full mix-blend-multiply dark:mix-blend-overlay filter blur-[100px] opacity-60 animate-blob" style={{ animationDelay: '2s' }} />
      
      {/* Bottom Center Blob */}
      <div className="absolute bottom-[-10%] left-[20%] w-[400px] h-[400px] sm:w-[600px] sm:h-[600px] bg-pink-500/20 rounded-full mix-blend-multiply dark:mix-blend-overlay filter blur-[100px] opacity-70 animate-blob" style={{ animationDelay: '4s' }} />
    </div>
  );
};
