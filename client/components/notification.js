/**
 * @file notification.js
 * @description Toast notification system.
 */

class ToastManager {
    constructor() {
        this.containerId = 'toast-container';
        this.initContainer();
    }

    initContainer() {
        let container = document.getElementById(this.containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = this.containerId;
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
    }

    /**
     * Show a toast notification
     * @param {string} message - Notification text
     * @param {string} type - 'info', 'success', 'error', 'warning'
     * @param {number} duration - ms to show
     */
    show(message, type = 'info', duration = 3000) {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast-item';

        let icon = '';
        let colorClass = '';

        switch (type) {
            case 'success':
                icon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-emerald-500"><path d="M20 6L9 17l-5-5"/></svg>`;
                colorClass = 'border-emerald-500/30';
                break;
            case 'error':
                icon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-rose-500"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>`;
                colorClass = 'border-rose-500/30';
                break;
            case 'warning':
                icon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-amber-500"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4M12 17h.01"/></svg>`;
                colorClass = 'border-amber-500/30';
                break;
            case 'info':
            default:
                icon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-indigo-400"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>`;
                colorClass = 'border-indigo-500/30';
                break;
        }

        toast.innerHTML = `
            <div class="mt-0.5">${icon}</div>
            <div class="flex-1">${message}</div>
        `;

        if (colorClass) {
            toast.classList.add(colorClass.split('-')[1] ? `border-l-2` : ''); // Small visual tweak
            toast.style.borderLeftColor = `var(--accent-${type === 'info' ? 'indigo' : type})`;
        }

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('leaving');
            toast.addEventListener('animationend', () => {
                toast.remove();
            });
        }, duration);
    }
}

export const toast = new ToastManager();
