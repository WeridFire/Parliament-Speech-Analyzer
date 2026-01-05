/**
 * SpeakerStatsTab - Speaker statistics and rankings
 * 
 * New Analytics tab displaying per-speaker metrics from speaker_stats:
 * - Speaker search/selector
 * - Profile card with detailed metrics
 * - Rankings by various categories
 */
import React, { useState, useMemo } from 'react';
import {
    UserCheck, Search, MessageSquare, Brain, Target,
    Calendar, BookOpen, Network, TrendingUp, TrendingDown,
    Users
} from 'lucide-react';
import NoDataMessage from '../NoDataMessage';
import RankingCard from '../../UI/RankingCard';
import SpeakerProfileCard from '../../UI/SpeakerProfileCard';
import CustomDropdown from '../../UI/CustomDropdown';

// Ranking categories configuration
const RANKING_CATEGORIES = [
    { id: 'most_verbose', label: 'Più Prolissi', icon: MessageSquare, color: '#ef4444', unit: 'parole' },
    { id: 'most_concise', label: 'Più Concisi', icon: MessageSquare, color: '#22c55e', unit: 'parole' },
    { id: 'most_questions', label: 'Più Interrogativi', icon: Brain, color: '#f59e0b', unit: '/1k' },
    { id: 'most_self_referential', label: 'Più Autoreferenziali', icon: Users, color: '#ec4899', unit: '/1k' },
    { id: 'most_negative', label: 'Più Negativi', icon: TrendingDown, color: '#ef4444', unit: '/1k' },
    { id: 'most_future_oriented', label: 'Orientati al Futuro', icon: TrendingUp, color: '#06b6d4', unit: '/1k' },
    { id: 'most_data_driven', label: 'Più Data-Driven', icon: Target, color: '#8b5cf6', unit: '/1k' },
    { id: 'most_consistent', label: 'Più Coerenti', icon: Target, color: '#22c55e', unit: '%' },
    { id: 'most_variable', label: 'Più Variabili', icon: Target, color: '#f59e0b', unit: '%' },
    { id: 'most_regular', label: 'Più Regolari', icon: Calendar, color: '#22c55e', unit: '%' },
    { id: 'richest_vocabulary', label: 'Vocabolario Più Ricco', icon: BookOpen, color: '#8b5cf6', unit: 'score' },
    { id: 'most_connected', label: 'Più Connessi', icon: Network, color: '#06b6d4', unit: 'score' }
];

