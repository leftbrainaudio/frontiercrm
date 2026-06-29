import { create } from 'zustand';
import type { User, AuthTokens } from '../types';
import apiClient from '../api/client';

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: {
    email: string;
    username: string;
    password: string;
    first_name: string;
    last_name: string;
    organization_name?: string;
  }) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
  setUser: (user: User) => void;
  init: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email, password) => {
    const { data } = await apiClient.post<AuthTokens>('/auth/login/', { email, password });
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    set({ tokens: data, isAuthenticated: true });
    await get().fetchMe();
  },

  signup: async (payload) => {
    const { data } = await apiClient.post<AuthTokens>('/auth/signup/', payload);
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    set({ tokens: data, isAuthenticated: true });
    await get().fetchMe();
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, tokens: null, isAuthenticated: false });
    window.location.href = '/login';
  },

  fetchMe: async () => {
    try {
      const { data } = await apiClient.get<User>('/accounts/me/');
      set({ user: data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  setUser: (user) => set({ user }),

  init: () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      set({ isAuthenticated: true, isLoading: true });
      get().fetchMe();
    } else {
      set({ isLoading: false });
    }
  },
}));