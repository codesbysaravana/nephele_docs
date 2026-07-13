/**
 * @file profile-card.js
 * @description Candidate profile display component.
 */

import { escapeHTML } from '../utils/helpers.js';

export function renderProfileCard(profile) {
    if (!profile || !profile.resume_data) return '';
    
    const d = profile.resume_data;
    const level = profile.candidate_level || 'UNKNOWN';
    const topics = profile.recommended_topics || [];
    
    let levelBadge = 'badge-slate';
    if (level === 'senior') levelBadge = 'badge-violet';
    if (level === 'mid') levelBadge = 'badge-indigo';
    if (level === 'junior') levelBadge = 'badge-emerald';

    return `
        <div class="card max-w-4xl mx-auto mt-8 fade-up p-8 shadow-sm">
            <div class="flex items-start justify-between border-b border-border-subtle pb-8 mb-8">
                <div>
                    <h2 class="text-3xl font-serif font-bold text-white mb-2 tracking-tight">${escapeHTML(d.name) || 'Unknown Candidate'}</h2>
                    <div class="flex items-center gap-3">
                        <span class="text-slate-400 font-mono text-sm">${escapeHTML(d.email) || 'No email provided'}</span>
                        <div class="w-1 h-1 rounded-full bg-slate-700"></div>
                        <span class="badge ${levelBadge} uppercase tracking-wider text-[10px]">${level}</span>
                    </div>
                </div>
                
                <div class="flex gap-2">
                    ${(d.github_url || d.linkedin_url) ? `
                        ${d.github_url ? `<a href="${escapeHTML(d.github_url)}" target="_blank" class="btn btn-secondary btn-sm" title="GitHub"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg></a>` : ''}
                        ${d.linkedin_url ? `<a href="${escapeHTML(d.linkedin_url)}" target="_blank" class="btn btn-secondary btn-sm" title="LinkedIn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg></a>` : ''}
                    ` : ''}
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <!-- Left Column -->
                <div class="space-y-6">
                    <div>
                        <h4 class="text-xs font-mono text-slate-500 mb-3 tracking-wider">SKILLS & TECHNOLOGIES</h4>
                        <div class="flex flex-wrap gap-2">
                            ${(d.skills && d.skills.length > 0) ? 
                                d.skills.map(skill => `<span class="tag">${escapeHTML(skill)}</span>`).join('') :
                                '<span class="text-sm text-slate-500">None detected</span>'
                            }
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="text-xs font-mono text-slate-500 mb-3 tracking-wider">RECOMMENDED TOPICS</h4>
                        <div class="flex flex-wrap gap-2">
                            ${topics.length > 0 ? 
                                topics.map(t => `<span class="badge badge-slate border-dashed">${escapeHTML(t)}</span>`).join('') :
                                '<span class="text-sm text-slate-500">None</span>'
                            }
                        </div>
                    </div>
                </div>

                <!-- Right Column -->
                <div class="space-y-6">
                    <div>
                        <h4 class="text-xs font-mono text-slate-500 mb-3 tracking-wider">EXPERIENCE (${d.years_of_experience || 0} YRS)</h4>
                        <div class="space-y-4">
                            ${(d.experience && d.experience.length > 0) ? 
                                d.experience.map(exp => `
                                    <div class="border-l-2 border-slate-800 pl-4">
                                        <div class="font-medium text-slate-200 text-sm">${escapeHTML(exp.role)}</div>
                                        <div class="text-xs text-slate-400 mt-1">${escapeHTML(exp.company)} • ${escapeHTML(exp.duration)}</div>
                                    </div>
                                `).join('') :
                                '<span class="text-sm text-slate-500">No experience listed</span>'
                            }
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}
