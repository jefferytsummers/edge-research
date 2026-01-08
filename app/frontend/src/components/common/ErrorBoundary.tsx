import { Component, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';
import { Card } from './Card';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Card className="m-4 bg-red-950/20 border-red-500/30">
          <div className="flex flex-col items-center text-center py-8">
            <AlertTriangle className="w-12 h-12 text-red-400 mb-4" />
            <h2 className="text-lg font-semibold text-red-300 mb-2">
              Something went wrong
            </h2>
            <p className="text-sm text-dark-400 mb-4 max-w-md">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <Button onClick={this.handleReset} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </div>
        </Card>
      );
    }

    return this.props.children;
  }
}

// Simpler functional wrapper for common use
interface ErrorFallbackProps {
  error?: Error | null;
  resetErrorBoundary?: () => void;
}

export function ErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  return (
    <Card className="m-4 bg-red-950/20 border-red-500/30">
      <div className="flex flex-col items-center text-center py-8">
        <AlertTriangle className="w-12 h-12 text-red-400 mb-4" />
        <h2 className="text-lg font-semibold text-red-300 mb-2">
          Something went wrong
        </h2>
        <p className="text-sm text-dark-400 mb-4 max-w-md">
          {error?.message || 'An unexpected error occurred'}
        </p>
        {resetErrorBoundary && (
          <Button onClick={resetErrorBoundary} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
        )}
      </div>
    </Card>
  );
}
