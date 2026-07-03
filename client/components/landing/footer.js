export function Footer() {
    return `
    <footer class="bg-surface w-full py-xl border-t border-white/5">
        <div class="max-w-[1440px] mx-auto px-gutter flex flex-col md:flex-row justify-between items-center gap-md">
            <div class="font-headline-md text-headline-md font-bold text-primary">
                Nephele
            </div>
            <nav class="flex gap-sm font-caption text-caption">
                <a class="text-on-surface-variant hover:text-primary transition-opacity duration-200" href="#">Documentation</a>
                <a class="text-on-surface-variant hover:text-primary transition-opacity duration-200" href="#">Privacy</a>
                <a class="text-on-surface-variant hover:text-primary transition-opacity duration-200" href="#">Terms</a>
                <a class="text-on-surface-variant hover:text-primary transition-opacity duration-200" href="#">Github</a>
            </nav>
            <div class="font-caption text-caption text-on-surface-variant">
                © 2026 Nephele OS. Robotic Intelligence Redefined.
            </div>
        </div>
    </footer>
    `;
}
