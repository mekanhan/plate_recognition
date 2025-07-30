/**
 * Main Application Controller
 * Orchestrates all components and manages application state
 */
import Sidebar from './components/layout/Sidebar.js';
import Header from './components/layout/Header.js';
import Dashboard from './pages/Dashboard.js';
import Cameras from './pages/CamerasPage.js';
import RecordingsPage from './pages/RecordingsPage.js';
import DetectionsPage from './pages/DetectionsPage.js';
import AnalyticsPage from './pages/AnalyticsPage.js';
import AlertsPage from './pages/AlertsPage.js';
import ReportsPage from './pages/ReportsPage.js';
import SettingsPage from './pages/SettingsPage.js';
import CameraSetupModal from './components/common/CameraSetupModal.js';
import SimpleCameraModal from './components/cameras/SimpleCameraModal.js';
import Modal from './components/common/Modal.js';

class LPRApplication {
    constructor() {
        this.currentPage = 'dashboard';
        this.components = {};
        this.modals = {};
        this.isInitialized = false;
        
        // Application state
        this.state = {
            user: {
                name: 'Security Admin',
                role: 'Administrator',
                permissions: ['cameras', 'detections', 'analytics', 'settings']
            },
            system: {
                online: true,
                version: '2.1.0',
                uptime: this.calculateUptime()
            }
        };

        this.init();
    }

    async init() {
        if (this.isInitialized) return;

        try {
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.initializeComponents());
            } else {
                this.initializeComponents();
            }

