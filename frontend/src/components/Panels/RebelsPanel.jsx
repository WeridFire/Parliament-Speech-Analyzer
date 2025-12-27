import React from 'react';
import { useAppState } from '../../contexts/StateContext';
import { AlertTriangle, TrendingUp, ChevronRight } from 'lucide-react';
import { getCleanName } from '../../utils/helpers';

const RebelsPanel = () => {
    const { data, openModal, toggleDeputySelection } = useAppState();

    if (!data || !data.rebels) return null;

    const topRebels = data.rebels;

    const handleRebelClick = (rebel) => {
        const baseRebelData = data.all_rebel_scores?.[rebel.deputy] || {};
        const rebelData = {
            deputy: rebel.deputy,
            rebel_pct: rebel.rebel_pct || baseRebelData.rebel_pct || 0,
            total_speeches: rebel.total_speeches || baseRebelData.total_speeches || 0,
            party: rebel.party || baseRebelData.party,
            cluster_distribution: baseRebelData.cluster_distribution || {},
            party_cluster_distribution: baseRebelData.party_cluster_distribution || {},
            speeches_in_main: baseRebelData.speeches_in_main || 0,
            main_cluster: baseRebelData.main_cluster
        };
        toggleDeputySelection(rebel.deputy);
        openModal('rebel', rebelData);
    };

    return (
        <aside className="rebels-sidebar">
            <div className="sidebar-header">
                <AlertTriangle size={20} className="header-icon" />
                <div>
                    <h2>Top Rebels</h2>
                    <p className="subtitle">Deputati fuori linea di partito</p>
                </div>
            </div>

            <div className="rebels-list">
                {topRebels.map((rebel, index) => {
                    const rebelScore = rebel.rebel_pct || 0;
                    const isHighRebel = rebelScore > 50;

                    return (
                        <div
                            key={rebel.deputy}
                            className={`rebel-card ${isHighRebel ? 'high-rebel' : ''}`}
                            onClick={() => handleRebelClick(rebel)}
                        >
                            <div className="rebel-rank">#{index + 1}</div>
                            <div className="rebel-info">
                                <div className="rebel-name">{getCleanName(rebel.deputy)}</div>
                                <div className="rebel-party">{rebel.party}</div>
                            </div>
                            <div className="rebel-score">
                                <TrendingUp size={14} />
                                <span>{rebelScore}%</span>
                            </div>
                            <ChevronRight size={16} className="rebel-arrow" />
                        </div>
                    );
                })}
            </div>

            <div className="rebels-footer">
                <p className="explanation">
                    Il <strong>Rebel Score</strong> indica la % di discorsi
                    in cluster diversi da quello dominante del partito.
                </p>
            </div>
        </aside>
    );
};

export default RebelsPanel;
