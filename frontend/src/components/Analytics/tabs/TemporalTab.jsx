/**
 * Temporal Tab - Topic trends, crisis index, and topic surfing
 * 
 * Accepts selectedPeriod prop for highlighting specific time periods
 */
import React, { useState, useMemo } from 'react';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import { TrendingUp, Activity, Zap, Shuffle } from 'lucide-react';

const Plot = createPlotlyComponent(Plotly);

// Color palette for topics
const TOPIC_COLORS = [
    '#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
    '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#3b82f6'
];

const TemporalTab = ({ analytics, clusters, selectedPeriod = {} }) => {
    const [selectedTopic, setSelectedTopic] = useState(null);

    const trends = analytics?.topic_trends || {};
    const crisis = analytics?.crisis_index || {};
    const surfing = analytics?.topic_surfing || {};

    // Topic trend line chart
    const trendChartData = useMemo(() => {
        if (!trends.global || !trends.periods) return null;

        const periods = trends.periods;
        const clusterIds = Object.keys(clusters).map(k => parseInt(k));

        const traces = clusterIds.map((cid, idx) => ({
            type: 'scatter',
            mode: 'lines+markers',
            name: clusters[cid]?.label || `Cluster ${cid}`,
            x: periods,
            y: periods.map(p => trends.global[p]?.[cid] || 0),
            line: { color: TOPIC_COLORS[idx % TOPIC_COLORS.length], width: 2 },
            marker: { size: 6 },
            visible: selectedTopic === null || selectedTopic === cid ? true : 'legendonly'
        }));

        return {
            data: traces,
            layout: {
                showlegend: true,
                legend: {
                    orientation: 'h',
                    y: -0.2,
                    x: 0.5,
                    xanchor: 'center',
                    font: { size: 10, color: '#94a3b8' }
                },
                xaxis: {
                    tickfont: { color: '#64748b', size: 10 },
                    tickangle: -45,
                    gridcolor: 'rgba(255,255,255,0.05)'
                },
                yaxis: {
                    title: { text: 'N° Discorsi', font: { size: 11, color: '#64748b' } },
                    tickfont: { color: '#64748b', size: 10 },
                    gridcolor: 'rgba(255,255,255,0.05)'
                },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                margin: { l: 50, r: 20, t: 20, b: 100 },
                hovermode: 'x unified'
            }
        };
    }, [trends, clusters, selectedTopic]);

    // Crisis ECG chart
    const crisisChartData = useMemo(() => {
        if (!crisis.global || !crisis.periods) return null;

        const periods = crisis.periods;
        const rates = periods.map(p => crisis.global[p]?.crisis_rate || 0);

        return {
            data: [{
                type: 'scatter',
                mode: 'lines',
                fill: 'tozeroy',
                name: 'Indice di Crisi',
                x: periods,
                y: rates,
                line: { color: '#ef4444', width: 2 },
                fillcolor: 'rgba(239, 68, 68, 0.2)'
            }],
            layout: {
                showlegend: false,
                xaxis: {
                    tickfont: { color: '#64748b', size: 10 },
                    tickangle: -45,
                    gridcolor: 'rgba(255,255,255,0.05)'
                },
                yaxis: {
                    title: { text: 'Crisi per 1000 parole', font: { size: 11, color: '#64748b' } },
                    tickfont: { color: '#64748b', size: 10 },
                    gridcolor: 'rgba(255,255,255,0.05)'
                },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                margin: { l: 60, r: 20, t: 20, b: 80 }
            }
        };
    }, [crisis]);

    // Top topic surfers
    const topSurfers = useMemo(() => {
        return Object.entries(surfing)
            .map(([name, data]) => ({ name, ...data }))
            .filter(s => s.topic_changes >= 2)
            .sort((a, b) => b.topic_changes - a.topic_changes)
            .slice(0, 15);
    }, [surfing]);

    // Most consistent speakers
    const mostConsistent = useMemo(() => {
        return Object.entries(surfing)
            .map(([name, data]) => ({ name, ...data }))
            .filter(s => s.n_periods >= 3)
            .sort((a, b) => b.consistency_score - a.consistency_score)
            .slice(0, 10);
    }, [surfing]);

    return (
        <div className="analytics-tab">
            <div className="tab-header">
                <h2><TrendingUp size={24} /> Analisi Temporale</h2>
                <p>Evoluzione dei temi, allarmi e chi cambia più spesso argomento</p>
            </div>

            <div className="analytics-grid">
                {/* Topic Trends */}
                <div className="analytics-card full-width">
                    <div className="card-header">
                        <h3><Activity size={18} /> Trend Tematici nel Tempo</h3>
                        <span className="card-subtitle">Distribuzione mensile dei topic</span>
                    </div>
                    <div className="card-content">
                        {trendChartData ? (
                            <div className="chart-container">
                                <Plot
                                    data={trendChartData.data}
                                    layout={trendChartData.layout}
                                    useResizeHandler={true}
                                    style={{ width: '100%', height: '350px' }}
                                    config={{ displayModeBar: false, responsive: true }}
                                />
                            </div>
                        ) : (
                            <div className="empty-state">
                                <Activity size={48} />
                                <p>Dati trend non disponibili</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Crisis ECG */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><Zap size={18} /> Elettrocardiogramma della Crisi</h3>
                        <span className="card-subtitle">Frequenza termini di allarme</span>
                    </div>
                    <div className="card-content">
                        {crisisChartData ? (
                            <div className="chart-container">
                                <Plot
                                    data={crisisChartData.data}
                                    layout={crisisChartData.layout}
                                    useResizeHandler={true}
                                    style={{ width: '100%', height: '250px' }}
                                    config={{ displayModeBar: false, responsive: true }}
                                />
                            </div>
                        ) : (
                            <div className="empty-state">
                                <Zap size={32} />
                                <p>Dati crisi non disponibili</p>
                            </div>
                        )}

                        {/* Crisis keywords preview */}
                        {crisis.crisis_keywords && (
                            <div style={{ marginTop: '12px' }}>
                                <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '8px' }}>
                                    Keywords monitorate:
                                </div>
                                <div className="keywords-cloud" style={{ gap: '4px', flexWrap: 'wrap' }}>
                                    {crisis.crisis_keywords.map(kw => (
                                        <span key={kw} className="keyword-tag" style={{
                                            fontSize: '10px',
                                            padding: '3px 8px',
                                            background: 'rgba(239, 68, 68, 0.15)',
                                            borderColor: 'rgba(239, 68, 68, 0.3)',
                                            color: '#fca5a5'
                                        }}>
                                            {kw}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Topic Surfers */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><Shuffle size={18} /> Topic Surfers</h3>
                        <span className="card-subtitle">Chi cambia più spesso argomento</span>
                    </div>
                    <div className="card-content">
                        {topSurfers.length > 0 ? (
                            <div className="ranking-list">
                                {topSurfers.map((surfer, idx) => (
                                    <div key={surfer.name} className="ranking-item">
                                        <span className={`ranking-position ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}`}>
                                            {idx + 1}
                                        </span>
                                        <div className="ranking-info">
                                            <div className="ranking-name">{surfer.name.split(' (')[0]}</div>
                                            <div className="ranking-party">
                                                {surfer.topic_changes} cambi in {surfer.n_periods} mesi
                                            </div>
                                        </div>
                                        <div className="score-bar-container">
                                            <div className="score-bar">
                                                <div
                                                    className="score-bar-fill"
                                                    style={{
                                                        width: `${100 - surfer.consistency_score}%`,
                                                        background: 'linear-gradient(90deg, #f59e0b, #d97706)'
                                                    }}
                                                />
                                            </div>
                                            <span className="score-value" style={{ color: '#f59e0b', fontSize: '11px' }}>
                                                {surfer.topic_changes}×
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state">
                                <Shuffle size={32} />
                                <p>Dati surfing non disponibili</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Most Consistent */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><TrendingUp size={18} /> I Più Costanti</h3>
                        <span className="card-subtitle">Chi resta fedele ai propri temi</span>
                    </div>
                    <div className="card-content">
                        {mostConsistent.length > 0 ? (
                            <div className="ranking-list">
                                {mostConsistent.map((speaker, idx) => (
                                    <div key={speaker.name} className="ranking-item">
                                        <span className={`ranking-position ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}`}>
                                            {idx + 1}
                                        </span>
                                        <div className="ranking-info">
                                            <div className="ranking-name">{speaker.name.split(' (')[0]}</div>
                                            <div className="ranking-party">
                                                {speaker.n_periods} mesi di attività
                                            </div>
                                        </div>
                                        <div className="score-bar-container">
                                            <div className="score-bar">
                                                <div
                                                    className="score-bar-fill"
                                                    style={{
                                                        width: `${speaker.consistency_score}%`,
                                                        background: 'linear-gradient(90deg, #22c55e, #16a34a)'
                                                    }}
                                                />
                                            </div>
                                            <span className="score-value" style={{ color: '#22c55e' }}>
                                                {speaker.consistency_score.toFixed(0)}%
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state">
                                <TrendingUp size={32} />
                                <p>Dati consistenza non disponibili</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TemporalTab;
