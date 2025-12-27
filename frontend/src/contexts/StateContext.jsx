import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';

const StateContext = createContext();

export const StateProvider = ({ children }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // State for data source: 'senate' or 'camera'
    const [dataSource, setDataSource] = useState('camera');

    // Filter/View State
    const [viewMode, setViewMode] = useState('speeches'); // 'speeches' | 'deputies'
    const [colorMode, setColorMode] = useState('cluster'); // 'cluster' | 'party'
    const [projectionMode, setProjectionMode] = useState('pca'); // 'pca' | 'custom'

    // Custom Axis State (default to clusters 0 and 1)
    const [customAxis, setCustomAxis] = useState({ x: 0, y: 1 });

    // Period Filter State (for semantic map)
    const [selectedPeriod, setSelectedPeriod] = useState({ year: null, month: null });

    // Selection State - MULTI-SELECT (array of deputy strings)
    const [selectedDeputies, setSelectedDeputies] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');

    // Sidebar visibility
    const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
    const [rightSidebarOpen, setRightSidebarOpen] = useState(false);

    // Toggle functions - opening one closes the other
    const toggleLeftSidebar = () => {
        setLeftSidebarOpen(prev => {
            if (!prev) setRightSidebarOpen(false);
            return !prev;
        });
    };

    const toggleRightSidebar = () => {
        setRightSidebarOpen(prev => {
            if (!prev) setLeftSidebarOpen(false);
            return !prev;
        });
    };

    // Modal State
    const [modal, setModal] = useState({ isOpen: false, type: null, data: null });

    const openModal = (type, data) => setModal({ isOpen: true, type, data });
    const closeModal = () => setModal({ isOpen: false, type: null, data: null });

    // Multi-select toggle function (max 4)
    const toggleDeputySelection = (deputy) => {
        setSelectedDeputies(prev => {
            if (prev.includes(deputy)) {
                return prev.filter(d => d !== deputy);
            } else {
                // Switch to deputies view when selecting
                setViewMode('deputies');
                // Limit to max 4 selected
                if (prev.length >= 4) {
                    // Remove oldest and add new
                    return [...prev.slice(1), deputy];
                }
                return [...prev, deputy];
            }
        });
    };

    const clearSelection = () => setSelectedDeputies([]);

    // Load Data based on dataSource
    const loadData = useCallback(async (source) => {
        setLoading(true);
        setError(null);

        // Determine which JSON file to load
        const filenameMap = {
            'combined': 'data.json',
            'senate': 'senato.json',
            'camera': 'camera.json'
        };
        const filename = filenameMap[source] || 'data.json';

        try {
            const response = await fetch(filename);
            if (!response.ok) {
                throw new Error(`Failed to load ${filename}`);
            }
            const jsonData = await response.json();
            setData(jsonData);
            setLoading(false);
        } catch (err) {
            console.error("Failed to load data:", err);
            setError(err);
            setLoading(false);
        }
    }, []);

    // Initial load
    useEffect(() => {
        loadData(dataSource);
    }, []);

    // Change data source
    const changeDataSource = useCallback((newSource) => {
        setDataSource(newSource);

        // Reset Interface State
        setSelectedDeputies([]);
        setSearchQuery('');
        setViewMode('speeches');
        setColorMode('cluster');
        setProjectionMode('pca');
        setCustomAxis({ x: 0, y: 1 });
        setSelectedPeriod({ year: null, month: null }); // Reset period filter
        closeModal();

        loadData(newSource);
    }, [loadData]);

    // Compute filtered data based on selected period
    const filteredData = useMemo(() => {
        if (!data) return null;

        // No period selected - use global data
        if (!selectedPeriod.year && !selectedPeriod.month) {
            return data;
        }

        // Get period key for lookup
        const yearKey = selectedPeriod.year ? String(selectedPeriod.year) : null;
        const monthKey = selectedPeriod.year && selectedPeriod.month
            ? `${selectedPeriod.year}-${selectedPeriod.month}`
            : null;

        // Get deputies from deputies_by_period (backend computed)
        let periodDeputies = data.deputies; // fallback to global
        if (data.deputies_by_period) {
            if (monthKey && data.deputies_by_period.by_month?.[monthKey]) {
                periodDeputies = data.deputies_by_period.by_month[monthKey];
            } else if (yearKey && data.deputies_by_period.by_year?.[yearKey]) {
                periodDeputies = data.deputies_by_period.by_year[yearKey];
            } else if (data.deputies_by_period.global) {
                periodDeputies = data.deputies_by_period.global;
            }
        }

        // Filter speeches by period
        const filterByPeriod = (speeches) => {
            if (!speeches) return speeches;

            return speeches.filter(speech => {
                if (!speech.date) return false;

                // Parse date (formats: YYYY-MM-DD, DD/MM/YYYY, etc.)
                let date;
                if (speech.date.includes('-')) {
                    // YYYY-MM-DD format
                    const parts = speech.date.split('-');
                    if (parts[0].length === 4) {
                        date = { year: parseInt(parts[0]), month: parseInt(parts[1]) };
                    } else {
                        date = { year: parseInt(parts[2]), month: parseInt(parts[1]) };
                    }
                } else if (speech.date.includes('/')) {
                    // DD/MM/YYYY format
                    const parts = speech.date.split('/');
                    date = { year: parseInt(parts[2]), month: parseInt(parts[1]) };
                } else {
                    return true; // Can't parse, include it
                }

                // Apply filters
                if (selectedPeriod.year && date.year !== selectedPeriod.year) {
                    return false;
                }
                if (selectedPeriod.month && date.month !== parseInt(selectedPeriod.month)) {
                    return false;
                }
                return true;
            });
        };

        return {
            ...data,
            speeches: filterByPeriod(data.speeches),
            deputies: periodDeputies
        };
    }, [data, selectedPeriod]);

    // Extract available periods from data - prefer backend data if available
    const availablePeriods = useMemo(() => {
        // Use backend-computed periods if available
        if (data?.deputies_by_period?.available_periods) {
            return data.deputies_by_period.available_periods;
        }

        // Fallback: compute from speeches
        if (!data?.speeches) return { years: [], months: [] };

        const yearsSet = new Set();
        const monthsSet = new Set();

        data.speeches.forEach(speech => {
            if (!speech.date) return;

            let year, month;
            if (speech.date.includes('-')) {
                const parts = speech.date.split('-');
                if (parts[0].length === 4) {
                    year = parseInt(parts[0]);
                    month = parts[1];
                } else {
                    year = parseInt(parts[2]);
                    month = parts[1];
                }
            } else if (speech.date.includes('/')) {
                const parts = speech.date.split('/');
                year = parseInt(parts[2]);
                month = parts[1].padStart(2, '0');
            }

            if (year) {
                yearsSet.add(year);
                if (month) {
                    monthsSet.add(`${year}-${month.padStart(2, '0')}`);
                }
            }
        });

        return {
            years: [...yearsSet].sort((a, b) => b - a),
            months: [...monthsSet].sort().reverse()
        };
    }, [data]);

    // Helper to check if custom projection is available
    const isCustomProjectionAvailable = data?.speeches?.[0]?.topic_scores !== undefined;

    // Check which sources are available
    const [availableSources, setAvailableSources] = useState(['camera']);

    useEffect(() => {
        // Check which data files exist
        const checkSources = async () => {
            const sources = [];

            try {
                const senateRes = await fetch('senato.json', { method: 'HEAD' });
                if (senateRes.ok) sources.push('senate');
            } catch (e) { }

            try {
                const cameraRes = await fetch('camera.json', { method: 'HEAD' });
                if (cameraRes.ok) sources.push('camera');
            } catch (e) { }

            // Default to camera if available, else senate, else empty
            if (sources.length > 0 && !sources.includes(dataSource)) {
                // If current source is not available, switch to first available
                // Prefer camera if available, otherwise just first one
                if (sources.includes('camera')) {
                    // already default
                } else {
                    setDataSource(sources[0]);
                }
            }

            setAvailableSources(sources);
        };

        checkSources();
    }, []);

    return (
        <StateContext.Provider value={{
            data,
            filteredData, // Data filtered by selectedPeriod for semantic map
            loading,
            error,
            dataSource, changeDataSource, availableSources,
            viewMode, setViewMode,
            colorMode, setColorMode,
            projectionMode, setProjectionMode,
            customAxis, setCustomAxis,
            selectedPeriod, setSelectedPeriod, availablePeriods, // Period filtering for semantic map
            selectedDeputies, setSelectedDeputies, toggleDeputySelection, clearSelection,
            searchQuery, setSearchQuery,
            leftSidebarOpen, toggleLeftSidebar,
            rightSidebarOpen, toggleRightSidebar,
            isCustomProjectionAvailable,
            modal, openModal, closeModal
        }}>
            {children}
        </StateContext.Provider>
    );
};

StateProvider.propTypes = {
    children: PropTypes.node.isRequired
};

export const useAppState = () => useContext(StateContext);
