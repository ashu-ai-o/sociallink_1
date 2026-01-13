import React, { useState, useRef } from 'react';
import { Trash2, Edit } from 'lucide-react';

interface SwipeableCardProps {
  onDelete?: () => void;
  onEdit?: () => void;
  children: React.ReactNode;
}

export const SwipeableCard: React.FC<SwipeableCardProps> = ({
  onDelete,
  onEdit,
  children,
}) => {
  const [translateX, setTranslateX] = useState(0);
  const [isSwiping, setIsSwiping] = useState(false);
  const startX = useRef(0);
  
  const handleTouchStart = (e: React.TouchEvent) => {
    startX.current = e.touches[0].clientX;
    setIsSwiping(true);
  };
  
  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isSwiping) return;
    const currentX = e.touches[0].clientX;
    const diff = currentX - startX.current;
    
    // Only allow left swipe (negative values)
    if (diff < 0) {
      setTranslateX(Math.max(diff, -150)); // Max swipe distance
    }
  };
  
  const handleTouchEnd = () => {
    setIsSwiping(false);
    
    // If swiped more than 50px, snap to actions
    if (translateX < -50) {
      setTranslateX(-150);
    } else {
      setTranslateX(0);
    }
  };
  
  return (
    <div className="relative overflow-hidden">
      {/* Action buttons (revealed on swipe) */}
      <div className="absolute right-0 top-0 bottom-0 flex">
        {onEdit && (
          <button
            onClick={onEdit}
            className="w-20 bg-blue-500 text-white flex items-center justify-center touch-manipulation"
          >
            <Edit className="w-5 h-5" />
          </button>
        )}
        {onDelete && (
          <button
            onClick={onDelete}
            className="w-20 bg-red-500 text-white flex items-center justify-center touch-manipulation"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        )}
      </div>
      
      {/* Card content */}
      <div
        className="relative bg-white transition-transform duration-200"
        style={{ transform: `translateX(${translateX}px)` }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {children}
      </div>
    </div>
  );
};

