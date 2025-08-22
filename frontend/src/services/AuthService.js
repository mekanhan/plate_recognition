/**
 * Authentication Service
 * Handles login, logout, token management, and user session
 */
class AuthService {
    constructor() {
        this.apiBase = 'http://localhost:8001';
        this.token = localStorage.getItem('lpr_auth_token');
        this.user = null;
        this.refreshInterval = null;
    }

    /**
     * Login with username and password
     */
    async login(username, password) {
        try {
            const response = await fetch(`${this.apiBase}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            
            // Store token and user info
            this.token = data.access_token;
            localStorage.setItem('lpr_auth_token', this.token);
            
            // Get current user info
            await this.getCurrentUser();
            
            // Start token refresh
            this.startTokenRefresh();
            
            // Dispatch login event
            window.dispatchEvent(new CustomEvent('userLogin', { 
                detail: { user: this.user } 
            }));

            return this.user;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    /**
     * Logout and clear session
     */
    logout() {
        // Clear token and user data
        this.token = null;
        this.user = null;
        localStorage.removeItem('lpr_auth_token');
        
        // Stop token refresh
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        // Dispatch logout event
        window.dispatchEvent(new CustomEvent('userLogout'));
        
        // Redirect to login or reload page
        this.showLoginForm();
    }

    /**
     * Get current user information
     */
    async getCurrentUser() {
        if (!this.token) {
            throw new Error('No authentication token');
        }

        try {
            const response = await fetch(`${this.apiBase}/api/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to get user info');
            }

            this.user = await response.json();
            return this.user;
        } catch (error) {
            console.error('Get user error:', error);
            throw error;
        }
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Get current user
     */
    getUser() {
        return this.user;
    }

    /**
     * Get authentication token
     */
    getToken() {
        return this.token;
    }

    /**
     * Check if user has specific permission
     */
    hasPermission(permission) {
        if (!this.user) return false;
        return this.user.permissions?.includes(permission) || this.user.role === 'admin';
    }

    /**
     * Get user role
     */
    getUserRole() {
        return this.user?.role || 'guest';
    }

    /**
     * Start automatic token refresh
     */
    startTokenRefresh() {
        // Refresh user info every 30 minutes
        this.refreshInterval = setInterval(async () => {
            try {
                await this.getCurrentUser();
            } catch (error) {
                console.warn('Token refresh failed, logging out:', error);
                this.logout();
            }
        }, 30 * 60 * 1000); // 30 minutes
    }

    /**
     * Show login form or redirect to homepage
     */
    showLoginForm() {
        // Check if we're on the homepage
        if (window.location.pathname.includes('index.html') || window.location.pathname === '/') {
            // We're already on homepage, let it handle authentication
            return;
        }
        
        // Redirect to homepage for authentication
        window.location.href = 'index.html';
    }

    /**
     * Create login modal HTML
     */
    createLoginModal() {
        const modal = document.createElement('div');
        modal.className = 'auth-modal-overlay';
        modal.id = 'login-modal';
        modal.innerHTML = `
            <div class="auth-modal">
                <div class="auth-modal-header">
                    <h2><i class="fas fa-shield-alt"></i> LPR System Login</h2>
                </div>
                <div class="auth-modal-body">
                    <form id="login-form" class="auth-form">
                        <div class="form-group">
                            <label for="login-username">Username</label>
                            <input type="text" id="login-username" name="username" required autocomplete="username">
                        </div>
                        <div class="form-group">
                            <label for="login-password">Password</label>
                            <input type="password" id="login-password" name="password" required autocomplete="current-password">
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary btn-login">
                                <i class="fas fa-sign-in-alt"></i> Login
                            </button>
                        </div>
                        <div id="login-error" class="error-message" style="display: none;"></div>
                    </form>
                </div>
                <div class="auth-modal-footer">
                    <small>License Plate Recognition Security System v2.1.0</small>
                </div>
            </div>
        `;

        // Add event listeners
        const form = modal.querySelector('#login-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleLoginSubmit(e);
        });

        // Prevent modal close by clicking overlay
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                e.preventDefault(); // Don't allow closing by clicking outside
            }
        });

        return modal;
    }

    /**
     * Handle login form submission
     */
    async handleLoginSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const username = formData.get('username');
        const password = formData.get('password');
        
        const submitBtn = form.querySelector('.btn-login');
        const errorDiv = form.querySelector('#login-error');
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
        errorDiv.style.display = 'none';
        
        try {
            await this.login(username, password);
            
            // Close login modal
            const modal = document.getElementById('login-modal');
            if (modal) {
                modal.remove();
            }
            
            // Show success message
            this.showToast('Login successful!', 'success');
            
        } catch (error) {
            // Show error
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
            
            // Reset button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${this.getToastIcon(type)}"></i>
            <span>${message}</span>
        `;

        // Find or create toast container
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);

        // Auto remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 3000);
    }

    /**
     * Get icon for toast type
     */
    getToastIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || 'fa-info-circle';
    }

}

// CSS Styles for authentication modal
const authStyles = `
.auth-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    backdrop-filter: blur(5px);
}

