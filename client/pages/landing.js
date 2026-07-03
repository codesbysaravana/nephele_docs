import { TopNavBar } from '../components/landing/navbar.js';
import { Footer } from '../components/landing/footer.js';
import { ThreeRobotHead } from '../js/three-robot.js';
import { store } from '../js/state.js';

let robotHeadInstance = null;
let intersectionObserver = null;

function HeroSection() {
    return `
    <section class="relative min-h-screen flex items-center justify-center pt-xl pb-xl px-gutter max-w-[1440px] mx-auto">
        <!-- 3D Animation Background -->
        <div class="absolute inset-0 w-full h-full z-0 opacity-80 pointer-events-none flex items-center justify-center">
            <div class="absolute inset-0 w-full h-full max-w-5xl mx-auto" style="display:block;">
                <div id="threejs-container-ANIMATION_2" style="width:100%;height:100%"></div>
            </div>
            <!-- Fallback radial gradient to support the 3D element -->
            <div class="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(173,198,255,0.05)_0%,transparent_50%)]"></div>
        </div>
        <div class="relative z-10 text-center w-full max-w-3xl fade-up-stitch mt-margin-safe">
            <h1 class="font-display-lg-mobile md:font-display-lg text-display-lg-mobile md:text-display-lg text-primary tracking-tighter mb-sm">
                Meet Nephele.
            </h1>
            <p class="font-body-lg text-body-lg text-on-surface-variant mb-lg font-light tracking-wide max-w-2xl mx-auto">
                An Intelligent Robotic Operating System.
            </p>
            <div class="flex flex-col sm:flex-row items-center justify-center gap-sm">
                <button onclick="window.location.hash='#home'" class="w-full sm:w-auto bg-primary text-on-primary px-lg py-sm rounded-DEFAULT font-body-md text-body-md hover:bg-surface-tint transition-colors cursor-pointer z-20 pointer-events-auto">
                    Initialize Interface
                </button>
                <button class="w-full sm:w-auto ghost-button text-primary px-lg py-sm rounded-DEFAULT font-body-md text-body-md cursor-pointer z-20 pointer-events-auto">
                    View Documentation
                </button>
            </div>
        </div>
    </section>
    `;
}

function CapabilitiesSection() {
    return `
    <!-- Identity Section -->
    <section class="py-xl px-gutter max-w-[1440px] mx-auto flex items-center justify-center min-h-[512px]" id="intelligence">
        <div class="max-w-4xl text-center fade-up-stitch">
            <h2 class="font-headline-md text-headline-md text-primary leading-relaxed tracking-tight">
                Beyond conversation. Beyond the screen. A living intelligence built for the physical world.
            </h2>
        </div>
    </section>

    <!-- Capabilities Section (Bento Grid) -->
    <section class="py-xl px-gutter max-w-[1440px] mx-auto" id="capabilities">
        <div class="mb-lg fade-up-stitch">
            <span class="font-label-mono text-label-mono text-secondary uppercase tracking-widest mb-xs block">Capabilities</span>
            <h2 class="font-headline-md text-headline-md text-primary">Core Systems</h2>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-md fade-up-stitch">
            <!-- Voice Intelligence -->
            <div class="glass-panel rounded-xl p-md lg:col-span-8 flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:active-glow transition-all duration-500">
                <div class="absolute inset-0 bg-gradient-to-br from-surface-container/50 to-transparent z-0"></div>
                <div class="relative z-10 mt-auto">
                    <span class="material-symbols-outlined text-secondary mb-sm" style="font-variation-settings: 'FILL' 1;">mic</span>
                    <h3 class="font-body-lg text-body-lg text-primary mb-xs">Voice Intelligence</h3>
                    <p class="font-body-md text-body-md text-on-surface-variant">Low-latency WebSocket streaming for instantaneous, natural human-machine dialogue.</p>
                </div>
            </div>
            
            <!-- Real-Time Vision -->
            <div class="glass-panel rounded-xl p-md lg:col-span-4 flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:active-glow transition-all duration-500">
                <div class="absolute inset-0 bg-gradient-to-bl from-surface-container/50 to-transparent z-0"></div>
                <div class="relative z-10 mt-auto">
                    <span class="material-symbols-outlined text-secondary mb-sm" style="font-variation-settings: 'FILL' 1;">visibility</span>
                    <h3 class="font-body-lg text-body-lg text-primary mb-xs">Real-Time Vision</h3>
                    <p class="font-body-md text-body-md text-on-surface-variant">Multimodal computer vision processing at the edge.</p>
                </div>
            </div>
            
            <!-- Professional Engine -->
            <div class="glass-panel rounded-xl p-md lg:col-span-5 flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:active-glow transition-all duration-500">
                <div class="absolute inset-0 bg-gradient-to-tr from-surface-container/50 to-transparent z-0"></div>
                <div class="relative z-10 mt-auto">
                    <span class="material-symbols-outlined text-secondary mb-sm" style="font-variation-settings: 'FILL' 1;">analytics</span>
                    <h3 class="font-body-lg text-body-lg text-primary mb-xs">Professional Engine</h3>
                    <p class="font-body-md text-body-md text-on-surface-variant">AI-driven resume analysis and adaptive mock interview simulations.</p>
                </div>
            </div>
            
            <!-- Orchestration -->
            <div class="glass-panel rounded-xl p-md lg:col-span-7 flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:active-glow transition-all duration-500">
                <div class="absolute inset-0 bg-gradient-to-tl from-surface-container/50 to-transparent z-0"></div>
                <div class="relative z-10 mt-auto">
                    <span class="material-symbols-outlined text-secondary mb-sm" style="font-variation-settings: 'FILL' 1;">schema</span>
                    <h3 class="font-body-lg text-body-lg text-primary mb-xs">Orchestration</h3>
                    <p class="font-body-md text-body-md text-on-surface-variant">A FastAPI-powered backbone providing seamless routing for modular AI components.</p>
                </div>
            </div>
        </div>
    </section>
    `;
}

