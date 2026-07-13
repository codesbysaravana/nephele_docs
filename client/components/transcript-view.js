/**
 * @file transcript-view.js
 * @description Conversation timeline for the live interview.
 */

import { escapeHTML } from '../utils/helpers.js';

export function renderTranscriptView(messages) {
    if (!messages || messages.length === 0) {
        return `
            <div class="flex-1 flex items-center justify-center text-on-surface-variant text-sm font-label-mono" id="transcript-empty">
                Listening for speech...
            </div>
            <div class="flex-1 overflow-y-auto pr-sm space-y-lg pb-md hidden" id="transcript-list"></div>
        `;
    }

    const msgsHtml = messages.map(msg => renderMessageBubble(msg)).join('');

    return `
        <div class="flex-1 overflow-y-auto pr-sm space-y-lg pb-md" id="transcript-list">
            ${msgsHtml}
        </div>
    `;
}

function renderMessageBubble(msg) {
    const isAgent = msg.role === 'assistant';
    const roleName = isAgent ? 'Nephele' : 'Candidate'; // Could read candidateName from store if available
    const time = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' });

    if (isAgent) {
        return `
            <div class="flex flex-col items-start max-w-[85%]">
                <span class="font-label-mono text-[10px] text-on-surface-variant uppercase mb-1 opacity-50">${roleName} • ${time}</span>
                <p class="font-transcript text-[24px] leading-relaxed text-primary font-light">
                    ${escapeHTML(msg.content)}
                </p>
                ${msg.score ? `<div class="font-label-mono text-[10px] text-[#10b981] mt-1">SCORE: ${msg.score.toFixed(1)}</div>` : ''}
            </div>
        `;
    } else {
        return `
            <div class="flex flex-col items-end max-w-[85%] ml-auto">
                <span class="font-label-mono text-[10px] text-on-surface-variant uppercase mb-1 opacity-50">${roleName} • ${time}</span>
                <div class="bg-[#1C1C28]/60 backdrop-blur-md px-md py-sm rounded-xl rounded-tr-sm border border-[#4b8eff]/10">
                    <p class="font-transcript text-[20px] leading-relaxed text-primary/90 font-light italic">
                        ${escapeHTML(msg.content)}
                    </p>
                </div>
            </div>
        `;
    }
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

    const div = document.createElement('div');
    // We don't add classes to div because renderMessageBubble returns the outer flex container
    // Wait, list.appendChild(div) creates a wrapper div. Let's just use insertAdjacentHTML.
    list.insertAdjacentHTML('beforeend', renderMessageBubble(msg));
    list.scrollTop = list.scrollHeight;
}
