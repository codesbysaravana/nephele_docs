/**
 * @file transcript-view.js
 * @description Conversation timeline for the live interview.
 */

import { escapeHTML } from '../utils/helpers.js';

export function renderTranscriptView(messages) {
    if (!messages || messages.length === 0) {
        return `
            <div class="flex-1 flex items-center justify-center text-slate-500 text-sm font-mono" id="transcript-empty">
                Listening for speech...
            </div>
            <div class="flex flex-col gap-4 overflow-y-auto w-full max-h-[300px] hidden" id="transcript-list"></div>
        `;
    }

    const msgsHtml = messages.map(msg => {
        const isAgent = msg.role === 'assistant';
        const roleName = isAgent ? 'Nephele' : 'Candidate';
        const bubbleClass = isAgent ? 'agent' : 'user';
        
        return `
            <div class="message-bubble ${bubbleClass}">
                <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5 font-mono">${roleName}</div>
                <div>${escapeHTML(msg.content)}</div>
                ${msg.score ? `<div class="message-meta text-emerald-500">SCORE: ${msg.score.toFixed(1)}</div>` : ''}
            </div>
        `;
    }).join('');

    return `
        <div class="flex flex-col gap-4 overflow-y-auto w-full max-h-[300px]" id="transcript-list">
            ${msgsHtml}
        </div>
    `;
}

/**
 * Append a single message to an existing transcript DOM without full re-render.
 */
export function appendTranscriptMessage(msg) {
    const list = document.getElementById('transcript-list');
    const emptyMsg = document.getElementById('transcript-empty');
    
    if (!list) return;
    
    if (emptyMsg) {
        emptyMsg.classList.add('hidden');
        list.classList.remove('hidden');
    }

    const isAgent = msg.role === 'assistant';
    const roleName = isAgent ? 'Nephele' : 'Candidate';
    const bubbleClass = isAgent ? 'agent' : 'user';
    
    const div = document.createElement('div');
    div.className = `message-bubble ${bubbleClass}`;
    div.innerHTML = `
        <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5 font-mono">${roleName}</div>
        <div>${escapeHTML(msg.content)}</div>
        ${msg.score ? `<div class="message-meta text-emerald-500">SCORE: ${msg.score.toFixed(1)}</div>` : ''}
    `;

    list.appendChild(div);
    list.scrollTop = list.scrollHeight;
}
