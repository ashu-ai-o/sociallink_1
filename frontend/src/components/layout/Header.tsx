// src/components/Layout/Header.tsx
import { Menu } from 'lucide-react';
import { useAppDispatch } from '../../hooks';
import { toggleSidebar } from '../../store/slices/uiSlice';

export const Header = () => {
  const dispatch = useAppDispatch();

  return (
    <header className="h-16 border-b border-[var(--border-primary)] bg-[var(--bg-primary)] flex items-center px-6">
      <button
        onClick={() => dispatch(toggleSidebar())}
        className="md:hidden p-2 rounded-lg hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]"
      >
        <Menu className="w-5 h-5" />
      </button>
    </header>
  );
};

