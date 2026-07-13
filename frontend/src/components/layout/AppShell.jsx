import { Outlet, NavLink } from 'react-router-dom';

export function ModuleRail() {
  return (
    <nav className="hidden md:flex flex-col h-screen fixed left-0 top-0 py-gutter bg-surface-container-lowest/80 backdrop-blur-3xl w-nav-width border-r border-white/10 z-50">
      <div className="px-gutter mb-xl flex items-center gap-sm">
        <img alt="System Operator Avatar" className="w-10 h-10 rounded-full border border-white/10 opacity-80 mix-blend-screen" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDOJBODjyGsntM86aU_vXu2CBqCaTAEAfGxEghm4nIqU9bVXpnhzsach9bfUVmxKG-issB3rpG0lDdD4iCIB81LCewOUaK4IA5cr0nrbaiHmBhp0NdHA8BZq3EFMzV2yB7SO-oExOdw2b0WzVaqodI84fzfv8D90Afp43IL8NVHFcZ7h-LmRbfp2wQW73tzMn4sEyR-jn2uAeheNnIfYfWRJI0TrNFMNjvEkGJf_43IaJdtFaM90HKC9s5K4qr2yvvWdAxmvnplncg"/>
        <div>
          <h1 className="font-display-lg text-[20px] leading-tight text-primary tracking-tighter">NEPHELE OS</h1>
          <p className="font-label-mono text-label-mono text-on-surface-variant opacity-60">V2.0.4 - ACTIVE</p>
        </div>
      </div>
      <div className="flex-1 px-sm flex flex-col gap-xs">
        <NavLink to="/home" className={({isActive}) => `flex items-center gap-md px-sm py-xs transition-all duration-300 rounded-full ${isActive ? 'text-primary bg-white/10' : 'text-on-surface-variant hover:text-primary hover:bg-white/5'}`}>
          <span className="material-symbols-outlined text-[20px]">psychology</span>
          <span className="font-body-md text-body-md">Neural Hub</span>
        </NavLink>
        <NavLink to="/interview" className={({isActive}) => `flex items-center gap-md px-sm py-xs transition-all duration-300 rounded-full ${isActive ? 'text-primary bg-white/10' : 'text-on-surface-variant hover:text-primary hover:bg-white/5'}`}>
          <span className="material-symbols-outlined text-[20px]">record_voice_over</span>
          <span className="font-body-md text-body-md">Live Interview</span>
        </NavLink>
        <NavLink to="/memory" className={({isActive}) => `flex items-center gap-md px-sm py-xs transition-all duration-300 rounded-full ${isActive ? 'text-primary bg-white/10' : 'text-on-surface-variant hover:text-primary hover:bg-white/5'}`}>
          <span className="material-symbols-outlined text-[20px]">database</span>
          <span className="font-body-md text-body-md">Memory Engine</span>
        </NavLink>
        <NavLink to="/settings" className={({isActive}) => `flex items-center gap-md px-sm py-xs transition-all duration-300 rounded-full ${isActive ? 'text-primary bg-white/10' : 'text-on-surface-variant hover:text-primary hover:bg-white/5'}`}>
          <span className="material-symbols-outlined text-[20px]">tune</span>
          <span className="font-body-md text-body-md">System Config</span>
        </NavLink>
      </div>
      <div className="px-gutter mt-auto flex items-center justify-between opacity-50">
        <span className="material-symbols-outlined text-[18px]">wifi</span>
        <span className="material-symbols-outlined text-[18px]">security</span>
        <span className="material-symbols-outlined text-[18px]">power</span>
      </div>
    </nav>
  );
}

export function AppShell() {
  return (
    <div className="bg-background text-on-surface font-body-lg antialiased overflow-hidden selection:bg-secondary-container selection:text-on-secondary-container min-h-screen">
      <ModuleRail />
      <main className="md:ml-nav-width h-screen flex flex-col relative">
        <Outlet />
      </main>
    </div>
  );
}
