/**
 * NoDataMessage - Component shown when analytics data is missing for a period
 */
import React from 'react';
import { Calendar, AlertCircle } from 'lucide-react';
import './NoDataMessage.css';

const NoDataMessage = ({
    featureName = 'questa analisi',
    period = null
}) => {
    const periodLabel = period?.year
        ? (period.month
            ? `${getMonthName(period.month)} ${period.year}`
            : `anno ${period.year}`)
        : 'questo periodo';

    return (
        <div className="no-data-message">
            <div className="no-data-icon">
                <Calendar size={32} />
            </div>
            <h3>Dati non disponibili</h3>
            <p>
                Sembra che per <strong>{periodLabel}</strong> non ci siano dati
                sufficienti per calcolare <strong>{featureName}</strong>.
            </p>
            <div className="no-data-hint">
                <AlertCircle size={14} />
                <span>Prova a selezionare un periodo diverso o "Tutti gli anni"</span>
            </div>
        </div>
    );
};

// Helper to get Italian month name
const getMonthName = (monthValue) => {
    const months = {
        '01': 'Gennaio', '02': 'Febbraio', '03': 'Marzo', '04': 'Aprile',
        '05': 'Maggio', '06': 'Giugno', '07': 'Luglio', '08': 'Agosto',
        '09': 'Settembre', '10': 'Ottobre', '11': 'Novembre', '12': 'Dicembre'
    };
    return months[monthValue] || monthValue;
};

export default NoDataMessage;
