import { useAuthStore } from '../store/auth';

export function useAuth() {
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoading = useAuthStore((s) => s.isLoading);
  const twoFactorToken = useAuthStore((s) => s.twoFactorToken);
  const isAwaiting2FA = useAuthStore((s) => s.isAwaiting2FA);
  const login = useAuthStore((s) => s.login);
  const signup = useAuthStore((s) => s.signup);
  const socialLogin = useAuthStore((s) => s.socialLogin);
  const verifyTwoFactor = useAuthStore((s) => s.verifyTwoFactor);
  const cancelTwoFactor = useAuthStore((s) => s.cancelTwoFactor);
  const logout = useAuthStore((s) => s.logout);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const setUser = useAuthStore((s) => s.setUser);

  return {
    user,
    isAuthenticated,
    isLoading,
    twoFactorToken,
    isAwaiting2FA,
    login,
    signup,
    socialLogin,
    verifyTwoFactor,
    cancelTwoFactor,
    logout,
    fetchMe,
    setUser,
  };
}