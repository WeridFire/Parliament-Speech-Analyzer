/**
 * Qualitative Tab - Sentiment, readability, and polarization analysis
 */
import React, { useMemo } from 'react';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import { MessageSquare, BookOpen, Swords, ThumbsUp, ThumbsDown } from 'lucide-react';
import NoDataMessage from '../NoDataMessage';

const Plot = createPlotlyComponent(Plotly);

const QualitativeTab = ({ analytics, clusters, selectedPeriod }) => {
    const sentiment = analytics?.topic_sentiment || {};
    const readability = analytics?.readability || {};
    const polarization = analytics?.polarization || {};

    // Check if we have any data
    const hasData = Object.keys(sentiment.by_cluster || {}).length > 0 ||
        Object.keys(readability.by_party || {}).length > 0;

    // Sentiment by cluster
    const clusterSentiment = useMemo(() => {
        const byCluster = sentiment.by_cluster || {};
        return Object.entries(byCluster)
            .map(([id, data]) => ({
                id: parseInt(id),
                label: data.label || clusters[id]?.label || `Cluster ${id}`,
                ...data
            }))
            .sort((a, b) => b.avg_sentiment - a.avg_sentiment);
    }, [sentiment, clusters]);

    // Sentiment chart
    const sentimentChartData = useMemo(() => {
        if (clusterSentiment.length === 0) return null;

        return {
            data: [{
                type: 'bar',
                x: clusterSentiment.map(c => c.label),
                y: clusterSentiment.map(c => c.avg_sentiment),
                marker: {
                    color: clusterSentiment.map(c =>
                        c.avg_sentiment > 0.05 ? '#22c55e' :
                            c.avg_sentiment < -0.05 ? '#ef4444' : '#64748b'
                    )
                },
                hovertemplate: '%{x}<br>Sentiment: %{y:.2f}<extra></extra>'
            }],
            layout: {
                showlegend: false,
                xaxis: {
                    tickangle: -45,
                    tickfont: { color: '#94a3b8', size: 10 }
                },
                yaxis: {
                    title: { text: 'Sentiment Score', font: { size: 11, color: '#64748b' } },
                    tickfont: { color: '#64748b', size: 10 },
                    gridcolor: 'rgba(255,255,255,0.05)',
                    zeroline: true,
                    zerolinecolor: 'rgba(255,255,255,0.2)',
                    range: [-0.5, 0.5]
                },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                margin: { l: 50, r: 20, t: 20, b: 100 }
            }
        };
    }, [clusterSentiment]);

    // Readability ranking
    const readabilityRanking = useMemo(() => {
        const byParty = readability.by_party || {};
        return Object.entries(byParty)
            .map(([party, data]) => ({ party, ...data }))
            .sort((a, b) => b.avg_score - a.avg_score);
    }, [readability]);

    // Top polarizers
    const topPolarizers = polarization.top_polarizers || [];
    const leastPolarizers = polarization.least_polarizers || [];

    // Party polarization
    const partyPolarization = useMemo(() => {
        const byParty = polarization.by_party || {};
        return Object.entries(byParty)
            .map(([party, data]) => ({ party, ...data }))
            .sort((a, b) => b.avg_score - a.avg_score);
    }, [polarization]);

    // Show no data message if period has no data
    if (!hasData && (selectedPeriod?.year || selectedPeriod?.month)) {
        return (
            <div className="analytics-tab">
                <div className="tab-header">
                    <h2><MessageSquare size={24} /> Analisi Qualitativa</h2>
                    <p>Sentiment per tema, complessità linguistica e linguaggio polarizzante</p>
                </div>
                <NoDataMessage featureName="l'analisi qualitativa" period={selectedPeriod} />
            </div>
        );
    }

    return (
        <div className="analytics-tab">
            <div className="tab-header">
                <h2><MessageSquare size={24} /> Analisi Qualitativa</h2>
                <p>Sentiment per tema, complessità linguistica e linguaggio polarizzante</p>
            </div>

            <div className="analytics-grid">
                {/* Topic Sentiment */}
                <div className="analytics-card full-width">
                    <div className="card-header">
                        <h3><ThumbsUp size={18} /> Sentiment per Tema</h3>
                        <span className="card-subtitle">Tono medio dei discorsi per cluster</span>
                    </div>
                    <div className="card-content">
                        {sentimentChartData ? (
                            <div className="chart-container">
                                <Plot
                                    data={sentimentChartData.data}
                                    layout={sentimentChartData.layout}
                                    useResizeHandler={true}
                                    style={{ width: '100%', height: '300px' }}
                                    config={{ displayModeBar: false, responsive: true }}
                                />
                            </div>
                        ) : (
                            <div className="empty-state">
                                <MessageSquare size={48} />
                                <p>Dati sentiment non disponibili</p>
                            </div>
                        )}

                        {/* Legend */}
                        <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', marginTop: '12px', fontSize: '12px' }}>
                            <span style={{ color: '#22c55e' }}>● Positivo</span>
                            <span style={{ color: '#64748b' }}>● Neutro</span>
                            <span style={{ color: '#ef4444' }}>● Negativo</span>
                        </div>
                    </div>
                </div>

                {/* Readability */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><BookOpen size={18} /> Indice Gulpease (Leggibilità)</h3>
                        <span className="card-subtitle">Complessità linguistica per partito</span>
                    </div>
                    <div className="card-content">
                        <div className="ranking-list">
                            {readabilityRanking.slice(0, 12).map((item, idx) => {
                                const isEasy = item.avg_score >= 80;
                                const isMedium = item.avg_score >= 55 && item.avg_score < 80;
                                const color = isEasy ? '#22c55e' : isMedium ? '#f59e0b' : '#ef4444';

                                return (
                                    <div key={item.party} className="ranking-item">
                                        <span className={`ranking-position ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}`}>
                                            {idx + 1}
                                        </span>
                                        <div className="ranking-info">
                                            <div className="ranking-name">{item.party}</div>
                                            <div className="ranking-party">
                                                {isEasy ? '📖 Facile' : isMedium ? '📚 Medio' : '🎓 Difficile'}
                                            </div>
                                        </div>
                                        <div className="score-bar-container">
                                            <div className="score-bar">
                                                <div
                                                    className="score-bar-fill"
                                                    style={{
                                                        width: `${item.avg_score}%`,
                                                        background: `linear-gradient(90deg, ${color}, ${color}cc)`
                                                    }}
                                                />
                                            </div>
                                            <span className="score-value" style={{ color }}>
                                                {item.avg_score.toFixed(0)}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Legend */}
                        <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', fontSize: '11px' }}>
                            <div style={{ color: '#94a3b8', marginBottom: '6px' }}>Scala Gulpease:</div>
                            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                                <span style={{ color: '#22c55e' }}>80+ Facile</span>
                                <span style={{ color: '#f59e0b' }}>55-79 Medio</span>
                                <span style={{ color: '#ef4444' }}>&lt;55 Difficile</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Polarization by Party */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><Swords size={18} /> Polarizzazione per Partito</h3>
                        <span className="card-subtitle">Linguaggio "noi vs loro"</span>
                    </div>
                    <div className="card-content">
                        <div className="ranking-list">
                            {partyPolarization.slice(0, 12).map((item, idx) => {
                                const color = item.avg_score > 50 ? '#ef4444' : item.avg_score > 20 ? '#f59e0b' : '#22c55e';

                                return (
                                    <div key={item.party} className="ranking-item">
                                        <span className={`ranking-position ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}`}>
                                            {idx + 1}
                                        </span>
                                        <div className="ranking-info">
                                            <div className="ranking-name">{item.party}</div>
                                            <div className="ranking-party">
                                                {item.classification === 'alta' ? '🔥 Alta' : item.classification === 'media' ? '⚠️ Media' : '✅ Bassa'}
                                            </div>
                                        </div>
                                        <div className="score-bar-container">
                                            <div className="score-bar">
                                                <div
                                                    className="score-bar-fill"
                                                    style={{
                                                        width: `${item.avg_score}%`,
                                                        background: `linear-gradient(90deg, ${color}, ${color}cc)`
                                                    }}
                                                />
                                            </div>
                                            <span className="score-value" style={{ color }}>
                                                {item.avg_score.toFixed(0)}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Top Polarizers */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><Swords size={18} /> Top Polarizzatori</h3>
                        <span className="card-subtitle">Deputati con linguaggio più divisivo</span>
                    </div>
                    <div className="card-content">
                        {topPolarizers.length > 0 ? (
                            <div className="ranking-list">
                                {topPolarizers.slice(0, 10).map((item, idx) => (
                                    <div key={item.speaker} className="ranking-item">
                                        <span className={`ranking-position ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}`}>
                                            {idx + 1}
                                        </span>
                                        <div className="ranking-info">
                                            <div className="ranking-name">{item.speaker.split(' (')[0]}</div>
                                            <div className="ranking-party">{item.party}</div>
                                        </div>
                                        <span className="score-value" style={{ color: '#ef4444' }}>
                                            {item.score.toFixed(0)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state">
                                <Swords size={32} />
                                <p>Dati non disponibili</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Least Polarizers */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><ThumbsUp size={18} /> Meno Polarizzatori</h3>
                        <span className="card-subtitle">Deputati con linguaggio più inclusivo</span>
                    </div>
                    <div className="card-content">
                        {leastPolarizers.length > 0 ? (
                            <div className="ranking-list">
                                {leastPolarizers.slice(0, 10).map((item, idx) => (
                                    <div key={item.speaker} className="ranking-item">
                                        <span className={`ranking-position ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}`}>
                                            {idx + 1}
                                        </span>
                                        <div className="ranking-info">
                                            <div className="ranking-name">{item.speaker.split(' (')[0]}</div>
                                            <div className="ranking-party">{item.party}</div>
                                        </div>
                                        <span className="score-value" style={{ color: '#22c55e' }}>
                                            {item.score.toFixed(0)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state">
                                <ThumbsUp size={32} />
                                <p>Dati non disponibili</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default QualitativeTab;