const SpeakerStatsTab = ({ analytics, clusters, selectedPeriod }) => {
    const [selectedSpeaker, setSelectedSpeaker] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedRankingCategory, setSelectedRankingCategory] = useState('most_verbose');

    // Extract speaker from analytics (key is 'speaker' not 'speaker_stats')
    const speakerStats = analytics?.speaker || {};
    const bySpeaker = speakerStats.by_speaker || {};
    const rankings = speakerStats.rankings || {};

    // Check if we have data
    const hasData = Object.keys(bySpeaker).length > 0;

    // Get list of speakers for search
    const speakers = useMemo(() => {
        return Object.keys(bySpeaker).sort();
    }, [bySpeaker]);

    // Filtered speakers based on search
    const filteredSpeakers = useMemo(() => {
        if (!searchQuery.trim()) return speakers.slice(0, 20);
        const q = searchQuery.toLowerCase();
        return speakers.filter(s => s.toLowerCase().includes(q)).slice(0, 20);
    }, [speakers, searchQuery]);

    // Get current ranking data
    const currentRanking = useMemo(() => {
        const category = RANKING_CATEGORIES.find(c => c.id === selectedRankingCategory);
        const data = rankings[selectedRankingCategory] || [];
        return { category, data };
    }, [rankings, selectedRankingCategory]);

    // Filter to only show categories that have data
    const availableCategories = useMemo(() => {
        return RANKING_CATEGORIES.filter(cat => rankings[cat.id]?.length > 0);
    }, [rankings]);

    // Show no data message if period has no data
    if (!hasData && (selectedPeriod?.year || selectedPeriod?.month)) {
        return (
            <div className="analytics-tab">
                <div className="tab-header">
                    <h2><UserCheck size={24} /> Statistiche Parlamentari</h2>
                    <p>Profilo dettagliato di ogni politico: stile, coerenza e attività</p>
                </div>
                <NoDataMessage featureName="le statistiche parlamentari" period={selectedPeriod} />
            </div>
        );
    }

    if (!hasData) {
        return (
            <div className="analytics-tab">
                <div className="tab-header">
                    <h2><UserCheck size={24} /> Statistiche Parlamentari</h2>
                    <p>Profilo dettagliato di ogni politico: stile, coerenza e attività</p>
                </div>
                <div className="analytics-card full-width">
                    <div className="card-content">
                        <div className="empty-state">
                            <UserCheck size={48} />
                            <p>Statistiche speaker non disponibili in questo dataset</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="analytics-tab speaker-stats-tab">
            <div className="tab-header">
                <h2><UserCheck size={24} /> Statistiche Parlamentari</h2>
                <p>Profilo dettagliato di ogni politico: stile, coerenza e attività</p>
            </div>

            <div className="analytics-grid">
                {/* Speaker Search */}
                <div className="analytics-card">
                    <div className="card-header">
                        <h3><Search size={18} /> Cerca Parlamentare</h3>
                        <span className="card-subtitle">{speakers.length} parlamentari</span>
                    </div>
                    <div className="card-content">
                        <div className="speaker-search">
                            <input
                                type="text"
                                placeholder="Cerca per nome..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="search-input"
                            />
                        </div>
                        <div className="speaker-list">
                            {filteredSpeakers.map(speaker => (
                                <button
                                    key={speaker}
                                    className={`speaker-item ${selectedSpeaker === speaker ? 'selected' : ''}`}
                                    onClick={() => setSelectedSpeaker(speaker)}
                                >
                                    <span className="speaker-name">{speaker.split(' (')[0]}</span>
                                    {bySpeaker[speaker]?.network?.party && (
                                        <span className="speaker-party">{bySpeaker[speaker].network.party}</span>
                                    )}
                                </button>
                            ))}
                            {filteredSpeakers.length === 0 && (
                                <div className="no-results">Nessun risultato</div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Speaker Profile */}
                <div className="analytics-card speaker-profile-wrapper">
                    <SpeakerProfileCard
                        speakerName={selectedSpeaker}
                        speakerStats={selectedSpeaker ? bySpeaker[selectedSpeaker] : null}
                        clusters={clusters}
                    />
                </div>

                {/* Rankings Section */}
                <div className="analytics-card full-width">
                    <div className="card-header" style={{ justifyContent: 'space-between' }}>
                        <h3><TrendingUp size={18} /> Classifiche</h3>
                        <div style={{ minWidth: '200px' }}>
                            <CustomDropdown
                                options={availableCategories.map(c => ({ value: c.id, label: c.label }))}
                                value={selectedRankingCategory}
                                onChange={(e) => setSelectedRankingCategory(e.target.value)}
                            />
                        </div>
                    </div>
                    <div className="card-content">
                        {currentRanking.data.length > 0 ? (
                            <div className="rankings-grid">
                                <RankingCard
                                    title={currentRanking.category?.label || 'Classifica'}
                                    icon={currentRanking.category?.icon || TrendingUp}
                                    rankings={currentRanking.data}
                                    color={currentRanking.category?.color || '#6366f1'}
                                    maxItems={10}
                                    formatValue={(v) => `${v.toFixed(1)} ${currentRanking.category?.unit || ''}`}
                                />
                            </div>
                        ) : (
                            <div className="empty-state">
                                <TrendingUp size={32} />
                                <p>Nessun dato disponibile per questa classifica</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SpeakerStatsTab;
