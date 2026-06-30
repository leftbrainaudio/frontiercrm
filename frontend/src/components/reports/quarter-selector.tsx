interface QuarterOption {
  value: string;
  label: string;
}

interface QuarterSelectorProps {
  selected: string;
  onChange: (quarter: string) => void;
  disabled?: boolean;
}

function buildQuarterOptions(): QuarterOption[] {
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentQ = Math.floor(now.getMonth() / 3) + 1;
  const options: QuarterOption[] = [];

  for (let offset = -4; offset <= 4; offset++) {
    const adjQ = ((currentQ + offset - 1) % 12 + 12) % 12 + 1;
    const adjYear = currentYear + Math.floor((currentQ + offset - 1) / 12);

    const value = `${adjYear}-Q${adjQ}`;
    const label = offset === 0 ? `${value} (Current)` : value;
    options.push({ value, label });
  }

  return options;
}

export function QuarterSelector({ selected, onChange, disabled }: QuarterSelectorProps) {
  const options = buildQuarterOptions();

  return (
    <div>
      <label
        htmlFor="quarter-selector"
        className="block text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider mb-1.5"
      >
        Forecast Quarter
      </label>
      <select
        id="quarter-selector"
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface px-3 py-2 text-sm text-text-primary dark:text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}