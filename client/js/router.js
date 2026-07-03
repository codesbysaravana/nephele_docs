/**
 * @file router.js
 * @description Client-side hash router managing workspace page visibility.
 * Prevents full DOM re-renders by toggling CSS classes on pre-rendered pages.
 */

import { ROUTES } from '../utils/constants.js';
import { store } from './state.js';
import { initLandingPage, cleanupLandingPage } from '../pages/landing.js';

/**
 * Update the active route in state and toggle page visibility.
 */
export function renderRoute() {
    let hash = window.location.hash || ROUTES.LANDING;

    // Validate hash and fallback to HOME if invalid
    const validRoutes = [ROUTES.LANDING, ROUTES.HOME, ROUTES.INTERVIEW, ROUTES.RESUME, ROUTES.CODING, ROUTES.SETTINGS];
    if (!validRoutes.includes(hash)) {
        hash = ROUTES.HOME;
        window.history.replaceState(null, '', window.location.pathname + hash);
    }
    
    // 1. Update state
    store.set({ activeRoute: hash });

    // 2. Toggle Workspace Pages
    const pages = {
        [ROUTES.LANDING]: document.getElementById('landing'),
        [ROUTES.HOME]: document.getElementById('page-home'),
        [ROUTES.INTERVIEW]: document.getElementById('page-interview'),
        [ROUTES.RESUME]: document.getElementById('page-resume'),
        [ROUTES.CODING]: document.getElementById('page-coding'),
        [ROUTES.SETTINGS]: document.getElementById('page-settings'),
    };

    // Ensure all exist before manipulating
    if (!pages[ROUTES.HOME]) return; 

    // Hide all
    Object.values(pages).forEach(page => {
        if (page) page.classList.remove('active');
    });

    // Show active (fallback to home)
    const activePage = pages[hash] || pages[ROUTES.HOME];
    if (activePage) activePage.classList.add('active');

    // Manage landing page lifecycle
    if (hash === ROUTES.LANDING) {
        initLandingPage();
    } else {
        cleanupLandingPage();
    }

    // 3. Update Module Rail Icons
    const railIcons = document.querySelectorAll('.rail-icon');
    railIcons.forEach(icon => {
        const href = icon.getAttribute('href');
        if (href === hash) {
            icon.classList.add('active');
            icon.setAttribute('aria-current', 'page');
        } else {
            icon.classList.remove('active');
            icon.setAttribute('aria-current', 'false');
        }
    });
}
