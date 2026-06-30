import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// ── Mock react-router-dom ─────────────────────────────────────────────

let mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...(actual as any),
    useNavigate: () => mockNavigate,
    useSearchParams: () => [new URLSearchParams('')],
  };
});

// ── Mock lucide-react icons ───────────────────────────────────────────

vi.mock('lucide-react', () => ({
  Building2: () => <span data-testid="icon-building">B</span>,
  UserPlus: () => <span data-testid="icon-userplus">U</span>,
  Upload: () => <span data-testid="icon-upload">Up</span>,
  Mail: () => <span data-testid="icon-mail">M</span>,
  GitBranch: () => <span data-testid="icon-gitbranch">G</span>,
  Check: () => <span data-testid="icon-check">✓</span>,
  ArrowRight: () => <span data-testid="icon-arrowright">→</span>,
  ArrowLeft: () => <span data-testid="icon-arrowleft">←</span>,
  X: () => <span data-testid="icon-x">×</span>,
  Rocket: () => <span data-testid="icon-rocket">R</span>,
  Users: () => <span>Users</span>,
  Puzzle: () => <span>Puzzle</span>,
  AlertCircle: () => <span>!</span>,
  MessageSquare: () => <span>Chat</span>,
  Video: () => <span>Video</span>,
  Plus: () => <span>+</span>,
  LogIn: () => <span>Login</span>,
  User: () => <span>User</span>,
}));

// ── Mock UI components ────────────────────────────────────────────────

vi.mock('../../components/atoms/button', () => ({
  Button: ({ children, loading, onClick, disabled, ...props }: any) => (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      data-loading={loading ? 'true' : 'false'}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </button>
  ),
}));

vi.mock('../../components/atoms/input', () => ({
  Input: ({ label, value, onChange, placeholder, ...props }: any) => (
    <div>
      {label && <label>{label}</label>}
      <input
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        {...props}
      />
    </div>
  ),
}));

vi.mock('../../components/atoms/select', () => ({
  Select: ({ label, value, onChange, children, ...props }: any) => (
    <div>
      {label && <label>{label}</label>}
      <select value={value} onChange={onChange} data-testid="select" {...props}>
        {children}
      </select>
    </div>
  ),
}));

vi.mock('../../components/ui/spinner', () => ({
  Spinner: () => <div data-testid="spinner">Loading...</div>,
}));

// ── Component under test imports ──────────────────────────────────────

import { StepIndicator } from '../../pages/onboarding/components/StepIndicator';
import { NavigationButtons } from '../../pages/onboarding/components/NavigationButtons';
import { OnboardingStep } from '../../pages/onboarding/components/OnboardingStep';
import { DoneStep } from '../../pages/onboarding/components/steps/DoneStep';
import { CompanySetupStep } from '../../pages/onboarding/components/steps/CompanySetupStep';
import { PipelineSetupStep } from '../../pages/onboarding/components/steps/PipelineSetupStep';
import { ConnectEmailStep } from '../../pages/onboarding/components/steps/ConnectEmailStep';
import { InviteTeamStep } from '../../pages/onboarding/components/steps/InviteTeamStep';
import { ImportDataStep } from '../../pages/onboarding/components/steps/ImportDataStep';
import type { OnboardingStatus } from '../../types';

// ══════════════════════════════════════════════════════════════════════
// StepIndicator
// ══════════════════════════════════════════════════════════════════════

