import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Video, Settings, AlertTriangle } from 'lucide-react';
import { Button, Card, StatusPill } from '@/components/common';
import { QuestionInput } from './QuestionInput';
import { StatusHistory } from './StatusHistory';
import { useConfigStore, useStreamStatus } from '@/store';
import { cn, formatTimestamp } from '@/lib/utils';
import type { Severity } from '@/types';

export function ExpandedFeed() {
  const { streamId } = useParams<{ streamId: string }>();
  const navigate = useNavigate();

  const feeds = useConfigStore((state) => state.feeds);
  const feed = feeds.find((f) => f.stream_id === streamId);
  const status = useStreamStatus(streamId || '');

  if (!feed || !streamId) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-dark-400 text-lg">Feed not found</p>
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            className="mt-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const severity = status?.severity || 'green';
  const isRed = severity === 'red';

  const severityBgColors: Record<Severity, string> = {
    green: 'from-green-500/5',
    yellow: 'from-yellow-500/5',
    red: 'from-red-500/10',
  };

  return (
    <div
      className={cn(
        'min-h-screen bg-gradient-to-b to-dark-900',
        severityBgColors[severity]
      )}
    >
      {/* Header */}
      <header className="border-b border-dark-800 bg-dark-900/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/dashboard')}
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Grid
              </Button>
              <h1 className="text-xl font-bold text-dark-100">
                {feed.name} - Expanded View
              </h1>
            </div>
            <Button variant="ghost" size="sm" onClick={() => navigate('/settings')}>
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video Feed - Left/Main */}
          <div className="lg:col-span-2 space-y-6">
            {/* Video Container */}
            <Card padding="none" className="overflow-hidden">
              <div className="aspect-video bg-dark-950 relative">
                {/* Placeholder for actual video */}
                <div className="absolute inset-0 flex flex-col items-center justify-center text-dark-500">
                  <Video className="w-16 h-16 mb-3" />
                  <span className="text-lg">Live Video Feed</span>
                  <span className="text-sm text-dark-600 mt-1">
                    {feed.source_uri}
                  </span>
                </div>

                {/* RED Alert overlay */}
                {isRed && (
                  <div className="absolute inset-0 bg-red-900/40 flex items-center justify-center">
                    <div className="bg-red-600 text-white px-6 py-3 rounded-lg font-bold text-lg flex items-center gap-3 animate-alert-pulse">
                      <AlertTriangle className="w-6 h-6" />
                      CRITICAL ALERT
                    </div>
                  </div>
                )}

                {/* Live indicator */}
                <div className="absolute top-4 right-4 flex items-center gap-2 bg-dark-900/80 px-3 py-1.5 rounded-lg">
                  <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                  <span className="text-sm text-dark-200">LIVE</span>
                </div>

                {/* Feed name */}
                <div className="absolute top-4 left-4 bg-dark-900/80 px-3 py-1.5 rounded-lg">
                  <span className="text-sm font-medium text-dark-200">
                    {feed.name}
                  </span>
                </div>
              </div>
            </Card>

            {/* Current Status */}
            <Card
              className={cn(
                'border-l-4',
                severity === 'green' && 'border-l-green-500',
                severity === 'yellow' && 'border-l-yellow-500',
                severity === 'red' && 'border-l-red-500'
              )}
            >
              <div className="flex items-start gap-4">
                <span className="text-4xl" role="img">
                  {status?.icon || '\uD83D\uDFE2'}
                </span>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <StatusPill severity={severity} />
                    {status?.timestamp && (
                      <span className="text-xs text-dark-500">
                        Last updated: {formatTimestamp(status.timestamp)}
                      </span>
                    )}
                  </div>
                  <p
                    className={cn(
                      'text-lg',
                      isRed ? 'text-red-300 font-medium' : 'text-dark-200'
                    )}
                  >
                    {status?.description || 'Initializing monitoring...'}
                  </p>
                </div>
              </div>
            </Card>

            {/* Q&A Section */}
            <Card>
              <QuestionInput
                streamId={streamId}
                onQuestionSent={(q, id) => {
                  console.log('Question sent:', q, id);
                }}
              />
            </Card>
          </div>

          {/* Sidebar - Right */}
          <div className="space-y-6">
            {/* Feed Info */}
            <Card>
              <h3 className="text-sm font-medium text-dark-300 mb-3">
                Feed Information
              </h3>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-dark-500">Name</dt>
                  <dd className="text-dark-200">{feed.name}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-dark-500">Status</dt>
                  <dd>
                    <StatusPill severity={severity} />
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-dark-500">Enabled</dt>
                  <dd className="text-dark-200">
                    {feed.enabled ? 'Yes' : 'No'}
                  </dd>
                </div>
              </dl>
            </Card>

            {/* Status History */}
            <Card>
              <StatusHistory streamId={streamId} maxItems={8} />
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
