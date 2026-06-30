import { useState } from 'react';
import { Input } from '../../../../components/atoms/input';
import { Select } from '../../../../components/atoms/select';
import { NavigationButtons } from '../NavigationButtons';
import type { OnboardingProgressPayload } from '../../../../types';

const INDUSTRIES = [
  'Technology',
  'Financial Services',
  'Healthcare',
  'Real Estate',
  'Recruitment',
  'Media',
  'Education',
  'Other',
];

interface Props {
  tenantName: string;
  tenantIndustry: string;
  tenantLogoUrl: string;
  onDone: (payload: OnboardingProgressPayload) => void;
  onSkip: () => void;
}

export function CompanySetupStep({ tenantName, tenantIndustry, onDone, onSkip }: Props) {
  const [name, setName] = useState(tenantName);
  const [industry, setIndustry] = useState(tenantIndustry);
  const [loading, setLoading] = useState(false);

  const handleNext = async () => {
    setLoading(true);
    await onDone({
      company: { name, industry },
      company_done: true,
    });
    setLoading(false);
  };

  return (
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">
        Set up your company
      </h1>
      <p className="text-gray-500 dark:text-slate-400 mb-8">
        Tell us about your business so we can tailor the experience.
      </p>
      <div className="max-w-md mx-auto space-y-4 text-left">
        <Input
          label="Company name"
          placeholder="e.g. Acme Corp"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Select
          label="Industry"
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
        >
          <option value="">Select industry...</option>
          {INDUSTRIES.map((i) => (
            <option key={i} value={i.toLowerCase()}>
              {i}
            </option>
          ))}
        </Select>
      </div>
      <NavigationButtons
        currentStep={0}
        totalSteps={6}
        onBack={() => {}}
        onNext={handleNext}
        onSkip={onSkip}
        onFinish={() => {}}
        isLastStep={false}
        loading={loading}
        nextLabel="Save & Continue"
      />
    </div>
  );
}