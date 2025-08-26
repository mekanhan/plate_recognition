/**
 * Toast Notification Service - Smart UX Feedback System
 * Provides consistent, accessible toast notifications across the application
 */

class ToastService {
    constructor() {
        this.container = null;
        this.toasts = new Map();
        this.defaultDuration = 5000;
        this.maxToasts = 5;
        
        this.init();
    }
    
    /**
     * Initialize the toast container
     */
    init() {
        // Create container if it doesn't exist
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            this.container.setAttribute('role', 'region');
            this.container.setAttribute('aria-label', 'Notifications');
            this.container.setAttribute('aria-live', 'polite');
            document.body.appendChild(this.container);
        }
    }
    
    /**
     * Show a toast notification
     * @param {Object} options - Toast configuration
     */
    show(options = {}) {
        const {
            type = 'info',
            title,
            message,
            duration = this.defaultDuration,
            persistent = false,
            actions = [],
            id = this.generateId()
        } = options;
        
        // Remove oldest toast if at max capacity
        if (this.toasts.size >= this.maxToasts) {
            const firstToast = this.toasts.keys().next().value;
            this.hide(firstToast);
        }
        
        // Create toast element
        const toast = this.createToast({
            id,
            type,
            title,
            message,
            duration,
            persistent,
            actions
        });
        
        // Add to container
        this.container.appendChild(toast);
        this.toasts.set(id, toast);
        
        // Show with animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto-dismiss if not persistent
        if (!persistent && duration > 0) {
            setTimeout(() => {
                this.hide(id);
            }, duration);
        }
        
        return id;
    }
    
    /**
     * Hide a specific toast
     */
    hide(id) {
        const toast = this.toasts.get(id);
        if (!toast) return;
        
        toast.classList.add('hide');
        toast.classList.remove('show');
        
        // Remove from DOM after animation
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            this.toasts.delete(id);
        }, 200);
    }
    
    /**
     * Hide all toasts
     */
    hideAll() {
        this.toasts.forEach((toast, id) => {
            this.hide(id);
        });
    }
    
    /**
     * Create toast element
     */
    createToast({ id, type, title, message, duration, persistent, actions }) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('data-toast-id', id);
        
        // Icon mapping
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'i',
            loading: '⟳'
        };
        
        let html = `
            <div class="toast-icon">
                ${icons[type] || icons.info}
            </div>
            <div class="toast-content">
                ${title ? `<h4 class="toast-title">${title}</h4>` : ''}
                ${message ? `<p class="toast-message">${message}</p>` : ''}
                ${actions.length > 0 ? this.createActions(actions) : ''}
            </div>
            <button class="toast-close" aria-label="Close notification">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add progress bar if auto-dismissing
        if (!persistent && duration > 0) {
            html += '<div class="toast-progress"></div>';
        }
        
        toast.innerHTML = html;
        
        // Add event listeners
        this.addToastListeners(toast, id);
        
        return toast;
    }
    
    /**
     * Create action buttons HTML
     */
    createActions(actions) {
        const actionsHtml = actions.map(action => 
            `<button class="toast-action" data-action="${action.id}">
                ${action.label}
            </button>`
        ).join('');
        
        return `<div class="toast-actions">${actionsHtml}</div>`;
    }
    
    /**
     * Add event listeners to toast
     */
    addToastListeners(toast, id) {
        // Close button
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn?.addEventListener('click', () => this.hide(id));
        
        // Click to dismiss
        toast.addEventListener('click', (e) => {
            if (!e.target.closest('.toast-action')) {
                this.hide(id);
            }
        });
        
        // Action buttons
        const actionButtons = toast.querySelectorAll('.toast-action');
        actionButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const actionId = e.target.getAttribute('data-action');
                this.handleAction(id, actionId);
            });
        });
        
        // Keyboard support
        toast.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hide(id);
            }
        });
    }
    
    /**
     * Handle action button clicks
     */
    handleAction(toastId, actionId) {
        const event = new CustomEvent('toast-action', {
            detail: { toastId, actionId }
        });
        document.dispatchEvent(event);
        
        // Hide toast after action
        this.hide(toastId);
    }
    
    /**
     * Generate unique ID
     */
    generateId() {
        return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Convenience methods for different toast types
     */
    success(title, message, options = {}) {
        return this.show({
            type: 'success',
            title,
            message,
            ...options
        });
    }
    
    error(title, message, options = {}) {
        return this.show({
            type: 'error',
            title,
            message,
            duration: 0, // Errors persist until manually dismissed
            ...options
        });
    }
    
    warning(title, message, options = {}) {
        return this.show({
            type: 'warning',
            title,
            message,
            ...options
        });
    }
    
    info(title, message, options = {}) {
        return this.show({
            type: 'info',
            title,
            message,
            ...options
        });
    }
    
    loading(title, message, options = {}) {
        return this.show({
            type: 'loading',
            title,
            message,
            persistent: true,
            ...options
        });
    }
    
    /**
     * Update an existing toast
     */
    update(id, options = {}) {
        const toast = this.toasts.get(id);
        if (!toast) return;
        
        const { title, message, type } = options;
        
        if (title) {
            const titleEl = toast.querySelector('.toast-title');
            if (titleEl) titleEl.textContent = title;
        }
        
        if (message) {
            const messageEl = toast.querySelector('.toast-message');
            if (messageEl) messageEl.textContent = message;
        }
        
        if (type) {
            // Update toast class
            toast.className = `toast toast-${type} show`;
            
            // Update icon
            const iconEl = toast.querySelector('.toast-icon');
            const icons = {
                success: '✓',
                error: '✕',
                warning: '⚠',
                info: 'i',
                loading: '⟳'
            };
            if (iconEl && icons[type]) {
                iconEl.textContent = icons[type];
            }
        }
    }
    
    /**
     * Show operation feedback with automatic state transitions
     */
    showOperation(title, options = {}) {
        const loadingId = this.loading(title, 'Processing...', options);
        
        return {
            success: (message = 'Completed successfully') => {
                this.hide(loadingId);
                return this.success(title, message, options);
            },
            error: (message = 'Operation failed') => {
                this.hide(loadingId);
                return this.error(title, message, options);
            },
            update: (message) => {
                this.update(loadingId, { message });
            },
            cancel: () => {
                this.hide(loadingId);
            }
        };
    }
}

// Create global instance
const toastService = new ToastService();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastService;
}

// Global API for easy access
window.toast = toastService;

export default toastService;