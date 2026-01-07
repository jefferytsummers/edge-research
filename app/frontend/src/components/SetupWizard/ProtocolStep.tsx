import { useState, useEffect } from 'react';
import { Button, Textarea, Card } from '@/components/common';
import { useConfigStore } from '@/store';
import { cn } from '@/lib/utils';
import type { ProtocolRules } from '@/types';

interface ProtocolStepProps {
  onNext: () => void;
  onBack: () => void;
}

interface ProtocolSection {
  key: keyof ProtocolRules;
  title: string;
  color: string;
  bgColor: string;
  borderColor: string;
  emoji: string;
  placeholder: string;
  description: string;
}

const protocolSections: ProtocolSection[] = [
  {
    key: 'green_rules',
    title: 'GREEN - Safe Behavior',
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/30',
    emoji: '\uD83D\uDFE2',
    placeholder:
      'Reading, watching TV, sleeping normally in bed, eating meals, sitting calmly...',
    description: 'Describe what constitutes safe, normal behavior:',
  },
  {
    key: 'yellow_rules',
    title: 'YELLOW - Needs Attention',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
    emoji: '\uD83D\uDFE1',
    placeholder:
      'Out of camera view, crouching in corners, minor injuries, pacing erratically...',
    description: 'Describe behavior that needs staff awareness:',
  },
  {
    key: 'red_rules',
    title: 'RED - Immediate Action Required',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    emoji: '\uD83D\uDD34',
    placeholder:
      'Unconscious on ground, severe injury, room is empty/resident has left, self-harm...',
    description: 'Describe critical situations requiring immediate response:',
  },
];

export function ProtocolStep({ onNext, onBack }: ProtocolStepProps) {
  const { protocols, setProtocols } = useConfigStore();
  const [localProtocols, setLocalProtocols] = useState<ProtocolRules>(protocols);

  useEffect(() => {
    setLocalProtocols(protocols);
  }, [protocols]);

  const handleChange = (key: keyof ProtocolRules, value: string) => {
    setLocalProtocols((prev) => ({ ...prev, [key]: value }));
  };

  const handleNext = () => {
    setProtocols(localProtocols);
    onNext();
  };

  const isValid =
    localProtocols.green_rules.trim().length > 0 &&
    localProtocols.yellow_rules.trim().length > 0 &&
    localProtocols.red_rules.trim().length > 0;

  return (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-dark-100 mb-2">
          Define Monitoring Protocols
        </h2>
        <p className="text-dark-400">
          Describe the behaviors that should trigger each severity level using natural
          language. The AI will use these descriptions to classify what it observes.
        </p>
      </div>

      <div className="space-y-6">
        {protocolSections.map((section) => (
          <Card
            key={section.key}
            className={cn(
              'border-l-4',
              section.bgColor,
              section.borderColor
            )}
          >
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">{section.emoji}</span>
              <h3 className={cn('font-semibold', section.color)}>
                {section.title}
              </h3>
            </div>
            <p className="text-sm text-dark-400 mb-3">{section.description}</p>
            <Textarea
              value={localProtocols[section.key]}
              onChange={(e) => handleChange(section.key, e.target.value)}
              placeholder={section.placeholder}
              rows={3}
              className={cn(
                'bg-dark-900/50 border-dark-600',
                'focus:border-transparent'
              )}
            />
          </Card>
        ))}
      </div>

      {/* Tips Section */}
      <Card className="mt-6" variant="outlined">
        <h4 className="text-sm font-medium text-dark-300 mb-2">Tips for effective protocols:</h4>
        <ul className="text-sm text-dark-400 space-y-1.5">
          <li className="flex items-start gap-2">
            <span className="text-dark-500">-</span>
            Be specific about observable behaviors (e.g., "lying on floor" instead of "in distress")
          </li>
          <li className="flex items-start gap-2">
            <span className="text-dark-500">-</span>
            Include multiple examples for each category
          </li>
          <li className="flex items-start gap-2">
            <span className="text-dark-500">-</span>
            For RED rules, include actionable scenarios that require immediate response
          </li>
        </ul>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button onClick={handleNext} disabled={!isValid}>
          Next: Review
        </Button>
      </div>
    </div>
  );
}
