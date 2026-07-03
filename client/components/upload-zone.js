/**
 * @file upload-zone.js
 * @description Drag-drop file upload component.
 */

export function renderUploadZone() {
    return `
        <div class="card max-w-2xl mx-auto mt-8">
            <h3 class="card-title text-center text-lg mb-2">Resume Intelligence</h3>
            <p class="card-subtitle text-center mb-8">Upload a PDF or DOCX to extract structured candidate profiles</p>
            
            <div id="drop-zone" class="upload-zone mb-6">
                <input type="file" id="resume-file-input" class="sr-only" accept=".pdf,.docx">
                
                <div id="upload-idle-state" class="flex flex-col items-center pointer-events-none">
                    <div class="w-12 h-12 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 mb-4">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                        </svg>
                    </div>
                    <p class="text-sm font-medium text-slate-200 mb-1">Click to upload or drag and drop</p>
                    <p class="text-xs text-slate-500 font-mono">PDF or DOCX (Max 10MB)</p>
                </div>

                <div id="upload-file-state" class="hidden flex-col items-center">
                    <div class="w-12 h-12 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400 mb-4">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                            <polyline points="10 9 9 9 8 9"></polyline>
                        </svg>
                    </div>
                    <p class="text-sm font-medium text-emerald-400 mb-1 truncate max-w-xs" id="selected-file-name"></p>
                    <p class="text-xs text-slate-500 font-mono" id="selected-file-size"></p>
                </div>
            </div>

            <div class="text-rose-400 text-xs text-center mb-6 min-h-[20px]" id="upload-error-box"></div>

            <div class="flex justify-center gap-4">
                <button id="clear-file-btn" class="btn btn-secondary hidden">Clear</button>
                <button id="upload-submit-btn" class="btn btn-primary" disabled>
                    Extract Profile
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </button>
            </div>
        </div>
    `;
}
