/**
 * @file constants.js
 * @description Application-wide constants, API base URLs, routes, and enum values.
 */

export const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : '';

export const WS_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'ws://localhost:8000'
    : `ws://${window.location.host}`;

export const ROUTES = {
    LANDING: '',
    HOME: '#home',
    RESUME: '#/resume',
    CODING: '#/coding',
    INTERVIEW: '#/interview',
    SETTINGS: '#/settings'
};

export const CODING_TOPICS = [
    'Arrays',
    'Strings',
    'Linked Lists',
    'Stacks',
    'Queues',
    'Hash Maps',
    'Trees',
    'BST',
    'Graphs',
    'Heaps',
    'Greedy',
    'Dynamic Programming'
];

export const CODING_DIFFICULTIES = [
    'Easy',
    'Medium',
    'Hard'
];

export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
export const ALLOWED_RESUME_EXTENSIONS = ['.pdf', '.docx'];
