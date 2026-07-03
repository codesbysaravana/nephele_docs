export function TopNavBar() {
    return `
    <header class="fixed top-0 w-full z-50 bg-surface/80 backdrop-blur-3xl border-b border-white/10 shadow-2xl shadow-secondary/5 transition-all duration-500">
        <div class="flex justify-between items-center px-gutter py-4 max-w-[1440px] mx-auto">
            <div class="font-headline-md text-headline-md font-bold tracking-tighter text-primary">
                Nephele
            </div>
            <nav class="hidden md:flex items-center gap-md font-body-md text-body-md">
                <a class="text-on-surface-variant hover:text-primary transition-colors duration-300 cursor-pointer" onclick="document.getElementById('capabilities').scrollIntoView({behavior: 'smooth'})">Capabilities</a>
                <a class="text-on-surface-variant hover:text-primary transition-colors duration-300 cursor-pointer" onclick="document.getElementById('intelligence').scrollIntoView({behavior: 'smooth'})">Intelligence</a>
                <a class="text-on-surface-variant hover:text-primary transition-colors duration-300 cursor-pointer" onclick="document.getElementById('architecture').scrollIntoView({behavior: 'smooth'})">Architecture</a>
                <a class="text-primary border-b border-primary pb-1 hover:text-primary transition-colors duration-300" href="#home">Initialize</a>
            </nav>
            <button onclick="window.location.hash='#home'" class="hidden md:inline-flex bg-primary text-on-primary px-sm py-xs rounded-DEFAULT font-caption text-caption hover:opacity-90 transition-opacity">
                Get Started
            </button>
            <!-- Mobile Menu Trigger -->
            <button class="md:hidden text-primary">
                <span class="material-symbols-outlined">menu</span>
            </button>
        </div>
    </header>
    `;
}
