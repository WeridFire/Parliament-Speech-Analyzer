import React, { useState } from 'react';
import { useAppState } from './contexts/StateContext';
import HomePage from './components/HomePage';
import ControlSidebar from './components/Controls/ControlSidebar';
import RebelsPanel from './components/Panels/RebelsPanel';
import ScatterPlot from './components/Chart/ScatterPlot';
import SpeechModal from './components/Modals/SpeechModal';
import RebelModal from './components/Modals/RebelModal';
import AnalyticsDashboard from './components/Analytics/AnalyticsDashboard';
import { Loader, PanelLeftClose, PanelLeft, PanelRightClose, PanelRight } from 'lucide-react';

const App = () => {
  // Page navigation: 'home' | 'mappa' | 'analytics'
  const [currentPage, setCurrentPage] = useState('home');

  const {
    data, loading, error,
    modal, closeModal,
    leftSidebarOpen, toggleLeftSidebar,
    rightSidebarOpen, toggleRightSidebar
  } = useAppState();

  // Home Page
  if (currentPage === 'home') {
    return (
      <HomePage
        onEnter={() => setCurrentPage('mappa')}
        onAnalytics={() => setCurrentPage('analytics')}
      />
    );
  }

  // Analytics Dashboard
  if (currentPage === 'analytics') {
    return (
      <AnalyticsDashboard
        onBack={() => setCurrentPage('mappa')}
      />
    );
  }

  // Mappa Semantica (main visualization)
  if (loading) return (
    <div className="loading-screen">
      <Loader className="animate-spin" size={48} />
      <span>Caricamento mappa semantica...</span>
    </div>
  );

  if (error) return (
    <div className="error-screen">
      <h2>Errore nel caricamento</h2>
      <p>{error.message}</p>
    </div>
  );

  return (
    <div className="app-container">
      {/* Left Sidebar Toggle */}
      <button
        className={`sidebar-toggle left ${!leftSidebarOpen ? 'collapsed' : ''}`}
        onClick={toggleLeftSidebar}
        title={leftSidebarOpen ? 'Chiudi controlli' : 'Apri controlli'}
      >
        {leftSidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeft size={18} />}
      </button>

      {/* Left Sidebar */}
      {leftSidebarOpen && (
        <ControlSidebar
          onGoHome={() => setCurrentPage('home')}
          onGoAnalytics={() => setCurrentPage('analytics')}
        />
      )}

      {/* Main Content */}
      <main className="main-content">
        <ScatterPlot />
      </main>

      {/* Right Sidebar */}
      {rightSidebarOpen && <RebelsPanel />}

      {/* Right Sidebar Toggle */}
      <button
        className={`sidebar-toggle right ${!rightSidebarOpen ? 'collapsed' : ''}`}
        onClick={toggleRightSidebar}
        title={rightSidebarOpen ? 'Chiudi rebels' : 'Apri rebels'}
      >
        {rightSidebarOpen ? <PanelRightClose size={18} /> : <PanelRight size={18} />}
      </button>

      {/* Modals */}
      {modal.isOpen && modal.type === 'speech' && (
        <SpeechModal speech={modal.data} onClose={closeModal} />
      )}

      {modal.isOpen && modal.type === 'rebel' && (
        <RebelModal
          rebelData={modal.data}
          clusters={data.clusters}
          onClose={closeModal}
        />
      )}
    </div>
  );
};

export default App;

