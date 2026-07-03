/**
 * @file settings.js
 * @description System preferences and session setup.
 */

import { escapeHTML } from '../utils/helpers.js';

export function renderSettings(state) {
    const s = state.settings || {};
    
    return `
        <div class="workspace-page" id="page-settings">
            <div class="workspace-header">
                <h2>System Preferences</h2>
                <p>Configure Nephele session defaults and debug tools.</p>
            </div>
            
            <div class="workspace-scroll">
                <div class="max-w-2xl mx-auto space-y-6 fade-up">
                    
                    <div class="card">
                        <h3 class="card-title text-base mb-4">Interview Profile Defaults</h3>
                        <div class="space-y-4">
                            <div>
                                <label class="label">Candidate Name</label>
                                <input type="text" id="setting-name" class="input" value="${escapeHTML(s.candidateName)}">
                            </div>
                            <div>
                                <label class="label">Target Role</label>
                                <input type="text" id="setting-role" class="input" value="${escapeHTML(s.targetRole)}">
                            </div>
                        </div>
                    </div>
                    
                    <div class="card bg-bg-deep border-border-subtle">
                        <h3 class="card-title text-base mb-2 text-rose-400">Danger Zone</h3>
                        <p class="text-xs text-slate-500 mb-4">These actions cannot be undone.</p>
                        
                        <div class="flex items-center justify-between py-3 border-t border-border-subtle">
                            <div>
                                <div class="font-medium text-sm text-slate-300">Clear Application State</div>
                                <div class="text-xs text-slate-500">Resets all cached profiles, questions, and session data.</div>
                            </div>
                            <button class="btn btn-danger btn-sm" id="btn-clear-state">Reset State</button>
                        </div>
                    </div>
                    
                </div>
            </div>
        </div>
    `;
}
