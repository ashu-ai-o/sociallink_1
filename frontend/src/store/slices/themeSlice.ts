import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

type ThemeMode = 'light' | 'dark';

interface ThemeState {
  mode: ThemeMode;
  systemPreference: ThemeMode;
}

const getSystemTheme = (): ThemeMode => {
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
};

const getSavedTheme = (): ThemeMode => {
  const saved = localStorage.getItem('theme') as ThemeMode;
  return saved || getSystemTheme();
};

const initialState: ThemeState = {
  mode: getSavedTheme(),
  systemPreference: getSystemTheme(),
};

const themeSlice = createSlice({
  name: 'theme',
  initialState,
  reducers: {
    toggleTheme: (state) => {
      state.mode = state.mode === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme', state.mode);
      document.documentElement.classList.toggle('dark', state.mode === 'dark');
    },
    setTheme: (state, action: PayloadAction<ThemeMode>) => {
      state.mode = action.payload;
      localStorage.setItem('theme', state.mode);
      document.documentElement.classList.toggle('dark', state.mode === 'dark');
    },
    setSystemPreference: (state, action: PayloadAction<ThemeMode>) => {
      state.systemPreference = action.payload;
    },
  },
});

export const { toggleTheme, setTheme, setSystemPreference } = themeSlice.actions;
export default themeSlice.reducer;
