import { useState, type FormEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button, Input } from '@/components/common';
import { useWebSocket } from '@/hooks';
import { cn } from '@/lib/utils';

interface QuestionInputProps {
  streamId: string;
  onQuestionSent?: (question: string, requestId: string) => void;
  className?: string;
}

export function QuestionInput({
  streamId,
  onQuestionSent,
  className,
}: QuestionInputProps) {
  const [question, setQuestion] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { sendQuery, isConnected } = useWebSocket({ autoConnect: false });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!question.trim() || !isConnected) return;

    setIsSubmitting(true);

    try {
      const requestId = sendQuery(streamId, question.trim());
      onQuestionSent?.(question.trim(), requestId);
      setQuestion('');
    } finally {
      // In a real app, you'd wait for the response
      setTimeout(() => setIsSubmitting(false), 500);
    }
  };

  const placeholderQuestions = [
    'Is the resident showing signs of distress?',
    'What is the resident currently doing?',
    'Are there any safety concerns visible?',
  ];

  return (
    <div className={cn('', className)}>
      <h3 className="text-sm font-medium text-dark-300 mb-3">Ask a Question</h3>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about this feed..."
          disabled={!isConnected || isSubmitting}
          className="flex-1"
        />
        <Button
          type="submit"
          disabled={!question.trim() || !isConnected || isSubmitting}
        >
          {isSubmitting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </form>

      {/* Quick question suggestions */}
      <div className="mt-3 flex flex-wrap gap-2">
        {placeholderQuestions.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => setQuestion(q)}
            className={cn(
              'text-xs px-2 py-1 rounded-full',
              'bg-dark-700 text-dark-400 hover:bg-dark-600 hover:text-dark-300',
              'transition-colors'
            )}
          >
            {q}
          </button>
        ))}
      </div>

      {!isConnected && (
        <p className="text-xs text-yellow-400 mt-2">
          Connecting to server...
        </p>
      )}
    </div>
  );
}
