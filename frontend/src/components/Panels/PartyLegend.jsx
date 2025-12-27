import React from 'react';
import { PARTY_CONFIG, PARTY_COLORS } from '../../utils/constants';

const PartyLegend = () => {
    return (
        <div className="control-group">
            <label>Legenda Partiti</label>
            <div className="party-legend" style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {Object.entries(PARTY_CONFIG).map(([party, config]) => {
                    const color = PARTY_COLORS[party] || '#888';

                    // Simple shape representation
                    let shape = '●';
                    if (config.shape === 'diamond') shape = '◆';
                    if (config.shape === 'square') shape = '■';
                    if (config.shape === 'triangle-up') shape = '▲';

                    return (
                        <div key={party} className="party-item" style={{
                            display: 'flex', alignItems: 'center', gap: '4px',
                            padding: '4px 8px', borderRadius: '4px',
                            background: 'rgba(255,255,255,0.05)',
                            fontSize: '0.75rem'
                        }}>
                            <span style={{ color: color, fontSize: '0.9rem' }}>{shape}</span>
                            <span>{config.label}</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default PartyLegend;
