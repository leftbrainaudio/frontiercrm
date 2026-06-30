import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// ── Module-level mocks (hoisted by Vitest) ───────────────────────────────

const mockSocialLogin = vi.fn().mockResolvedValue(undefined);

// Mutable holder so tests can set search params dynamically
let mockSearchParams = '';
vi.mock('react-router-dom', () => ({
  MemoryRouter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Link: ({ to, children, className }: any) => <a href={to} className={className}>{children}</a>,
  useSearchParams: () => [new URLSearchParams(mockSearchParams)],
  useNavigate: () => vi.fn(),
}));

vi.mock('../../store/auth', () => ({
  useAuthStore: vi.fn((sel?: unknown) => {
    const state = {
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      signup: vi.fn(),
      socialLogin: mockSocialLogin,
      logout: vi.fn(),
      fetchMe: vi.fn(),
      setUser: vi.fn(),
      init: vi.fn(),
    };
    return typeof sel === 'function' ? sel(state) : state;
  }),
}));

vi.mock('../../hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    socialLogin: mockSocialLogin,
    logout: vi.fn(),
    fetchMe: vi.fn(),
    setUser: vi.fn(),
  })),
}));

vi.mock('../../components/atoms/button', () => ({
  Button: ({ children, loading, ...props }: any) => (
    <button {...props}>{loading ? 'Loading...' : children}</button>
  ),
}));

vi.mock('../../components/atoms/input', () => ({
  Input: ({ label, error, ...props }: any) => (
    <div>
      {label && <label>{label}</label>}
      <input {...props} />
      {error && <span role="alert">{error}</span>}
    </div>
  ),
}));

// Import components after mocks (Vitest hoists vi.mock calls)
import { LoginPage } from '../../pages/auth/login';
import { SocialCallbackPage } from '../../pages/auth/social-callback';

// ── Login page ───────────────────────────────────────────────────────────

describe('LoginPage - OAuth buttons', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('fetch', vi.fn());
  });

  it('renders the "Continue with Google" button', () => {
    render(<LoginPage />);
    expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument();
  });

  it('renders the "Continue with Microsoft" button', () => {
    render(<LoginPage />);
    expect(screen.getByRole('button', { name: /continue with microsoft/i })).toBeInTheDocument();
  });

  it('Google button calls /api/auth/social/google/init/ on click and redirects', async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce({
      json: async () => ({ authorization_url: 'https://accounts.google.com/o/oauth2/auth?state=xyz' }),
    } as Response);

    // Stub window.location.href
    const originalLocation = window.location;
    // @ts-expect-error - reassigning Location
    delete window.location;
    window.location = { ...originalLocation, href: '' };

    const user = userEvent.setup();
    render(<LoginPage />);
    await user.click(screen.getByRole('button', { name: /continue with google/i }));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/social/google/init/');
    });
    await waitFor(() => {
      expect(window.location.href).toBe('https://accounts.google.com/o/oauth2/auth?state=xyz');
    });

    // Restore
    window.location = originalLocation;
  });

  it('Microsoft button calls /api/auth/social/microsoft/init/ on click and redirects', async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce({
      json: async () => ({ authorization_url: 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?state=abc' }),
    } as Response);

    const originalLocation = window.location;
    // @ts-expect-error - reassigning Location
    delete window.location;
    window.location = { ...originalLocation, href: '' };

    const user = userEvent.setup();
    render(<LoginPage />);
    await user.click(screen.getByRole('button', { name: /continue with microsoft/i }));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/social/microsoft/init/');
    });
    await waitFor(() => {
      expect(window.location.href).toBe('https://login.microsoftonline.com/common/oauth2/v2.0/authorize?state=abc');
    });

    window.location = originalLocation;
  });

  it('Google button gracefully handles fetch error (does not throw)', async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const originalLocation = window.location;
    // @ts-expect-error - reassigning Location
    delete window.location;
    window.location = { ...originalLocation, href: '' };

    const user = userEvent.setup();
    render(<LoginPage />);
    await user.click(screen.getByRole('button', { name: /continue with google/i }));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/social/google/init/');
    });
    expect(window.location.href).toBe('');

    window.location = originalLocation;
  });

  it('renders the Google SVG icon', () => {
    render(<LoginPage />);
    const container = screen.getByRole('button', { name: /continue with google/i });
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('renders the Microsoft SVG icon', () => {
    render(<LoginPage />);
    const container = screen.getByRole('button', { name: /continue with microsoft/i });
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });
});

// ── Social callback page ─────────────────────────────────────────────────

describe('SocialCallbackPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = '';
  });

  it('shows loading spinner when code is present', () => {
    mockSearchParams = 'code=test-auth-code';
    render(<SocialCallbackPage />);
    expect(screen.getByText(/signing you in/i)).toBeInTheDocument();
    expect(screen.getByText(/please wait/i)).toBeInTheDocument();
  });

  it('calls socialLogin with provider and code from URL search params', async () => {
    mockSearchParams = 'code=test-auth-code&state=google';
    render(<SocialCallbackPage />);

    await waitFor(() => {
      expect(mockSocialLogin).toHaveBeenCalledWith(
        'google',
        'test-auth-code',
        'http://localhost:3000/auth/callback',
      );
    });
  });

  it('defaults provider to "google" when no state param is present', async () => {
    mockSearchParams = 'code=test-auth-code';
    render(<SocialCallbackPage />);

    await waitFor(() => {
      expect(mockSocialLogin).toHaveBeenCalledWith(
        'google',
        'test-auth-code',
        expect.stringContaining('/auth/callback'),
      );
    });
  });

  it('shows error message when no code is present in URL', () => {
    mockSearchParams = '';
    render(<SocialCallbackPage />);
    expect(screen.getByText(/sign-in failed/i)).toBeInTheDocument();
    expect(screen.getByText(/no authorization code received/i)).toBeInTheDocument();
  });

  it('shows "Back to login" link when there is an error', () => {
    mockSearchParams = '';
    render(<SocialCallbackPage />);
    expect(screen.getByText(/back to login/i)).toBeInTheDocument();
  });

  it('shows error when socialLogin rejects', async () => {
    mockSocialLogin.mockRejectedValueOnce({
      response: { data: { error: 'Authentication failed. Please try again.' } },
    });

    mockSearchParams = 'code=bad-code&state=google';
    render(<SocialCallbackPage />);

    await waitFor(() => {
      expect(screen.getByText(/authentication failed/i)).toBeInTheDocument();
    });
  });

  it('shows generic error when socialLogin rejects without response data', async () => {
    mockSocialLogin.mockRejectedValueOnce(new Error('Network failure'));

    mockSearchParams = 'code=fail-code&state=microsoft';
    render(<SocialCallbackPage />);

    await waitFor(() => {
      expect(screen.getByText(/authentication failed/i)).toBeInTheDocument();
    });
  });
});