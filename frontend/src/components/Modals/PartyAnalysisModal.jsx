import React, { useState, useMemo } from 'react';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import { X, Building2 } from 'lucide-react';
import { useAppState } from '../../contexts/StateContext';
import { PARTY_CONFIG } from '../../utils/constants';

const Plot = createPlotlyComponent(Plotly);

// Color palette for parties without configured colors
const DEFAULT_COLORS = [
    '#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
    '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#3b82f6'
];

const PartyAnalysisModal = ({ onClose }) => {
    const { data } = useAppState();
    const [selectedParties, setSelectedParties] = useState([]);

    // Get list of parties from speeches with counts
    const parties = useMemo(() => {
        if (!data?.speeches) return [];
        const partyCount = {};
        data.speeches.forEach(s => {
            if (s.party && s.party !== 'Unknown Group') {
                partyCount[s.party] = (partyCount[s.party] || 0) + 1;
            }
        });
        return Object.entries(partyCount)
            .map(([name, count]) => ({ name, count }))
            .sort((a, b) => b.count - a.count);
    }, [data]);

    // Toggle party selection
    const toggleParty = (party) => {
        setSelectedParties(prev => {
            if (prev.includes(party)) {
                return prev.filter(p => p !== party);
            }
            return [...prev, party];
        });
    };

    // Get color for a party
    const getPartyColor = (party, index) => {
        return PARTY_CONFIG[party]?.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length];
    };

    // Calculate topic distribution for a party
    const getPartyDistribution = (party) => {
        if (!party || !data?.speeches || !data?.clusters) return null;

        const clusterCounts = {};
        let total = 0;

        data.speeches.forEach(s => {
            if (s.party === party) {
                const cluster = s.cluster;
                clusterCounts[cluster] = (clusterCounts[cluster] || 0) + 1;
                total++;
            }
        });

        if (total === 0) return null;

        const clusterIds = Object.keys(data.clusters).map(k => parseInt(k));
        const distribution = clusterIds.map(cid => ({
            id: cid,
            label: data.clusters[cid]?.label || `Cluster ${cid}`,
            count: clusterCounts[cid] || 0,
            percentage: Math.round(((clusterCounts[cid] || 0) / total) * 100)
        }));

        return { distribution, total };
    };

    // Generate chart data for all selected parties
    const chartData = useMemo(() => {
        if (!data?.clusters || selectedParties.length === 0) return { traces: [], layout: {} };

        const clusterIds = Object.keys(data.clusters).map(k => parseInt(k));
        const labels = clusterIds.map(cid => data.clusters[cid]?.label || `Cluster ${cid}`);

        const traces = selectedParties.map((party, idx) => {
            const partyData = getPartyDistribution(party);
            if (!partyData) return null;

            return {
                name: party,
                type: 'bar',
                x: labels,
                y: clusterIds.map(cid => {
                    const item = partyData.distribution.find(d => d.id === cid);
                    return item ? item.percentage : 0;
                }),
                marker: { color: getPartyColor(party, idx) },
                hovertemplate: `<b>${party}</b><br>%{x}: %{y}%<extra></extra>`
            };
        }).filter(Boolean);

        const layout = {
            barmode: 'group',
            showlegend: true,
            legend: {
                x: 0.5, y: 1.15,
                xanchor: 'center',
                orientation: 'h',
                font: { size: 10, color: '#94a3b8' }
            },
            xaxis: {
                tickangle: -45,
                tickfont: { size: 9, color: '#64748b' },
                automargin: true
            },
            yaxis: {
                title: { text: '% Discorsi', font: { size: 11, color: '#64748b' } },
                tickfont: { size: 10, color: '#64748b' },
                gridcolor: 'rgba(255,255,255,0.05)'
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 45, r: 15, t: 50, b: 120 },
            autosize: true
        };

        return { traces, layout };
    }, [selectedParties, data]);

    // Selected parties with their data
    const selectedPartiesData = useMemo(() => {
        return selectedParties.map((party, idx) => ({
            name: party,
            color: getPartyColor(party, idx),
            data: getPartyDistribution(party)
        }));
    }, [selectedParties, data]);

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="party-analysis-modal comparison" onClick={e => e.stopPropagation()} style={{ maxWidth: '900px' }}>
                <div className="party-analysis-header">
                    <div className="header-content">
                        <Building2 size={20} />
                        <h2>Confronta Partiti</h2>
                    </div>
                    <button className="close-btn" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>

                <div className="party-analysis-content">
                    {/* Party Selector - Styled Chips */}
                    <div style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '8px',
                        marginBottom: '20px',
                        maxHeight: '200px',
                        overflowY: 'auto',
                        padding: '4px'
                    }}>
                        {parties.map((party, idx) => {
                            const isSelected = selectedParties.includes(party.name);
                            const color = isSelected ? getPartyColor(party.name, selectedParties.indexOf(party.name)) : '#64748b';
                            return (
                                <button
                                    key={party.name}
                                    onClick={() => toggleParty(party.name)}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        padding: '8px 14px',
                                        borderRadius: '20px',
                                        cursor: 'pointer',
                                        background: isSelected
                                            ? `linear-gradient(135deg, ${color}30 0%, ${color}15 100%)`
                                            : 'rgba(255,255,255,0.03)',
                                        border: isSelected
                                            ? `2px solid ${color}`
                                            : '2px solid rgba(255,255,255,0.1)',
                                        transition: 'all 0.2s ease',
                                        fontSize: '13px',
                                        color: isSelected ? color : '#94a3b8',
                                        fontWeight: isSelected ? '600' : '400'
                                    }}
                                >
                                    {isSelected && <span style={{ fontSize: '10px' }}>✓</span>}
                                    <span>{party.name}</span>
                                    <span style={{
                                        fontSize: '10px',
                                        opacity: 0.7,
                                        background: 'rgba(0,0,0,0.2)',
                                        padding: '2px 6px',
                                        borderRadius: '10px'
                                    }}>{party.count}</span>
                                </button>
                            );
                        })}
                    </div>

                    {/* Selected Parties Summary */}
                    {selectedParties.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
                            {selectedPartiesData.map(p => p.data && (
                                <div key={p.name} style={{
                                    padding: '6px 12px',
                                    borderRadius: '20px',
                                    background: `${p.color}20`,
                                    border: `1px solid ${p.color}`,
                                    fontSize: '12px'
                                }}>
                                    <span style={{ color: p.color, fontWeight: '600' }}>{p.name}</span>
                                    <span style={{ color: '#94a3b8', marginLeft: '6px' }}>{p.data.total} discorsi</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Comparison Chart */}
                    {selectedParties.length > 0 && (
                        <div className="party-chart">
                            <h3>Distribuzione Tematica</h3>
                            <div className="chart-container">
                                <Plot
                                    data={chartData.traces}
                                    layout={chartData.layout}
                                    useResizeHandler={true}
                                    style={{ width: '100%', height: '350px' }}
                                    config={{ displayModeBar: false, responsive: true }}
                                />
                            </div>
                        </div>
                    )}

                    {selectedParties.length === 0 && (
                        <div className="no-data" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                            <Building2 size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
                            <p>Seleziona uno o più partiti per confrontare la loro distribuzione tematica.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PartyAnalysisModal;
