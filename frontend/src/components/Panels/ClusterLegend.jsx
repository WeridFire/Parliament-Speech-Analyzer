import React from 'react';
import { useAppState } from '../../contexts/StateContext';
import { CLUSTER_COLORS } from '../../utils/constants';

const ClusterLegend = () => {
    const { data } = useAppState();

    if (!data) return null;

    const clusters = data.clusters || {};

    return (
        <div className="control-group">
            <label>Cluster Semantici</label>
            <div className="cluster-legend" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {Object.entries(clusters).map(([id, info]) => {
                    const idx = parseInt(id);
                    const color = CLUSTER_COLORS[idx % CLUSTER_COLORS.length];

                    return (
                        <div key={id} className="cluster-item" style={{
                            display: 'flex', alignItems: 'center', gap: '8px',
                            padding: '6px 8px', borderRadius: '6px',
                            background: 'rgba(255,255,255,0.05)',
                            cursor: 'pointer', transition: 'all 0.2s'
                        }}>
                            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: color }}></div>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: '0.8rem', fontWeight: '500' }}>{info.label}</div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                                    {info.keywords && info.keywords.slice(0, 3).join(', ')}
                                </div>
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{info.count}</div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default ClusterLegend;
