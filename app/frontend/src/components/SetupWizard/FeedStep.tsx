import { useState } from 'react';
import { Plus, Trash2, CheckCircle, Loader2, Video, Wifi } from 'lucide-react';
import { Button, Input, Card } from '@/components/common';
import { ConnectionTestModal } from './ConnectionTestModal';
import { useConfigStore } from '@/store';
import { useConfigApi } from '@/hooks';
import { cn } from '@/lib/utils';
import type { StreamConfig } from '@/types';

interface FeedStepProps {
  onNext: () => void;
  onBack?: () => void;
}

interface FeedFormData {
  name: string;
  source_uri: string;
}

type ConnectionStatus = 'idle' | 'testing' | 'success' | 'error';

export function FeedStep({ onNext, onBack }: FeedStepProps) {
  const { feeds, addFeed, removeFeed } = useConfigStore();
  const { testConnection, loading } = useConfigApi();

  const [formData, setFormData] = useState<FeedFormData>({
    name: '',
    source_uri: '',
  });
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('idle');
  const [connectionError, setConnectionError] = useState<string>('');
  const [showTestModal, setShowTestModal] = useState(false);
  const [testModalUri, setTestModalUri] = useState('');

  const handleInputChange = (field: keyof FeedFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setConnectionStatus('idle');
    setConnectionError('');
  };

  const handleTestConnection = async () => {
    if (!formData.source_uri) return;

    setConnectionStatus('testing');
    setConnectionError('');

    const result = await testConnection(formData.source_uri);

    if (result?.success) {
      setConnectionStatus('success');
    } else {
      setConnectionStatus('error');
      setConnectionError(result?.error || 'Connection failed');
    }
  };

  const openTestModal = (uri: string) => {
    setTestModalUri(uri);
    setShowTestModal(true);
  };

  const handleAddFeed = () => {
    if (!formData.name || !formData.source_uri) return;

    addFeed({
      name: formData.name,
      source_uri: formData.source_uri,
    });

    setFormData({ name: '', source_uri: '' });
    setConnectionStatus('idle');
    setConnectionError('');
  };

  const handleRemoveFeed = (streamId: string) => {
    removeFeed(streamId);
  };

  const canAddFeed = formData.name && formData.source_uri;
  const canProceed = feeds.length > 0;

  return (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-dark-100 mb-2">Add Camera Feeds</h2>
        <p className="text-dark-400">
          Configure the camera feeds you want to monitor. Add RTSP URLs or select demo feeds.
        </p>
      </div>

      {/* Add Feed Form */}
      <Card className="mb-6">
        <div className="space-y-4">
          <Input
            label="Feed Name"
            placeholder="e.g., Room 101"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
          />

          <div className="flex gap-3">
            <div className="flex-1">
              <Input
                label="Source URL"
                placeholder="rtsp://192.168.1.101:554/stream"
                value={formData.source_uri}
                onChange={(e) => handleInputChange('source_uri', e.target.value)}
                error={connectionStatus === 'error' ? connectionError : undefined}
              />
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={handleTestConnection}
                disabled={!formData.source_uri || loading}
                className="whitespace-nowrap"
              >
                {connectionStatus === 'testing' ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Testing...
                  </>
                ) : (
                  'Test Connection'
                )}
              </Button>
            </div>
          </div>

          {connectionStatus === 'success' && (
            <div className="flex items-center gap-2 text-green-400 text-sm">
              <CheckCircle className="w-4 h-4" />
              Connection successful
            </div>
          )}

          <Button
            onClick={handleAddFeed}
            disabled={!canAddFeed}
            className="w-full"
          >
            <Plus className="w-4 h-4" />
            Add Feed
          </Button>
        </div>
      </Card>

      {/* Demo Feeds Quick Add */}
      <Card className="mb-6" variant="outlined">
        <p className="text-sm text-dark-400 mb-3">Quick add demo feeds:</p>
        <div className="flex flex-wrap gap-2">
          {[
            { name: 'Room 101', uri: 'rtsp://demo:8554/room101' },
            { name: 'Room 102', uri: 'rtsp://demo:8554/room102' },
            { name: 'Room 103', uri: 'rtsp://demo:8554/room103' },
            { name: 'Common Area', uri: 'rtsp://demo:8554/common' },
          ].map((demo) => (
            <Button
              key={demo.uri}
              variant="ghost"
              size="sm"
              onClick={() =>
                addFeed({ name: demo.name, source_uri: demo.uri })
              }
              disabled={feeds.some((f) => f.source_uri === demo.uri)}
            >
              <Plus className="w-3 h-3" />
              {demo.name}
            </Button>
          ))}
        </div>
      </Card>

      {/* Added Feeds List */}
      {feeds.length > 0 && (
        <Card className="mb-6">
          <h3 className="text-sm font-medium text-dark-300 mb-3">
            Added Feeds ({feeds.length})
          </h3>
          <div className="space-y-2">
            {feeds.map((feed) => (
              <FeedListItem
                key={feed.stream_id}
                feed={feed}
                onRemove={() => handleRemoveFeed(feed.stream_id)}
                onTest={() => openTestModal(feed.source_uri)}
              />
            ))}
          </div>
        </Card>
      )}

      {/* Connection Test Modal */}
      <ConnectionTestModal
        isOpen={showTestModal}
        onClose={() => setShowTestModal(false)}
        sourceUri={testModalUri}
        feedName={feeds.find(f => f.source_uri === testModalUri)?.name}
      />

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <div>
          {onBack && (
            <Button variant="ghost" onClick={onBack}>
              Back
            </Button>
          )}
        </div>
        <Button onClick={onNext} disabled={!canProceed}>
          Next: Define Rules
        </Button>
      </div>
    </div>
  );
}

interface FeedListItemProps {
  feed: StreamConfig;
  onRemove: () => void;
  onTest: () => void;
}

function FeedListItem({ feed, onRemove, onTest }: FeedListItemProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between p-3 rounded-lg',
        'bg-dark-700/50 border border-dark-600'
      )}
    >
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-dark-600 flex items-center justify-center">
          <Video className="w-4 h-4 text-dark-300" />
        </div>
        <div>
          <p className="font-medium text-dark-100">{feed.name}</p>
          <p className="text-sm text-dark-400 truncate max-w-xs">
            {feed.source_uri}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={onTest} title="Test connection">
          <Wifi className="w-4 h-4 text-dark-400 hover:text-blue-400" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onRemove} title="Remove feed">
          <Trash2 className="w-4 h-4 text-dark-400 hover:text-red-400" />
        </Button>
      </div>
    </div>
  );
}