            this.isInitialized = true;
        } catch (error) {
            console.error('Failed to initialize application:', error);
            this.showError('Application failed to initialize. Please refresh the page.');
        }
    }

    initializeComponents() {
        // Create main layout structure if it doesn't exist
        this.createApplicationLayout();

        // Initialize layout components
        this.components.sidebar = new Sidebar();
        this.components.header = new Header();

        // Initialize page components
        this.initializePages();

        // Initialize modals
        this.initializeModals();

        // Set up global event listeners
        this.attachGlobalEventListeners();

        // Load initial page
        this.navigateToPage(this.getInitialPage());

        // Start application services
        this.startServices();

        console.log('LPR Application initialized successfully');
    }

    createApplicationLayout() {
        // Check if layout already exists
        if (document.querySelector('.sidebar') && document.querySelector('.main-content')) {
            return;
        }

        // Create main application structure
        const appStructure = `
            <nav class="sidebar"></nav>
            <main class="main-content">
                <header class="top-header"></header>
                
                <!-- Page Sections -->
                <section id="dashboard" class="content-section active"></section>
                <section id="cameras" class="content-section"></section>
                <section id="recordings" class="content-section"></section>
                <section id="detections" class="content-section"></section>
                <section id="analytics" class="content-section"></section>
                <section id="alerts" class="content-section"></section>
                <section id="reports" class="content-section"></section>
                <section id="settings" class="content-section"></section>
            </main>
            
            <!-- Loading Overlay -->
            <div class="loading-overlay" id="loading-overlay">
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Loading...</span>
                </div>
            </div>
            
            <!-- Toast Container -->
            <div class="toast-container" id="toast-container"></div>
        `;

        document.body.innerHTML = appStructure;
    }

    initializePages() {
        this.components.pages = {
            dashboard: new Dashboard(),
            cameras: new Cameras(),
            recordings: new RecordingsPage(),
            detections: new DetectionsPage(),
            analytics: new AnalyticsPage(),
            alerts: new AlertsPage(),
            reports: new ReportsPage(),
            settings: new SettingsPage()
        };
    }

    initializeModals() {
        this.modals.cameraSetup = new CameraSetupModal();
        this.modals.simpleCamera = new SimpleCameraModal();
    }

    attachGlobalEventListeners() {
        // Page navigation events
        window.addEventListener('navigate', (e) => {
            this.handleNavigation(e.detail);
        });

        // Page change events from sidebar
        window.addEventListener('pageChange', (e) => {
            this.navigateToPage(e.detail.pageId);
        });

        // Data refresh events
        window.addEventListener('dataRefresh', () => {
            this.refreshCurrentPage();
        });

        // Camera events
        window.addEventListener('cameraAdded', (e) => {
            this.handleCameraAdded(e.detail);
        });

        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleGlobalKeyboard(e);
        });

        // Hash change for direct URL navigation
        window.addEventListener('hashchange', () => {
            const page = window.location.hash.substring(1) || 'dashboard';
            this.navigateToPage(page);
        });

        // Before unload warning for unsaved changes
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges()) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            }
        });
    }

    navigateToPage(pageId) {
        if (!this.isValidPage(pageId)) {
            console.warn(`Invalid page: ${pageId}`);
            return;
        }

        // Clean up current page before navigating
        this.cleanupCurrentPage();

        // Hide current page
        const currentSection = document.querySelector('.content-section.active');
        if (currentSection) {
            currentSection.classList.remove('active');
        }

        // Show new page
        const newSection = document.getElementById(pageId);
        if (newSection) {
            newSection.classList.add('active');
        }

        // Update sidebar active state
        if (this.components.sidebar) {
            this.components.sidebar.setActiveItem(pageId);
        }

        // Update page title
        document.title = `LPR System - ${this.capitalizeFirst(pageId)}`;

        // Update current page
        this.currentPage = pageId;

        // Initialize page component if needed
        if (!this.components.pages[pageId]) {
            this.loadPageComponent(pageId);
        }

        // Track page view
        this.trackPageView(pageId);
    }

    async loadPageComponent(pageId) {
        try {
            this.showLoading();

            // All pages are now pre-initialized, but this could be used for lazy loading
            if (!this.components.pages[pageId]) {
                switch (pageId) {
                    case 'detections':
                        this.components.pages[pageId] = new DetectionsPage();
                        break;
                    case 'analytics':
                        this.components.pages[pageId] = new AnalyticsPage();
                        break;
                    case 'alerts':
                        this.components.pages[pageId] = new AlertsPage();
                        break;
                    case 'reports':
                        this.components.pages[pageId] = new ReportsPage();
                        break;
                    case 'settings':
                        this.components.pages[pageId] = new SettingsPage();
                        break;
                }
            }

            this.hideLoading();
        } catch (error) {
            console.error(`Failed to load page component: ${pageId}`, error);
            this.hideLoading();
            this.showError(`Failed to load ${pageId} page`);
        }
    }

    cleanupCurrentPage() {
        // Clean up current page components to prevent memory leaks and black screens
        const currentPageComponent = this.components.pages[this.currentPage];
        
        if (currentPageComponent && typeof currentPageComponent.destroy === 'function') {
            try {
                currentPageComponent.destroy();
                console.log(`${this.currentPage} page cleaned up successfully`);
            } catch (error) {
                console.warn(`Error cleaning up ${this.currentPage} page:`, error);
            }
        }
        
        // Re-initialize the page component after cleanup (for when user navigates back)
        if (this.currentPage === 'cameras') {
            try {
                this.components.pages.cameras = new Cameras();
                console.log('Cameras page component re-initialized');
            } catch (error) {
                console.warn('Error re-initializing cameras page:', error);
            }
        }
    }

    handleNavigation(detail) {
        const { page, action, section } = detail;

        if (page) {
            this.navigateToPage(page);
        }

        if (action) {
            this.handlePageAction(page, action, section);
        }
    }

    handlePageAction(page, action, section) {
        switch (action) {
            case 'add':
                if (page === 'cameras') {
                    this.showAddCameraModal();
                }
                break;
            case 'edit':
                // Handle edit actions
                break;
            case 'delete':
                // Handle delete actions
                break;
        }
    }

    handleCameraAdded(cameraData) {
        // Refresh camera list
        if (this.components.pages.cameras) {
            this.components.pages.cameras.loadCameras();
        }

        // Update dashboard metrics
        if (this.components.pages.dashboard) {
            this.components.pages.dashboard.loadData();
        }

        // Show success message
        this.showToast('Camera added successfully', 'success');
    }

    handleGlobalKeyboard(e) {
        // Ctrl/Cmd + R for refresh
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            this.refreshCurrentPage();
        }

        // Ctrl/Cmd + N for new camera
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            this.showAddCameraModal();
        }

        // Escape to close modals
        if (e.key === 'Escape') {
            this.closeTopModal();
        }
    }

    // Modal management
    showAddCameraModal() {
        if (this.modals.simpleCamera) {
            this.modals.simpleCamera.show();
        }
    }

    closeTopModal() {
        // Close the topmost modal
        Object.values(this.modals).forEach(modal => {
            if (modal.isVisible) {
                modal.hide();
            }
        });
    }

    // Service management
    startServices() {
        // Start periodic data refresh
        this.startDataRefreshService();

        // Start system health monitoring
        this.startHealthMonitoring();

        // Start notification polling
        this.startNotificationService();
    }

    startDataRefreshService() {
        // Refresh data every 30 seconds
        setInterval(() => {
            if (this.currentPage === 'dashboard') {
                this.refreshCurrentPage();
            }
        }, 30000);
    }

    startHealthMonitoring() {
        // Check system health every minute
        setInterval(() => {
            this.checkSystemHealth();
        }, 60000);
    }

    startNotificationService() {
        // Poll for notifications every 10 seconds
        setInterval(() => {
            this.checkForNotifications();
        }, 10000);
    }

    // Data management
    refreshCurrentPage() {
        const currentPageComponent = this.components.pages[this.currentPage];
        if (currentPageComponent && typeof currentPageComponent.loadData === 'function') {
            currentPageComponent.loadData();
        }
    }

    async checkSystemHealth() {
        try {
            // This would make an actual API call
            const health = await this.fetchSystemHealth();
            
            if (this.components.header) {
                this.components.header.setSystemStatus(health);
            }
        } catch (error) {
            console.error('Health check failed:', error);
        }
    }

    async checkForNotifications() {
        try {
            // This would make an actual API call
            const notifications = await this.fetchNotifications();
            
            notifications.forEach(notification => {
                if (this.components.header) {
                    this.components.header.addNotification(notification);
                }
            });
        } catch (error) {
            console.error('Notification check failed:', error);
        }
    }

    // UI helpers
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.querySelector('span').textContent = message;
            overlay.style.display = 'flex';
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icon = this.getToastIcon(type);
        toast.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
            <button class="toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Close button functionality
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.remove();
        });

        container.appendChild(toast);

        // Auto remove
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, duration);
    }

    showError(message, details = null) {
        console.error('Application Error:', message, details);
        this.showToast(message, 'error', 5000);
    }

    // Utility methods
    getInitialPage() {
        const hash = window.location.hash.substring(1);
        return this.isValidPage(hash) ? hash : 'dashboard';
    }

    isValidPage(pageId) {
        const validPages = ['dashboard', 'cameras', 'recordings', 'detections', 'analytics', 'alerts', 'reports', 'settings'];
        return validPages.includes(pageId);
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    getToastIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || 'fa-info-circle';
    }

    calculateUptime() {
        // This would calculate actual uptime
        return '15d 4h 23m';
    }

    hasUnsavedChanges() {
        // Check if any forms have unsaved changes
        return false;
    }

    trackPageView(pageId) {
        // Analytics tracking would go here
        console.log(`Page view: ${pageId}`);
    }

    // Mock API methods (would be replaced with actual API calls)
    async fetchSystemHealth() {
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    online: true,
                    uptime: this.calculateUptime(),
                    lastUpdate: new Date()
                });
            }, 100);
        });
    }

    async fetchNotifications() {
        return new Promise(resolve => {
            setTimeout(() => {
                resolve([]); // No new notifications for now
            }, 100);
        });
    }

    // Public API for external access
    getComponent(name) {
        return this.components[name];
    }

    getModal(name) {
        return this.modals[name];
    }

    getCurrentPage() {
        return this.currentPage;
    }

    getState() {
        return { ...this.state };
    }

    // Cleanup method
    destroy() {
        // Stop all services
        clearInterval(this.dataRefreshInterval);
        clearInterval(this.healthCheckInterval);
        clearInterval(this.notificationInterval);

        // Destroy all components
        Object.values(this.components).forEach(component => {
            if (component && typeof component.destroy === 'function') {
                component.destroy();
            }
        });

        // Destroy all modals
        Object.values(this.modals).forEach(modal => {
            if (modal && typeof modal.destroy === 'function') {
                modal.destroy();
            }
        });

        // Remove event listeners
        window.removeEventListener('navigate', this.handleNavigation);
        window.removeEventListener('pageChange', this.navigateToPage);
        window.removeEventListener('dataRefresh', this.refreshCurrentPage);

        this.isInitialized = false;
    }
}

// Initialize application when DOM is ready
function initializeApp() {
    window.lprApp = new LPRApplication();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    // DOM is already loaded
    initializeApp();
}

// Export for module systems
export default LPRApplication;