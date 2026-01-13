import React from 'react';

interface MobileCardProps {
  title: string;
  children: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const MobileCard: React.FC<MobileCardProps> = ({
  title,
  children,
  action,
  className = '',
}) => {
  return (
    <div className={`bg-white border border-gray-200 rounded-xl ${className}`}>
      {/* Header - Touch friendly */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {action}
      </div>
      
      {/* Content - Extra padding on mobile */}
      <div className="p-4 sm:p-6">
        {children}
      </div>
    </div>
  );
};


