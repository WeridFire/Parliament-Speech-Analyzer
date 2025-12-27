/**
 * CustomDropdown - Stylized dropdown component
 * 
 * Replaces native <select> with fully customizable styled dropdown
 */
import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import './CustomDropdown.css';

const CustomDropdown = ({
    options,
    value,
    onChange,
    placeholder = 'Seleziona...',
    className = ''
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    // Close on click outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Find current selected label
    const selectedOption = options.find(opt => opt.value === value);
    const displayLabel = selectedOption?.label || placeholder;

    const handleSelect = (optValue) => {
        onChange({ target: { value: optValue } });
        setIsOpen(false);
    };

    return (
        <div
            ref={dropdownRef}
            className={`custom-dropdown ${className} ${isOpen ? 'open' : ''}`}
        >
            <button
                type="button"
                className="dropdown-trigger"
                onClick={() => setIsOpen(!isOpen)}
            >
                <span className={!value ? 'placeholder' : ''}>
                    {displayLabel}
                </span>
                <ChevronDown size={14} className={`dropdown-arrow ${isOpen ? 'rotated' : ''}`} />
            </button>

            {isOpen && (
                <div className="dropdown-menu">
                    {options.map(option => (
                        <button
                            key={option.value}
                            type="button"
                            className={`dropdown-item ${option.value === value ? 'selected' : ''}`}
                            onClick={() => handleSelect(option.value)}
                        >
                            <span>{option.label}</span>
                            {option.value === value && <Check size={14} />}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

export default CustomDropdown;
