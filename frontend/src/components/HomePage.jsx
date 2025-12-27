import React from 'react';
import { Map, GitBranch, Users, TrendingUp, ArrowRight, Github, Sparkles, BarChart3 } from 'lucide-react';

const HomePage = ({ onEnter, onAnalytics }) => {
    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%)',
            color: '#e2e8f0',
            overflow: 'auto'
        }}>
            {/* Hero Section */}
            <header style={{
                padding: '40px 20px 30px',
                textAlign: 'center',
                maxWidth: '800px',
                margin: '0 auto'
            }}>
                <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '10px',
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                    padding: '6px 16px',
                    borderRadius: '30px',
                    marginBottom: '20px',
                    fontSize: '13px',
                    fontWeight: '500'
                }}>
                    <Sparkles size={16} />
                    Analisi Semantica con AI
                </div>

                <h1 style={{
                    fontSize: 'clamp(2rem, 4vw, 3rem)',
                    fontWeight: '700',
                    lineHeight: '1.1',
                    margin: '0 0 16px 0',
                    background: 'linear-gradient(135deg, #fff 0%, #94a3b8 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                }}>
                    Mappa Semantica del<br />Parlamento Italiano
                </h1>

                <p style={{
                    fontSize: '1rem',
                    color: '#94a3b8',
                    maxWidth: '550px',
                    margin: '0 auto 24px',
                    lineHeight: '1.6'
                }}>
                    Esplora i discorsi di Camera e Senato attraverso una visualizzazione interattiva
                    basata su intelligenza artificiale. Scopri i temi, confronta i partiti
                    e identifica i "ribelli" politici.
                </p>

                <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <button
                        onClick={onEnter}
                        style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '12px 24px',
                            fontSize: '1rem',
                            fontWeight: '600',
                            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                            border: 'none',
                            borderRadius: '10px',
                            color: '#fff',
                            cursor: 'pointer',
                            transition: 'transform 0.2s, box-shadow 0.2s',
                            boxShadow: '0 4px 15px rgba(99, 102, 241, 0.35)'
                        }}
                        onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                        onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}
                    >
                        <Map size={20} /> Esplora la Mappa
                    </button>

                    <button
                        onClick={onAnalytics}
                        style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '12px 24px',
                            fontSize: '1rem',
                            fontWeight: '600',
                            background: 'rgba(255, 255, 255, 0.05)',
                            border: '2px solid rgba(99, 102, 241, 0.5)',
                            borderRadius: '10px',
                            color: '#a5b4fc',
                            cursor: 'pointer',
                            transition: 'transform 0.2s, background 0.2s'
                        }}
                        onMouseOver={e => {
                            e.currentTarget.style.transform = 'translateY(-2px)';
                            e.currentTarget.style.background = 'rgba(99, 102, 241, 0.15)';
                        }}
                        onMouseOut={e => {
                            e.currentTarget.style.transform = 'translateY(0)';
                            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                        }}
                    >
                        <BarChart3 size={20} /> Dashboard Analytics
                    </button>
                </div>
            </header>

            {/* Features Section */}
            <section style={{
                padding: '30px 20px',
                maxWidth: '1100px',
                margin: '0 auto'
            }}>
                <h2 style={{
                    textAlign: 'center',
                    fontSize: '1.4rem',
                    fontWeight: '600',
                    marginBottom: '24px',
                    color: '#e2e8f0'
                }}>
                    Come Funziona
                </h2>

                <div style={{
                    display: 'flex',
                    gap: '20px',
                    overflowX: 'auto',
                    paddingTop: '10px',
                    paddingBottom: '20px',
                    marginTop: '-10px',
                    scrollSnapType: 'x mandatory',
                    WebkitOverflowScrolling: 'touch',
                    scrollbarWidth: 'none',
                    msOverflowStyle: 'none'
                }} className="hide-scrollbar">
                    <FeatureCard
                        icon={<Map size={28} />}
                        title="Mappa Semantica"
                        description="Ogni punto rappresenta un discorso. Discorsi simili per contenuto appaiono vicini nello spazio, creando cluster tematici naturali."
                        color="#6366f1"
                    />
                    <FeatureCard
                        icon={<GitBranch size={28} />}
                        title="Clustering Automatico"
                        description="L'AI raggruppa automaticamente i discorsi per tema: economia, giustizia, sanità e altro. Puoi esplorare ogni cluster nel dettaglio."
                        color="#22c55e"
                    />
                    <FeatureCard
                        icon={<Users size={28} />}
                        title="Confronto Partiti"
                        description="Analizza e confronta la distribuzione tematica dei partiti. Scopri quali temi dominano il discorso di ogni forza politica."
                        color="#f59e0b"
                    />
                    <FeatureCard
                        icon={<TrendingUp size={28} />}
                        title="Indice Ribelli"
                        description="Identifica i deputati che parlano di temi diversi dalla linea del loro partito. Un indicatore di indipendenza o trasversalità."
                        color="#ef4444"
                    />
                </div>
            </section>

            {/* How to Use Section */}
            <section style={{
                padding: '30px 20px',
                background: 'rgba(0,0,0,0.2)',
                marginTop: '20px'
            }}>
                <div style={{ maxWidth: '700px', margin: '0 auto' }}>
                    <h2 style={{
                        textAlign: 'center',
                        fontSize: '1.4rem',
                        fontWeight: '600',
                        marginBottom: '24px',
                        color: '#e2e8f0'
                    }}>
                        Guida Rapida
                    </h2>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <GuideStep number="1" text="Scegli la fonte dati: Camera dei Deputati o Senato della Repubblica" />
                        <GuideStep number="2" text="Esplora la mappa: clicca sui punti per leggere i discorsi, zoom per dettagli" />
                        <GuideStep number="3" text="Filtra per partito o cluster tematico usando i controlli a sinistra" />
                        <GuideStep number="4" text="Confronta i partiti con lo strumento di analisi tematica" />
                        <GuideStep number="5" text="Scopri i 'ribelli' nel pannello dedicato sulla destra" />
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer style={{
                padding: '20px',
                textAlign: 'center',
                borderTop: '1px solid rgba(255,255,255,0.05)'
            }}>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '20px' }}>
                    <a
                        href="https://github.com/WeridFire"
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#64748b', transition: 'color 0.2s' }}
                        onMouseOver={e => e.currentTarget.style.color = '#fff'}
                        onMouseOut={e => e.currentTarget.style.color = '#64748b'}
                    >
                        <Github size={22} />
                    </a>
                </div>
                <p style={{ color: '#475569', fontSize: '11px', marginTop: '12px', margin: '12px 0 0' }}>
                    Dati: Resoconti stenografici • XIX Legislatura
                </p>
            </footer>
        </div>
    );
};

