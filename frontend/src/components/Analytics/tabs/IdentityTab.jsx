/**
 * Identity Tab - Thematic fingerprints, generalism index, distinctive keywords
 */
import React, { useState, useMemo } from 'react';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import { Target, Fingerprint, Scale, Tag } from 'lucide-react';
import NoDataMessage from '../NoDataMessage';
import WordCloud from '../../UI/WordCloud';

const Plot = createPlotlyComponent(Plotly);

const IdentityTab = ({ analytics, clusters, selectedPeriod }) => {
    const [selectedParty, setSelectedParty] = useState(null);
    const [viewMode, setViewMode] = useState('party'); // 'party' | 'deputy'

    const fingerprints = analytics?.thematic_fingerprints || {};
    const generalismData = analytics?.generalism_index || {};
    const keywords = analytics?.distinctive_keywords || {};

    // Check if we have any data
    const hasData = Object.keys(fingerprints.by_party || {}).length > 0 ||
        Object.keys(generalismData.by_party || {}).length > 0;

    // Get parties list
    const parties = useMemo(() => {
        return Object.keys(fingerprints.by_party || {}).sort();
    }, [fingerprints]);

    // Auto-select first party if none selected
    React.useEffect(() => {
        if (!selectedParty && parties.length > 0) {
            setSelectedParty(parties[0]);
        }
    }, [parties, selectedParty]);

    // Radar chart data for selected party
    const radarData = useMemo(() => {
        if (!selectedParty || !fingerprints.by_party?.[selectedParty]) return null;

        const partyData = fingerprints.by_party[selectedParty];
        const clusterLabels = Object.entries(clusters).map(([id, c]) => c.label || `Cluster ${id}`);
        const values = Object.keys(clusters).map(id => partyData[id] || 0);

        return {
            data: [{
                type: 'scatterpolar',
                r: [...values, values[0]], // Close the polygon
                theta: [...clusterLabels, clusterLabels[0]],
                fill: 'toself',
                fillcolor: 'rgba(99, 102, 241, 0.2)',
                line: { color: '#6366f1', width: 2 },
                marker: { size: 6, color: '#6366f1' },
                name: selectedParty
            }],
            layout: {
                polar: {
                    radialaxis: {
                        visible: true,
                        range: [0, 1],
                        tickfont: { size: 10, color: '#64748b' },
                        gridcolor: 'rgba(255,255,255,0.1)'
                    },
                    angularaxis: {
                        tickfont: { size: 11, color: '#94a3b8' },
                        gridcolor: 'rgba(255,255,255,0.1)'
                    },
                    bgcolor: 'transparent'
                },
                showlegend: false,
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                margin: { l: 60, r: 60, t: 40, b: 40 }
            }
        };
    }, [selectedParty, fingerprints, clusters]);

    // Top generalists and specialists
    const generalismRanking = useMemo(() => {
        const data = viewMode === 'party' ? generalismData.by_party : generalismData.by_deputy;
        if (!data) return { generalists: [], specialists: [] };

        const items = Object.entries(data)
            .map(([name, info]) => ({ name, ...info }))
            .filter(item => item.n_speeches >= 5);

        const sorted = [...items].sort((a, b) => b.score - a.score);

        return {
            generalists: sorted.slice(0, 10),
            specialists: sorted.slice(-10).reverse()
        };
    }, [generalismData, viewMode]);

    // Keywords for selected party
    const partyKeywords = selectedParty ? keywords[selectedParty] || [] : [];

    // Show no data message if period has no data
    if (!hasData && (selectedPeriod?.year || selectedPeriod?.month)) {
        return (
            <div className="analytics-tab">
                <div className="tab-header">
                    <h2><Target size={24} /> Analisi dell'Identità</h2>
                    <p>DNA politico: temi distintivi, specializzazione e vocabolario esclusivo</p>
                </div>
                <NoDataMessage featureName="l'analisi dell'identità" period={selectedPeriod} />
            </div>
        );
    }

    return (
        <div className="analytics-tab">
            <div className="tab-header">
                <h2><Target size={24} /> Analisi dell'Identità</h2>
                <p>DNA politico: temi distintivi, specializzazione e vocabolario esclusivo</p>
            </div>

            <div className="analytics-grid">
                {/* Thematic Radar */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><Fingerprint size={18} /> Radar Tematico</h3>
                        <span className="card-subtitle">Similarità semantica per cluster</span>
                    </div>

                    {/* Party Selector */}
                    <div className="party-selector">
                        {parties.map(party => (
                            <button
                                key={party}
                                className={`party-chip ${selectedParty === party ? 'selected' : ''}`}
                                onClick={() => setSelectedParty(party)}
                            >
                                {party}
                            </button>
                        ))}
                    </div>

                    <div className="card-content">
                        {radarData && (
                            <div className="chart-container">
                                <Plot
                                    data={radarData.data}
                                    layout={radarData.layout}
                                    useResizeHandler={true}
                                    style={{ width: '100%', height: '350px' }}
                                    config={{ displayModeBar: false, responsive: true }}
                                />
                            </div>
                        )}
                    </div>
                </div>

                {/* Distinctive Keywords - WordCloud */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><Tag size={18} /> Vocabolario Distintivo</h3>
                        <span className="card-subtitle">{selectedParty || 'Seleziona un partito'}</span>
                    </div>
                    <div className="card-content" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '320px' }}>
                        {partyKeywords.length > 0 ? (
                            <WordCloud
                                words={partyKeywords}
                                width={380}
                                height={300}
                                minFontSize={12}
                                maxFontSize={30}
                            />
                        ) : (
                            <div className="empty-state">
                                <Tag size={32} />
                                <p>Seleziona un partito per vedere le parole chiave</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Generalism Ranking */}
                <div className="analytics-card full-width">
                    <div className="card-header">
                        <h3><Scale size={18} /> Indice di Generalismo</h3>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                                className={`party-chip ${viewMode === 'party' ? 'selected' : ''}`}
                                onClick={() => setViewMode('party')}
                            >
                                Per Partito
                            </button>
                            <button
                                className={`party-chip ${viewMode === 'deputy' ? 'selected' : ''}`}
                                onClick={() => setViewMode('deputy')}
                            >
                                Per Deputato
                            </button>
                        </div>
                    </div>
                    <div className="card-content" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                        {/* Generalists */}
                        <div>
                            <h4 style={{ color: '#22c55e', marginBottom: '12px', fontSize: '14px' }}>
                                🎯 Top Generalisti
                            </h4>
                            <div className="ranking-list">
                                {generalismRanking.generalists.map((item, idx) => (
                                    <div key={item.name} className="ranking-item">
                                        <span className={`ranking-position ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}`}>
                                            {idx + 1}
                                        </span>
                                        <div className="ranking-info">
                                            <div className="ranking-name">{item.name}</div>
                                            <div className="ranking-party">{item.n_speeches} discorsi</div>
                                        </div>
                                        <div className="score-bar-container">
                                            <div className="score-bar">
                                                <div
                                                    className="score-bar-fill"
                                                    style={{
                                                        width: `${item.score}%`,
                                                        background: 'linear-gradient(90deg, #22c55e, #16a34a)'
                                                    }}
                                                />
                                            </div>
                                            <span className="score-value" style={{ color: '#22c55e' }}>
                                                {item.score.toFixed(0)}%
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Specialists */}
                        <div>
                            <h4 style={{ color: '#f59e0b', marginBottom: '12px', fontSize: '14px' }}>
                                🔬 Top Specialisti
                            </h4>
                            <div className="ranking-list">
                                {generalismRanking.specialists.map((item, idx) => (
                                    <div key={item.name} className="ranking-item">
                                        <span className={`ranking-position ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}`}>
                                            {idx + 1}
                                        </span>
                                        <div className="ranking-info">
                                            <div className="ranking-name">{item.name}</div>
                                            <div className="ranking-party">
                                                Tema: {clusters[item.dominant_topic]?.label || `Cluster ${item.dominant_topic}`}
                                            </div>
                                        </div>
                                        <div className="score-bar-container">
                                            <div className="score-bar">
                                                <div
                                                    className="score-bar-fill"
                                                    style={{
                                                        width: `${item.score}%`,
                                                        background: 'linear-gradient(90deg, #f59e0b, #d97706)'
                                                    }}
                                                />
                                            </div>
                                            <span className="score-value" style={{ color: '#f59e0b' }}>
                                                {item.score.toFixed(0)}%
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default IdentityTab;
