/**
 * @file challenge-view.js
 * @description Coding problem display.
 */

import { escapeHTML } from '../utils/helpers.js';

export function renderChallengeView(question) {
    if (!question) return '';
    
    let difficultyColor = 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10';
    if (question.difficulty === 'hard') difficultyColor = 'text-rose-400 border-rose-500/20 bg-rose-500/10';
    else if (question.difficulty === 'medium') difficultyColor = 'text-amber-400 border-amber-500/20 bg-amber-500/10';

    return `
        <div class="card mt-6 fade-up">
            <div class="flex justify-between items-start mb-6">
                <div>
                    <h3 class="text-xl font-bold text-white mb-2">${escapeHTML(question.title)}</h3>
                    <div class="flex gap-2">
                        <span class="badge ${difficultyColor} uppercase tracking-wider text-[10px]">${question.difficulty}</span>
                        <span class="badge badge-slate uppercase tracking-wider text-[10px]">${question.topic}</span>
                    </div>
                </div>
                <div class="text-xs text-slate-500 font-mono">
                    TARGET: ${question.target_complexity}
                </div>
            </div>
            
            <div class="space-y-6 text-sm text-slate-300 leading-relaxed">
                <div>
                    <h4 class="text-xs font-mono text-slate-500 mb-2 tracking-wider">PROBLEM STATEMENT</h4>
                    <p>${escapeHTML(question.description)}</p>
                </div>
                
                ${question.examples && question.examples.length > 0 ? `
                    <div>
                        <h4 class="text-xs font-mono text-slate-500 mb-2 tracking-wider">EXAMPLES</h4>
                        <div class="space-y-3">
                            ${question.examples.map(ex => `
                                <div class="bg-bg-deep p-3 rounded-lg border border-border-subtle font-mono text-xs">
                                    <div class="text-indigo-300 mb-1">Input: ${escapeHTML(ex.input)}</div>
                                    <div class="text-emerald-300 mb-1">Output: ${escapeHTML(ex.output)}</div>
                                    ${ex.explanation ? `<div class="text-slate-500 mt-2">Explanation: ${escapeHTML(ex.explanation)}</div>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${question.constraints && question.constraints.length > 0 ? `
                    <div>
                        <h4 class="text-xs font-mono text-slate-500 mb-2 tracking-wider">CONSTRAINTS</h4>
                        <ul class="list-disc list-inside space-y-1 text-slate-400">
                            ${question.constraints.map(c => `<li>${escapeHTML(c)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
            
            <!-- Explanation Input Form -->
            <div class="mt-8 pt-6 border-t border-border-subtle">
                <h4 class="text-xs font-mono text-slate-500 mb-3 tracking-wider">PROVIDE YOUR VERBAL EXPLANATION</h4>
                <div class="flex flex-col gap-3">
                    <textarea 
                        id="coding-explanation-input" 
                        class="input font-sans text-sm h-32" 
                        placeholder="Explain your approach, data structures, algorithm, and time/space complexity..."
                    ></textarea>
                    
                    <div class="flex justify-between items-center">
                        <span class="text-xs text-slate-500" id="coding-eval-error"></span>
                        <button id="btn-submit-explanation" class="btn btn-primary">
                            Evaluate Approach
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}
