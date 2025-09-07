const API_BASE = 'http://localhost:8001';
let loginModal, signupModal;

document.addEventListener('DOMContentLoaded', function() {
    initializeModals();
    initializeAnimations();
    initializeNavigation();
    checkExistingAuth();
});

function initializeModals() {
    loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    signupModal = new bootstrap.Modal(document.getElementById('signupModal'));
    
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('signupForm').addEventListener('submit', handleSignup);
}

function initializeAnimations() {
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
    
    document.querySelectorAll('.feature-card, .tech-feature').forEach(el => {
        observer.observe(el);
    });
}

function initializeNavigation() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
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

function checkExistingAuth() {
    const token = localStorage.getItem('lpr_auth_token');
    if (token) {
        showDashboardOption();
    }
}

function showDashboardOption() {
    const loginButtons = document.querySelectorAll('[onclick="showLoginModal()"]');
    loginButtons.forEach(btn => {
        btn.innerHTML = '<i class="fas fa-tachometer-alt"></i> Go to Dashboard';
        btn.onclick = () => window.location.href = '/';
    });
}

function showLoginModal() {
    hideError('loginError');
    document.getElementById('loginForm').reset();
    loginModal.show();
}

function showSignupModal() {
    hideError('signupError');
    hideSuccess('signupSuccess');
    document.getElementById('signupForm').reset();
    signupModal.show();
}

function switchToLogin() {
    signupModal.hide();
    setTimeout(() => showLoginModal(), 300);
}

function switchToSignup() {
    loginModal.hide();
    setTimeout(() => showSignupModal(), 300);
}

async function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const username = formData.get('username') || document.getElementById('loginUsername').value;
    const password = formData.get('password') || document.getElementById('loginPassword').value;
    
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
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
        localStorage.setItem('lpr_auth_token', data.access_token);
        console.log('Login successful, token stored:', data.access_token.substring(0, 50) + '...');
        showSuccess('Login successful! Redirecting to dashboard...');
        
        setTimeout(() => {
            console.log('Redirecting to dashboard');
            window.location.href = '/';
        }, 1500);
    } catch (error) {
        showError('loginError', error.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

async function handleSignup(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const firstName = formData.get('firstName') || document.getElementById('signupFirstName').value;
    const lastName = formData.get('lastName') || document.getElementById('signupLastName').value;
    const email = formData.get('email') || document.getElementById('signupEmail').value;
    const username = formData.get('username') || document.getElementById('signupUsername').value;
    const password = formData.get('password') || document.getElementById('signupPassword').value;
    const confirmPassword = formData.get('confirmPassword') || document.getElementById('signupConfirmPassword').value;
    
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    if (password !== confirmPassword) {
        showError('signupError', 'Passwords do not match');
        return;
    }
    
    if (password.length < 8) {
        showError('signupError', 'Password must be at least 8 characters long');
        return;
    }
    
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
        
        showSuccess('signupSuccess', 'Account created successfully! You can now login.');
        form.reset();
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        
        setTimeout(() => {
            switchToLogin();
        }, 2000);
    } catch (error) {
        showError('signupError', error.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

function scrollToDemo() {
    const heroDemo = document.querySelector('.hero-demo');
    if (heroDemo) {
        heroDemo.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }
}

function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        setTimeout(() => hideError(elementId), 5000);
    }
}

function hideError(elementId) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

function showSuccess(elementId, message) {
    if (typeof elementId === 'string' && typeof message === 'undefined') {
        showToast(elementId, 'success');
        return;
    }
    
    const successElement = document.getElementById(elementId);
    if (successElement) {
        successElement.textContent = message;
        successElement.style.display = 'block';
        setTimeout(() => hideSuccess(elementId), 5000);
    }
}

function hideSuccess(elementId) {
    const successElement = document.getElementById(elementId);
    if (successElement) {
        successElement.style.display = 'none';
    }
}

function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
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
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function initializeDemoInteractions() {
    const demoCamera = document.querySelector('.demo-camera');
    if (demoCamera) {
        demoCamera.addEventListener('click', () => {
            showToast('Camera feed simulation - Click "Get Started" to access real cameras!', 'info');
        });
    }
}

document.addEventListener('DOMContentLoaded', initializeDemoInteractions);

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

window.showLoginModal = showLoginModal;
window.showSignupModal = showSignupModal;
window.switchToLogin = switchToLogin;
window.switchToSignup = switchToSignup;
window.scrollToDemo = scrollToDemo;