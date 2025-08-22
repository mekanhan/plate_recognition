/**
 * Homepage JavaScript functionality
 * Handles authentication modals, navigation, and interactions
 */

// API Configuration
const API_BASE = 'http://localhost:8001';

// Global state
let loginModal, signupModal;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    initializeModals();
    initializeAnimations();
    initializeNavigation();
    checkExistingAuth();
});

/**
 * Initialize Bootstrap modals
 */
function initializeModals() {
    loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    signupModal = new bootstrap.Modal(document.getElementById('signupModal'));
    
    // Form event listeners
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('signupForm').addEventListener('submit', handleSignup);
}

/**
 * Initialize page animations
 */
function initializeAnimations() {
    // Add intersection observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
            }
        });
    }, observerOptions);
    
    // Observe feature cards and tech features
    document.querySelectorAll('.feature-card, .tech-feature').forEach(el => {
        observer.observe(el);
    });
}

/**
 * Initialize smooth navigation
 */
function initializeNavigation() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Check if user is already authenticated
 */
function checkExistingAuth() {
    const token = localStorage.getItem('lpr_auth_token');
    if (token) {
        // Show option to go directly to dashboard
        showDashboardOption();
    }
}

/**
 * Show dashboard access option for authenticated users
 */
function showDashboardOption() {
    const loginButtons = document.querySelectorAll('[onclick="showLoginModal()"]');
    loginButtons.forEach(btn => {
        btn.innerHTML = '<i class="fas fa-tachometer-alt"></i> Go to Dashboard';
        btn.onclick = () => window.location.href = '/';
    });
}

/**
 * Show login modal
 */
function showLoginModal() {
    // Clear any previous errors
    hideError('loginError');
    document.getElementById('loginForm').reset();
    loginModal.show();
}

/**
 * Show signup modal
 */
function showSignupModal() {
    // Clear any previous errors/success messages
    hideError('signupError');
    hideSuccess('signupSuccess');
    document.getElementById('signupForm').reset();
    signupModal.show();
}

/**
 * Switch from signup to login modal
 */
function switchToLogin() {
    signupModal.hide();
    setTimeout(() => showLoginModal(), 300);
}

/**
 * Switch from login to signup modal
 */
function switchToSignup() {
    loginModal.hide();
    setTimeout(() => showSignupModal(), 300);
}

/**
 * Handle login form submission
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const username = formData.get('username') || document.getElementById('loginUsername').value;
    const password = formData.get('password') || document.getElementById('loginPassword').value;
    
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
    hideError('loginError');
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/login`, {
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
        
        // Store authentication token
        localStorage.setItem('lpr_auth_token', data.access_token);
        
        // Debug log
        console.log('Login successful, token stored:', data.access_token.substring(0, 50) + '...');
        
        // Show success and redirect
        showSuccess('Login successful! Redirecting to dashboard...');
        
        setTimeout(() => {
            console.log('Redirecting to dashboard');
            window.location.href = '/';
        }, 1500);
        
    } catch (error) {
        showError('loginError', error.message);
        
        // Reset button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

/**
 * Handle signup form submission
 */
async function handleSignup(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Get form values
    const firstName = formData.get('firstName') || document.getElementById('signupFirstName').value;
    const lastName = formData.get('lastName') || document.getElementById('signupLastName').value;
    const email = formData.get('email') || document.getElementById('signupEmail').value;
    const username = formData.get('username') || document.getElementById('signupUsername').value;
    const password = formData.get('password') || document.getElementById('signupPassword').value;
    const confirmPassword = formData.get('confirmPassword') || document.getElementById('signupConfirmPassword').value;
    
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    // Validate passwords match
    if (password !== confirmPassword) {
        showError('signupError', 'Passwords do not match');
        return;
    }
    
    // Validate password strength
    if (password.length < 8) {
        showError('signupError', 'Password must be at least 8 characters long');
        return;
    }
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
    hideError('signupError');
    hideSuccess('signupSuccess');
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/quick-setup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Account creation failed');
        }

        // Show success message
        showSuccess('signupSuccess', 'Account created successfully! You can now login.');
        form.reset();
        
        // Reset button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        
        // Auto-switch to login after 2 seconds
        setTimeout(() => {
            switchToLogin();
        }, 2000);
        
    } catch (error) {
        showError('signupError', error.message);
        
        // Reset button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

/**
 * Scroll to demo section
 */
function scrollToDemo() {
    const heroDemo = document.querySelector('.hero-demo');
    if (heroDemo) {
        heroDemo.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }
}

/**
 * Show error message
 */
function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => hideError(elementId), 5000);
    }
}

/**
 * Hide error message
 */
function hideError(elementId) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

/**
 * Show success message
 */
function showSuccess(elementId, message) {
    if (typeof elementId === 'string' && typeof message === 'undefined') {
        // If only one parameter, it's a general success message
        showToast(elementId, 'success');
        return;
    }
    
    const successElement = document.getElementById(elementId);
    if (successElement) {
        successElement.textContent = message;
        successElement.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => hideSuccess(elementId), 5000);
    }
}

/**
 * Hide success message
 */
function hideSuccess(elementId) {
    const successElement = document.getElementById(elementId);
    if (successElement) {
        successElement.style.display = 'none';
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'primary'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-times-circle' : 'fa-info-circle'} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove from DOM when hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * Handle demo interactions
 */
function initializeDemoInteractions() {
    // Add click handlers for demo elements
    const demoCamera = document.querySelector('.demo-camera');
    if (demoCamera) {
        demoCamera.addEventListener('click', () => {
            showToast('Camera feed simulation - Click "Get Started" to access real cameras!', 'info');
        });
    }
}

// Initialize demo interactions when page loads
document.addEventListener('DOMContentLoaded', initializeDemoInteractions);

// Smooth navbar background on scroll
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.backgroundColor = 'rgba(52, 58, 64, 0.95)';
        navbar.style.backdropFilter = 'blur(10px)';
    } else {
        navbar.style.backgroundColor = 'rgba(52, 58, 64, 0.8)';
        navbar.style.backdropFilter = 'none';
    }
});

// Export functions for global access
window.showLoginModal = showLoginModal;
window.showSignupModal = showSignupModal;
window.switchToLogin = switchToLogin;
window.switchToSignup = switchToSignup;
window.scrollToDemo = scrollToDemo;