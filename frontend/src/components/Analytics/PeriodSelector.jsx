/**
 * PeriodSelector - Reusable component for selecting time period (year/month)
 * 
 * Used in AnalyticsDashboard to filter analytics by year and month.
 * Follows DRY principles and matches existing UI patterns.
 */
import React from 'react';
import { Calendar } from 'lucide-react';
import CustomDropdown from '../UI/CustomDropdown';

// Month names in Italian
const MONTHS = [
    { value: '01', label: 'Gennaio' },
    { value: '02', label: 'Febbraio' },
    { value: '03', label: 'Marzo' },
    { value: '04', label: 'Aprile' },
    { value: '05', label: 'Maggio' },
    { value: '06', label: 'Giugno' },
    { value: '07', label: 'Luglio' },
    { value: '08', label: 'Agosto' },
    { value: '09', label: 'Settembre' },
    { value: '10', label: 'Ottobre' },
    { value: '11', label: 'Novembre' },
    { value: '12', label: 'Dicembre' }
];

const PeriodSelector = ({
    availablePeriods,
    selectedPeriod,
    onPeriodChange
}) => {
    // Extract available years and get months for selected year
    const years = availablePeriods?.years || [];
    const allMonths = availablePeriods?.months || [];

    // Get months available for selected year
    const monthsForYear = selectedPeriod.year
        ? allMonths.filter(m => m.startsWith(`${selectedPeriod.year}-`))
            .map(m => m.split('-')[1])
        : [];

    const handleYearChange = (e) => {
        const year = e.target.value ? parseInt(e.target.value) : null;
        onPeriodChange({ year, month: null });
    };

    const handleMonthChange = (e) => {
        const month = e.target.value || null;
        onPeriodChange({
            year: selectedPeriod.year,
            month
        });
    };

    // Get label for current selection
    const getPeriodLabel = () => {
        if (!selectedPeriod.year) return 'Tutti i periodi';
        if (!selectedPeriod.month) return `Anno ${selectedPeriod.year}`;
        const monthLabel = MONTHS.find(m => m.value === selectedPeriod.month)?.label || selectedPeriod.month;
        return `${monthLabel} ${selectedPeriod.year}`;
    };

    // Build year options
    const yearOptions = [
        { value: '', label: 'Tutti gli anni' },
        ...years.map(year => ({ value: String(year), label: String(year) }))
    ];

    // Build month options
    const monthOptions = [
        { value: '', label: "Tutto l'anno" },
        ...MONTHS.filter(m => monthsForYear.includes(m.value))
    ];

    return (
        <div className="period-selector">
            <Calendar size={16} className="period-icon" />

            {/* Year Select */}
            <CustomDropdown
                options={yearOptions}
                value={selectedPeriod.year ? String(selectedPeriod.year) : ''}
                onChange={handleYearChange}
                placeholder="Tutti gli anni"
            />

            {/* Month Select - only visible when year is selected */}
            {selectedPeriod.year && monthsForYear.length > 0 && (
                <CustomDropdown
                    options={monthOptions}
                    value={selectedPeriod.month || ''}
                    onChange={handleMonthChange}
                    placeholder="Tutto l'anno"
                />
            )}

            {/* Current period badge */}
            <span className="period-badge">{getPeriodLabel()}</span>
        </div>
    );
};

export default PeriodSelector;

