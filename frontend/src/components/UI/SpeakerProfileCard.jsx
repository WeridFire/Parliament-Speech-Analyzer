/**
 * SpeakerProfileCard - Displays detailed speaker statistics
 * 
 * Shows verbosity, linguistic patterns, consistency, topic leadership,
 * intervention patterns, vocabulary, and network metrics for a selected speaker.
 */
import React, { useMemo } from 'react';
import PropTypes from 'prop-types';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import {
    MessageSquare, Brain, Target, Calendar,
    BookOpen, Network, Award, TrendingUp
} from 'lucide-react';

const Plot = createPlotlyComponent(Plotly);

// Interpretation labels in Italian
const INTERPRETATION_LABELS = {
    'very_consistent': 'Molto Consistente',
    'consistent': 'Consistente',
    'moderate': 'Moderato',
    'variable': 'Variabile',
    'highly_variable': 'Molto Variabile',
    'very_regular': 'Molto Regolare',
    'regular': 'Regolare',
    'sporadic': 'Sporadico',
    'very_sporadic': 'Molto Sporadico',
    'very_rich': 'Molto Ricco',
    'rich': 'Ricco',
    'limited': 'Limitato',
    'very_limited': 'Molto Limitato'
};

/**
 * Single stat display
 */
const StatItem = ({ label, value, unit, icon: Icon }) => (
    <div className="speaker-stat-item">
        {Icon && <Icon size={16} className="stat-icon" />}
        <div className="stat-content">
            <span className="stat-value">{value}{unit && <small> {unit}</small>}</span>
            <span className="stat-label">{label}</span>
        </div>
    </div>
);

StatItem.propTypes = {
    label: PropTypes.string.isRequired,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    unit: PropTypes.string,
    icon: PropTypes.elementType
};

/**
 * Score gauge component
 */
const ScoreGauge = ({ score, label, interpretation, color = '#6366f1' }) => (
    <div className="score-gauge">
        <div className="gauge-visual">
            <div
                className="gauge-fill"
                style={{
                    width: `${Math.min(100, Math.max(0, score))}%`,
                    background: `linear-gradient(90deg, ${color}40, ${color})`
                }}
            />
            <span className="gauge-value" style={{ color }}>{score?.toFixed(0) || 0}</span>
        </div>
        <div className="gauge-labels">
            <span className="gauge-label">{label}</span>
            {interpretation && (
                <span className="gauge-interpretation">
                    {INTERPRETATION_LABELS[interpretation] || interpretation}
                </span>
            )}
        </div>
    </div>
);

ScoreGauge.propTypes = {
    score: PropTypes.number,
    label: PropTypes.string.isRequired,
    interpretation: PropTypes.string,
    color: PropTypes.string
};

