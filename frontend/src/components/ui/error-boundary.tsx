import { Component, type ReactNode, type ErrorInfo } from 'react';
import { AlertTriangle, RefreshCw, ArrowLeft } from 'lucide-react';
import { Button } from '../atoms/button';

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Optional custom fallback UI instead of the default */
  fallback?: ReactNode | ((error: Error, reset: () => void) => ReactNode);
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log the error to the console in development
    console.error('[ErrorBoundary]', error, errorInfo.componentStack);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  private handleGoBack = () => {
    window.history.back();
    this.handleReset();
  };

  render() {
    if (this.state.hasError) {
      const error = this.state.error!;

      if (this.props.fallback) {
        if (typeof this.props.fallback === 'function') {
          return this.props.fallback(error, this.handleReset);
        }
        return this.props.fallback;
      }

      return (
        <div
          className="flex flex-col items-center justify-center py-20 px-6 text-center"
          role="alert"
        >
          <div className="mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-red-50 dark:bg-red-900/30">
            <AlertTriangle className="h-10 w-10 text-red-500 dark:text-red-400" />
          </div>

          <h2 className="text-xl font-semibold text-text-primary dark:text-dark-text-primary">
            Something went wrong
          </h2>

          <p className="mt-2 max-w-md text-sm text-text-secondary dark:text-dark-text-secondary">
            An unexpected error occurred. Try refreshing the page or go back to where you were.
          </p>

          {error.message && (
            <p className="mt-3 max-w-md text-xs text-text-tertiary dark:text-dark-text-tertiary font-mono bg-surface-secondary dark:bg-dark-surface-secondary rounded-md px-3 py-2">
              {error.message}
            </p>
          )}

          <div className="mt-8 flex items-center gap-3">
            <Button variant="secondary" icon={<ArrowLeft className="h-4 w-4" />} onClick={this.handleGoBack}>
              Go back
            </Button>
            <Button icon={<RefreshCw className="h-4 w-4" />} onClick={this.handleReset}>
              Try again
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}