/**
 * @file coding.js
 * @description Coding challenge workspace.
 */

import { renderChallengeView } from '../components/challenge-view.js';
import { renderEvaluationCard } from '../components/evaluation-card.js';

export function renderCodingWorkspace(state) {
    return `
        <div class="workspace-page" id="page-coding">
            <div class="workspace-header">
                <h2>Adaptive Coding Challenge</h2>
                <p>Generate algorithmic interview problems and evaluate verbal explanations</p>
            </div>
            
            <div class="workspace-scroll">
                <!-- Generator Form -->
                <div class="card max-w-4xl mx-auto">
                    <h3 class="text-xs font-mono text-slate-500 mb-4 tracking-wider">GENERATE CHALLENGE</h3>
                    <div class="flex flex-wrap gap-4 items-end">
                        <div class="flex-1 min-w-[200px]">
                            <label class="label">Topic Area</label>
                            <select id="coding-topic" class="input">
                                <option value="algorithms">Algorithms & Data Structures</option>
                                <option value="system_design">System Design</option>
                                <option value="frontend">Frontend Architecture</option>
                                <option value="backend">Backend & APIs</option>
                                <option value="database">Database Design</option>
                            </select>
                        </div>
                        
                        <div class="flex-1 min-w-[150px]">
                            <label class="label">Difficulty</label>
                            <select id="coding-difficulty" class="input">
                                <option value="easy">Easy</option>
                                <option value="medium" selected>Medium</option>
                                <option value="hard">Hard</option>
                            </select>
                        </div>
                        
                        <button id="btn-generate-coding" class="btn btn-primary h-[42px]">
                            Generate Challenge
                        </button>
                    </div>
                    <div class="text-rose-400 text-xs mt-3 min-h-[16px]" id="coding-gen-error"></div>
                </div>

                <!-- Challenge & Evaluation Area -->
                <div id="coding-question-container" class="max-w-4xl mx-auto">
                    ${state.currentCodingQuestion ? renderChallengeView(state.currentCodingQuestion) : ''}
                    ${state.currentCodingEvaluation ? renderEvaluationCard(state.currentCodingEvaluation) : ''}
                </div>
            </div>
        </div>
    `;
}
