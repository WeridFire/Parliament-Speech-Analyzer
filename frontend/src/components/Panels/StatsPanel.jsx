import React from 'react';
import { useAppState } from '../../contexts/StateContext';

const StatsPanel = () => {
    const { data } = useAppState();

    if (!data) return null;

    const stats = data.stats || {};

    return (
        <div className="control-group">
            <label>Statistiche</label>
            <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                <div className="stat-item" style={{ background: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '8px', textAlign: 'center' }}>
                    <span className="stat-value" style={{ display: 'block', fontSize: '1.2rem', color: 'var(--primary)', fontWeight: '600' }}>
                        {stats.total_speeches || 0}
                    </span>
                    <span className="stat-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Discorsi</span>
                </div>
                <div className="stat-item" style={{ background: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '8px', textAlign: 'center' }}>
                    <span className="stat-value" style={{ display: 'block', fontSize: '1.2rem', color: 'var(--primary)', fontWeight: '600' }}>
                        {stats.total_deputies || 0}
                    </span>
                    <span className="stat-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Deputati</span>
                </div>
                <div className="stat-item" style={{ background: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '8px', textAlign: 'center' }}>
                    <span className="stat-value" style={{ display: 'block', fontSize: '1.2rem', color: 'var(--primary)', fontWeight: '600' }}>
                        {stats.total_parties || 0}
                    </span>
                    <span className="stat-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Partiti</span>
                </div>
            </div>
        </div>
    );
};

export default StatsPanel;
