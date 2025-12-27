import React from 'react';
import { useAppState } from '../../contexts/StateContext';
import { X, Users } from 'lucide-react';
import { getCleanName } from '../../utils/helpers';

const SelectionBar = () => {
    const { selectedDeputies, toggleDeputySelection, clearSelection } = useAppState();

    if (selectedDeputies.length === 0) return null;

    return (
        <div className="selection-bar">
            <div className="selection-info">
                <Users size={16} />
                <span className="selection-count">{selectedDeputies.length} deputati selezionati</span>
            </div>

            <div className="selection-chips">
                {selectedDeputies.slice(0, 5).map(deputy => (
                    <div key={deputy} className="selection-chip">
                        <span>{getCleanName(deputy)}</span>
                        <button onClick={() => toggleDeputySelection(deputy)}>
                            <X size={12} />
                        </button>
                    </div>
                ))}
                {selectedDeputies.length > 5 && (
                    <span className="more-count">+{selectedDeputies.length - 5} altri</span>
                )}
            </div>

            <button className="clear-all-btn" onClick={clearSelection}>
                <X size={14} />
                <span>Deseleziona tutti</span>
            </button>
        </div>
    );
};

export default SelectionBar;
