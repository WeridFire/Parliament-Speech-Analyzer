import { useMemo } from 'react';
import { Select, SegmentedControl } from '../ui';
import { monthName } from '../lib/format';
import { CHAMBER_LIST } from '../data/DataProvider';

/**
 * Chamber + period controls.
 *
 * Previously duplicated: once in ControlSidebar for the map, once in
 * PeriodSelector for the dashboard, with slightly different behaviour. Both
 * now render this, bound to the URL.
 */
export function PeriodControls({
  chamber,
  availableChambers,
  onChamberChange,
  period,
  periods,
  onPeriodChange,
  className,
  compact = false,
}) {
  const yearOptions = useMemo(
    () => (periods?.years ?? []).map((y) => ({ value: String(y), label: String(y) })),
    [periods],
  );

  // Only offer months the selected year actually has data for.
  const monthOptions = useMemo(() => {
    if (!period?.year) return [];
    const prefix = `${period.year}-`;
    return (periods?.months ?? [])
      .filter((m) => m.startsWith(prefix))
      .map((m) => m.slice(5))
      .sort()
      .map((mm) => ({ value: mm, label: monthName(mm) }));
  }, [periods, period?.year]);

  return (
    <div className={className}>
      <div className="flex flex-wrap items-end gap-3">
        <SegmentedControl
          label={compact ? undefined : 'Fonte'}
          value={chamber}
          onChange={onChamberChange}
          size={compact ? 'sm' : 'md'}
          options={CHAMBER_LIST.map((c) => ({
            value: c.id,
            label: c.label,
            disabled: !availableChambers.includes(c.id),
          }))}
        />

        <Select
          label={compact ? undefined : 'Anno'}
          hideLabel={compact}
          value={period?.year ? String(period.year) : ''}
          placeholder="Tutti gli anni"
          options={yearOptions}
          className="w-36"
          onChange={(v) => onPeriodChange({ year: v ? Number(v) : null, month: null })}
        />

        <Select
          label={compact ? undefined : 'Mese'}
          hideLabel={compact}
          value={period?.month ?? ''}
          placeholder="Tutti i mesi"
          options={monthOptions}
          disabled={!period?.year || monthOptions.length === 0}
          className="w-36"
          onChange={(v) => onPeriodChange({ year: period.year, month: v || null })}
        />
      </div>
    </div>
  );
}
