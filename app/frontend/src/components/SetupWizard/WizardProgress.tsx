import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';

interface WizardProgressProps {
  currentStep: number;
  steps: { title: string; description?: string }[];
}

export function WizardProgress({ currentStep, steps }: WizardProgressProps) {
  return (
    <div className="flex items-center justify-center mb-8">
      {steps.map((step, index) => {
        const stepNumber = index + 1;
        const isCompleted = currentStep > stepNumber;
        const isCurrent = currentStep === stepNumber;

        return (
          <div key={index} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all',
                  isCompleted && 'bg-green-500 text-white',
                  isCurrent && 'bg-blue-500 text-white ring-4 ring-blue-500/30',
                  !isCompleted && !isCurrent && 'bg-dark-700 text-dark-400'
                )}
              >
                {isCompleted ? (
                  <Check className="w-5 h-5" />
                ) : (
                  stepNumber
                )}
              </div>
              <div className="mt-2 text-center">
                <p
                  className={cn(
                    'text-sm font-medium',
                    isCurrent ? 'text-dark-100' : 'text-dark-400'
                  )}
                >
                  {step.title}
                </p>
              </div>
            </div>
            {index < steps.length - 1 && (
              <div
                className={cn(
                  'w-20 h-1 mx-4 rounded-full transition-colors',
                  currentStep > stepNumber + 1 || isCompleted
                    ? 'bg-green-500'
                    : 'bg-dark-700'
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
