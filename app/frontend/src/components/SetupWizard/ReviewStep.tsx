import { useState } from 'react';
import { Video, CheckSquare, Square, Loader2 } from 'lucide-react';
import { Button, Card } from '@/components/common';
import { useConfigStore } from '@/store';
import { useConfigApi } from '@/hooks';
import { cn } from '@/lib/utils';
import { truncate } from '@/lib/utils';

interface ReviewStepProps {
  onComplete: () => void;
  onBack: () => void;
}

export function ReviewStep({ onComplete, onBack }: ReviewStepProps) {
  const { feeds, protocols, markConfigured } = useConfigStore();
  const { saveProtocols, error } = useConfigApi();
  const [saveConfig, setSaveConfig] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleStartMonitoring = async () => {
    setIsSubmitting(true);

    try {
      // Save protocols to backend
      const success = await saveProtocols(protocols);

      if (success) {
        markConfigured();
        onComplete();
      }
    } catch (err) {
      console.error('Failed to save configuration:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-dark-100 mb-2">
          Review Configuration
        </h2>
        <p className="text-dark-400">
          Review your settings before starting monitoring.
        </p>
      </div>

      {/* Camera Feeds Summary */}
      <Card className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-dark-100">
            Camera Feeds ({feeds.length})
          </h3>
        </div>
        <div className="space-y-2">
          {feeds.map((feed) => (
            <div
              key={feed.stream_id}
              className="flex items-center gap-3 p-3 rounded-lg bg-dark-700/50"
            >
              <Video className="w-4 h-4 text-dark-400" />
              <div className="flex-1">
                <span className="font-medium text-dark-200">{feed.name}</span>
                <span className="text-dark-500 mx-2">-</span>
                <span className="text-sm text-dark-400">
                  {truncate(feed.source_uri, 45)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Protocols Summary */}
      <Card className="mb-6">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">Protocols</h3>
        <div className="space-y-3">
          <ProtocolSummaryItem
            emoji="\uD83D\uDFE2"
            label="GREEN"
            value={protocols.green_rules}
            colorClass="text-green-400"
          />
          <ProtocolSummaryItem
            emoji="\uD83D\uDFE1"
            label="YELLOW"
            value={protocols.yellow_rules}
            colorClass="text-yellow-400"
          />
          <ProtocolSummaryItem
            emoji="\uD83D\uDD34"
            label="RED"
            value={protocols.red_rules}
            colorClass="text-red-400"
          />
        </div>
      </Card>

      {/* Save Option */}
      <Card className="mb-6" variant="outlined">
        <button
          type="button"
          onClick={() => setSaveConfig(!saveConfig)}
          className="flex items-center gap-3 w-full text-left"
        >
          {saveConfig ? (
            <CheckSquare className="w-5 h-5 text-blue-400" />
          ) : (
            <Square className="w-5 h-5 text-dark-500" />
          )}
          <span className="text-dark-200">Save configuration for future sessions</span>
        </button>
      </Card>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button
          onClick={handleStartMonitoring}
          disabled={isSubmitting}
          className="bg-green-600 hover:bg-green-700"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Starting...
            </>
          ) : (
            'Start Monitoring'
          )}
        </Button>
      </div>
    </div>
  );
}

interface ProtocolSummaryItemProps {
  emoji: string;
  label: string;
  value: string;
  colorClass: string;
}

function ProtocolSummaryItem({
  emoji,
  label,
  value,
  colorClass,
}: ProtocolSummaryItemProps) {
  return (
    <div className="flex items-start gap-2 p-3 rounded-lg bg-dark-700/50">
      <span>{emoji}</span>
      <div className="flex-1">
        <span className={cn('font-medium', colorClass)}>{label}:</span>
        <span className="text-dark-300 ml-2">{truncate(value, 100)}</span>
      </div>
    </div>
  );
}