function ArchitectureSection() {
    return `
    <!-- Architecture Preview -->
    <section class="py-xl px-gutter max-w-[1440px] mx-auto border-t border-white/5" id="architecture">
        <div class="mb-lg fade-up-stitch text-center">
            <span class="font-label-mono text-label-mono text-secondary uppercase tracking-widest mb-xs block">Architecture</span>
            <h2 class="font-headline-md text-headline-md text-primary">System Topology</h2>
        </div>
        
        <div class="glass-panel rounded-xl p-md max-w-4xl mx-auto fade-up-stitch milled-border relative">
            <!-- Decorative grid background -->
            <div class="absolute inset-0 opacity-[0.03] pointer-events-none" style="background-image: radial-gradient(#fff 1px, transparent 1px); background-size: 24px 24px;"></div>
            
            <div class="relative z-10 grid grid-cols-1 sm:grid-cols-2 gap-y-lg gap-x-md">
                <!-- Edge AI -->
                <div class="flex items-start gap-sm">
                    <div class="w-xs h-xs bg-secondary rounded-full mt-2 shadow-[0_0_10px_rgba(173,198,255,0.8)] flex-shrink-0"></div>
                    <div>
                        <h4 class="font-body-lg text-body-lg text-primary mb-1">Edge AI</h4>
                        <p class="font-body-md text-body-md text-on-surface-variant">Localized processing for critical latency-sensitive operations.</p>
                    </div>
                </div>
                
                <!-- WebSocket Streaming -->
                <div class="flex items-start gap-sm">
                    <div class="w-xs h-xs bg-secondary rounded-full mt-2 shadow-[0_0_10px_rgba(173,198,255,0.8)] flex-shrink-0"></div>
                    <div>
                        <h4 class="font-body-lg text-body-lg text-primary mb-1">WebSocket Streaming</h4>
                        <p class="font-body-md text-body-md text-on-surface-variant">Continuous full-duplex communication channels.</p>
                    </div>
                </div>
                
                <!-- Modular Modules -->
                <div class="flex items-start gap-sm">
                    <div class="w-xs h-xs bg-secondary rounded-full mt-2 shadow-[0_0_10px_rgba(173,198,255,0.8)] flex-shrink-0"></div>
                    <div>
                        <h4 class="font-body-lg text-body-lg text-primary mb-1">Modular Modules</h4>
                        <p class="font-body-md text-body-md text-on-surface-variant">Hot-swappable intelligence nodes for specialized tasks.</p>
                    </div>
                </div>
                
                <!-- FastAPI Backend -->
                <div class="flex items-start gap-sm">
                    <div class="w-xs h-xs bg-secondary rounded-full mt-2 shadow-[0_0_10px_rgba(173,198,255,0.8)] flex-shrink-0"></div>
                    <div>
                        <h4 class="font-body-lg text-body-lg text-primary mb-1">FastAPI Backend</h4>
                        <p class="font-body-md text-body-md text-on-surface-variant">High-performance async routing and state management.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>
    `;
}

function setupScrollAnimations(containerElement) {
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    intersectionObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    containerElement.querySelectorAll('.fade-up-stitch').forEach((el) => {
        intersectionObserver.observe(el);
    });
    
    // Trigger initial visible elements
    setTimeout(() => {
        containerElement.querySelectorAll('.fade-up-stitch').forEach((el) => {
            const rect = el.getBoundingClientRect();
            if(rect.top < window.innerHeight) {
                el.classList.add('visible');
            }
        });
    }, 100);
}

export function LandingPage() {
    return `
        <div class="workspace-page" id="landing" style="background-color: #0A0A0A;">
            <div class="w-full h-full overflow-y-auto overflow-x-hidden relative selection:bg-secondary selection:text-on-secondary">
                ${TopNavBar()}
                <main>
                    ${HeroSection()}
                    ${CapabilitiesSection()}
                    ${ArchitectureSection()}
                </main>
                ${Footer()}
            </div>
        </div>
    `;
}

export function initLandingPage() {
    // Hide UI Chrome when on Landing Page
    const rail = document.querySelector('.module-rail');
    const status = document.querySelector('.status-bar');
    if (rail) rail.style.display = 'none';
    if (status) status.style.display = 'none';

    // Initialize 3D Robot Head
    if (!robotHeadInstance) {
        robotHeadInstance = new ThreeRobotHead('threejs-container-ANIMATION_2');
        robotHeadInstance.init();
    }

    // Setup intersection observer
    const pageEl = document.getElementById('landing');
    if (pageEl) {
        setupScrollAnimations(pageEl);
    }
}

export function cleanupLandingPage() {
    // Show UI Chrome when leaving Landing Page
    const rail = document.querySelector('.module-rail');
    const status = document.querySelector('.status-bar');
    if (rail) rail.style.display = 'flex';
    if (status) status.style.display = 'flex';

    if (robotHeadInstance) {
        robotHeadInstance.destroy();
        robotHeadInstance = null;
    }

    if (intersectionObserver) {
        intersectionObserver.disconnect();
        intersectionObserver = null;
    }
}
