import React, { useState } from 'react';
import { useAppState } from '../../contexts/StateContext';
import { Search, Sliders, X, HelpCircle, Building2, Github, Instagram, Linkedin, Mail, Home, BarChart3, Calendar } from 'lucide-react';
import GuideModal from '../Modals/GuideModal';
import PartyAnalysisModal from '../Modals/PartyAnalysisModal';
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

const ControlSidebar = ({ onGoHome, onGoAnalytics }) => {
    const {
        data,
        viewMode, setViewMode,
        colorMode, setColorMode,
        projectionMode, setProjectionMode,
        customAxis, setCustomAxis,
        isCustomProjectionAvailable,
        searchQuery, setSearchQuery,
        selectedDeputies, toggleDeputySelection, clearSelection,
        dataSource, changeDataSource, availableSources,
        selectedPeriod, setSelectedPeriod, availablePeriods
    } = useAppState();

    const [showGuide, setShowGuide] = useState(false);
    const [showPartyAnalysis, setShowPartyAnalysis] = useState(false);

    if (!data) return null;

    const clusters = data.clusters || {};

    // Get months for selected year
    const monthsForYear = selectedPeriod.year
        ? (availablePeriods?.months || [])
            .filter(m => m.startsWith(`${selectedPeriod.year}-`))
            .map(m => m.split('-')[1])
        : [];

    const handleAxisChange = (axis, value) => {
        setCustomAxis(prev => ({ ...prev, [axis]: parseInt(value) }));
    };

    const handleYearChange = (e) => {
        const year = e.target.value ? parseInt(e.target.value) : null;
        setSelectedPeriod({ year, month: null });
    };

    const handleMonthChange = (e) => {
        const month = e.target.value || null;
        setSelectedPeriod(prev => ({ ...prev, month }));
    };

    return (
        <aside id="left-panel" className="panel">
            <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2><Sliders size={18} style={{ marginRight: 8 }} /> Controlli</h2>
                {onGoHome && (
                    <button
                        onClick={onGoHome}
                        title="Torna alla Home"
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '6px 10px',
                            background: 'rgba(99, 102, 241, 0.15)',
                            border: '1px solid rgba(99, 102, 241, 0.3)',
                            borderRadius: '6px',
                            color: '#a5b4fc',
                            fontSize: '12px',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                    >
                        <Home size={14} />
                    </button>
                )}
            </div>

            <div className="panel-content">
                {/* Data Source Selector */}
                <div className="control-group">
                    <label>Fonte Dati</label>
                    <div className="toggle-group">

                        <button
                            className={`toggle-btn ${dataSource === 'senate' ? 'active' : ''}`}
                            onClick={() => changeDataSource('senate')}
                            disabled={!availableSources.includes('senate')}
                        >
                            Senato
                        </button>
                        <button
                            className={`toggle-btn ${dataSource === 'camera' ? 'active' : ''}`}
                            onClick={() => changeDataSource('camera')}
                            disabled={!availableSources.includes('camera')}
                        >
                            Camera
                        </button>
                    </div>
                </div>

                {/* Period Filter */}
                <div className="control-group">
                    <label><Calendar size={14} style={{ marginRight: 4, verticalAlign: 'middle' }} />Periodo</label>
                    <div className="period-selects">
                        <CustomDropdown
                            options={[
                                { value: '', label: 'Tutti gli anni' },
                                ...(availablePeriods?.years || []).map(year => ({
                                    value: String(year),
                                    label: String(year)
                                }))
                            ]}
                            value={selectedPeriod.year ? String(selectedPeriod.year) : ''}
                            onChange={(e) => handleYearChange({ target: { value: e.target.value } })}
                            placeholder="Tutti gli anni"
                        />
                        {selectedPeriod.year && monthsForYear.length > 0 && (
                            <CustomDropdown
                                options={[
                                    { value: '', label: "Tutto l'anno" },
                                    ...MONTHS.filter(m => monthsForYear.includes(m.value))
                                ]}
                                value={selectedPeriod.month || ''}
                                onChange={(e) => handleMonthChange({ target: { value: e.target.value } })}
                                placeholder="Tutto l'anno"
                            />
                        )}
                    </div>
                </div>

                {/* View Mode */}
                <div className="control-group">
                    <label>Visualizza</label>
                    <div className="toggle-group">
                        <button
                            className={`toggle-btn ${viewMode === 'speeches' ? 'active' : ''}`}
                            onClick={() => setViewMode('speeches')}
                        >
                            Discorsi
                        </button>
                        <button
                            className={`toggle-btn ${viewMode === 'deputies' ? 'active' : ''}`}
                            onClick={() => setViewMode('deputies')}
                        >
                            Deputati
                        </button>
                    </div>
                </div>

                {/* Color Mode */}
                <div className="control-group">
                    <label>Colora per</label>
                    <div className="toggle-group">
                        <button
                            className={`toggle-btn ${colorMode === 'cluster' ? 'active' : ''}`}
                            onClick={() => setColorMode('cluster')}
                        >
                            Cluster
                        </button>
                        <button
                            className={`toggle-btn ${colorMode === 'party' ? 'active' : ''}`}
                            onClick={() => setColorMode('party')}
                        >
                            Partito
                        </button>
                    </div>
                </div>

                {/* Projection Mode */}
                <div className="control-group">
                    <label>Proiezione</label>
                    <div className="toggle-group">
                        <button
                            className={`toggle-btn ${projectionMode === 'pca' ? 'active' : ''}`}
                            onClick={() => setProjectionMode('pca')}
                        >
                            Standard (PCA)
                        </button>
                        <button
                            className={`toggle-btn ${projectionMode === 'custom' ? 'active' : ''}`}
                            onClick={() => isCustomProjectionAvailable && setProjectionMode('custom')}
                            disabled={!isCustomProjectionAvailable}
                            title={!isCustomProjectionAvailable ? "Disponibile solo con Topic Custom" : ""}
                        >
                            Custom
                        </button>
                    </div>

                    {/* Custom Axis Selectors */}
                    {projectionMode === 'custom' && (
                        <div className="custom-axis-controls" style={{ marginTop: '10px' }}>
                            <div className="axis-selector">
                                <label>Asse X</label>
                                <select
                                    value={customAxis.x}
                                    onChange={(e) => handleAxisChange('x', e.target.value)}
                                >
                                    {Object.entries(clusters).map(([id, c]) => (
                                        <option key={`x-${id}`} value={id}>{c.label}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="axis-selector" style={{ marginTop: '5px' }}>
                                <label>Asse Y</label>
                                <select
                                    value={customAxis.y}
                                    onChange={(e) => handleAxisChange('y', e.target.value)}
                                >
                                    {Object.entries(clusters).map(([id, c]) => (
                                        <option key={`y-${id}`} value={id}>{c.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    )}
                </div>

                {/* Search */}
                <div className="control-group search-section">
                    <label>Cerca Deputato</label>
                    <div className="search-box">
                        <Search size={16} className="search-icon" />
                        <input
                            type="text"
                            placeholder="Nome cognome..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                        {/* Clear button - only for search query */}
                        {searchQuery && (
                            <button
                                onClick={() => { setSearchQuery(''); clearSelection(); }}
                                style={{
                                    position: 'absolute', right: '10px',
                                    background: 'none', border: 'none',
                                    color: 'var(--text-muted)', cursor: 'pointer'
                                }}
                            >
                                <X size={14} />
                            </button>
                        )}
                    </div>

                    {/* Search Results Dropdown */}
                    {searchQuery.length > 1 && (
                        <div className="search-results" style={{
                            marginTop: '0.5rem', maxHeight: '200px', overflowY: 'auto',
                            background: 'rgba(0,0,0,0.3)', borderRadius: '6px',
                            border: '1px solid var(--glass-border)'
                        }}>
                            {data.deputies
                                .filter(d => {
                                    const q = (searchQuery || '').toLowerCase();
                                    return (d.name || '').toLowerCase().includes(q) ||
                                        (d.party || '').toLowerCase().includes(q) ||
                                        (d.role || '').toLowerCase().includes(q);
                                })
                                .slice(0, 10) // Limit results
                                .map(d => (
                                    <div
                                        key={d.deputy}
                                        className="search-result"
                                        onClick={() => {
                                            toggleDeputySelection(d.deputy);
                                            setSearchQuery(''); // Close dropdown
                                        }}
                                        style={{
                                            padding: '8px', cursor: 'pointer',
                                            fontSize: '0.85rem', borderBottom: '1px solid rgba(255,255,255,0.05)'
                                        }}
                                        onMouseEnter={(e) => e.target.style.background = 'rgba(255,255,255,0.1)'}
                                        onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                    >
                                        <div style={{ fontWeight: '500' }}>
                                            {/* Convert ALL CAPS names to Title Case for display if from Senato */}
                                            {d.name && d.name === d.name.toUpperCase() && d.name.length > 3
                                                ? d.name.charAt(0) + d.name.slice(1).toLowerCase()
                                                : d.name}
                                        </div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            {d.party}
                                            {d.role && (
                                                <span style={{
                                                    marginLeft: '6px',
                                                    color: 'rgba(255,255,255,0.6)',
                                                    fontStyle: 'italic'
                                                }}>
                                                    • {d.role}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                ))
                            }
                            {data.deputies.filter(d => (d.name || '').toLowerCase().includes((searchQuery || '').toLowerCase())).length === 0 && (
                                <div style={{ padding: '10px', color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center' }}>
                                    Nessun risultato
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Selected Deputies - Chips */}
                {selectedDeputies.length > 0 && (
                    <div style={{ marginTop: '12px' }}>
                        <div style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '6px'
                        }}>
                            {selectedDeputies.map(deputy => {
                                const deputyName = deputy ? deputy.split(' (')[0] : deputy;
                                return (
                                    <div key={deputy} style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '4px',
                                        background: 'rgba(99, 102, 241, 0.2)',
                                        border: '1px solid rgba(99, 102, 241, 0.4)',
                                        padding: '4px 8px',
                                        borderRadius: '14px',
                                        fontSize: '11px',
                                        color: '#a5b4fc'
                                    }}>
                                        <span>{deputyName}</span>
                                        <button
                                            onClick={() => toggleDeputySelection(deputy)}
                                            style={{
                                                background: 'none',
                                                border: 'none',
                                                color: '#a5b4fc',
                                                cursor: 'pointer',
                                                padding: '0',
                                                display: 'flex',
                                                alignItems: 'center'
                                            }}
                                        >
                                            <X size={10} />
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                        <button
                            onClick={clearSelection}
                            style={{
                                marginTop: '8px',
                                background: 'none',
                                border: 'none',
                                color: 'var(--text-muted)',
                                fontSize: '11px',
                                cursor: 'pointer',
                                padding: '4px 0'
                            }}
                        >
                            Deseleziona tutti
                        </button>
                    </div>
                )}

                <hr style={{ borderColor: 'var(--glass-border)', margin: '20px 0' }} />

                {/* Guide Button */}
                <button
                    className="guide-btn"
                    onClick={() => setShowGuide(true)}
                >
                    <HelpCircle size={16} />
                    <span>Come interpretare i dati</span>
                </button>

                {/* Party Analysis Button */}
                <button
                    className="guide-btn party-analysis-btn"
                    onClick={() => setShowPartyAnalysis(true)}
                    style={{
                        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                        border: 'none',
                        color: '#fff',
                        fontWeight: '600',
                        padding: '12px 16px',
                        marginTop: '12px'
                    }}
                >
                    <Building2 size={18} />
                    <span>⚔️ Confronta Partiti</span>
                </button>

                {/* Analytics Dashboard Button */}
                {onGoAnalytics && (
                    <button
                        className="guide-btn analytics-btn"
                        onClick={onGoAnalytics}
                        style={{
                            background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                            border: 'none',
                            color: '#fff',
                            fontWeight: '600',
                            padding: '12px 16px',
                            marginTop: '8px'
                        }}
                    >
                        <BarChart3 size={18} />
                        <span>📊 Dashboard Analytics</span>
                    </button>
                )}

                {/* Credits */}
                <div className="credits-footer">
                    <div className="social-links">
                        <a href="https://github.com/WeridFire" target="_blank" rel="noopener noreferrer" title="GitHub">
                            <Github size={16} />
                        </a>
                        <a href="https://www.instagram.com/maretti_filippo/" target="_blank" rel="noopener noreferrer" title="Instagram">
                            <Instagram size={16} />
                        </a>
                        <a href="https://www.linkedin.com/in/filippo-maretti-967a092b3/" target="_blank" rel="noopener noreferrer" title="LinkedIn">
                            <Linkedin size={16} />
                        </a>
                    </div>
                </div>
            </div>

            {/* Guide Modal */}
            {showGuide && <GuideModal onClose={() => setShowGuide(false)} />}

            {/* Party Analysis Modal */}
            {showPartyAnalysis && <PartyAnalysisModal onClose={() => setShowPartyAnalysis(false)} />}
        </aside>
    );
};

export default ControlSidebar;

