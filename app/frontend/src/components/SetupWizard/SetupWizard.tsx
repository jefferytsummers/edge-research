import { useState } from 'react';
import { WizardProgress } from './WizardProgress';
import { FeedStep } from './FeedStep';
import { ProtocolStep } from './ProtocolStep';
import { ReviewStep } from './ReviewStep';
import { ModelStatusIndicator } from '../Dashboard/ModelStatusIndicator';

interface SetupWizardProps {
  onComplete: () => void;
}

const wizardSteps = [
  { title: 'Add Feeds', description: 'Configure camera sources' },
  { title: 'Define Rules', description: 'Set monitoring protocols' },
  { title: 'Review', description: 'Confirm and start' },
];

export function SetupWizard({ onComplete }: SetupWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);

  const goNext = () => setCurrentStep((prev) => Math.min(prev + 1, 3));
  const goBack = () => setCurrentStep((prev) => Math.max(prev - 1, 1));

  return (
    <div className="min-h-screen bg-dark-900 flex flex-col">
      {/* Header */}
      <header className="border-b border-dark-800 bg-dark-900/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-dark-100">
                Newport Demo - Setup Wizard
              </h1>
              <ModelStatusIndicator />
            </div>
            <span className="text-sm text-dark-400">
              Step {currentStep} of {wizardSteps.length}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 py-8">
        <div className="max-w-3xl mx-auto px-6">
          <WizardProgress currentStep={currentStep} steps={wizardSteps} />

          <div className="mt-8">
            {currentStep === 1 && <FeedStep onNext={goNext} />}
            {currentStep === 2 && (
              <ProtocolStep onNext={goNext} onBack={goBack} />
            )}
            {currentStep === 3 && (
              <ReviewStep onComplete={onComplete} onBack={goBack} />
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-800 py-4">
        <div className="max-w-3xl mx-auto px-6">
          <p className="text-center text-sm text-dark-500">
            Newport Demo - AI-Powered Behavioral Monitoring
          </p>
        </div>
      </footer>
    </div>
  );
}
