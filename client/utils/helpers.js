/**
 * @file helpers.js
 * @description Utility and helper functions used across UI components and pages.
 */

/**
 * Debounce a function call so it only executes after a specified delay.
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, wait = 300) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

/**
 * Format bytes into human-readable strings (KB, MB).
 * @param {number} bytes - Number of bytes
 * @returns {string} Formatted string
 */
export function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Escape HTML strings to prevent XSS attacks.
 * @param {string} str - Raw string
 * @returns {string} Safe escaped HTML string
 */
export function escapeHTML(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Generate a unique ID string.
 * @returns {string} Unique identifier
 */
export function generateId() {
    return 'id-' + Math.random().toString(36).substr(2, 9);
}

/**
 * Format a score (0-10) with appropriate badge color classes.
 * @param {number} score - Numeric score
 * @returns {{ text: string, colorClass: string }} Score presentation object
 */
export function formatScoreBadge(score) {
    const num = Number(score) || 0;
    let colorClass = 'badge-rose';
    if (num >= 8.0) {
        colorClass = 'badge-emerald';
    } else if (num >= 5.0) {
        colorClass = 'badge-amber';
    }
    return {
        text: num.toFixed(1) + ' / 10',
        colorClass
    };
}

/**
 * Format seconds into HH:MM:SS
 * @param {number} totalSeconds
 * @returns {string} Formatted time string
 */
export function formatTime(totalSeconds) {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);
    
    return [
        hours.toString().padStart(2, '0'),
        minutes.toString().padStart(2, '0'),
        seconds.toString().padStart(2, '0')
    ].join(':');
}
