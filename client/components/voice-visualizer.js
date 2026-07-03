/**
 * @file voice-visualizer.js
 * @description Audio-reactive ring visualization for speech feedback.
 */

export function renderVoiceVisualizer(isActive) {
    const hiddenClass = isActive ? '' : 'hidden';
    
    return `
        <div class="voice-viz-container ${hiddenClass}" id="voice-visualizer">
            <div class="flex items-center gap-1.5 justify-center h-8">
                <div class="w-1 bg-cyan-400 rounded-full h-3 animate-[pulse_1s_ease-in-out_infinite]"></div>
                <div class="w-1 bg-cyan-400 rounded-full h-6 animate-[pulse_0.8s_ease-in-out_infinite_0.2s]"></div>
                <div class="w-1 bg-cyan-400 rounded-full h-8 animate-[pulse_1.2s_ease-in-out_infinite_0.4s]"></div>
                <div class="w-1 bg-cyan-400 rounded-full h-4 animate-[pulse_0.9s_ease-in-out_infinite_0.1s]"></div>
                <div class="w-1 bg-cyan-400 rounded-full h-5 animate-[pulse_1.1s_ease-in-out_infinite_0.3s]"></div>
            </div>
            <div class="text-[9px] uppercase tracking-[0.2em] text-cyan-500 mt-2 font-mono text-center opacity-70">
                Mic Active
            </div>
        </div>
    `;
}

export function toggleVoiceVisualizer(isActive) {
    const el = document.getElementById('voice-visualizer');
    if (el) {
        if (isActive) {
            el.classList.remove('hidden');
        } else {
            el.classList.add('hidden');
        }
    }
}
