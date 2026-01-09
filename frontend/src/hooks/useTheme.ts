import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from './';
import { toggleTheme as toggleThemeAction, setSystemPreference } from '../store/slices/themeSlice';

export const useTheme = () => {
  const dispatch = useAppDispatch();
  const theme = useAppSelector((state) => state.theme.mode);

  useEffect(() => {
    // Apply theme on mount
    document.documentElement.classList.toggle('dark', theme === 'dark');

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      dispatch(setSystemPreference(e.matches ? 'dark' : 'light'));
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme, dispatch]);

  const toggleTheme = () => {
    dispatch(toggleThemeAction());
  };

  return { theme, toggleTheme };
};