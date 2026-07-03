/**
 * @file status-bar.js
 * @description Bottom connection/session bar.
 */

export function renderStatusBar(healthStatus, sessionId, interviewState) {
    const isOnline = healthStatus !== null;
    const dotClass = isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500';
    const statusText = isOnline 
        ? `ONLINE • ${healthStatus?.active_sessions || 0} SESSIONS`
        : 'OFFLINE';

    return `
        <div class="status-bar">
            <div class="flex items-center gap-2 cursor-pointer" id="status-health-btn" title="Click to refresh health">
                <div class="w-2 h-2 rounded-full ${dotClass}"></div>
                <span>${statusText}</span>
            </div>
            
            <div class="flex-1"></div>
            
            ${sessionId ? `
                <div class="flex items-center gap-4 text-xs">
                    <span class="text-indigo-400">SESSION: ${sessionId.split('-')[0]}</span>
                    <span>STATE: ${interviewState || 'IDLE'}</span>
                </div>
            ` : ''}
            
            <div id="status-time">00:00:00</div>
        </div>
    `;
}
