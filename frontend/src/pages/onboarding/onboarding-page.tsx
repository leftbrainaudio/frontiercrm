import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Button } from '../../components/atoms/button';
import { Input } from '../../components/atoms/input';
import { Card } from '../../components/molecules/card';
import { Building2, Users, Rocket, ArrowRight, ArrowLeft, Check } from 'lucide-react';
import apiClient from '../../api/client';

type Plan = 'smb' | 'enterprise' | null;

interface StepProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  onNext?: () => void;
  onBack?: () => void;
  nextLabel?: string;
  loading?: boolean;
  canNext?: boolean;
}

function Step({ title, subtitle, children, onNext, onBack, nextLabel = 'Continue', loading, canNext = true }: StepProps) {
  return (
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">{title}</h1>
      <p className="text-gray-500 dark:text-slate-400 mb-8">{subtitle}</p>
      <div className="max-w-lg mx-auto">{children}</div>
      <div className="flex items-center justify-center gap-3 mt-8">
        {onBack && (
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft size={16} className="mr-1" /> Back
          </Button>
        )}
        {onNext && (
          <Button onClick={onNext} loading={loading} disabled={!canNext}>
            {nextLabel} <ArrowRight size={16} className="ml-1" />
          </Button>
        )}
      </div>
    </div>
  );
}

export function OnboardingPage() {
  const navigate = useNavigate();
  const { user, setUser } = useAuth();
  const [step, setStep] = useState(0);
  const [plan, setPlan] = useState<Plan>(null);
  const [teamSize, setTeamSize] = useState('');
  const [role, setRole] = useState('');
  const [loading, setLoading] = useState(false);

  const completeOnboarding = async () => {
    setLoading(true);
    try {
      await apiClient.patch('/accounts/me/', {
        is_onboarded: true,
        metadata: { plan, team_size: teamSize, role },
      });
      if (user) setUser({ ...user, is_onboarded: true });
      navigate('/dashboard');
    } catch {
      // Even if API fails, go to dashboard
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    // Step 0: Welcome
    <Step
      key="welcome"
      title="Welcome to FrontierCRM"
      subtitle="Let's get you set up in under 2 minutes"
      onNext={() => setStep(1)}
    >
      <div className="flex justify-center mb-6">
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-brand-600 text-white font-bold text-3xl">
          F
        </div>
      </div>
      <p className="text-gray-600 dark:text-slate-300 text-sm leading-relaxed">
        The modern CRM built for teams who want to close more deals, 
        manage relationships better, and grow revenue faster.
      </p>
    </Step>,

    // Step 1: Choose plan
    <Step
      key="plan"
      title="What describes your team best?"
      subtitle="We'll tailor the experience to match your needs"
      onNext={() => setStep(2)}
      onBack={() => setStep(0)}
      canNext={plan !== null}
    >
      <div className="grid grid-cols-2 gap-4">
        <Card
          variant={plan === 'smb' ? 'interactive' : 'outline'}
          className={`p-6 cursor-pointer text-center transition-all ${
            plan === 'smb' ? 'ring-2 ring-brand-500 border-brand-500' : ''
          }`}
          onClick={() => setPlan('smb')}
        >
          <div className="flex justify-center mb-3">
            <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/30">
              <Building2 size={28} className="text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-slate-100">Small Business</h3>
          <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
            1-25 users, simple pipeline, core features
          </p>
        </Card>

        <Card
          variant={plan === 'enterprise' ? 'interactive' : 'outline'}
          className={`p-6 cursor-pointer text-center transition-all ${
            plan === 'enterprise' ? 'ring-2 ring-brand-500 border-brand-500' : ''
          }`}
          onClick={() => setPlan('enterprise')}
        >
          <div className="flex justify-center mb-3">
            <div className="p-3 rounded-xl bg-purple-50 dark:bg-purple-900/30">
              <Users size={28} className="text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-slate-100">Enterprise</h3>
          <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
            25+ users, advanced pipeline, integrations, permissions
          </p>
        </Card>
      </div>
    </Step>,

    // Step 2: Details
    <Step
      key="details"
      title="Tell us a bit more"
      subtitle="Help us personalize your experience"
      onNext={() => setStep(3)}
      onBack={() => setStep(1)}
      canNext={!!teamSize}
    >
      <div className="space-y-4 text-left">
        <Input
          label="Team size"
          placeholder="e.g. 5, 15, 50"
          value={teamSize}
          onChange={(e) => setTeamSize(e.target.value)}
        />
        <Input
          label="Your role"
          placeholder="e.g. Sales manager, Founder, CSO"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        />
      </div>
    </Step>,

    // Step 3: Ready
    <Step
      key="ready"
      title="You're all set!"
      subtitle={plan === 'enterprise' 
        ? "Enterprise workspace ready. Let's start managing deals." 
        : "Your CRM is ready to go."}
      onNext={completeOnboarding}
      onBack={() => setStep(2)}
      nextLabel="Go to Dashboard"
      loading={loading}
    >
      <div className="space-y-4 text-left">
        <div className="p-4 rounded-xl bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800">
          <div className="flex items-center gap-3">
            <Check size={20} className="text-green-600 dark:text-green-400" />
            <div>
              <p className="font-medium text-green-800 dark:text-green-200">Account created</p>
              <p className="text-sm text-green-600 dark:text-green-400">{user?.email}</p>
            </div>
          </div>
        </div>
        <div className="p-4 rounded-xl bg-brand-50 dark:bg-brand-900/30 border border-brand-200 dark:border-brand-800">
          <div className="flex items-center gap-3">
            <Rocket size={20} className="text-brand-600 dark:text-brand-400" />
            <div>
              <p className="font-medium text-brand-800 dark:text-brand-200">Ready to grow</p>
              <p className="text-sm text-brand-600 dark:text-brand-400">
                {plan === 'enterprise' ? 'Enterprise features unlocked' : 'Start adding contacts and deals'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </Step>,
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Progress dots */}
        <div className="flex justify-center gap-2 mb-8">
          {steps.map((_, i) => (
            <div
              key={i}
              className={`h-2 w-2 rounded-full transition-all ${
                i === step ? 'w-8 bg-brand-500' : i < step ? 'bg-brand-300' : 'bg-gray-300 dark:bg-slate-600'
              }`}
            />
          ))}
        </div>

        {/* Step content */}
        <Card className="p-8 animate-fade-in" key={step}>
          {steps[step]}
        </Card>
      </div>
    </div>
  );
}