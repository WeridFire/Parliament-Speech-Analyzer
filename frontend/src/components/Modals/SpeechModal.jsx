import React from 'react';
import { X } from 'lucide-react';
import { getCleanName } from '../../utils/helpers';

const SpeechModal = ({ speech, onClose }) => {
    if (!speech) return null;

    // Clean text: remove leading punctuation and capitalize first letter
    const cleanText = (text) => {
        if (!text) return '';
        // Remove leading punctuation, spaces, and special chars
        let cleaned = text.replace(/^[\s.,;:!?'"()\-–—]+/, '').trim();
        // Capitalize first letter
        if (cleaned.length > 0) {
            cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
        }
        return cleaned;
    };

    const displayText = cleanText(speech.text || speech.snippet || '');

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>{getCleanName(speech.deputy)}</h3>
                    <button className="modal-close-btn" onClick={onClose}><X size={20} /></button>
                </div>
                <div className="modal-body">
                    <div className="modal-meta">
                        <span className="party-tag">{speech.party || 'Unknown'}</span>
                        <span className="cluster-tag">{speech.cluster_label || `Cluster ${speech.cluster}`}</span>
                        <span className="date-tag">{speech.date || 'N/A'}</span>
                    </div>

                    <div className="speech-text">
                        <div className="snippet">
                            {/* Show snippet or truncated text */}
                            {displayText.length > 400 ? displayText.slice(0, 400) + '...' : displayText}
                            <br />
                            {speech.url && (
                                <a
                                    href={speech.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="read-more-btn"
                                    style={{ display: 'inline-block', marginTop: '10px', textDecoration: 'none' }}
                                >
                                    Leggi originale su {speech.source === 'camera' ? 'camera.it' : 'senato.it'} →
                                </a>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SpeechModal;
