/**
 * @file resume.js
 * @description Resume workspace.
 */

import { renderUploadZone } from '../components/upload-zone.js';
import { renderProfileCard } from '../components/profile-card.js';
import { escapeHTML } from '../utils/helpers.js';

export function renderResumeWorkspace(state) {
    return `
        <div class="workspace-page" id="page-resume">
            <div class="workspace-header">
                <h2>Resume Intelligence Pipeline</h2>
                <p>Upload resume documents to extract structured profiles via Groq LLM</p>
            </div>
            
            <div class="workspace-scroll">
                <!-- Upload Area -->
                ${renderUploadZone()}
                
                <!-- Profile Area -->
                <div id="resume-profile-container">
                    ${state.candidateProfile ? renderProfileCard(state.candidateProfile) : ''}
                </div>
                
                <!-- Questions Area -->
                <div id="resume-questions-container" class="max-w-4xl mx-auto mt-6">
                    ${state.resumeQuestions && state.resumeQuestions.length > 0 ? `
                        <div class="card fade-up">
                            <h3 class="card-title text-base mb-4">Generated Personalized Interview Questions</h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                                ${state.resumeQuestions.map((q, idx) => `
                                    <div class="bg-bg-panel p-3.5 rounded-xl border border-border-subtle text-xs text-slate-300 flex items-start gap-2.5">
                                        <span class="w-5 h-5 rounded-full bg-indigo-500/10 text-indigo-400 font-bold flex items-center justify-center shrink-0 mt-0.5">${idx + 1}</span>
                                        <span class="leading-relaxed">${escapeHTML(q)}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}
