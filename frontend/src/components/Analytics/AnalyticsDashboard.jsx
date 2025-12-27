/**
 * Analytics Dashboard - Main page for advanced political analytics
 * 
 * Features 4 tabs: Identity, Relations, Temporal, Qualitative
 * Supports filtering by year and month via PeriodSelector
 */
import React, { useState, useMemo } from 'react';
import { useAppState } from '../../contexts/StateContext';
import {
    Target, Users, TrendingUp, MessageSquare,
    ArrowLeft, Loader, BarChart3
} from 'lucide-react';
import IdentityTab from './tabs/IdentityTab';
import RelationsTab from './tabs/RelationsTab';
import TemporalTab from './tabs/TemporalTab';
import QualitativeTab from './tabs/QualitativeTab';
import PeriodSelector from './PeriodSelector';
import './AnalyticsDashboard.css';

const TABS = [
    { id: 'identity', label: 'Identità', icon: Target, color: '#6366f1' },
    { id: 'relations', label: 'Relazioni', icon: Users, color: '#22c55e' },
    { id: 'temporal', label: 'Trend', icon: TrendingUp, color: '#f59e0b' },
    { id: 'qualitative', label: 'Qualità', icon: MessageSquare, color: '#ef4444' }
];

const AnalyticsDashboard = ({ onBack }) => {
    const { data, loading, dataSource, changeDataSource, availableSources } = useAppState();
    const [activeTab, setActiveTab] = useState('identity');
    const [selectedPeriod, setSelectedPeriod] = useState({ year: null, month: null });

    // Reset period when data source changes
    React.useEffect(() => {
        setSelectedPeriod({ year: null, month: null });
    }, [dataSource]);

    // Helper function to get analytics for the selected period (DRY)
    const getAnalyticsForPeriod = useMemo(() => {
        if (!data?.analytics) return null;

        const analytics = data.analytics;

        // If no period selected, use global metrics
        if (!selectedPeriod.year) {
            return analytics.global || analytics;
        }

        // If year selected but no month, use yearly metrics
        if (selectedPeriod.year && !selectedPeriod.month) {
            const yearKey = String(selectedPeriod.year);
            return analytics.by_year?.[yearKey] || analytics.global || analytics;
        }

        // If both year and month selected, use monthly metrics
        if (selectedPeriod.year && selectedPeriod.month) {
            const monthKey = `${selectedPeriod.year}-${selectedPeriod.month}`;
            return analytics.by_month?.[monthKey] || analytics.global || analytics;
        }

        return analytics.global || analytics;
    }, [data?.analytics, selectedPeriod]);

    // Get available periods from data
    const availablePeriods = useMemo(() => {
        return data?.analytics?.available_periods || { years: [], months: [] };
    }, [data?.analytics]);

    if (loading) {
        return (
            <div className="analytics-loading">
                <Loader className="animate-spin" size={48} />
                <span>Caricamento analytics...</span>
            </div>
        );
    }

    if (!data?.analytics) {
        return (
            <div className="analytics-error">
                <BarChart3 size={64} style={{ opacity: 0.3 }} />
                <h2>Analytics non disponibili</h2>
                <p>I dati analytics non sono stati trovati nel dataset.</p>
                <button className="back-btn" onClick={onBack}>
                    <ArrowLeft size={18} /> Torna alla Mappa
                </button>
            </div>
        );
    }

    const clusters = data.clusters || {};

    // Get temporal analytics (always from global since it has time series data)
    const temporalAnalytics = data.analytics.global?.temporal || data.analytics.temporal || {};

    const renderTabContent = () => {
        // Using dataSource + period as key to force re-render when either changes
        const key = `${dataSource}-${selectedPeriod.year}-${selectedPeriod.month}`;

        switch (activeTab) {
            case 'identity':
                return <IdentityTab key={key} analytics={getAnalyticsForPeriod?.identity} clusters={clusters} selectedPeriod={selectedPeriod} />;
            case 'relations':
                return <RelationsTab key={key} analytics={getAnalyticsForPeriod?.relations} clusters={clusters} selectedPeriod={selectedPeriod} />;
            case 'temporal':
                // Temporal tab always uses global temporal data (it shows time series)
                return <TemporalTab key={key} analytics={temporalAnalytics} clusters={clusters} selectedPeriod={selectedPeriod} />;
            case 'qualitative':
                return <QualitativeTab key={key} analytics={getAnalyticsForPeriod?.qualitative} clusters={clusters} selectedPeriod={selectedPeriod} />;
            default:
                return null;
        }
    };

    return (
        <div className="analytics-dashboard">
            {/* Header */}
            <header className="analytics-header">
                <div className="header-left">
                    <button className="back-btn" onClick={onBack}>
                        <ArrowLeft size={18} />
                        <span>Mappa</span>
                    </button>
                    <div className="header-title">
                        <BarChart3 size={24} />
                        <h1>Analytics Dashboard</h1>
                    </div>
                </div>

                {/* Controls: Period Selector + Data Source */}
                <div className="header-controls">
                    {/* Period Selector - hidden on Trend tab since it shows time series */}
                    {activeTab !== 'temporal' && (
                        <PeriodSelector
                            availablePeriods={availablePeriods}
                            selectedPeriod={selectedPeriod}
                            onPeriodChange={setSelectedPeriod}
                        />
                    )}

                    {/* Data Source Toggle */}
                    <div className="source-toggle">
                        <button
                            className={`source-btn ${dataSource === 'senate' ? 'active' : ''}`}
                            onClick={() => changeDataSource('senate')}
                            disabled={!availableSources.includes('senate')}
                        >
                            Senato
                        </button>
                        <button
                            className={`source-btn ${dataSource === 'camera' ? 'active' : ''}`}
                            onClick={() => changeDataSource('camera')}
                            disabled={!availableSources.includes('camera')}
                        >
                            Camera
                        </button>
                    </div>
                </div>
            </header>

            {/* Tab Navigation */}
            <nav className="analytics-tabs">
                {TABS.map(tab => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            className={`tab-btn ${isActive ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab.id)}
                            style={{
                                '--tab-color': tab.color,
                                borderColor: isActive ? tab.color : 'transparent'
                            }}
                        >
                            <Icon size={18} />
                            <span>{tab.label}</span>
                        </button>
                    );
                })}
            </nav>

            {/* Tab Content */}
            <main className="analytics-content">
                {renderTabContent()}
            </main>
        </div>
    );
};

export default AnalyticsDashboard;
