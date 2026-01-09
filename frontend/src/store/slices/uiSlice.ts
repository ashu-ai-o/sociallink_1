import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  sidebar: {
    isOpen: boolean;
    isCollapsed: boolean;
  };
  settings: {
    isOpen: boolean;
    activeTab: string;
  };
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
  }>;
}

const initialState: UIState = {
  sidebar: {
    isOpen: false,
    isCollapsed: false,
  },
  settings: {
    isOpen: false,
    activeTab: 'general',
  },
  notifications: [],
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebar.isOpen = !state.sidebar.isOpen;
    },
    closeSidebar: (state) => {
      state.sidebar.isOpen = false;
    },
    openSettings: (state) => {
      state.settings.isOpen = true;
    },
    closeSettings: (state) => {
      state.settings.isOpen = false;
    },
    setSettingsTab: (state, action: PayloadAction<string>) => {
      state.settings.activeTab = action.payload;
    },
    addNotification: (
      state,
      action: PayloadAction<Omit<UIState['notifications'][0], 'id'>>
    ) => {
      state.notifications.push({
        ...action.payload,
        id: Date.now().toString(),
      });
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(
        (n) => n.id !== action.payload
      );
    },
  },
});

export const {
  toggleSidebar,
  closeSidebar,
  openSettings,
  closeSettings,
  setSettingsTab,
  addNotification,
  removeNotification,
} = uiSlice.actions;

export default uiSlice.reducer;


