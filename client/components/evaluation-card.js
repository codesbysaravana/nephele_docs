/**
 * @file evaluation-card.js
 * @description Score visualization for coding evaluation.
 */

import { formatScoreBadge, escapeHTML } from '../utils/helpers.js';

export function renderEvaluationCard(evalData) {
    if (!evalData || !evalData.scores) return '';
    
    const overall = formatScoreBadge(evalData.overall_score);
    const scores = evalData.scores;

    // Helper to render score bars
    const renderBar = (label, scoreValue) => {
        const score = Number(scoreValue) || 0;
        const percent = score * 10;
        let colorClass = 'low';
        if (score >= 8.0) colorClass = 'high';
        else if (score >= 5.0) colorClass = 'mid';

        return `
            <div class="mb-3">
                <div class="flex justify-between text-[10px] font-mono mb-1.5">
                    <span class="text-slate-400 tracking-wider">${label}</span>
                    <span class="text-slate-300 font-bold">${score.toFixed(1)}/10</span>
                </div>
                <div class="score-bar-track">
                    <div class="score-bar-fill ${colorClass}" style="width: ${percent}%"></div>
                </div>
            </div>
        `;
    };

    return `
        <div class="card mt-6 border-indigo-500/30 bg-indigo-500/5 fade-up">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-white flex items-center gap-2">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-indigo-400"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                    Evaluation Results
                </h3>
                <div class="text-right">
                    <div class="text-[10px] text-slate-500 font-mono mb-1">OVERALL SCORE</div>
                    <div class="text-2xl font-bold ${overall.colorClass.split(' ')[1]}">${evalData.overall_score.toFixed(1)}<span class="text-sm opacity-50">/10</span></div>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <!-- Scores -->
                <div>
                    <h4 class="text-xs font-mono text-slate-500 mb-4 tracking-wider">METRICS</h4>
                    ${renderBar('ALGORITHMIC LOGIC', scores.algorithmic_logic)}
                    ${renderBar('DATA STRUCTURES', scores.data_structures)}
                    ${renderBar('TIME COMPLEXITY', scores.time_complexity)}
                    ${renderBar('SPACE COMPLEXITY', scores.space_complexity)}
                    ${renderBar('COMMUNICATION', scores.communication_clarity)}
                </div>

                <!-- Feedback -->
                <div class="space-y-4 text-sm">
                    <div>
                        <h4 class="text-xs font-mono text-slate-500 mb-2 tracking-wider">STRENGTHS</h4>
                        <div class="bg-emerald-500/10 border border-emerald-500/20 p-3 rounded-lg text-emerald-100/90 leading-relaxed">
                            ${escapeHTML(evalData.strengths)}
                        </div>
                    </div>
                    <div>
                        <h4 class="text-xs font-mono text-slate-500 mb-2 tracking-wider">WEAKNESSES</h4>
                        <div class="bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg text-rose-100/90 leading-relaxed">
                            ${escapeHTML(evalData.weaknesses)}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-6 pt-6 border-t border-border-subtle">
                <h4 class="text-xs font-mono text-slate-500 mb-3 tracking-wider">DETAILED FEEDBACK</h4>
                <p class="text-sm text-slate-300 leading-relaxed bg-bg-panel/50 p-4 rounded-xl border border-border-subtle">
                    ${escapeHTML(evalData.detailed_feedback)}
                </p>
            </div>
        </div>
    `;
}
