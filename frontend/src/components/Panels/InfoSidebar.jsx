import React from 'react';
import { BarChart2 } from 'lucide-react';
import StatsPanel from './StatsPanel';
import ClusterLegend from './ClusterLegend';
import PartyLegend from './PartyLegend';

const InfoSidebar = () => {
    return (
        <aside className="panel" style={{ borderLeft: '1px solid var(--glass-border)', borderRight: 'none' }}>
            <div className="panel-header">
                <h2><BarChart2 size={18} style={{ marginRight: 8 }} /> Insights</h2>
            </div>

            <div className="panel-content">
                <StatsPanel />
                <hr style={{ borderColor: 'var(--glass-border)', margin: '20px 0' }} />
                <ClusterLegend />
                <hr style={{ borderColor: 'var(--glass-border)', margin: '20px 0' }} />
                <PartyLegend />
            </div>
        </aside>
    );
};

export default InfoSidebar;