// Feature Card Component
const FeatureCard = ({ icon, title, description, color }) => (
    <div style={{
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: '16px',
        padding: '30px',
        minWidth: '280px',
        maxWidth: '300px',
        flexShrink: 0,
        scrollSnapAlign: 'start',
        transition: 'transform 0.2s, border-color 0.2s'
    }}
        onMouseOver={e => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.borderColor = color;
        }}
        onMouseOut={e => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)';
        }}
    >
        <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '12px',
            background: `${color}20`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: color,
            marginBottom: '20px'
        }}>
            {icon}
        </div>
        <h3 style={{
            fontSize: '1.2rem',
            fontWeight: '600',
            margin: '0 0 12px',
            color: '#e2e8f0'
        }}>{title}</h3>
        <p style={{
            fontSize: '0.95rem',
            color: '#94a3b8',
            margin: 0,
            lineHeight: '1.6'
        }}>{description}</p>
    </div>
);

// Guide Step Component
const GuideStep = ({ number, text }) => (
    <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        padding: '16px 20px',
        background: 'rgba(255,255,255,0.03)',
        borderRadius: '12px',
        border: '1px solid rgba(255,255,255,0.05)'
    }}>
        <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: '700',
            fontSize: '14px',
            flexShrink: 0
        }}>
            {number}
        </div>
        <span style={{ color: '#cbd5e1', fontSize: '15px' }}>{text}</span>
    </div>
);

export default HomePage;
