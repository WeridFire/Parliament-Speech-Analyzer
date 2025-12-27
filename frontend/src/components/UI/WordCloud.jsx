/**
 * WordCloud Component - Enhanced canvas-based word cloud visualization
 */
import React, { useRef, useEffect, useMemo } from 'react';

// Vibrant color palette
const COLORS = [
    '#818cf8', '#a78bfa', '#c084fc', '#22d3ee', '#34d399',
    '#fbbf24', '#fb7185', '#60a5fa', '#4ade80', '#f472b6',
];

const WordCloud = ({
    words = [],
    width = 400,
    height = 320,
    minFontSize = 10,
    maxFontSize = 38
}) => {
    const canvasRef = useRef(null);

    // Transform words with exponential weight decay
    const wordData = useMemo(() => {
        if (!words.length) return [];

        return words.slice(0, 50).map((word, index) => ({
            text: word,
            // Exponential decay for more dramatic size differences
            weight: Math.pow(0.85, index),
            color: COLORS[index % COLORS.length]
        }));
    }, [words]);

    // Calculate font sizes with dramatic scaling
    const scaledWords = useMemo(() => {
        if (!wordData.length) return [];

        const maxWeight = wordData[0]?.weight || 1;

        return wordData.map(word => ({
            ...word,
            fontSize: Math.round(minFontSize + (word.weight / maxWeight) * (maxFontSize - minFontSize))
        }));
    }, [wordData, minFontSize, maxFontSize]);

    // Draw word cloud
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !scaledWords.length) return;

        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;

        canvas.width = width * dpr;
        canvas.height = height * dpr;
        ctx.scale(dpr, dpr);
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;

        ctx.clearRect(0, 0, width, height);

        const placedWords = [];
        const centerX = width / 2;
        const centerY = height / 2;

        // Sort by size (largest first)
        const sortedWords = [...scaledWords].sort((a, b) => b.fontSize - a.fontSize);

        sortedWords.forEach((word) => {
            // Use system font stack for cleaner look
            ctx.font = `700 ${word.fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
            const metrics = ctx.measureText(word.text);
            const textWidth = metrics.width;
            const textHeight = word.fontSize * 0.8;

            let angle = Math.random() * Math.PI * 2;
            let radius = 0;
            let placed = false;
            let attempts = 0;

            while (!placed && attempts < 1000) {
                const x = centerX + radius * Math.cos(angle) - textWidth / 2;
                const y = centerY + radius * Math.sin(angle) + textHeight / 2;

                const pad = 5;
                if (x >= pad && x + textWidth <= width - pad &&
                    y - textHeight >= pad && y + pad <= height) {

                    const collision = placedWords.some(pw => {
                        const gap = 3;
                        return !(x + textWidth + gap < pw.x ||
                            x > pw.x + pw.width + gap ||
                            y - textHeight > pw.y + gap ||
                            y < pw.y - pw.height - gap);
                    });

                    if (!collision) {
                        ctx.fillStyle = word.color;
                        ctx.fillText(word.text, x, y);

                        placedWords.push({
                            x, y,
                            width: textWidth,
                            height: textHeight
                        });
                        placed = true;
                    }
                }

                angle += 0.25;
                radius += 0.35;
                attempts++;
            }
        });

    }, [scaledWords, width, height]);

    if (!words.length) {
        return (
            <div style={{
                width: '100%',
                height,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#64748b'
            }}>
                Nessuna parola distintiva
            </div>
        );
    }

    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%',
            height: '100%',
            minHeight: height
        }}>
            <canvas ref={canvasRef} />
        </div>
    );
};

export default WordCloud;