describe('StepIndicator', () => {
  const defaultProps = {
    currentStep: 0,
    completedSteps: new Set<string>(),
    skippedSteps: [] as string[],
    onStepClick: vi.fn(),
  };

  it('renders all 5 onboarding steps', () => {
    render(<StepIndicator {...defaultProps} />);
    expect(screen.getByText('Company')).toBeInTheDocument();
    expect(screen.getByText('Invite')).toBeInTheDocument();
    expect(screen.getByText('Import')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Pipeline')).toBeInTheDocument();
  });

  it('marks current step with brand ring', () => {
    render(<StepIndicator {...defaultProps} currentStep={2} />);
    const allButtons = screen.getAllByRole('button');
    expect(allButtons[2].className).toContain('ring-2');
  });

  it('shows checkmark for completed steps', () => {
    const completed = new Set(['company', 'invite']);
    render(<StepIndicator {...defaultProps} completedSteps={completed} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons[0].textContent).toBe('✓');
    expect(buttons[1].textContent).toBe('✓');
    expect(buttons[2].textContent).toBe('3');
  });

  it('shows strikethrough for skipped steps', () => {
    render(<StepIndicator {...defaultProps} skippedSteps={['import']} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons[2].className).toContain('line-through');
  });

  it('calls onStepClick when clicking a completed step', () => {
    const onStepClick = vi.fn();
    const completed = new Set(['company']);
    render(
      <StepIndicator
        {...defaultProps}
        completedSteps={completed}
        onStepClick={onStepClick}
      />,
    );
    fireEvent.click(screen.getAllByRole('button')[0]);
    expect(onStepClick).toHaveBeenCalledWith(0);
  });
});

// ══════════════════════════════════════════════════════════════════════
// NavigationButtons
// ══════════════════════════════════════════════════════════════════════

describe('NavigationButtons', () => {
  const defaultProps = {
    currentStep: 0,
    totalSteps: 6,
    onBack: vi.fn(),
    onNext: vi.fn(),
    onSkip: vi.fn(),
    onFinish: vi.fn(),
    isLastStep: false,
  };

  it('hides Back button on first step', () => {
    render(<NavigationButtons {...defaultProps} currentStep={0} />);
    expect(screen.queryByText(/Back/)).not.toBeInTheDocument();
  });

  it('shows Back button after first step', () => {
    render(<NavigationButtons {...defaultProps} currentStep={2} />);
    expect(screen.getByText(/Back/)).toBeInTheDocument();
  });

  it('shows Skip link on every step', () => {
    render(<NavigationButtons {...defaultProps} currentStep={0} />);
    expect(screen.getByText('Skip')).toBeInTheDocument();
  });

  it('shows Go to Dashboard button on last step', () => {
    render(<NavigationButtons {...defaultProps} isLastStep={true} />);
    expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();
    expect(screen.queryByText(/Continue/)).not.toBeInTheDocument();
  });

  it('shows Continue button on non-last steps', () => {
    render(<NavigationButtons {...defaultProps} isLastStep={false} />);
    expect(screen.getByText(/Continue/)).toBeInTheDocument();
    expect(screen.queryByText('Go to Dashboard')).not.toBeInTheDocument();
  });

  it('calls onNext when Continue is clicked', () => {
    const onNext = vi.fn();
    render(<NavigationButtons {...defaultProps} isLastStep={false} onNext={onNext} />);
    fireEvent.click(screen.getByText(/Continue/));
    expect(onNext).toHaveBeenCalledOnce();
  });

  it('calls onFinish when Go to Dashboard is clicked', () => {
    const onFinish = vi.fn();
    render(<NavigationButtons {...defaultProps} isLastStep={true} onFinish={onFinish} />);
    fireEvent.click(screen.getByText('Go to Dashboard'));
    expect(onFinish).toHaveBeenCalledOnce();
  });

  it('calls onSkip when Skip is clicked', () => {
    const onSkip = vi.fn();
    render(<NavigationButtons {...defaultProps} onSkip={onSkip} />);
    fireEvent.click(screen.getByText('Skip'));
    expect(onSkip).toHaveBeenCalledOnce();
  });

  it('disables buttons while loading', () => {
    render(<NavigationButtons {...defaultProps} loading={true} />);
    expect(screen.getByRole('button', { name: /loading/i })).toBeDisabled();
  });

  it('shows custom skip label', () => {
    render(
      <NavigationButtons
        {...defaultProps}
        skipLabel={"Skip — I'll import later"}
      />,
    );
    expect(screen.getByText("Skip — I'll import later")).toBeInTheDocument();
  });
});

// ══════════════════════════════════════════════════════════════════════
// CompanySetupStep
// ══════════════════════════════════════════════════════════════════════

describe('CompanySetupStep', () => {
  const defaultProps = {
    tenantName: '',
    tenantIndustry: '',
    tenantLogoUrl: '',
    onDone: vi.fn(),
    onSkip: vi.fn(),
  };

  const renderComponent = (overrides = {}) =>
    render(
      <BrowserRouter>
        <CompanySetupStep {...defaultProps} {...overrides} />
      </BrowserRouter>,
    );

  it('renders the form with company name and industry', () => {
    renderComponent();
    expect(screen.getByText('Set up your company')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g. Acme Corp')).toBeInTheDocument();
    expect(screen.getByTestId('select')).toBeInTheDocument();
  });

  it('pre-fills company name and industry from props', () => {
    renderComponent({ tenantName: 'Acme Corp', tenantIndustry: 'technology' });
    expect(screen.getByPlaceholderText('e.g. Acme Corp')).toHaveValue('Acme Corp');
    expect(screen.getByTestId('select')).toHaveValue('technology');
  });

  it('calls onDone with company data on Save & Continue', () => {
    const onDone = vi.fn().mockResolvedValue(undefined);
    renderComponent({ onDone, tenantName: 'Acme', tenantIndustry: 'tech' });

    fireEvent.click(screen.getByText(/Save.*Continue/));
    expect(onDone).toHaveBeenCalledWith({
      company: { name: 'Acme', industry: 'tech' },
      company_done: true,
    });
  });

  it('calls onSkip when Skip is clicked', () => {
    const onSkip = vi.fn();
    renderComponent({ onSkip });
    fireEvent.click(screen.getByText('Skip'));
    expect(onSkip).toHaveBeenCalledOnce();
  });
});

// ── Mock apiClient ────────────────────────────────────────────────────

const mockApiGet = vi.fn();
const mockApiPost = vi.fn();
vi.mock('../../api/client', () => ({
  default: {
    get: (...args: any[]) => mockApiGet(...args),
    post: (...args: any[]) => mockApiPost(...args),
    patch: (...args: any[]) => mockApiPost(...args),
  },
}));

// ── Mock useOnboarding hook ────────────────────────────────────────────

const mockFetchStatus = vi.fn();
const mockUpdateProgress = vi.fn();
vi.mock('../../pages/onboarding/hooks/useOnboarding', () => ({
  useOnboarding: () => ({
    status: null,
    loading: false,
    error: null,
    fetchStatus: mockFetchStatus,
    updateProgress: mockUpdateProgress,
  }),
}));

// ══════════════════════════════════════════════════════════════════════
// OnboardingStep (base layout component)
// ══════════════════════════════════════════════════════════════════════

describe('OnboardingStep', () => {
  const defaultProps = {
    currentStep: 0,
    totalSteps: 6,
    title: 'Test Step',
    subtitle: 'A test step description',
    children: <div data-testid="step-content">Step content here</div>,
  };

  it('renders title and subtitle', () => {
    render(<OnboardingStep {...defaultProps} />);
    expect(screen.getByText('Test Step')).toBeInTheDocument();
    expect(screen.getByText('A test step description')).toBeInTheDocument();
  });

  it('renders children in the content area', () => {
    render(<OnboardingStep {...defaultProps} />);
    expect(screen.getByTestId('step-content')).toHaveTextContent(
      'Step content here',
    );
  });

  it('renders NavigationButtons with correct currentStep', () => {
    render(
      <OnboardingStep {...defaultProps} currentStep={2} totalSteps={6} />,
    );
    // Back button visible because currentStep > 0
    expect(screen.getByText(/Back/)).toBeInTheDocument();
  });

  it('passes onBack callback when provided', () => {
    const onBack = vi.fn();
    render(
      <OnboardingStep
        {...defaultProps}
        currentStep={2}
        onBack={onBack}
      />,
    );
    fireEvent.click(screen.getByText(/Back/));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it('shows Go to Dashboard when isLastStep is true', () => {
    render(<OnboardingStep {...defaultProps} isLastStep={true} />);
    expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();
  });

  it('shows Continue on non-last steps', () => {
    render(<OnboardingStep {...defaultProps} isLastStep={false} />);
    expect(screen.getByText(/Continue/)).toBeInTheDocument();
  });

  it('calls onSkip when Skip is clicked', () => {
    const onSkip = vi.fn();
    render(<OnboardingStep {...defaultProps} onSkip={onSkip} />);
    fireEvent.click(screen.getByText('Skip'));
    expect(onSkip).toHaveBeenCalledOnce();
  });

  it('renders custom skip label', () => {
    render(
      <OnboardingStep
        {...defaultProps}
        skipLabel={"Skip — I'll do it later"}
      />,
    );
    expect(
      screen.getByText("Skip — I'll do it later"),
    ).toBeInTheDocument();
  });
});

// ══════════════════════════════════════════════════════════════════════
// DoneStep
// ══════════════════════════════════════════════════════════════════════

describe('DoneStep', () => {
  const onFinish = vi.fn();
  const defaultStatus: OnboardingStatus = {
    is_onboarded: false,
    company_done: true,
    invite_done: true,
    import_done: true,
    email_done: true,
    pipeline_done: true,
    skipped_steps: [],
    tenant: { name: 'Acme', logo_url: '', industry: 'tech' },
  };

  it('renders "You\'re all set!" heading', () => {
    render(<DoneStep status={defaultStatus} onFinish={onFinish} loading={false} />);
    expect(screen.getByText("You're all set!")).toBeInTheDocument();
  });

  it('shows "All steps completed" when nothing was skipped', () => {
    render(<DoneStep status={defaultStatus} onFinish={onFinish} loading={false} />);
    expect(screen.getByText('🚀 All steps completed')).toBeInTheDocument();
  });

  it('shows skipped count when steps were skipped', () => {
    const statusWithSkips: OnboardingStatus = {
      ...defaultStatus,
      skipped_steps: ['import'],
    };
    render(
      <DoneStep status={statusWithSkips} onFinish={onFinish} loading={false} />,
    );
    expect(screen.getByText(/1 step skipped/)).toBeInTheDocument();
  });

  it('shows plural skipped count for multiple skips', () => {
    const statusWithSkips: OnboardingStatus = {
      ...defaultStatus,
      skipped_steps: ['import', 'email'],
    };
    render(
      <DoneStep status={statusWithSkips} onFinish={onFinish} loading={false} />,
    );
    expect(screen.getByText(/2 steps skipped/)).toBeInTheDocument();
  });

  it('calls onFinish when Go to Dashboard is clicked', () => {
    const finish = vi.fn();
    render(<DoneStep status={defaultStatus} onFinish={finish} loading={false} />);
    fireEvent.click(screen.getByText(/Go to Dashboard/));
    expect(finish).toHaveBeenCalledOnce();
  });

  it('disables button when loading', () => {
    render(<DoneStep status={defaultStatus} onFinish={onFinish} loading={true} />);
    expect(screen.getByRole('button', { name: /loading/i })).toBeDisabled();
  });
});

// ══════════════════════════════════════════════════════════════════════
// PipelineSetupStep
// ══════════════════════════════════════════════════════════════════════

describe('PipelineSetupStep', () => {
  const defaultProps = { onDone: vi.fn(), onSkip: vi.fn() };

  it('renders all 4 pipeline template options', () => {
    render(<PipelineSetupStep {...defaultProps} />);
    expect(screen.getByText('Sales Pipeline')).toBeInTheDocument();
    expect(screen.getByText('SaaS Sales Pipeline')).toBeInTheDocument();
    expect(screen.getByText('Recruitment Pipeline')).toBeInTheDocument();
    expect(screen.getByText('Custom Pipeline')).toBeInTheDocument();
  });

  it('renders stage counts for each template', () => {
    render(<PipelineSetupStep {...defaultProps} />);
    // Sales and Recruiting both have 5 stages
    expect(screen.getAllByText(/5 stages/)).toHaveLength(2);
    expect(screen.getByText(/4 stages/)).toBeInTheDocument();
    expect(screen.getByText(/3 stages/)).toBeInTheDocument();
  });

  it('shows Continue button by default', () => {
    render(<PipelineSetupStep {...defaultProps} />);
    expect(screen.getByText(/Continue/)).toBeInTheDocument();
  });

  it('calls onSkip when Skip is clicked', () => {
    const onSkip = vi.fn();
    render(<PipelineSetupStep {...defaultProps} onSkip={onSkip} />);
    fireEvent.click(screen.getByText('Skip'));
    expect(onSkip).toHaveBeenCalledOnce();
  });
});

// ══════════════════════════════════════════════════════════════════════
// ConnectEmailStep
// ══════════════════════════════════════════════════════════════════════

describe('ConnectEmailStep', () => {
  const defaultProps = { onDone: vi.fn(), onSkip: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "Connect your email" heading', () => {
    render(<ConnectEmailStep {...defaultProps} />);
    expect(screen.getByText('Connect your email')).toBeInTheDocument();
  });

  it('renders Connect Gmail button when email not connected', () => {
    render(<ConnectEmailStep {...defaultProps} />);
    expect(screen.getByText('Connect Gmail')).toBeInTheDocument();
  });

  it('renders Skip button with custom label', () => {
    render(<ConnectEmailStep {...defaultProps} />);
    expect(
      screen.getByText("Skip — I'll connect later"),
    ).toBeInTheDocument();
  });

  it('calls onSkip when Skip is clicked', () => {
    const onSkip = vi.fn();
    render(<ConnectEmailStep {...defaultProps} onSkip={onSkip} />);
    fireEvent.click(screen.getByText("Skip — I'll connect later"));
    expect(onSkip).toHaveBeenCalledOnce();
  });

  it('renders Continue button', () => {
    render(<ConnectEmailStep {...defaultProps} />);
    expect(screen.getByText(/Continue/)).toBeInTheDocument();
  });
});

// ══════════════════════════════════════════════════════════════════════
// InviteTeamStep
// ══════════════════════════════════════════════════════════════════════

describe('InviteTeamStep', () => {
  const defaultProps = { onDone: vi.fn(), onSkip: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "Invite your team" heading', () => {
    render(<InviteTeamStep {...defaultProps} />);
    expect(screen.getByText('Invite your team')).toBeInTheDocument();
  });

  it('renders email input and Add button', () => {
    render(<InviteTeamStep {...defaultProps} />);
    expect(
      screen.getByPlaceholderText('colleague@company.com'),
    ).toBeInTheDocument();
    expect(screen.getByText('Add')).toBeInTheDocument();
  });

  it('renders Skip button', () => {
    render(<InviteTeamStep {...defaultProps} />);
    expect(screen.getByText('Skip')).toBeInTheDocument();
  });

  it('calls onSkip when Skip is clicked', () => {
    const onSkip = vi.fn();
    render(<InviteTeamStep {...defaultProps} onSkip={onSkip} />);
    fireEvent.click(screen.getByText('Skip'));
    expect(onSkip).toHaveBeenCalledOnce();
  });

  it('renders Continue button', () => {
    render(<InviteTeamStep {...defaultProps} />);
    expect(screen.getByText(/Continue/)).toBeInTheDocument();
  });
});

// ══════════════════════════════════════════════════════════════════════
// ImportDataStep
// ══════════════════════════════════════════════════════════════════════

describe('ImportDataStep', () => {
  const defaultProps = { onDone: vi.fn(), onSkip: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "Import your data" heading', () => {
    render(<ImportDataStep {...defaultProps} />);
    expect(screen.getByText('Import your data')).toBeInTheDocument();
  });

  it('renders Import CSV button', () => {
    render(<ImportDataStep {...defaultProps} />);
    expect(screen.getByText('Import CSV')).toBeInTheDocument();
  });

  it('renders Skip button with custom label', () => {
    render(<ImportDataStep {...defaultProps} />);
    expect(
      screen.getByText("Skip — I'll import later"),
    ).toBeInTheDocument();
  });

  it('calls onSkip when Skip is clicked', () => {
    const onSkip = vi.fn();
    render(<ImportDataStep {...defaultProps} onSkip={onSkip} />);
    fireEvent.click(screen.getByText("Skip — I'll import later"));
    expect(onSkip).toHaveBeenCalledOnce();
  });

  it('renders Continue button', () => {
    render(<ImportDataStep {...defaultProps} />);
    expect(screen.getByText(/Continue/)).toBeInTheDocument();
  });
});