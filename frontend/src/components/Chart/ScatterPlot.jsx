import React, { useMemo } from 'react';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import { useAppState } from '../../contexts/StateContext';
import { CLUSTER_COLORS, PARTY_COLORS, PARTY_CONFIG } from '../../utils/constants';
import { getCleanName, getPartyFromDeputy } from '../../utils/helpers';

const Plot = createPlotlyComponent(Plotly);

const ScatterPlot = () => {
    const {
        data, // Keep original data for clusters/modals
        filteredData, // Use filtered data for visualization
        loading,
        viewMode, colorMode, projectionMode, customAxis,
        selectedDeputies, toggleDeputySelection,
        openModal
    } = useAppState();

    const traces = useMemo(() => {
        if (!filteredData || loading) return [];

        const traceList = [];

        if (viewMode === 'speeches') {
            const speeches = filteredData.speeches;
            let partitions = {};

            if (colorMode === 'cluster') {
                speeches.forEach((s, i) => {
                    s._index = i;
                    if (!partitions[s.cluster]) partitions[s.cluster] = [];
                    partitions[s.cluster].push(s);
                });
            } else { // party
                speeches.forEach((s, i) => {
                    s._index = i;
                    const p = s.party || 'Unknown Group';
                    if (!partitions[p]) partitions[p] = [];
                    partitions[p].push(s);
                });
            }

            Object.entries(partitions).forEach(([key, groupSpeeches]) => {
                let name, color, symbol;

                if (colorMode === 'cluster') {
                    const clusterId = parseInt(key);
                    const clusterInfo = data.clusters[clusterId] || { label: `Cluster ${clusterId}` };
                    name = clusterInfo.label;
                    color = CLUSTER_COLORS[clusterId % CLUSTER_COLORS.length];
                    symbol = groupSpeeches.map(s => {
                        const p = s.party || 'Unknown Group';
                        return PARTY_CONFIG[p]?.shape || 'circle';
                    });
                } else { // party
                    const party = key;
                    const config = PARTY_CONFIG[party] || { label: party, shape: 'circle' };
                    name = config.label;
                    color = PARTY_COLORS[party] || '#888';
                    symbol = config.shape || 'circle';
                }

                const xData = groupSpeeches.map(s =>
                    projectionMode === 'custom' ? (s.topic_scores ? s.topic_scores[customAxis.x] : 0) : s.x
                );
                const yData = groupSpeeches.map(s =>
                    projectionMode === 'custom' ? (s.topic_scores ? s.topic_scores[customAxis.y] : 0) : s.y
                );

                traceList.push({
                    x: xData,
                    y: yData,
                    mode: 'markers',
                    type: 'scatter',
                    name: name,
                    text: groupSpeeches.map(s => {
                        const name = getCleanName(s.deputy);
                        const party = s.party || getPartyFromDeputy(s.deputy);
                        const cluster = s.cluster_label || `Cluster ${s.cluster}`;
                        return `<b>${name}</b><br>Partito: ${party}<br>Cluster: ${cluster}<br>Data: ${s.date || 'N/A'}`;
                    }),
                    hoverinfo: 'text',
                    marker: {
                        size: selectedDeputies.length > 0 ?
                            groupSpeeches.map(s => selectedDeputies.includes(s.deputy) ? 16 : 6) : 8,
                        color: color,
                        opacity: selectedDeputies.length > 0 ?
                            groupSpeeches.map(s => selectedDeputies.includes(s.deputy) ? 1 : 0.2) : 0.7,
                        symbol: symbol,
                        line: { width: 0.5, color: 'rgba(255,255,255,0.3)' }
                    },
                    customdata: groupSpeeches.map(s => ({ type: 'speech', index: s._index, deputy: s.deputy }))
                });
            });

        } else { // Deputies View
            const deputies = filteredData.deputies || data.deputies || [];
            if (deputies.length === 0) return [];

            let partitions = {};

            if (colorMode === 'cluster') {
                deputies.forEach((d, i) => {
                    d._index = i;
                    if (!partitions[d.cluster]) partitions[d.cluster] = [];
                    partitions[d.cluster].push(d);
                });
            } else {
                deputies.forEach((d, i) => {
                    d._index = i;
                    const p = d.party || 'Unknown Group';
                    if (!partitions[p]) partitions[p] = [];
                    partitions[p].push(d);
                });
            }

            Object.entries(partitions).forEach(([key, groupDeputies]) => {
                let name, color, symbol;

                if (colorMode === 'cluster') {
                    const clusterId = parseInt(key);
                    const clusterInfo = data.clusters[clusterId] || { label: `Cluster ${clusterId}` };
                    name = clusterInfo.label;
                    color = CLUSTER_COLORS[clusterId % CLUSTER_COLORS.length];
                    symbol = 'circle';
                } else {
                    const party = key;
                    const config = PARTY_CONFIG[party] || { label: party };
                    name = config.label;
                    color = PARTY_COLORS[party] || '#888';
                    symbol = 'circle';
                }

                // Deputies Custom Projection Logic
                const xData = groupDeputies.map(d =>
                    projectionMode === 'custom' ? (d.topic_scores ? d.topic_scores[customAxis.x] : 0) : d.x
                );
                const yData = groupDeputies.map(d =>
                    projectionMode === 'custom' ? (d.topic_scores ? d.topic_scores[customAxis.y] : 0) : d.y
                );

                traceList.push({
                    x: xData,
                    y: yData,
                    mode: 'markers',
                    type: 'scatter',
                    name: name,
                    text: groupDeputies.map(d =>
                        `<b>${d.name}</b><br>Partito: ${d.party}<br>Discorsi: ${d.n_speeches}<br>Cluster: ${d.cluster_label}<br>Rebel: ${d.rebel_pct}%`
                    ),
                    hoverinfo: 'text',
                    marker: {
                        size: groupDeputies.map(d => {
                            const baseSize = Math.min(8 + d.n_speeches * 0.5, 20);
                            return selectedDeputies.includes(d.deputy) ? baseSize + 10 : baseSize;
                        }),
                        color: color,
                        opacity: selectedDeputies.length > 0 ?
                            groupDeputies.map(d => selectedDeputies.includes(d.deputy) ? 1 : 0.3) : 0.9,
                        symbol: symbol,
                        line: {
                            width: groupDeputies.map(d => selectedDeputies.includes(d.deputy) ? 3 : 1),
                            color: groupDeputies.map(d => selectedDeputies.includes(d.deputy) ? '#fff' : 'rgba(255,255,255,0.5)')
                        }
                    },
                    customdata: groupDeputies.map(d => ({ type: 'deputy', deputy: d.deputy }))
                });
            });
        }

        return traceList;
    }, [filteredData, loading, viewMode, colorMode, projectionMode, customAxis, selectedDeputies]);

    const layout = useMemo(() => {
        let xTitle = 'PC1';
        let yTitle = 'PC2';

        if (projectionMode === 'custom' && data?.clusters) {
            const xLabel = data.clusters[customAxis.x]?.label || '';
            const yLabel = data.clusters[customAxis.y]?.label || '';
            xTitle = `Similarity: ${xLabel}`;
            yTitle = `Similarity: ${yLabel}`;
        }

        return {
            title: false,
            autosize: true,
            hovermode: 'closest',
            dragmode: 'zoom',
            showlegend: true,
            legend: { x: 1.02, y: 1, bgcolor: 'rgba(26, 26, 46, 0.95)', font: { color: '#e5e5e5' } },
            margin: { l: 50, r: 20, t: 20, b: 50 },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#e0e0e0' },
            xaxis: {
                showgrid: true,
                gridcolor: 'rgba(255,255,255,0.1)',
                zerolinecolor: 'rgba(255,255,255,0.2)',
                title: { text: xTitle, font: { color: '#888' } }
            },
            yaxis: {
                showgrid: true,
                gridcolor: 'rgba(255,255,255,0.1)',
                zerolinecolor: 'rgba(255,255,255,0.2)',
                title: { text: yTitle, font: { color: '#888' } }
            }
        };
    }, [projectionMode, customAxis, data]);

    const handleClick = (event) => {
        const point = event.points[0];
        const custom = point.customdata;
        if (custom) {
            if (custom.type === 'speech') {
                openModal('speech', data.speeches[custom.index]);
            } else if (custom.type === 'deputy') {
                // Toggle selection for multi-select
                toggleDeputySelection(custom.deputy);

                // Also open modal with rebel data
                const depName = custom.deputy;
                const key = Object.keys(data.all_rebel_scores || {}).find(k => k.includes(depName)) || depName;
                const rebelInfo = data.all_rebel_scores?.[key];

                if (rebelInfo) {
                    // Add deputy field since it's the key, not stored inside
                    openModal('rebel', { ...rebelInfo, deputy: key });
                } else {
                    const basicRebelPayload = {
                        deputy: depName,
                        rebel_pct: 0,
                        total_speeches: 0,
                        cluster_distribution: {},
                        party_cluster_distribution: {}
                    };
                    openModal('rebel', basicRebelPayload);
                }
            }
        }
    };

    if (loading) return <div className="text-white">Loading data...</div>;

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <Plot
                data={traces}
                layout={layout}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
                onClick={handleClick}
                config={{ responsive: true, displayModeBar: true }}
            />
        </div>
    );
};

export default ScatterPlot;
