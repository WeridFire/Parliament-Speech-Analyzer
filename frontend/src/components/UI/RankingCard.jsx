/**
 * RankingCard - Reusable ranking list component
 * 
 * DRY component to display top N rankings with score bars
 */
import React from 'react';
import PropTypes from 'prop-types';

/**
 * @param {Object} props
 * @param {string} props.title - Card title
 * @param {string} [props.subtitle] - Optional subtitle
 * @param {React.ComponentType} props.icon - Lucide icon component
 * @param {Array<[string, number]>} props.rankings - Array of [name, score] tuples
 * @param {function} [props.formatValue] - Custom value formatter (default: toFixed(0))
 * @param {string} [props.color='#6366f1'] - Theme color for bars
 * @param {number} [props.maxItems=10] - Max items to show
 * @param {boolean} [props.showBar=true] - Whether to show score bars
 * @param {function} [props.getSubtitle] - Optional function to get subtitle for each item
 */
const RankingCard = ({
    title,
    subtitle,
    icon: Icon,
    rankings = [],
    formatValue = (v) => typeof v === 'number' ? v.toFixed(0) : v,
    color = '#6366f1',
    maxItems = 10,
    showBar = true,
    getSubtitle = null
}) => {
    if (!rankings || rankings.length === 0) {
        return (
            <div className="analytics-card">
                <div className="card-header">
                    <h3>{Icon && <Icon size={18} />} {title}</h3>
                    {subtitle && <span className="card-subtitle">{subtitle}</span>}
                </div>
                <div className="card-content">
                    <div className="empty-state">
                        {Icon && <Icon size={32} />}
                        <p>Dati non disponibili</p>
                    </div>
                </div>
            </div>
        );
    }

    // Normalize rankings - ensure we have max value for percentage
    const maxScore = Math.max(...rankings.map(([, score]) => Math.abs(score)));
    const displayItems = rankings.slice(0, maxItems);

    return (
        <div className="analytics-card">
            <div className="card-header">
                <h3>{Icon && <Icon size={18} />} {title}</h3>
                {subtitle && <span className="card-subtitle">{subtitle}</span>}
            </div>
            <div className="card-content">
                <div className="ranking-list">
                    {displayItems.map(([name, score], idx) => {
                        const percentage = maxScore > 0 ? (Math.abs(score) / maxScore) * 100 : 0;
                        const positionClass = idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : '';
                        
                        return (
                            <div key={name} className="ranking-item">
                                <span className={`ranking-position ${positionClass}`}>
                                    {idx + 1}
                                </span>
                                <div className="ranking-info">
                                    <div className="ranking-name">{name.split(' (')[0]}</div>
                                    {getSubtitle && (
                                        <div className="ranking-party">{getSubtitle(name, score, idx)}</div>
                                    )}
                                </div>
                                {showBar ? (
                                    <div className="score-bar-container">
                                        <div className="score-bar">
                                            <div
                                                className="score-bar-fill"
                                                style={{
                                                    width: `${percentage}%`,
                                                    background: `linear-gradient(90deg, ${color}, ${color}cc)`
                                                }}
                                            />
                                        </div>
                                        <span className="score-value" style={{ color }}>
                                            {formatValue(score)}
                                        </span>
                                    </div>
                                ) : (
                                    <span className="score-value" style={{ color }}>
                                        {formatValue(score)}
                                    </span>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

RankingCard.propTypes = {
    title: PropTypes.string.isRequired,
    subtitle: PropTypes.string,
    icon: PropTypes.elementType,
    rankings: PropTypes.arrayOf(PropTypes.array).isRequired,
    formatValue: PropTypes.func,
    color: PropTypes.string,
    maxItems: PropTypes.number,
    showBar: PropTypes.bool,
    getSubtitle: PropTypes.func
};

export default RankingCard;
