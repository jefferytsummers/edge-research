import { useState, useEffect, useCallback } from 'react';
import { CheckCircle, XCircle, Loader2, Wifi, Monitor, Timer } from 'lucide-react';
import { Modal, ModalFooter, Button } from '@/components/common';
import { useConfigApi } from '@/hooks';
import { cn } from '@/lib/utils';
import type { ConnectionTestResult } from '@/types';

interface ConnectionTestModalProps {
  isOpen: boolean;
  onClose: () => void;
  sourceUri: string;
  feedName?: string;
}

type TestStage = 'connecting' | 'probing' | 'complete' | 'error';

export function ConnectionTestModal({
  isOpen,
  onClose,
  sourceUri,
  feedName,
}: ConnectionTestModalProps) {
  const { testConnection } = useConfigApi();
  const [stage, setStage] = useState<TestStage>('connecting');
  const [result, setResult] = useState<ConnectionTestResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const runTest = useCallback(async () => {
    setStage('connecting');
    setResult(null);
    setErrorMessage(null);

    // Simulate connection stage
    await new Promise((resolve) => setTimeout(resolve, 800));
    setStage('probing');

    // Run actual test
    const testResult = await testConnection(sourceUri);

    if (testResult) {
      setResult(testResult);
      setStage(testResult.success ? 'complete' : 'error');
      if (!testResult.success && testResult.error) {
        setErrorMessage(testResult.error);
      }
    } else {
      setStage('error');
      setErrorMessage('Failed to connect to test service');
    }
  }, [sourceUri, testConnection]);

  useEffect(() => {
    if (isOpen) {
      runTest();
    }
  }, [isOpen, runTest]);

  const handleRetry = () => {
    runTest();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Connection Test" size="sm">
      <div className="space-y-6">
        {/* Feed Info */}
        <div className="text-center">
          {feedName && (
            <p className="text-lg font-medium text-dark-100 mb-1">{feedName}</p>
          )}
          <p className="text-sm text-dark-400 font-mono break-all">{sourceUri}</p>
        </div>

        {/* Test Progress */}
        <div className="space-y-3">
          <TestStep
            label="Connecting to stream"
            status={
              stage === 'connecting'
                ? 'loading'
                : stage === 'error' && !result
                ? 'error'
                : 'complete'
            }
            icon={<Wifi className="w-4 h-4" />}
          />
          <TestStep
            label="Probing stream info"
            status={
              stage === 'connecting'
                ? 'pending'
                : stage === 'probing'
                ? 'loading'
                : stage === 'error'
                ? 'error'
                : 'complete'
            }
            icon={<Monitor className="w-4 h-4" />}
          />
        </div>

        {/* Results */}
        {stage === 'complete' && result && (
          <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
            <div className="flex items-center gap-2 text-green-400 mb-3">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">Connection Successful</span>
            </div>
            <dl className="grid grid-cols-2 gap-2 text-sm">
              {result.resolution && (
                <>
                  <dt className="text-dark-400">Resolution:</dt>
                  <dd className="text-dark-200">{result.resolution}</dd>
                </>
              )}
              {result.fps && (
                <>
                  <dt className="text-dark-400">Frame Rate:</dt>
                  <dd className="text-dark-200">{result.fps} fps</dd>
                </>
              )}
            </dl>
          </div>
        )}

        {stage === 'error' && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
            <div className="flex items-center gap-2 text-red-400 mb-2">
              <XCircle className="w-5 h-5" />
              <span className="font-medium">Connection Failed</span>
            </div>
            <p className="text-sm text-dark-300">
              {errorMessage || 'Unable to connect to the stream. Please verify the URL and ensure the camera is online.'}
            </p>
          </div>
        )}
      </div>

      <ModalFooter>
        {stage === 'error' && (
          <Button variant="outline" onClick={handleRetry}>
            <Timer className="w-4 h-4 mr-2" />
            Retry
          </Button>
        )}
        <Button
          onClick={onClose}
          variant={stage === 'complete' ? 'primary' : 'ghost'}
        >
          {stage === 'complete' ? 'Done' : 'Close'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

interface TestStepProps {
  label: string;
  status: 'pending' | 'loading' | 'complete' | 'error';
  icon: React.ReactNode;
}

function TestStep({ label, status, icon }: TestStepProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg transition-colors',
        status === 'loading' && 'bg-blue-500/10',
        status === 'complete' && 'bg-green-500/5',
        status === 'error' && 'bg-red-500/10',
        status === 'pending' && 'opacity-50'
      )}
    >
      {/* Status Icon */}
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center',
          status === 'pending' && 'bg-dark-700 text-dark-500',
          status === 'loading' && 'bg-blue-500/20 text-blue-400',
          status === 'complete' && 'bg-green-500/20 text-green-400',
          status === 'error' && 'bg-red-500/20 text-red-400'
        )}
      >
        {status === 'loading' ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : status === 'complete' ? (
          <CheckCircle className="w-4 h-4" />
        ) : status === 'error' ? (
          <XCircle className="w-4 h-4" />
        ) : (
          icon
        )}
      </div>

      {/* Label */}
      <span
        className={cn(
          'text-sm font-medium',
          status === 'pending' && 'text-dark-500',
          status === 'loading' && 'text-blue-300',
          status === 'complete' && 'text-green-300',
          status === 'error' && 'text-red-300'
        )}
      >
        {label}
      </span>

      {/* Status Text */}
      <span
        className={cn(
          'ml-auto text-xs',
          status === 'pending' && 'text-dark-600',
          status === 'loading' && 'text-blue-400',
          status === 'complete' && 'text-green-400',
          status === 'error' && 'text-red-400'
        )}
      >
        {status === 'pending' && 'Waiting...'}
        {status === 'loading' && 'Testing...'}
        {status === 'complete' && 'Success'}
        {status === 'error' && 'Failed'}
      </span>
    </div>
  );
}