const SpeakerProfileCard = ({ speakerName, speakerStats, clusters }) => {
    if (!speakerStats) {
        return (
            <div className="speaker-profile-card empty">
                <div className="empty-state">
                    <MessageSquare size={48} />
                    <p>Seleziona un parlamentare per vedere le statistiche</p>
                </div>
            </div>
        );
    }

    const {
        verbosity = {},
        linguistic = {},
        consistency = {},
        topic_leadership = {},
        intervention = {},  // Note: backend uses 'intervention' not 'intervention_patterns'
        vocabulary = {},
        network = {}
    } = speakerStats;

    // Radar chart for linguistic profile
    const radarData = useMemo(() => {
        const metrics = [
            { label: 'Domande', value: linguistic.question_rate || 0, max: 20 },
            { label: 'Auto-ref.', value: linguistic.self_reference_rate || 0, max: 30 },
            { label: 'Negazioni', value: linguistic.negation_rate || 0, max: 50 },
            { label: 'Futuro', value: linguistic.temporal_orientation > 1 ? 10 : 0, max: 10 },
            { label: 'Passato', value: linguistic.temporal_orientation < 1 ? 10 : 0, max: 10 },
            { label: 'Dati', value: linguistic.data_citation_rate || 0, max: 10 }
        ];

        const values = metrics.map(m => Math.min(100, (m.value / m.max) * 100));
        const labels = metrics.map(m => m.label);

        return {
            data: [{
                type: 'scatterpolar',
                r: [...values, values[0]],
                theta: [...labels, labels[0]],
                fill: 'toself',
                fillcolor: 'rgba(99, 102, 241, 0.2)',
                line: { color: '#6366f1', width: 2 },
                marker: { size: 6, color: '#6366f1' }
            }],
            layout: {
                polar: {
                    radialaxis: {
                        visible: true,
                        range: [0, 100],
                        tickfont: { size: 9, color: '#64748b' },
                        gridcolor: 'rgba(255,255,255,0.1)'
                    },
                    angularaxis: {
                        tickfont: { size: 10, color: '#94a3b8' },
                        gridcolor: 'rgba(255,255,255,0.1)'
                    },
                    bgcolor: 'transparent'
                },
                showlegend: false,
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                margin: { l: 50, r: 50, t: 30, b: 30 }
            }
        };
    }, [linguistic]);

    // Get temporal orientation label
    const temporalLabel = (linguistic.temporal_orientation || 1) > 1 ? '🚀 Visionario' : '📜 Nostalgico';

    return (
        <div className="speaker-profile-card">
            {/* Header */}
            <div className="profile-header">
                <h3>{speakerName}</h3>
                {network.party && <span className="party-badge">{network.party}</span>}
            </div>

            <div className="profile-grid">
                {/* Verbosity Section */}
                <div className="profile-section">
                    <h4><MessageSquare size={16} /> Prolissità</h4>
                    <div className="stats-row">
                        <StatItem
                            label="Parole/discorso"
                            value={verbosity.avg_words_per_speech?.toFixed(0) || 0}
                        />
                        <StatItem
                            label="Frasi/discorso"
                            value={verbosity.avg_sentences_per_speech?.toFixed(1) || 0}
                        />
                        <StatItem
                            label="Parole/frase"
                            value={verbosity.avg_words_per_sentence?.toFixed(1) || 0}
                        />
                    </div>
                </div>

                {/* Linguistic Radar */}
                <div className="profile-section linguistic-radar">
                    <h4><Brain size={16} /> Profilo Linguistico</h4>
                    <div className="radar-container">
                        <Plot
                            data={radarData.data}
                            layout={radarData.layout}
                            useResizeHandler={true}
                            style={{ width: '100%', height: '200px' }}
                            config={{ displayModeBar: false, responsive: true }}
                        />
                    </div>
                    <div className="temporal-badge">
                        Orientamento: {temporalLabel}
                    </div>
                </div>

                {/* Scores Section */}
                <div className="profile-section scores">
                    <h4><Target size={16} /> Metriche</h4>
                    <ScoreGauge
                        score={consistency.score}
                        label="Coerenza Tematica"
                        interpretation={consistency.classification}
                        color="#22c55e"
                    />
                    <ScoreGauge
                        score={intervention.regularity_score}
                        label="Regolarità Interventi"
                        interpretation={intervention.activity_ratio > 50 ? 'regular' : 'sporadic'}
                        color="#f59e0b"
                    />
                    <ScoreGauge
                        score={vocabulary.type_token_ratio * 100}
                        label="Ricchezza Lessicale"
                        interpretation={vocabulary.classification}
                        color="#8b5cf6"
                    />
                </div>

                {/* Intervention Patterns */}
                <div className="profile-section">
                    <h4><Calendar size={16} /> Pattern di Intervento</h4>
                    <div className="stats-row">
                        <StatItem
                            label="Mesi attivi"
                            value={intervention.active_months || 0}
                            unit={`/ ${intervention.total_months || 0}`}
                        />
                        <StatItem
                            label="Media mensile"
                            value={intervention.avg_speeches_per_month?.toFixed(1) || 0}
                        />
                        <StatItem
                            label="Burst Score"
                            value={intervention.burst_score?.toFixed(0) || 0}
                        />
                    </div>
                </div>

                {/* Vocabulary */}
                <div className="profile-section">
                    <h4><BookOpen size={16} /> Vocabolario</h4>
                    <div className="stats-row">
                        <StatItem
                            label="Parole uniche"
                            value={vocabulary.vocabulary_size?.toLocaleString() || 0}
                        />
                        <StatItem
                            label="TTR"
                            value={(vocabulary.type_token_ratio * 100)?.toFixed(1) || 0}
                            unit="%"
                        />
                        <StatItem
                            label="Hapax"
                            value={(vocabulary.hapax_ratio * 100)?.toFixed(1) || 0}
                            unit="%"
                        />
                    </div>
                </div>

                {/* Network */}
                <div className="profile-section">
                    <h4><Network size={16} /> Rete di Menzioni</h4>
                    <div className="stats-row">
                        <StatItem
                            label="Menzioni fatte"
                            value={network.mentions_given || 0}
                        />
                        <StatItem
                            label="Menzioni ricevute"
                            value={network.mentions_received || 0}
                        />
                        <StatItem
                            label="Network Score"
                            value={(network.mentions_given || 0) + (network.mentions_received || 0)}
                        />
                    </div>
                    {network.top_mentioned?.length > 0 && (
                        <div className="mentions-list">
                            <span className="mentions-label">Più menzionati:</span>
                            {network.top_mentioned.slice(0, 3).map(([name, count]) => (
                                <span key={name} className="mention-chip">
                                    {name.split(' ')[0]} ({count})
                                </span>
                            ))}
                        </div>
                    )}
                </div>

                {/* Topic Leadership */}
                {topic_leadership.topics_led_labels?.length > 0 && (
                    <div className="profile-section topic-leadership">
                        <h4><Award size={16} /> Leadership di Tema</h4>
                        <div className="topic-badges">
                            {topic_leadership.topics_led_labels.map((topic, idx) => (
                                <span key={idx} className="topic-badge leader">
                                    👑 {topic}
                                </span>
                            ))}
                        </div>
                        {topic_leadership.dominant_topic_label && (
                            <div className="dominant-topic">
                                <TrendingUp size={14} />
                                <span>Tema dominante: <strong>{topic_leadership.dominant_topic_label}</strong></span>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

SpeakerProfileCard.propTypes = {
    speakerName: PropTypes.string,
    speakerStats: PropTypes.object,
    clusters: PropTypes.object
};

export default SpeakerProfileCard;
