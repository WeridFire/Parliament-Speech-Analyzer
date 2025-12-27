import React, { useMemo } from 'react';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import { X, TrendingUp, Users, BarChart3, Info } from 'lucide-react';
import { getCleanName, getPartyFromDeputy } from '../../utils/helpers';
import { CLUSTER_COLORS } from '../../utils/constants';

const Plot = createPlotlyComponent(Plotly);

const RebelModal = ({ rebelData, clusters, onClose }) => {
    if (!rebelData) return null;

    // Extract name and party - use helper functions as fallback
    const deputyStr = rebelData.deputy || '';
    const deputyName = getCleanName(deputyStr) || 'Deputato';
    const partyName = rebelData.party || getPartyFromDeputy(deputyStr) || 'N/A';

    const rebelScore = rebelData.rebel_pct || 0;
    const totalSpeeches = rebelData.total_speeches || 0;
    const speechesInMain = rebelData.speeches_in_main || 0;
    const inLinePercent = totalSpeeches > 0 ? Math.round((speechesInMain / totalSpeeches) * 100) : 0;

    // Determine rebel severity
    let severityClass = 'low';
    let severityLabel = 'Moderato';
    if (rebelScore > 60) {
        severityClass = 'high';
        severityLabel = 'Alto';
    } else if (rebelScore > 40) {
        severityClass = 'medium';
        severityLabel = 'Medio';
    }

    const chartData = useMemo(() => {
        if (!clusters) return { traces: [], layout: {} };

        const clusterIds = Object.keys(clusters).map(k => parseInt(k));
        const clusterLabels = clusterIds.map(cid => clusters[cid]?.label || `Cluster ${cid}`);

        const deputyDist = clusterIds.map(cid => {
            const count = rebelData.cluster_distribution?.[cid] || 0;
            return totalSpeeches > 0 ? Math.round((count / totalSpeeches) * 100) : 0;
        });

        const partyDist = clusterIds.map(cid => rebelData.party_cluster_distribution?.[cid] || 0);

        const mainCluster = rebelData.main_cluster;

        const traces = [
            {
                name: 'Deputato',
                x: clusterLabels,
                y: deputyDist,
                type: 'bar',
                hovertemplate: '<b>%{x}</b><br>Deputato: %{y}%<extra></extra>',
                marker: {
                    color: clusterIds.map(cid =>
                        cid === mainCluster ? '#ef4444' : CLUSTER_COLORS[cid % CLUSTER_COLORS.length]
                    ),
                    line: { width: 0 }
                }
            },
            {
                name: 'Media Partito',
                x: clusterLabels,
                y: partyDist,
                type: 'bar',
                hovertemplate: '<b>%{x}</b><br>Media Partito: %{y}%<extra></extra>',
                marker: {
                    color: 'rgba(148, 163, 184, 0.4)',
                    line: { width: 1, color: 'rgba(148, 163, 184, 0.6)' }
                }
            }
        ];

        const layout = {
            barmode: 'group',
            showlegend: true,
            legend: {
                x: 0.5, y: 1.15,
                xanchor: 'center',
                orientation: 'h',
                font: { size: 11, color: '#94a3b8' }
            },
            xaxis: {
                tickangle: -30,
                tickfont: { size: 10, color: '#64748b' },
                automargin: true
            },
            yaxis: {
                title: { text: '% Discorsi', font: { size: 11, color: '#64748b' } },
                tickfont: { size: 10, color: '#64748b' },
                gridcolor: 'rgba(255,255,255,0.05)'
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 45, r: 15, t: 40, b: 80 },
            autosize: true
        };

        return { traces, layout };
    }, [rebelData, clusters, totalSpeeches]);

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="rebel-modal" onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div className="rebel-modal-header">
                    <div className="header-content">
                        <h2>{deputyName}</h2>
                        <span className="party-badge">{partyName}</span>
                    </div>
                    <button className="close-btn" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>

                {/* Score Hero */}
                <div className={`rebel-score-hero ${severityClass}`}>
                    <div className="score-circle">
                        <TrendingUp size={24} />
                        <span className="score-value">{rebelScore}%</span>
                    </div>
                    <div className="score-info">
                        <span className="score-label">Rebel Score</span>
                        <span className={`severity-badge ${severityClass}`}>{severityLabel}</span>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="stats-grid">
                    <div className="stat-card">
                        <Users size={18} />
                        <div className="stat-content">
                            <span className="stat-value">{totalSpeeches}</span>
                            <span className="stat-label">Discorsi Totali</span>
                        </div>
                    </div>
                    <div className="stat-card">
                        <BarChart3 size={18} />
                        <div className="stat-content">
                            <span className="stat-value">{speechesInMain} ({inLinePercent}%)</span>
                            <span className="stat-label">In Linea col Partito</span>
                        </div>
                    </div>
                </div>

                {/* Chart */}
                <div className="chart-section">
                    <h3>Distribuzione Cluster</h3>
                    <div className="chart-container">
                        <Plot
                            data={chartData.traces}
                            layout={chartData.layout}
                            useResizeHandler={true}
                            style={{ width: '100%', height: '240px' }}
                            config={{ displayModeBar: false, responsive: true }}
                        />
                    </div>
                </div>

                {/* Explanation */}
                <div className="info-box">
                    <Info size={16} />
                    <p>
                        Questo deputato parla di temi diversi rispetto alla maggioranza del suo partito
                        nel <strong>{rebelScore}%</strong> dei suoi interventi.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default RebelModal;
