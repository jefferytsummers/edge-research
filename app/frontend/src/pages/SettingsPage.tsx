import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Settings,
  Video,
  FileText,
  Trash2,
  RefreshCw,
  Plus,
  Loader2,
} from 'lucide-react';
import { Button, Card, Input, Textarea } from '@/components/common';
import { useConfigStore } from '@/store';
import { useConfigApi } from '@/hooks';
import { cn, truncate } from '@/lib/utils';
import type { ProtocolRules } from '@/types';

export function SettingsPage() {
  const navigate = useNavigate();
  const { feeds, protocols, setProtocols, removeFeed, addFeed, resetConfig } =
    useConfigStore();
  const { addFeed: addFeedApi, deleteFeed: deleteFeedApi, saveProtocols, loading, error } = useConfigApi();

  const [editingProtocols, setEditingProtocols] = useState(false);
  const [localProtocols, setLocalProtocols] = useState<ProtocolRules>(protocols);
  const [showAddFeed, setShowAddFeed] = useState(false);
  const [newFeed, setNewFeed] = useState({ name: '', source_uri: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSaveProtocols = async () => {
    setIsSubmitting(true);
    try {
      const success = await saveProtocols(localProtocols);
      if (success) {
        setProtocols(localProtocols);
        setEditingProtocols(false);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddFeed = async () => {
    if (newFeed.name && newFeed.source_uri) {
      setIsSubmitting(true);
      try {
        const result = await addFeedApi(newFeed);
        if (result) {
          addFeed({ ...newFeed, stream_id: result.stream_id, enabled: true });
          setNewFeed({ name: '', source_uri: '' });
          setShowAddFeed(false);
        }
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  const handleDeleteFeed = async (streamId: string) => {
    if (!window.confirm('Are you sure you want to delete this feed?')) {
      return;
    }
    setIsSubmitting(true);
    try {
      const success = await deleteFeedApi(streamId);
      if (success) {
        removeFeed(streamId);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    if (
      window.confirm(
        'Are you sure you want to reset all settings? This will remove all feeds and reset protocols to defaults.'
      )
    ) {
      resetConfig();
      navigate('/setup');
    }
  };

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="border-b border-dark-800 bg-dark-900/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/dashboard')}
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>
              <h1 className="text-xl font-bold text-dark-100 flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Settings
              </h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-3xl mx-auto px-6 py-6 space-y-6">
        {/* Error Display */}
        {error && (
          <Card className="bg-red-950/30 border-red-500/30">
            <div className="flex items-center gap-2 text-red-400">
              <span>Error: {error}</span>
            </div>
          </Card>
        )}

        {/* Camera Feeds Section */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Video className="w-5 h-5 text-dark-400" />
              <h2 className="text-lg font-semibold text-dark-100">
                Camera Feeds ({feeds.length})
              </h2>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAddFeed(!showAddFeed)}
            >
              <Plus className="w-4 h-4" />
              Add Feed
            </Button>
          </div>

          {/* Add Feed Form */}
          {showAddFeed && (
            <div className="mb-4 p-4 rounded-lg bg-dark-700/50 border border-dark-600">
              <div className="space-y-3">
                <Input
                  label="Feed Name"
                  placeholder="e.g., Room 105"
                  value={newFeed.name}
                  onChange={(e) =>
                    setNewFeed((prev) => ({ ...prev, name: e.target.value }))
                  }
                />
                <Input
                  label="Source URL"
                  placeholder="rtsp://192.168.1.105:554/stream"
                  value={newFeed.source_uri}
                  onChange={(e) =>
                    setNewFeed((prev) => ({ ...prev, source_uri: e.target.value }))
                  }
                />
                <div className="flex justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowAddFeed(false)}
                    disabled={isSubmitting}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleAddFeed}
                    disabled={!newFeed.name || !newFeed.source_uri || isSubmitting}
                  >
                    {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Add'}
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Feed List */}
          <div className="space-y-2">
            {feeds.map((feed) => (
              <div
                key={feed.stream_id}
                className="flex items-center justify-between p-3 rounded-lg bg-dark-700/50"
              >
                <div>
                  <p className="font-medium text-dark-200">{feed.name}</p>
                  <p className="text-sm text-dark-400 truncate max-w-xs">
                    {truncate(feed.source_uri, 40)}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteFeed(feed.stream_id)}
                  disabled={isSubmitting}
                  className="text-dark-400 hover:text-red-400"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))}
            {feeds.length === 0 && (
              <p className="text-center text-dark-500 py-4">
                No feeds configured
              </p>
            )}
          </div>
        </Card>

        {/* Protocols Section */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-dark-400" />
              <h2 className="text-lg font-semibold text-dark-100">
                Monitoring Protocols
              </h2>
            </div>
            {!editingProtocols && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditingProtocols(true)}
              >
                Edit
              </Button>
            )}
          </div>

          {editingProtocols ? (
            <div className="space-y-4">
              <ProtocolInput
                label="GREEN - Safe Behavior"
                color="green"
                value={localProtocols.green_rules}
                onChange={(v) =>
                  setLocalProtocols((prev) => ({ ...prev, green_rules: v }))
                }
              />
              <ProtocolInput
                label="YELLOW - Needs Attention"
                color="yellow"
                value={localProtocols.yellow_rules}
                onChange={(v) =>
                  setLocalProtocols((prev) => ({ ...prev, yellow_rules: v }))
                }
              />
              <ProtocolInput
                label="RED - Immediate Action"
                color="red"
                value={localProtocols.red_rules}
                onChange={(v) =>
                  setLocalProtocols((prev) => ({ ...prev, red_rules: v }))
                }
              />
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="ghost"
                  onClick={() => {
                    setLocalProtocols(protocols);
                    setEditingProtocols(false);
                  }}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button onClick={handleSaveProtocols} disabled={isSubmitting}>
                  {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Save Changes
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <ProtocolDisplay
                label="GREEN"
                value={protocols.green_rules}
                color="green"
              />
              <ProtocolDisplay
                label="YELLOW"
                value={protocols.yellow_rules}
                color="yellow"
              />
              <ProtocolDisplay
                label="RED"
                value={protocols.red_rules}
                color="red"
              />
            </div>
          )}
        </Card>

        {/* Danger Zone */}
        <Card className="border border-red-500/30">
          <div className="flex items-center gap-2 mb-4">
            <RefreshCw className="w-5 h-5 text-red-400" />
            <h2 className="text-lg font-semibold text-red-300">Danger Zone</h2>
          </div>
          <p className="text-sm text-dark-400 mb-4">
            Reset all settings to default. This will remove all camera feeds and
            reset protocol rules.
          </p>
          <Button variant="danger" onClick={handleReset}>
            Reset Configuration
          </Button>
        </Card>
      </main>
    </div>
  );
}

interface ProtocolInputProps {
  label: string;
  color: 'green' | 'yellow' | 'red';
  value: string;
  onChange: (value: string) => void;
}

function ProtocolInput({ label, color, value, onChange }: ProtocolInputProps) {
  const colorClasses = {
    green: 'border-l-green-500 bg-green-500/5',
    yellow: 'border-l-yellow-500 bg-yellow-500/5',
    red: 'border-l-red-500 bg-red-500/5',
  };

  return (
    <div className={cn('border-l-4 pl-4 py-2', colorClasses[color])}>
      <label className="block text-sm font-medium text-dark-300 mb-2">
        {label}
      </label>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={2}
        className="bg-dark-800"
      />
    </div>
  );
}

interface ProtocolDisplayProps {
  label: string;
  value: string;
  color: 'green' | 'yellow' | 'red';
}

function ProtocolDisplay({ label, value, color }: ProtocolDisplayProps) {
  const colorClasses = {
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
  };

  return (
    <div className="flex items-start gap-2 p-3 rounded-lg bg-dark-700/50">
      <span className={cn('font-medium text-sm', colorClasses[color])}>
        {label}:
      </span>
      <span className="text-sm text-dark-300">{truncate(value, 120)}</span>
    </div>
  );
}
