import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ThreeRobotHead } from '../utils/three-robot';

export function Landing() {
  const navigate = useNavigate();
  const threeRef = useRef(null);

  useEffect(() => {
    let robotHead = null;
    if (threeRef.current) {
      robotHead = new ThreeRobotHead('threejs-container-ANIMATION_2');
      robotHead.init();
    }
    return () => {
      if (robotHead) {
        robotHead.destroy();
      }
    };
  }, []);

  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '0px',
      threshold: 0.1
    };

    const observer = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    const elements = document.querySelectorAll('.fade-up');
    elements.forEach((el) => {
      observer.observe(el);
    });

    // Trigger initial visible elements
    setTimeout(() => {
      elements.forEach((el) => {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight) {
          el.classList.add('visible');
        }
      });
    }, 100);

    return () => observer.disconnect();
  }, []);

  return (
    <div className="bg-[#0A0A0A] text-[#e5e2e1] antialiased overflow-x-hidden selection:bg-secondary selection:text-on-secondary min-h-screen">
      {/* TopNavBar */}
      <header className="fixed top-0 w-full z-50 bg-surface/80 backdrop-blur-3xl border-b border-white/10 shadow-2xl shadow-secondary/5 transition-all duration-500">
        <div className="flex justify-between items-center px-gutter py-4 max-w-[1440px] mx-auto">
          <div className="font-headline-md text-headline-md font-bold tracking-tighter text-primary">
            Nephele
          </div>
          <nav className="hidden md:flex items-center gap-md font-body-md text-body-md">
            <a className="text-on-surface-variant hover:text-primary transition-colors duration-300" href="#capabilities">Capabilities</a>
            <a className="text-on-surface-variant hover:text-primary transition-colors duration-300" href="#intelligence">Intelligence</a>
            <a className="text-on-surface-variant hover:text-primary transition-colors duration-300" href="#architecture">Architecture</a>
            <a className="text-primary border-b border-primary pb-1 hover:text-primary transition-colors duration-300" href="#initialize">Initialize</a>
          </nav>
          <button
            onClick={() => window.location.href = 'https://nephele-production.vercel.app/'}
            className="hidden md:inline-flex bg-primary text-on-primary px-sm py-xs rounded-DEFAULT font-caption text-caption hover:opacity-90 transition-opacity"
          >
            Get Started
          </button>
          <button className="md:hidden text-primary">
            <span className="material-symbols-outlined">menu</span>
          </button>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="relative min-h-screen flex items-center justify-center pt-xl pb-xl px-gutter max-w-[1440px] mx-auto">
          <div className="absolute inset-0 w-full h-full z-0 opacity-80 pointer-events-none flex items-center justify-center">
            <div className="absolute inset-0 w-full h-full max-w-5xl mx-auto" style={{ display: 'block' }}>
              <div id="threejs-container-ANIMATION_2" ref={threeRef} style={{ width: '100%', height: '100%' }}></div>
            </div>
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(173,198,255,0.05)_0%,transparent_50%)]"></div>
          </div>

          <div className="relative z-10 text-center w-full max-w-3xl fade-up mt-margin-safe pointer-events-auto">
            <h1 className="font-display-lg-mobile md:font-display-lg text-display-lg-mobile md:text-display-lg text-primary tracking-tighter mb-sm">
              Meet Nephele.
            </h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant mb-lg font-light tracking-wide max-w-2xl mx-auto">
              An Intelligent Robotic Operating System.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-sm">
              <button
                onClick={() => window.location.href = 'https://nephele-production.vercel.app/'}
                className="w-full sm:w-auto bg-primary text-on-primary px-lg py-sm rounded-DEFAULT font-body-md text-body-md hover:bg-surface-tint transition-colors"
              >
                Initialize Interface
              </button>
              <button className="w-full sm:w-auto ghost-button text-primary px-lg py-sm rounded-DEFAULT font-body-md text-body-md">
                View Documentation
              </button>
            </div>
          </div>
        </section>

        {/* Identity Section */}
        <section className="py-xl px-gutter max-w-[1440px] mx-auto flex items-center justify-center min-h-[512px]" id="intelligence">
          <div className="max-w-4xl text-center fade-up">
            <h2 className="font-headline-md text-headline-md text-primary leading-relaxed tracking-tight">
              Beyond conversation. Beyond the screen. A living intelligence built for the physical world.
            </h2>
          </div>
        </section>

        {/* Capabilities Section */}
        <section className="py-xl px-gutter max-w-[1440px] mx-auto" id="capabilities">
          <div className="mb-lg fade-up">
            <span className="font-label-mono text-label-mono text-secondary uppercase tracking-widest mb-xs block">Capabilities</span>
            <h2 className="font-headline-md text-headline-md text-primary">Core Systems</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-md fade-up">
            {/* Voice Intelligence */}
            <div className="glass-panel rounded-xl p-md lg:col-span-8 flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:active-glow transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-surface-container/50 to-transparent z-0"></div>
              <div className="relative z-10 mt-auto">
                <span className="material-symbols-outlined text-secondary mb-sm" style={{ fontVariationSettings: "'FILL' 1" }}>mic</span>
                <h3 className="font-body-lg text-body-lg text-primary mb-xs">Voice Intelligence</h3>
                <p className="font-body-md text-body-md text-on-surface-variant">Low-latency WebSocket streaming for instantaneous, natural human-machine dialogue.</p>
              </div>
            </div>

            {/* Real-Time Vision */}
            <div className="glass-panel rounded-xl p-md lg:col-span-4 flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:active-glow transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-bl from-surface-container/50 to-transparent z-0"></div>
              <div className="relative z-10 mt-auto">
                <span className="material-symbols-outlined text-secondary mb-sm" style={{ fontVariationSettings: "'FILL' 1" }}>visibility</span>
                <h3 className="font-body-lg text-body-lg text-primary mb-xs">Real-Time Vision</h3>
                <p className="font-body-md text-body-md text-on-surface-variant">Multimodal computer vision processing at the edge.</p>
              </div>
            </div>

            {/* Professional Engine */}
            <div className="glass-panel rounded-xl p-md lg:col-span-5 flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:active-glow transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-tr from-surface-container/50 to-transparent z-0"></div>
              <div className="relative z-10 mt-auto">
                <span className="material-symbols-outlined text-secondary mb-sm" style={{ fontVariationSettings: "'FILL' 1" }}>analytics</span>
                <h3 className="font-body-lg text-body-lg text-primary mb-xs">Professional Engine</h3>
                <p className="font-body-md text-body-md text-on-surface-variant">AI-driven resume analysis and adaptive mock interview simulations.</p>
              </div>
            </div>

            {/* Orchestration */}
            <div className="glass-panel rounded-xl p-md lg:col-span-7 flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:active-glow transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-tl from-surface-container/50 to-transparent z-0"></div>
              <div className="relative z-10 mt-auto">
                <span className="material-symbols-outlined text-secondary mb-sm" style={{ fontVariationSettings: "'FILL' 1" }}>schema</span>
                <h3 className="font-body-lg text-body-lg text-primary mb-xs">Orchestration</h3>
                <p className="font-body-md text-body-md text-on-surface-variant">A FastAPI-powered backbone providing seamless routing for modular AI components.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Architecture Section */}
        <section className="py-xl px-gutter max-w-[1440px] mx-auto border-t border-white/5" id="architecture">
          <div className="mb-lg fade-up text-center">
            <span className="font-label-mono text-label-mono text-secondary uppercase tracking-widest mb-xs block">Architecture</span>
            <h2 className="font-headline-md text-headline-md text-primary">System Topology</h2>
          </div>

          <div className="glass-panel rounded-xl p-md max-w-4xl mx-auto fade-up milled-border relative">
            <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

            <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 gap-y-lg gap-x-md">
              <div className="flex items-start gap-sm">
                <div className="w-xs h-xs bg-secondary rounded-full mt-2 shadow-[0_0_10px_rgba(173,198,255,0.8)]"></div>
                <div>
                  <h4 className="font-body-lg text-body-lg text-primary mb-1">Edge AI</h4>
                  <p className="font-body-md text-body-md text-on-surface-variant">Localized processing for critical latency-sensitive operations.</p>
                </div>
              </div>

              <div className="flex items-start gap-sm">
                <div className="w-xs h-xs bg-secondary rounded-full mt-2 shadow-[0_0_10px_rgba(173,198,255,0.8)]"></div>
                <div>
                  <h4 className="font-body-lg text-body-lg text-primary mb-1">WebSocket Streaming</h4>
                  <p className="font-body-md text-body-md text-on-surface-variant">Continuous full-duplex communication channels.</p>
                </div>
              </div>

              <div className="flex items-start gap-sm">
                <div className="w-xs h-xs bg-secondary rounded-full mt-2 shadow-[0_0_10px_rgba(173,198,255,0.8)]"></div>
                <div>
                  <h4 className="font-body-lg text-body-lg text-primary mb-1">Modular Modules</h4>
                  <p className="font-body-md text-body-md text-on-surface-variant">Hot-swappable intelligence nodes for specialized tasks.</p>
                </div>
              </div>

              <div className="flex items-start gap-sm">
                <div className="w-xs h-xs bg-secondary rounded-full mt-2 shadow-[0_0_10px_rgba(173,198,255,0.8)]"></div>
                <div>
                  <h4 className="font-body-lg text-body-lg text-primary mb-1">FastAPI Backend</h4>
                  <p className="font-body-md text-body-md text-on-surface-variant">High-performance async routing and state management.</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-surface w-full py-xl border-t border-white/5">
        <div className="max-w-[1440px] mx-auto px-gutter flex flex-col md:flex-row justify-between items-center gap-md">
          <div className="font-headline-md text-headline-md font-bold text-primary">
            Nephele
          </div>
          <nav className="flex gap-sm font-caption text-caption">
            <a className="text-on-surface-variant hover:text-primary transition-opacity duration-200" href="#">Documentation</a>
            <a className="text-on-surface-variant hover:text-primary transition-opacity duration-200" href="#">Privacy</a>
            <a className="text-on-surface-variant hover:text-primary transition-opacity duration-200" href="#">Terms</a>
            <a className="text-on-surface-variant hover:text-primary transition-opacity duration-200" href="#">Github</a>
          </nav>
          <div className="font-caption text-caption text-on-surface-variant">
            © 2024 Nephele OS. Robotic Intelligence Redefined.
          </div>
        </div>
      </footer>
    </div>
  );
}
