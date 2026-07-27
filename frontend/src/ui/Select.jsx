import { ChevronDown } from 'lucide-react';
import { useId } from 'react';
import { cn } from '../lib/cn';

/**
 * Styled native <select>.
 *
 * Deliberately native rather than the previous div-based CustomDropdown, which
 * had no keyboard handling, no ARIA roles and no mobile affordance. A native
 * control gets all of that for free and is a fraction of the code.
 */
export function Select({
  label,
  value,
  onChange,
  options,
  placeholder,
  hideLabel = false,
  className,
  disabled,
  id: idProp,
}) {
  const autoId = useId();
  const id = idProp ?? autoId;

  return (
    <div className={cn('min-w-0', className)}>
      {label ? (
        <label
          htmlFor={id}
          className={cn(
            'mb-1.5 block text-label text-muted',
            hideLabel && 'sr-only',
          )}
        >
          {label.toUpperCase()}
        </label>
      ) : null}

      <div className="relative">
        <select
          id={id}
          value={value ?? ''}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          className={cn(
            'w-full appearance-none rounded-sm border border-rule bg-surface',
            'py-1.5 pr-8 pl-2.5 text-body text-ink',
            'transition-colors duration-150 hover:border-rule-strong',
            'disabled:cursor-not-allowed disabled:text-muted disabled:opacity-60',
          )}
        >
          {placeholder ? <option value="">{placeholder}</option> : null}
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <ChevronDown
          size={14}
          className="pointer-events-none absolute top-1/2 right-2.5 -translate-y-1/2 text-muted"
          aria-hidden="true"
        />
      </div>
    </div>
  );
}

/**
 * Two-to-four mutually exclusive options shown inline. Used for chamber,
 * view mode and colour mode — previously three separate hand-rolled
 * `.toggle-group` implementations.
 */
export function SegmentedControl({ label, value, onChange, options, className, size = 'md' }) {
  return (
    <div className={cn('min-w-0', className)}>
      {label ? <span className="mb-1.5 block text-label text-muted">{label.toUpperCase()}</span> : null}
      <div
        role="group"
        aria-label={label}
        className="inline-flex rounded-sm border border-rule bg-sunken p-0.5"
      >
        {options.map((o) => {
          const active = o.value === value;
          return (
            <button
              key={o.value}
              type="button"
              disabled={o.disabled}
              aria-pressed={active}
              onClick={() => onChange(o.value)}
              className={cn(
                'rounded-xs font-medium whitespace-nowrap transition-colors duration-150',
                size === 'sm' ? 'px-2 py-0.5 text-label' : 'px-3 py-1 text-body',
                active
                  ? 'bg-surface text-ink shadow-[0_0_0_1px_var(--rule)]'
                  : 'text-secondary hover:text-ink',
                o.disabled && 'cursor-not-allowed opacity-40 hover:text-secondary',
              )}
            >
              {o.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
