import { useState, useEffect } from 'react';
import { Shield, Check, Copy, Download, AlertTriangle, RefreshCw, Eye, EyeOff, Smartphone, Lock } from 'lucide-react';
import { Button } from '../../components/atoms/button';
import { Input } from '../../components/atoms/input';
import { Card } from '../../components/molecules/card';
import { Modal } from '../../components/molecules/modal';
import { Skeleton } from '../../components/atoms/skeleton';
import apiClient from '../../api/client';
import toast from 'react-hot-toast';
import type { TwoFactorStatus, TwoFactorSetupResponse, TwoFactorConfirmResponse } from '../../types';

type SetupStep = 'idle' | 'qr' | 'verify' | 'recovery-codes' | 'active';

export function SecurityPage() {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<TwoFactorStatus | null>(null);
  const [setupStep, setSetupStep] = useState<SetupStep>('idle');
  const [setupData, setSetupData] = useState<TwoFactorSetupResponse | null>(null);
  const [confirmCode, setConfirmCode] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [codesRevealed, setCodesRevealed] = useState(false);
  const [codesSaved, setCodesSaved] = useState(false);

  // Disable modal
  const [disableOpen, setDisableOpen] = useState(false);
  const [disablePassword, setDisablePassword] = useState('');
  const [disableCode, setDisableCode] = useState('');
  const [disabling, setDisabling] = useState(false);

  // Regenerate modal
  const [regenerateOpen, setRegenerateOpen] = useState(false);
  const [regenerateCode, setRegenerateCode] = useState('');
  const [regenerating, setRegenerating] = useState(false);
  const [newCodes, setNewCodes] = useState<string[]>([]);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<TwoFactorStatus>('/auth/2fa/status/');
      setStatus(data);
      setSetupStep(data.totp_enabled ? 'active' : 'idle');
    } catch {
      toast.error('Failed to load 2FA status.');
    } finally {
      setLoading(false);
    }
  };

  const handleStartSetup = async () => {
    try {
      const { data } = await apiClient.post<TwoFactorSetupResponse>('/auth/2fa/setup/');
      setSetupData(data);
      setSetupStep('qr');
      setConfirmCode('');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to start 2FA setup.');
    }
  };

  const handleConfirmCode = async () => {
    if (!confirmCode.trim() || confirmCode.length !== 6) {
      toast.error('Please enter a 6-digit code.');
      return;
    }
    try {
      const { data } = await apiClient.post<TwoFactorConfirmResponse>('/auth/2fa/confirm/', {
        code: confirmCode,
      });
      setRecoveryCodes(data.recovery_codes);
      setCodesRevealed(false);
      setCodesSaved(false);
      setSetupStep('recovery-codes');
    } catch (err: any) {
      toast.error(err?.response?.data?.code?.[0] || 'Invalid code. Please try again.');
    }
  };

  const handleFinishSetup = () => {
    setSetupStep('active');
    setStatus((prev) => prev ? { ...prev, totp_enabled: true, has_recovery_codes: true, remaining_recovery_codes: 10 } : null);
    toast.success('Two-factor authentication enabled.');
  };

  const handleDisable = async () => {
    if (!disablePassword || !disableCode) {
      toast.error('Please enter your password and a TOTP code.');
      return;
    }
    setDisabling(true);
    try {
      await apiClient.post('/auth/2fa/disable/', {
        password: disablePassword,
        code: disableCode,
      });
      setStatus((prev) => prev ? { ...prev, totp_enabled: false, has_recovery_codes: false, remaining_recovery_codes: 0 } : null);
      setSetupStep('idle');
      setDisableOpen(false);
      setDisablePassword('');
      setDisableCode('');
      toast.success('Two-factor authentication disabled.');
    } catch (err: any) {
      toast.error(err?.response?.data?.code?.[0] || err?.response?.data?.password?.[0] || 'Failed to disable 2FA.');
    } finally {
      setDisabling(false);
    }
  };

  const handleRegenerate = async () => {
    if (!regenerateCode.trim() || regenerateCode.length !== 6) {
      toast.error('Please enter a valid 6-digit TOTP code.');
      return;
    }
    setRegenerating(true);
    try {
      const { data } = await apiClient.post('/auth/2fa/recovery-codes/regenerate/', {
        code: regenerateCode,
      });
      setNewCodes(data.recovery_codes);
      setCodesRevealed(false);
      setCodesSaved(false);
    } catch (err: any) {
      toast.error(err?.response?.data?.code?.[0] || 'Invalid TOTP code.');
    } finally {
      setRegenerating(false);
    }
  };

  const copyCodes = (codes: string[]) => {
    navigator.clipboard.writeText(codes.join('\n')).then(() => {
      toast.success('Recovery codes copied to clipboard.');
    });
  };

  const downloadCodes = (codes: string[]) => {
    const blob = new Blob([codes.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'frontiercrm-recovery-codes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton width="200px" height={24} />
        <Skeleton width="100%" height={100} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div>
        <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
          Security Settings
        </h3>
        <p className="text-sm text-text-secondary dark:text-dark-text-secondary mt-1">
          Manage two-factor authentication and security preferences.
        </p>
      </div>

      {/* ── 2FA Section ── */}
      <Card padding="lg" className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100 dark:bg-brand-900/30">
              <Shield className="h-5 w-5 text-brand-600 dark:text-brand-400" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">
                Two-Factor Authentication
              </h4>
              <p className="text-xs text-text-secondary dark:text-dark-text-secondary mt-0.5">
                {setupStep === 'active' || status?.totp_enabled
                  ? 'Your account is protected with 2FA'
                  : 'Add an extra layer of security to your account'}
              </p>
            </div>
          </div>
          {setupStep === 'active' || status?.totp_enabled ? (
            <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 px-2.5 py-1 rounded-full">
              <Check className="h-3.5 w-3.5" />
              Enabled
            </span>
          ) : null}
        </div>

        {/* ── Idle state (not set up) ── */}
        {setupStep === 'idle' && !status?.totp_enabled && (
          <div className="pt-2">
            <Button onClick={handleStartSetup} icon={<Smartphone className="h-4 w-4" />}>
              Enable Two-Factor Authentication
            </Button>
          </div>
        )}

        {/* ── QR Code Step ── */}
        {setupStep === 'qr' && setupData && (
          <div className="space-y-4 pt-2">
            <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
              Scan this QR code with your authenticator app (Google Authenticator, Authy, 1Password, etc.),
              or enter the secret key manually.
            </p>

            {/* QR Code */}
            <div className="flex justify-center">
              <div className="bg-white p-4 rounded-xl border border-border dark:border-dark-border">
                <img
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(setupData.provisioning_uri)}`}
                  alt="QR Code for 2FA setup"
                  className="h-48 w-48"
                  onError={(e) => {
                    // Fallback: render provisioning URI as text
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              </div>
            </div>

            {/* Manual entry */}
            <div className="bg-surface-secondary dark:bg-dark-surface-secondary rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary mb-1">
                    Secret key (manual entry)
                  </p>
                  <code className="text-sm font-mono text-text-primary dark:text-dark-text-primary select-all">
                    {setupData.secret}
                  </code>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(setupData.secret);
                    toast.success('Secret key copied.');
                  }}
                  className="p-2 rounded-lg hover:bg-surface dark:hover:bg-dark-surface text-text-secondary hover:text-text-primary transition-colors"
                >
                  <Copy className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Verify code */}
            <div className="space-y-3 pt-2">
              <p className="text-sm font-medium text-text-primary dark:text-dark-text-primary">
                Verify the code from your authenticator app:
              </p>
              <div className="flex gap-3">
                <Input
                  placeholder="000000"
                  value={confirmCode}
                  onChange={(e) => {
                    const val = e.target.value.replace(/\D/g, '').slice(0, 6);
                    setConfirmCode(val);
                  }}
                  className="max-w-[160px] text-center text-lg tracking-widest"
                  inputMode="numeric"
                  maxLength={6}
                />
                <Button onClick={handleConfirmCode} disabled={confirmCode.length !== 6}>
                  Verify & Enable
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ── Save Recovery Codes Step ── */}
        {setupStep === 'recovery-codes' && recoveryCodes.length > 0 && (
          <div className="space-y-4 pt-2">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
              <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  Save these recovery codes
                </p>
                <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                  Each code can be used once to access your account if you lose your authenticator device.
                  Store them somewhere safe (password manager, safe, etc.).
                </p>
              </div>
            </div>

            {/* Codes list */}
            <div className="relative">
              <div className="bg-surface-secondary dark:bg-dark-surface-secondary rounded-lg p-4 font-mono text-sm">
                <div className="space-y-1.5">
                  {recoveryCodes.map((code, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-text-tertiary dark:text-dark-text-tertiary w-6 text-right text-xs">
                        {i + 1}.
                      </span>
                      <span className={codesRevealed ? 'text-text-primary dark:text-dark-text-primary' : 'text-text-primary dark:text-dark-text-primary tracking-widest'}>
                        {codesRevealed ? code : '••••-••••'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setCodesRevealed(!codesRevealed)}
                className="absolute top-2 right-2 p-1.5 rounded-lg hover:bg-surface dark:hover:bg-dark-surface text-text-secondary hover:text-text-primary transition-colors"
              >
                {codesRevealed ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>

            {/* Action buttons */}
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" icon={<Copy className="h-4 w-4" />} onClick={() => copyCodes(recoveryCodes)}>
                Copy
              </Button>
              <Button variant="outline" size="sm" icon={<Download className="h-4 w-4" />} onClick={() => downloadCodes(recoveryCodes)}>
                Download
              </Button>
            </div>

            {/* Confirm checkbox */}
            <label className="flex items-start gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={codesSaved}
                onChange={(e) => setCodesSaved(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 dark:border-slate-600 text-brand-600 focus:ring-brand-500"
              />
              <span className="text-sm text-text-secondary dark:text-dark-text-secondary">
                I have saved my recovery codes in a safe place
              </span>
            </label>

            <Button onClick={handleFinishSetup} disabled={!codesSaved}>
              Continue
            </Button>
          </div>
        )}

        {/* ── Active State ── */}
        {(setupStep === 'active' || status?.totp_enabled) && setupStep !== 'recovery-codes' && (
          <div className="space-y-4 pt-2">
            {/* Recovery codes status */}
            <div className="bg-surface-secondary dark:bg-dark-surface-secondary rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="h-4 w-4 text-text-secondary dark:text-dark-text-secondary" />
                  <div>
                    <p className="text-sm font-medium text-text-primary dark:text-dark-text-primary">
                      Recovery Codes
                    </p>
                    <p className="text-xs text-text-secondary dark:text-dark-text-secondary mt-0.5">
                      {status?.remaining_recovery_codes ?? 0} of 10 remaining
                    </p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  icon={<RefreshCw className="h-4 w-4" />}
                  onClick={() => {
                    setRegenerateOpen(true);
                    setRegenerateCode('');
                    setNewCodes([]);
                  }}
                >
                  Regenerate
                </Button>
              </div>
            </div>

            {/* Disable button */}
            <Button
              variant="secondary"
              onClick={() => {
                setDisableOpen(true);
                setDisablePassword('');
                setDisableCode('');
              }}
            >
              Disable Two-Factor Authentication
            </Button>

            {/* Tenant enforcement notice */}
            {status?.tenant_requires_2fa && (
              <div className="flex items-start gap-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                <Shield className="h-4 w-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                <p className="text-xs text-blue-700 dark:text-blue-300">
                  2FA is required by your organization. You cannot disable it while this policy is active.
                </p>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* ── Disable Modal ── */}
      <Modal
        open={disableOpen}
        onClose={() => setDisableOpen(false)}
        title="Disable Two-Factor Authentication"
        size="sm"
        footer={
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setDisableOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleDisable}
              loading={disabling}
              disabled={!disablePassword || !disableCode}
              variant="secondary"
            >
              Disable 2FA
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
            Disabling two-factor authentication reduces your account security.
            Please verify your identity to continue.
          </p>
          <Input
            label="Current Password"
            type="password"
            value={disablePassword}
            onChange={(e) => setDisablePassword(e.target.value)}
            placeholder="Enter your password"
            required
          />
          <Input
            label="Authenticator Code"
            placeholder="000000"
            value={disableCode}
            onChange={(e) => {
              const val = e.target.value.replace(/\D/g, '').slice(0, 6);
              setDisableCode(val);
            }}
            helperText="Or enter a recovery code"
            inputMode="numeric"
            maxLength={6}
            required
          />
        </div>
      </Modal>

      {/* ── Regenerate Modal ── */}
      <Modal
        open={regenerateOpen}
        onClose={() => {
          if (newCodes.length === 0) setRegenerateOpen(false);
        }}
        title="Regenerate Recovery Codes"
        size="sm"
        footer={
          newCodes.length > 0 ? (
            <Button onClick={() => { setRegenerateOpen(false); setNewCodes([]); fetchStatus(); }}>
              Done
            </Button>
          ) : (
            <div className="flex gap-3">
              <Button variant="secondary" onClick={() => setRegenerateOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleRegenerate}
                loading={regenerating}
                disabled={regenerateCode.length !== 6}
              >
                Generate New Codes
              </Button>
            </div>
          )
        }
      >
        {newCodes.length === 0 ? (
          <div className="space-y-4">
            <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
              This will invalidate all existing recovery codes and generate 10 new ones.
              Enter your current TOTP code to authorize.
            </p>
            <Input
              label="Authenticator Code"
              placeholder="000000"
              value={regenerateCode}
              onChange={(e) => {
                const val = e.target.value.replace(/\D/g, '').slice(0, 6);
                setRegenerateCode(val);
              }}
              inputMode="numeric"
              maxLength={6}
              required
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
              <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  New recovery codes generated
                </p>
                <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                  Your old codes are no longer valid. Save these new codes.
                </p>
              </div>
            </div>

            <div className="bg-surface-secondary dark:bg-dark-surface-secondary rounded-lg p-4 font-mono text-sm">
              <div className="space-y-1.5">
                {newCodes.map((code, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-text-tertiary dark:text-dark-text-tertiary w-6 text-right text-xs">{i + 1}.</span>
                    <span>{code}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" icon={<Copy className="h-4 w-4" />} onClick={() => copyCodes(newCodes)}>
                Copy
              </Button>
              <Button variant="outline" size="sm" icon={<Download className="h-4 w-4" />} onClick={() => downloadCodes(newCodes)}>
                Download
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
