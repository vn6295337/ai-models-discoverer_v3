import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  query: '',
  response: null,
  loading: false,
  error: null,
  llmUsed: null,
  category: null,
  responseTime: null,
  isOffline: false,
  offlineQueued: false,
  cachedResponse: false,
  messages: [], // Array of {id, type: 'user'|'assistant', text, llmUsed, category, responseTime, isCached, isQueued}
};

const querySlice = createSlice({
  name: 'query',
  initialState,
  reducers: {
    setQuery(state, action) {
      state.query = action.payload;
    },
    setLoading(state, action) {
      state.loading = action.payload;
    },
    setResponse(state, action) {
      state.response = action.payload.response;
      state.llmUsed = action.payload.llmUsed;
      state.category = action.payload.category;
      state.responseTime = action.payload.responseTime;
      state.error = null;
    },
    setError(state, action) {
      state.error = action.payload;
      state.response = null;
    },
    setOfflineStatus(state, action) {
      state.isOffline = action.payload;
    },
    setOfflineQueued(state, action) {
      state.offlineQueued = action.payload;
    },
    setCachedResponse(state, action) {
      state.cachedResponse = action.payload;
    },
    resetQuery(state) {
      state.query = '';
      state.response = null;
      state.error = null;
      state.llmUsed = null;
      state.category = null;
      state.responseTime = null;
      state.offlineQueued = false;
      state.cachedResponse = false;
    },
    addMessage(state, action) {
      state.messages.push(action.payload);
    },
    updateLastMessage(state, action) {
      if (state.messages.length > 0) {
        state.messages[state.messages.length - 1] = {
          ...state.messages[state.messages.length - 1],
          ...action.payload,
        };
      }
    },
    updateMessage(state, action) {
      const { id, updates } = action.payload;
      const messageIndex = state.messages.findIndex(msg => msg.id === id);
      if (messageIndex !== -1) {
        state.messages[messageIndex] = {
          ...state.messages[messageIndex],
          ...updates,
        };
      }
    },
    clearMessages(state) {
      state.messages = [];
    },
  },
});

export const {
  setQuery,
  setLoading,
  setResponse,
  setError,
  setOfflineStatus,
  setOfflineQueued,
  setCachedResponse,
  resetQuery,
  addMessage,
  updateLastMessage,
  updateMessage,
  clearMessages,
} = querySlice.actions;

export default querySlice.reducer;
