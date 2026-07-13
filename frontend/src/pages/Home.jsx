import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { api } from '../api/apiClient';
import { useState } from 'react';

export function Home() {
  const navigate = useNavigate();
  const { settings, setSettings, setActiveSessionId, setInterviewState } = useAppStore();
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setLoading(true);
    try {
      const res = await api.createSession(settings.candidateName, settings.targetRole);
      setActiveSessionId(res.session_id);
      setInterviewState('IDLE');
      navigate('/interview');
    } catch (e) {
      console.error(e);
      alert("Failed to create session. Is backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-margin-safe relative h-full w-full">
      {/* Ambient Background */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-secondary-container/5 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-1/4 right-1/4 w-128 h-128 bg-primary/5 rounded-full blur-[150px]"></div>
      </div>
      
      {/* Center Configuration Panel */}
      <div className="glass-panel w-full max-w-[640px] rounded-xl p-md md:p-lg flex flex-col gap-md fade-up-stitch glow-active relative overflow-hidden group">
        <div className="absolute -top-32 -right-32 w-64 h-64 bg-secondary-container/10 rounded-full blur-[80px] group-hover:bg-secondary-container/20 transition-all duration-700 pointer-events-none"></div>
        
        <header className="flex flex-col gap-xs mb-sm fade-up-stitch delay-100 relative z-10">
          <span className="font-label-mono text-label-mono text-on-surface-variant uppercase tracking-widest flex items-center gap-xs">
            <span className="w-2 h-2 rounded-full bg-secondary-container animate-pulse"></span>
            INITIALIZATION
          </span>
          <h1 className="font-display-lg text-headline-md md:text-[40px] text-primary tracking-tight leading-tight mt-unit">Initialize Interview Session</h1>
          <p className="font-body-md text-body-md text-on-surface-variant/80 max-w-md mt-unit">Configure operational parameters for the upcoming neural assessment. Precision inputs required.</p>
        </header>
        
        <form className="flex flex-col gap-sm fade-up-stitch delay-200 relative z-10">
          <div className="flex flex-col gap-xs group/input">
            <label className="font-label-mono text-label-mono text-on-surface-variant group-focus-within/input:text-primary transition-colors" htmlFor="candidateName">Candidate Name</label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-sm top-1/2 -translate-y-1/2 text-on-surface-variant/50 group-focus-within/input:text-primary transition-colors">person</span>
              <input 
                className="input-inset w-full rounded p-sm pl-[48px] font-body-md text-body-md text-primary focus:outline-none transition-all placeholder:text-on-surface-variant/30" 
                id="candidateName" 
                placeholder="e.g. Subject Alpha" 
                type="text"
                value={settings.candidateName}
                onChange={(e) => setSettings({ candidateName: e.target.value })}
              />
            </div>
          </div>
          
          <div className="flex flex-col gap-xs group/input">
            <label className="font-label-mono text-label-mono text-on-surface-variant group-focus-within/input:text-primary transition-colors" htmlFor="targetRole">Target Role</label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-sm top-1/2 -translate-y-1/2 text-on-surface-variant/50 group-focus-within/input:text-primary transition-colors">work</span>
              <input 
                className="input-inset w-full rounded p-sm pl-[48px] font-body-md text-body-md text-primary focus:outline-none transition-all placeholder:text-on-surface-variant/30" 
                id="targetRole" 
                placeholder="e.g. Systems Architect" 
                type="text"
                value={settings.targetRole}
                onChange={(e) => setSettings({ targetRole: e.target.value })}
              />
            </div>
          </div>
          
          <div className="mt-md fade-up-stitch delay-300">
            <button 
              className="w-full bg-primary text-on-primary font-label-mono text-label-mono uppercase tracking-wider py-sm rounded flex items-center justify-center gap-xs hover:bg-white/90 hover:shadow-[0_0_30px_0_rgba(75,142,255,0.3)] transition-all duration-300 active:scale-[0.98] disabled:opacity-50" 
              type="button"
              onClick={handleStart}
              disabled={loading}
            >
              <span className="material-symbols-outlined text-[18px]">mic</span>
              {loading ? "INITIALIZING..." : "Begin Voice Interview"}
            </button>
          </div>
        </form>
        
        <div className="absolute bottom-sm left-sm right-sm flex justify-between items-center border-t border-white/5 pt-sm fade-up-stitch delay-400">
          <span className="font-label-mono text-[10px] text-on-surface-variant/50 uppercase">SYS_RDY :: AWAITING_INPUT</span>
          <span className="font-label-mono text-[10px] text-secondary-container/70 uppercase flex items-center gap-1">
            <span className="material-symbols-outlined text-[12px]">lock</span> SECURE CHANNEL
          </span>
        </div>
      </div>
    </div>
  );
}
