import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { api } from '../../utils/api';

interface Automation {
  id: string;
  name: string;
  trigger_type: string;
  trigger_keywords: string[];
  dm_message: string;
  is_active: boolean;
  total_triggers: number;
  total_dms_sent: number;
  total_comment_replies: number;
  enable_comment_reply: boolean;
  comment_reply_message: string;
  use_ai_enhancement: boolean;
}

interface AutomationsState {
  items: Automation[];
  currentAutomation: Automation | null;
  loading: boolean;
  error: string | null;
  filters: {
    status: 'all' | 'active' | 'inactive';
    search: string;
  };
}

const initialState: AutomationsState = {
  items: [],
  currentAutomation: null,
  loading: false,
  error: null,
  filters: {
    status: 'all',
    search: '',
  },
};

// Async Thunks
export const fetchAutomations = createAsyncThunk(
  'automations/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.getAutomations();
      return response.results || response;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const createAutomation = createAsyncThunk(
  'automations/create',
  async (data: any, { rejectWithValue }) => {
    try {
      const response = await api.createAutomation(data);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateAutomation = createAsyncThunk(
  'automations/update',
  async ({ id, data }: { id: string; data: any }, { rejectWithValue }) => {
    try {
      const response = await api.updateAutomation(id, data);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const deleteAutomation = createAsyncThunk(
  'automations/delete',
  async (id: string, { rejectWithValue }) => {
    try {
      await api.deleteAutomation(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const toggleAutomation = createAsyncThunk(
  'automations/toggle',
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await api.toggleAutomation(id);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

const automationsSlice = createSlice({
  name: 'automations',
  initialState,
  reducers: {
    setFilter: (
      state,
      action: PayloadAction<{ key: keyof AutomationsState['filters']; value: any }>
    ) => {
      state.filters[action.payload.key] = action.payload.value;
    },
    clearFilters: (state) => {
      state.filters = initialState.filters;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch
      .addCase(fetchAutomations.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAutomations.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchAutomations.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Create
      .addCase(createAutomation.fulfilled, (state, action) => {
        state.items.unshift(action.payload);
      })
      // Update
      .addCase(updateAutomation.fulfilled, (state, action) => {
        const index = state.items.findIndex((a) => a.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      // Delete
      .addCase(deleteAutomation.fulfilled, (state, action) => {
        state.items = state.items.filter((a) => a.id !== action.payload);
      })
      // Toggle
      .addCase(toggleAutomation.fulfilled, (state, action) => {
        const index = state.items.findIndex((a) => a.id === action.payload.id);
        if (index !== -1) {
          state.items[index].is_active = action.payload.is_active;
        }
      });
  },
});

export const { setFilter, clearFilters } = automationsSlice.actions;
export default automationsSlice.reducer;

