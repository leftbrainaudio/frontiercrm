import { create } from 'zustand';
import type { User, AuthTokens, TwoFactorRequiredResponse } from '../types';
import apiClient from '../api/client';

interface MembershipInfo {
  id: string | null;
  role_id: string | null;
  role_name: string | null;
  is_admin: boolean;
  is_owner: boolean;
  permissions: Record<string, boolean>;
}

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  membership: MembershipInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  // ── 2FA state ──────────────────────────────────────────────────────
  twoFactorToken: string | null;
  isAwaiting2FA: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: {
    email: string;
    username: string;
    password: string;
    first_name: string;
    last_name: string;
    organization_name?: string;
  }) => Promise<void>;
  socialLogin: (provider: string, code: string, redirectUri?: string) => Promise<void>;
  verifyTwoFactor: (code: string, isRecovery?: boolean) => Promise<void>;
  cancelTwoFactor: () => void;
  logout: () => void;
  fetchMe: () => Promise<void>;
  fetchMembership: () => Promise<void>;
  setUser: (user: User) => void;
  init: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  tokens: null,
  membership: null,
  isAuthenticated: false,
  isLoading: true,
  twoFactorToken: null,
  isAwaiting2FA: false,

  login: async (email, password) => {
    const { data } = await apiClient.post<AuthTokens | TwoFactorRequiredResponse>('/auth/login/', { email, password });

    // Check if 2FA is required
    if ('2fa_required' in data && data['2fa_required']) {
      set({ twoFactorToken: data['2fa_token'], isAwaiting2FA: true, isLoading: false });
      return;
    }

    const tokens = data as AuthTokens;
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
    set({ tokens, isAuthenticated: true, isAwaiting2FA: false, twoFactorToken: null });
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
    set({
      user: null,
      tokens: null,
      isAuthenticated: false,
      twoFactorToken: null,
      isAwaiting2FA: false,
    });
    window.location.href = '/login';
  },

  socialLogin: async (provider, code, redirectUri) => {
    const { data } = await apiClient.post<AuthTokens | TwoFactorRequiredResponse>('/auth/social/', {
      provider,
      code,
      redirect_uri: redirectUri,
    });

    // Check if 2FA is required
    if ('2fa_required' in data && data['2fa_required']) {
      set({ twoFactorToken: data['2fa_token'], isAwaiting2FA: true, isLoading: false });
      return;
    }

    const tokens = data as AuthTokens;
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
    set({ tokens, isAuthenticated: true });
    await get().fetchMe();
  },

  verifyTwoFactor: async (code, isRecovery = false) => {
    const { twoFactorToken } = get();
    if (!twoFactorToken) {
      throw new Error('No 2FA token available');
    }

    const { data } = await apiClient.post<AuthTokens>('/auth/2fa/verify/', {
      '2fa_token': twoFactorToken,
      code,
      is_recovery: isRecovery,
    });

    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    set({ tokens: data, isAuthenticated: true, isAwaiting2FA: false, twoFactorToken: null });
    await get().fetchMe();
  },

  cancelTwoFactor: () => {
    set({ twoFactorToken: null, isAwaiting2FA: false });
  },

  fetchMe: async () => {
    try {
      const { data } = await apiClient.get<User>('/accounts/me/');
      set({ user: data, isLoading: false });
      // Also fetch membership for RBAC
      get().fetchMembership();
    } catch {
      set({ isLoading: false });
    }
  },

  fetchMembership: async () => {
    try {
      const { data } = await apiClient.get('/teams/memberships/me/');
      set({ membership: data });
    } catch {
      // No membership = user has no tenant yet (signup flow)
      set({ membership: null });
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