.auth-modal {
    background: var(--bg-primary, #ffffff);
    border-radius: 12px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    max-width: 400px;
    width: 90%;
    max-height: 90vh;
    overflow: auto;
    animation: modalSlideIn 0.3s ease-out;
}

.auth-modal-header {
    padding: 24px 24px 16px;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    text-align: center;
}

.auth-modal-header h2 {
    margin: 0;
    color: var(--text-primary, #333333);
    font-size: 1.5rem;
    font-weight: 600;
}

.auth-modal-header i {
    color: var(--primary-color, #007bff);
    margin-right: 8px;
}

.auth-modal-body {
    padding: 24px;
}

.auth-form .form-group {
    margin-bottom: 20px;
}

.auth-form label {
    display: block;
    margin-bottom: 6px;
    color: var(--text-primary, #333333);
    font-weight: 500;
}

.auth-form input {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid var(--border-color, #e0e0e0);
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.2s ease;
    background: var(--bg-secondary, #ffffff);
    color: var(--text-primary, #333333);
    box-sizing: border-box;
}

.auth-form input:focus {
    outline: none;
    border-color: var(--primary-color, #007bff);
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.form-actions {
    margin-top: 24px;
    text-align: center;
}

.btn-login {
    width: 100%;
    padding: 14px 24px;
    background: var(--primary-color, #007bff);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.btn-login:hover:not(:disabled) {
    background: var(--primary-hover, #0056b3);
}

.btn-login:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

.error-message {
    margin-top: 16px;
    padding: 12px;
    background: #fee;
    border: 1px solid #fcc;
    border-radius: 6px;
    color: #c33;
    font-size: 14px;
    text-align: center;
}

.auth-modal-footer {
    padding: 16px 24px;
    text-align: center;
    border-top: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-secondary, #f8f9fa);
    color: var(--text-secondary, #666666);
    border-radius: 0 0 12px 12px;
}

.toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10001;
    pointer-events: none;
}

.toast {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    margin-bottom: 8px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    animation: toastSlideIn 0.3s ease-out;
    pointer-events: auto;
    min-width: 300px;
}

.toast i {
    margin-right: 8px;
    font-size: 16px;
}

.toast-success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.toast-error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.toast-warning {
    background: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

.toast-info {
    background: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
}

@keyframes modalSlideIn {
    from {
        opacity: 0;
        transform: translateY(-50px) scale(0.9);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

@keyframes toastSlideIn {
    from {
        opacity: 0;
        transform: translateX(100%);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Dark theme support */
[data-theme="dark"] .auth-modal {
    background: var(--bg-primary, #2d3748);
    color: var(--text-primary, #ffffff);
}

[data-theme="dark"] .auth-modal-header {
    border-bottom-color: var(--border-color, #4a5568);
}

[data-theme="dark"] .auth-form input {
    background: var(--bg-secondary, #4a5568);
    border-color: var(--border-color, #6b7280);
    color: var(--text-primary, #ffffff);
}

[data-theme="dark"] .auth-modal-footer {
    background: var(--bg-secondary, #374151);
    border-top-color: var(--border-color, #4a5568);
}
`;

// Inject CSS styles
if (!document.getElementById('auth-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'auth-styles';
    styleSheet.textContent = authStyles;
    document.head.appendChild(styleSheet);
}

export default AuthService;