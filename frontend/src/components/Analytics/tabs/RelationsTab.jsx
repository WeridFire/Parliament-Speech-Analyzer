/**
 * Relations Tab - Party affinity, cohesion, and thematic overlap
 */
import React, { useMemo } from 'react';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import { Users, Network, Target, UserCheck } from 'lucide-react';
import NoDataMessage from '../NoDataMessage';

const Plot = createPlotlyComponent(Plotly);

const RelationsTab = ({ analytics, clusters, selectedPeriod }) => {
    const affinity = analytics?.affinity_matrix || {};
    const cohesion = analytics?.party_cohesion || {};
    const overlap = analytics?.thematic_overlap || {};
    const crossParty = analytics?.cross_party_pairs || [];

    // Check if we have any data
    const hasData = (affinity.parties?.length > 0) ||
        (Object.keys(cohesion).length > 0);

    // Affinity Heatmap
    const heatmapData = useMemo(() => {
        if (!affinity.parties || !affinity.matrix) return null;

        const parties = affinity.parties;
        const matrix = affinity.matrix;

        return {
            data: [{
                type: 'heatmap',
                z: matrix,
                x: parties,
                y: parties,
                colorscale: [
                    [0, '#0f172a'],
                    [0.5, '#6366f1'],
                    [1, '#22c55e']
                ],
                hoverongaps: false,
                showscale: true,
                colorbar: {
                    title: 'Similarità',
                    titleside: 'right',
                    tickfont: { color: '#64748b', size: 10 },
                    titlefont: { color: '#94a3b8', size: 11 }
                }
            }],
            layout: {
                xaxis: {
                    tickangle: -45,
                    tickfont: { color: '#94a3b8', size: 10 },
                    side: 'bottom'
                },
                yaxis: {
                    tickfont: { color: '#94a3b8', size: 10 },
                    autorange: 'reversed'
                },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                margin: { l: 120, r: 50, t: 20, b: 120 }
            }
        };
    }, [affinity]);

    // Cohesion ranking
    const cohesionRanking = useMemo(() => {
        return Object.entries(cohesion)
            .map(([party, data]) => ({ party, ...data }))
            .sort((a, b) => b.cohesion_score - a.cohesion_score);
    }, [cohesion]);

    // Thematic overlap analysis
    const overlapAnalysis = useMemo(() => {
        const items = Object.entries(overlap).map(([id, data]) => ({
            id: parseInt(id),
            ...data
        }));

        const bipartisan = items
            .filter(i => i.classification === 'bipartisan')
            .sort((a, b) => b.overlap_score - a.overlap_score);

        const polarized = items
            .filter(i => i.classification !== 'bipartisan' && i.classification !== 'mixed')
            .sort((a, b) => a.overlap_score - b.overlap_score);

        return { bipartisan, polarized };
    }, [overlap]);

    // Cross-party pairs that cross political divide
    const bridgePairs = useMemo(() => {
        return crossParty
            .filter(p => p.crosses_divide)
            .slice(0, 10);
    }, [crossParty]);

    // Show no data message if period has no data
    if (!hasData && (selectedPeriod?.year || selectedPeriod?.month)) {
        return (
            <div className="analytics-tab">
                <div className="tab-header">
                    <h2><Users size={24} /> Analisi Relazionale</h2>
                    <p>Affinità tra partiti, coesione interna e temi trasversali</p>
                </div>
                <NoDataMessage featureName="l'analisi relazionale" period={selectedPeriod} />
            </div>
        );
    }

    return (
        <div className="analytics-tab">
            <div className="tab-header">
                <h2><Users size={24} /> Analisi Relazionale</h2>
                <p>Affinità tra partiti, coesione interna e temi trasversali</p>
            </div>

            <div className="analytics-grid">
                {/* Affinity Heatmap */}
                <div className="analytics-card full-width">
                    <div className="card-header">
                        <h3><Network size={18} /> Matrice di Affinità</h3>
                        <span className="card-subtitle">Similarità semantica tra partiti</span>
                    </div>
                    <div className="card-content">
                        {heatmapData ? (
                            <div className="chart-container">
                                <Plot
                                    data={heatmapData.data}
                                    layout={heatmapData.layout}
                                    useResizeHandler={true}
                                    style={{ width: '100%', height: '450px' }}
                                    config={{ displayModeBar: false, responsive: true }}
                                />
                            </div>
                        ) : (
                            <div className="empty-state">
                                <Network size={48} />
                                <p>Dati affinità non disponibili</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Party Cohesion */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><Target size={18} /> Coesione Interna</h3>
                        <span className="card-subtitle">Quanto è compatto ogni partito</span>
                    </div>
                    <div className="card-content">
                        <div className="ranking-list">
                            {cohesionRanking.slice(0, 12).map((item, idx) => (
                                <div key={item.party} className="ranking-item">
                                    <span className={`ranking-position ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}`}>
                                        {idx + 1}
                                    </span>
                                    <div className="ranking-info">
                                        <div className="ranking-name">{item.party}</div>
                                        <div className="ranking-party">{item.n_members} membri</div>
                                    </div>
                                    <div className="score-bar-container">
                                        <div className="score-bar">
                                            <div
                                                className="score-bar-fill"
                                                style={{
                                                    width: `${item.cohesion_score}%`,
                                                    background: item.cohesion_score > 70
                                                        ? 'linear-gradient(90deg, #22c55e, #16a34a)'
                                                        : item.cohesion_score > 40
                                                            ? 'linear-gradient(90deg, #f59e0b, #d97706)'
                                                            : 'linear-gradient(90deg, #ef4444, #dc2626)'
                                                }}
                                            />
                                        </div>
                                        <span className="score-value" style={{
                                            color: item.cohesion_score > 70 ? '#22c55e' : item.cohesion_score > 40 ? '#f59e0b' : '#ef4444'
                                        }}>
                                            {item.cohesion_score.toFixed(0)}%
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Cross-Party Pairs */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><UserCheck size={18} /> Ponti Politici</h3>
                        <span className="card-subtitle">Coppie cross-coalizione più simili</span>
                    </div>
                    <div className="card-content">
                        {bridgePairs.length > 0 ? (
                            <div className="ranking-list">
                                {bridgePairs.map((pair, idx) => (
                                    <div key={`${pair.speaker1}-${pair.speaker2}`} className="ranking-item" style={{ flexDirection: 'column', alignItems: 'stretch', gap: '8px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <span className={`ranking-position ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}`}>
                                                    {idx + 1}
                                                </span>
                                                <span style={{ fontSize: '12px', color: '#22c55e' }}>
                                                    {(pair.similarity * 100).toFixed(0)}% sim.
                                                </span>
                                            </div>
                                        </div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                                            <div>
                                                <div style={{ color: '#e2e8f0', fontWeight: 500 }}>{pair.speaker1.split(' (')[0]}</div>
                                                <div style={{ color: '#64748b', fontSize: '11px' }}>{pair.party1}</div>
                                            </div>
                                            <div style={{ color: '#64748b' }}>↔</div>
                                            <div style={{ textAlign: 'right' }}>
                                                <div style={{ color: '#e2e8f0', fontWeight: 500 }}>{pair.speaker2.split(' (')[0]}</div>
                                                <div style={{ color: '#64748b', fontSize: '11px' }}>{pair.party2}</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state">
                                <UserCheck size={32} />
                                <p>Nessuna coppia cross-coalizione trovata{selectedPeriod?.year ? ` per ${selectedPeriod.month ? 'questo mese' : 'quest\'anno'}. Prova un periodo diverso.` : ''}</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Thematic Overlap */}
                <div className="analytics-card full-width">
                    <div className="card-header">
                        <h3><Users size={18} /> Temi Bipartisan vs Polarizzati</h3>
                        <span className="card-subtitle">Distribuzione sinistra/destra per tema</span>
                    </div>
                    <div className="card-content" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                        {/* Bipartisan */}
                        <div>
                            <h4 style={{ color: '#22c55e', marginBottom: '12px', fontSize: '14px' }}>
                                🤝 Temi Bipartisan
                            </h4>
                            {overlapAnalysis.bipartisan.length > 0 ? (
                                <div className="ranking-list">
                                    {overlapAnalysis.bipartisan.slice(0, 5).map(item => (
                                        <div key={item.id} className="ranking-item">
                                            <div className="ranking-info" style={{ flex: 1 }}>
                                                <div className="ranking-name">{item.label}</div>
                                                <div style={{ display: 'flex', gap: '12px', marginTop: '4px', fontSize: '11px' }}>
                                                    <span style={{ color: '#ef4444' }}>SX {item.left_pct?.toFixed(0)}%</span>
                                                    <span style={{ color: '#3b82f6' }}>DX {item.right_pct?.toFixed(0)}%</span>
                                                </div>
                                            </div>
                                            <span className="score-value" style={{ color: '#22c55e' }}>
                                                {item.overlap_score?.toFixed(0)}%
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p style={{ color: '#64748b', fontSize: '13px' }}>Nessun tema bipartisan rilevato{selectedPeriod?.year ? `. Prova un periodo diverso.` : ''}</p>
                            )}
                        </div>

                        {/* Polarized */}
                        <div>
                            <h4 style={{ color: '#ef4444', marginBottom: '12px', fontSize: '14px' }}>
                                ⚡ Temi Polarizzati
                            </h4>
                            {overlapAnalysis.polarized.length > 0 ? (
                                <div className="ranking-list">
                                    {overlapAnalysis.polarized.slice(0, 5).map(item => (
                                        <div key={item.id} className="ranking-item">
                                            <div className="ranking-info" style={{ flex: 1 }}>
                                                <div className="ranking-name">{item.label}</div>
                                                <div style={{ display: 'flex', gap: '12px', marginTop: '4px', fontSize: '11px' }}>
                                                    <span style={{ color: '#ef4444' }}>SX {item.left_pct?.toFixed(0)}%</span>
                                                    <span style={{ color: '#3b82f6' }}>DX {item.right_pct?.toFixed(0)}%</span>
                                                </div>
                                            </div>
                                            <span
                                                className="score-value"
                                                style={{
                                                    color: item.classification === 'left-leaning' ? '#ef4444' : '#3b82f6',
                                                    fontSize: '11px'
                                                }}
                                            >
                                                {item.classification === 'left-leaning' ? '← SX' : 'DX →'}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p style={{ color: '#64748b', fontSize: '13px' }}>Nessun tema fortemente polarizzato{selectedPeriod?.year ? `. Prova un periodo diverso.` : ''}</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RelationsTab;
