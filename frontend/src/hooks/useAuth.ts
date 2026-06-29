import { useAuthStore } from '../store/auth';

export function useAuth() {
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoading = useAuthStore((s) => s.isLoading);
  const login = useAuthStore((s) => s.login);
  const signup = useAuthStore((s) => s.signup);
  const logout = useAuthStore((s) => s.logout);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const setUser = useAuthStore((s) => s.setUser);

  return { user, isAuthenticated, isLoading, login, signup, logout, fetchMe, setUser };
}