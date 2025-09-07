class AuthService {
    constructor() {
        this.apiBase = 'http://localhost:8001';
        this.token = localStorage.getItem('lpr_auth_token');
        this.user = null;
        this.refreshInterval = null;
    }

    async login(username, password) {
        try {
            const response = await fetch(`${this.apiBase}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username,
                    password
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('lpr_auth_token', this.token);
            
            await this.getCurrentUser();
            this.startTokenRefresh();
            
            window.dispatchEvent(new CustomEvent('userLogin', {
                detail: {
                    user: this.user
                }
            }));

            return this.user;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    async logout() {
        console.log('🔄 Logout initiated');

        try {
            await this.performServerLogout();
        } catch (error) {
            console.warn('Server logout encountered issues:', error);
        }

        await this.performClientLogout();
        console.log('✅ AuthService logout completed');
    }

    async performServerLogout() {
        if (!this.token) {
            console.log('⏩ No token available for server logout');
            return;
        }

        console.log('📡 Attempting server-side logout...');

        try {
            const response = await fetch(`${this.apiBase}/api/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 5000
            });

            if (response.ok) {
                console.log('✅ Server logout successful');
            } else {
                console.warn(`⚠️ Server logout returned ${response.status}`);
            }
        } catch (error) {
            console.warn('❌ Server logout failed:', error);
            throw error;
        }
    }

    async performClientLogout() {
        console.log('🧹 Performing client-side cleanup...');

        this.resetAuthServiceState();
        this.clearAllStorageData();
        this.stopBackgroundProcesses();
        this.notifyLogoutComplete();
        this.showToast('Logged out successfully', 'success');

        await new Promise(resolve => setTimeout(resolve, 500));
        this.redirectToHomepage();
    }

    resetAuthServiceState() {
        this.token = null;
        this.user = null;
        console.log('🔄 AuthService state reset');
    }

    clearAllStorageData() {
        const storageKeys = [
            'lpr_auth_token',
            'user-session',
            'auth-token',
            'access_token',
            'refresh_token',
            'user_data',
            'auth_state',
            'login_timestamp',
            'session_id',
            'authToken',
            'userSession',
            'currentUser'
        ];

        storageKeys.forEach(key => {
            localStorage.removeItem(key);
            sessionStorage.removeItem(key);
        });

        console.log('🗑️ All storage data cleared');
    }

    stopBackgroundProcesses() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.log('⏹️ Token refresh stopped');
        }
    }

    notifyLogoutComplete() {
        window.dispatchEvent(new CustomEvent('userLogout', {
            detail: {
                timestamp: new Date().toISOString(),
                source: 'AuthService'
            }
        }));
        console.log('📢 Logout event dispatched');
    }

    redirectToHomepage() {
        const baseUrl = window.location.origin;
        const loginUrl = baseUrl + '/login.html';
        window.location.replace(loginUrl);
    }

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

    isAuthenticated() {
        return !!this.token;
    }

    async testConnection() {
        try {
            const response = await fetch(`${this.apiBase}/health`, {
                method: 'GET',
                timeout: 5000
            });
            return response.ok;
        } catch (error) {
            console.warn('Auth service connection test failed:', error);
            return false;
        }
    }

    getUser() {
        return this.user;
    }

    getToken() {
        return this.token;
    }

    hasPermission(permission) {
        if (!this.user) return false;
        return this.user.permissions?.includes(permission) || 
               this.user.role === 'admin';
    }

    getUserRole() {
        return this.user?.role || 'guest';
    }

    startTokenRefresh() {
        this.refreshInterval = setInterval(async () => {
            try {
                await this.getCurrentUser();
            } catch (error) {
                console.warn('Token refresh failed, logging out:', error);
                this.logout();
            }
        }, 30 * 60 * 1000);
    }

    showLoginForm() {
        if (window.location.pathname.includes('login.html')) {
            return;
        }
        window.location.href = 'login.html';
    }

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
                        <div id="login-error" class="error-message" style="display:none;"></div>
                    </form>
                </div>
                <div class="auth-modal-footer">
                    <small>License Plate Recognition Security System v2.1.0</small>
                </div>
            </div>
        `;

        const form = modal.querySelector('#login-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleLoginSubmit(e);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                e.preventDefault();
            }
        });

        return modal;
    }

    async handleLoginSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const username = formData.get('username');
        const password = formData.get('password');

        const submitBtn = form.querySelector('.btn-login');
        const errorDiv = form.querySelector('#login-error');

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
        errorDiv.style.display = 'none';

        try {
            await this.login(username, password);
            const modal = document.getElementById('login-modal');
            if (modal) {
                modal.remove();
            }
            this.showToast('Login successful!', 'success');
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${this.getToastIcon(type)}"></i>
            <span>${message}</span>
        `;

        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        container.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 3000);
    }

    getToastIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || 'fa-info-circle';
    }
}const authStyles=` .auth-modal-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);display:flex;align-items:center;justify-content:center;z-index:10000;backdrop-filter:blur(5px);}.auth-modal{background:var(--bg-primary,#ffffff);border-radius:12px;box-shadow:0 20px 40px rgba(0,0,0,0.3);max-width:400px;width:90%;max-height:90vh;overflow:auto;animation:modalSlideIn 0.3s ease-out;}.auth-modal-header{padding:24px 24px 16px;border-bottom:1px solid var(--border-color,#e0e0e0);text-align:center;}.auth-modal-header h2{margin:0;color:var(--text-primary,#333333);font-size:1.5rem;font-weight:600;}.auth-modal-header i{color:var(--primary-color,#007bff);margin-right:8px;}.auth-modal-body{padding:24px;}.auth-form .form-group{margin-bottom:20px;}.auth-form label{display:block;margin-bottom:6px;color:var(--text-primary,#333333);font-weight:500;}.auth-form input{width:100%;padding:12px 16px;border:2px solid var(--border-color,#e0e0e0);border-radius:8px;font-size:16px;transition:border-color 0.2s ease;background:var(--bg-secondary,#ffffff);color:var(--text-primary,#333333);box-sizing:border-box;}.auth-form input:focus{outline:none;border-color:var(--primary-color,#007bff);box-shadow:0 0 0 3px rgba(0,123,255,0.1);}.form-actions{margin-top:24px;text-align:center;}.btn-login{width:100%;padding:14px 24px;background:var(--primary-color,#007bff);color:white;border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;transition:background-color 0.2s ease;}.btn-login:hover:not(:disabled){background:var(--primary-hover,#0056b3);}.btn-login:disabled{opacity:0.7;cursor:not-allowed;}.error-message{margin-top:16px;padding:12px;background:#fee;border:1px solid #fcc;border-radius:6px;color:#c33;font-size:14px;text-align:center;}.auth-modal-footer{padding:16px 24px;text-align:center;border-top:1px solid var(--border-color,#e0e0e0);background:var(--bg-secondary,#f8f9fa);color:var(--text-secondary,#666666);border-radius:0 0 12px 12px;}.toast-container{position:fixed;top:20px;right:20px;z-index:10001;pointer-events:none;}.toast{display:flex;align-items:center;padding:12px 16px;margin-bottom:8px;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.15);animation:toastSlideIn 0.3s ease-out;pointer-events:auto;min-width:300px;}.toast i{margin-right:8px;font-size:16px;}.toast-success{background:#d4edda;color:#155724;border:1px solid #c3e6cb;}.toast-error{background:#f8d7da;color:#721c24;border:1px solid #f5c6cb;}.toast-warning{background:#fff3cd;color:#856404;border:1px solid #ffeaa7;}.toast-info{background:#d1ecf1;color:#0c5460;border:1px solid #bee5eb;}@keyframes modalSlideIn{from{opacity:0;transform:translateY(-50px)scale(0.9);}to{opacity:1;transform:translateY(0)scale(1);}}@keyframes toastSlideIn{from{opacity:0;transform:translateX(100%);}to{opacity:1;transform:translateX(0);}}[data-theme="dark"] .auth-modal{background:var(--bg-primary,#2d3748);color:var(--text-primary,#ffffff);}[data-theme="dark"] .auth-modal-header{border-bottom-color:var(--border-color,#4a5568);}[data-theme="dark"] .auth-form input{background:var(--bg-secondary,#4a5568);border-color:var(--border-color,#6b7280);color:var(--text-primary,#ffffff);}[data-theme="dark"] .auth-modal-footer{background:var(--bg-secondary,#374151);border-top-color:var(--border-color,#4a5568);}`;if(!document.getElementById('auth-styles')){const styleSheet=document.createElement('style');styleSheet.id='auth-styles';styleSheet.textContent=authStyles;document.head.appendChild(styleSheet);}export default AuthService;