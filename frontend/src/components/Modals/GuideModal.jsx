import React from 'react';
import { X, BarChart3, Users, TrendingUp, Layers } from 'lucide-react';

const GuideModal = ({ onClose }) => {
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="guide-modal" onClick={e => e.stopPropagation()}>
                <div className="guide-header">
                    <h2>Come interpretare la mappa</h2>
                    <button className="close-btn" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>

                <div className="guide-content">
                    <div className="guide-section">
                        <div className="guide-icon"><BarChart3 size={20} /></div>
                        <div>
                            <h3>Il Grafico</h3>
                            <p>Ogni punto rappresenta un discorso (o un deputato, a seconda della vista).
                                I punti vicini trattano argomenti simili.</p>
                        </div>
                    </div>

                    <div className="guide-section">
                        <div className="guide-icon"><Layers size={20} /></div>
                        <div>
                            <h3>I Cluster</h3>
                            <p>I colori indicano i cluster tematici: gruppi di discorsi che trattano
                                argomenti simili (es. Economia, Giustizia, Ambiente).</p>
                        </div>
                    </div>

                    <div className="guide-section">
                        <div className="guide-icon"><Users size={20} /></div>
                        <div>
                            <h3>Vista Deputati</h3>
                            <p>Nella vista "Deputati", ogni punto è la posizione media di tutti i discorsi
                                di quel deputato. La dimensione indica il numero di interventi.</p>
                        </div>
                    </div>

                    <div className="guide-section">
                        <div className="guide-icon"><TrendingUp size={20} /></div>
                        <div>
                            <h3>Rebel Score</h3>
                            <p>Indica la percentuale di discorsi in cui un deputato parla di temi diversi
                                rispetto alla maggioranza del suo partito. Un valore alto indica indipendenza tematica.</p>
                        </div>
                    </div>

                    <div className="guide-tip">
                        <strong>Suggerimento:</strong> Usa la proiezione "Custom" per confrontare
                        direttamente due temi specifici sugli assi X e Y.
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GuideModal;
