import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock all dependencies before any static imports
vi.mock('react-router-dom', () => ({
  RouterProvider: vi.fn(() => <div data-testid="router-provider">Router Mock</div>),
  createBrowserRouter: vi.fn(() => ({})),
}));

vi.mock('@tanstack/react-query', () => ({
  QueryClient: vi.fn(),
  QueryClientProvider: vi.fn(
    ({ children }: { children: React.ReactNode }) => <div data-testid="query-provider">{children}</div>,
  ),
}));

vi.mock('react-hot-toast', () => ({
  Toaster: vi.fn(() => <div data-testid="toaster">Toaster</div>),
}));

vi.mock('../../store/auth', () => ({
  useAuthStore: vi.fn((sel?: unknown) => {
    if (typeof sel === 'function') return vi.fn();
    return {};
  }),
}));

vi.mock('../../router', () => ({
  router: {},
}));

// Static import of App - vitest will use the mocked dependencies
import App from '../../App';

describe('App smoke test', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    const { container } = render(<App />);
    expect(container).toBeInTheDocument();
  });

  it('renders QueryClientProvider wrapper', () => {
    render(<App />);
    expect(screen.getByTestId('query-provider')).toBeInTheDocument();
  });

  it('renders Toaster component', () => {
    render(<App />);
    expect(screen.getByTestId('toaster')).toBeInTheDocument();
  });

  it('renders RouterProvider', () => {
    render(<App />);
    expect(screen.getByTestId('router-provider')).toBeInTheDocument();
  });
});