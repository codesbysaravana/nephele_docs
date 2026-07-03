/**
 * @file validators.js
 * @description Client-side validation routines for files and forms.
 */

import { ALLOWED_RESUME_EXTENSIONS, MAX_FILE_SIZE_BYTES } from './constants.js';

/**
 * Validate a resume file upload.
 * @param {File} file - File selected by user
 * @returns {{ valid: boolean, error: string|null }} Validation result
 */
export function validateResumeFile(file) {
    if (!file) {
        return { valid: false, error: 'Please select a resume file to upload.' };
    }

    const name = file.name.toLowerCase();
    const hasValidExtension = ALLOWED_RESUME_EXTENSIONS.some(ext => name.endsWith(ext));

    if (!hasValidExtension) {
        return {
            valid: false,
            error: `Unsupported file type. Please upload a PDF (.pdf) or Word document (.docx).`
        };
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
        return {
            valid: false,
            error: `File size exceeds 10 MB limit. Your file is ${(file.size / (1024 * 1024)).toFixed(1)} MB.`
        };
    }

    if (file.size === 0) {
        return { valid: false, error: 'The selected file is empty.' };
    }

    return { valid: true, error: null };
}

/**
 * Validate non-empty string input.
 * @param {string} val - Input value
 * @param {string} fieldName - Display name for error message
 * @returns {{ valid: boolean, error: string|null }} Validation result
 */
export function validateRequiredString(val, fieldName = 'Field') {
    if (!val || typeof val !== 'string' || val.trim().length === 0) {
        return { valid: false, error: `${fieldName} is required.` };
    }
    return { valid: true, error: null };
}
