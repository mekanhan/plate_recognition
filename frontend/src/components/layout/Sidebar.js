/**
 * Sidebar Navigation Component
 * Handles main application navigation and user information
 */
class Sidebar {
    constructor() {
        this.isCollapsed = false;
        this.activeMenuItem = 'dashboard';
        this.menuItems = [
            { id: 'dashboard', icon: 'fas fa-tachometer-alt', label: 'Dashboard', badge: null },
            { id: 'cameras', icon: 'fas fa-video', label: 'Cameras', badge: 'camera-count' },
            { id: 'recordings', icon: 'fas fa-film', label: 'Recordings', badge: 'recording-count' },
            { id: 'detections', icon: 'fas fa-search', label: 'Detections', badge: 'detection-alerts' },
            { id: 'analytics', icon: 'fas fa-chart-bar', label: 'Analytics', badge: null },
            { id: 'alerts', icon: 'fas fa-bell', label: 'Alerts', badge: 'alert-count' },
            { id: 'reports', icon: 'fas fa-file-alt', label: 'Reports', badge: null },
            { id: 'settings', icon: 'fas fa-cog', label: 'Settings', badge: null }
        ];
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
        this.updateBadges();
    }

    render() {
        const sidebarContainer = document.querySelector('.sidebar') || this.createSidebarContainer();
        sidebarContainer.innerHTML = this.getTemplate();
    }

    createSidebarContainer() {
        const sidebar = document.createElement('nav');
        sidebar.className = 'sidebar';
        document.body.insertBefore(sidebar, document.body.firstChild);
        return sidebar;
    }

    getTemplate() {
        return `
            <div class="sidebar-header">
                <div class="logo">
                    <img src="vision_port_text.png" alt="Vision Port" class="logo-text">
                    <img src="logo.png" alt="LPR System Logo" class="logo-icon">
                </div>
                <button class="sidebar-collapse-btn" id="sidebar-collapse-btn">
                    <i class="fas fa-bars"></i>
                </button>
            </div>
            
            <ul class="sidebar-menu">
                ${this.menuItems.map(item => this.renderMenuItem(item)).join('')}
            </ul>
            
            <div class="sidebar-footer">
                <div class="user-info">
                    <i class="fas fa-user-circle"></i>
                    <div class="user-details">
                        <span class="user-name">Security Admin</span>
                        <span class="user-role">Administrator</span>
                    </div>
                </div>
                <button class="logout-btn">
                    <i class="fas fa-sign-out-alt"></i>
                </button>
            </div>
        `;
    }

    renderMenuItem(item) {
        const isActive = item.id === this.activeMenuItem ? 'active' : '';
        const badgeHtml = item.badge ? `<span class="badge" id="${item.badge}"></span>` : '';
        
        return `
            <li class="menu-item ${isActive}">
                <a href="#${item.id}" class="menu-link" data-page="${item.id}">
                    <i class="${item.icon}"></i>
                    <span>${item.label}</span>
                    ${badgeHtml}
                </a>
            </li>
        `;
    }

    attachEventListeners() {
        // Sidebar collapse toggle
        const collapseBtn = document.getElementById('sidebar-collapse-btn');
        if (collapseBtn) {
            collapseBtn.addEventListener('click', () => this.toggleCollapse());
        }

        // Menu item navigation
        const menuLinks = document.querySelectorAll('.menu-link');
        menuLinks.forEach(link => {
            link.addEventListener('click', (e) => this.handleMenuClick(e));
        });

        // Logout button
        const logoutBtn = document.querySelector('.logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }
    }

    toggleCollapse() {
        this.isCollapsed = !this.isCollapsed;
        const appLayout = document.querySelector('.app-layout');
        const sidebar = document.querySelector('.sidebar');
        
        if (appLayout) {
            appLayout.setAttribute('data-nav-expanded', (!this.isCollapsed).toString());
        }
        
        // Keep legacy classes for backward compatibility during migration
        if (this.isCollapsed) {
            sidebar.classList.add('collapsed');
        } else {
            sidebar.classList.remove('collapsed');
        }

        // Store preference
        localStorage.setItem('sidebar-collapsed', this.isCollapsed.toString());
    }

    handleMenuClick(e) {
        e.preventDefault();
        const pageId = e.currentTarget.dataset.page;
        
        if (pageId && pageId !== this.activeMenuItem) {
            this.setActiveMenuItem(pageId);
            this.navigateToPage(pageId);
        }
    }

    setActiveMenuItem(pageId) {
        // Remove active class from current item
        const currentActive = document.querySelector('.menu-item.active');
        if (currentActive) {
            currentActive.classList.remove('active');
        }

        // Add active class to new item
        const newActive = document.querySelector(`[data-page="${pageId}"]`).closest('.menu-item');
        if (newActive) {
            newActive.classList.add('active');
        }

        this.activeMenuItem = pageId;
    }

    navigateToPage(pageId) {
        // Hide all content sections
        const sections = document.querySelectorAll('.content-section');
        sections.forEach(section => section.classList.remove('active'));

        // Show target section
        const targetSection = document.getElementById(pageId);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        // Update URL hash
        window.location.hash = pageId;

        // Trigger page change event
        window.dispatchEvent(new CustomEvent('pageChange', { 
            detail: { pageId, previousPage: this.activeMenuItem } 
        }));
    }

    updateBadges() {
        // Update camera count
        this.updateBadge('camera-count', '12');
        
        // Update detection alerts
        this.updateBadge('detection-alerts', '3', 'warning');
        
        // Update alert count
        this.updateBadge('alert-count', '2', 'danger');
    }

    updateBadge(badgeId, count, type = '') {
        const badge = document.getElementById(badgeId);
        if (badge) {
            badge.textContent = count;
            badge.className = `badge ${type}`;
        }
    }

    handleLogout() {
        if (confirm('Are you sure you want to logout?')) {
            // Clear any stored data
            localStorage.clear();
            sessionStorage.clear();
            
            // Redirect to login page
            window.location.href = '/login';
        }
    }

    // Public methods for external control
    setActiveItem(pageId) {
        this.setActiveMenuItem(pageId);
    }

    setBadgeCount(badgeId, count, type = '') {
        this.updateBadge(badgeId, count, type);
    }

    // Initialize from stored preferences
    loadPreferences() {
        const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
        
        if (isCollapsed) {
            // Don't call toggleCollapse() as it would toggle the state
            // Instead, directly set the collapsed state
            this.isCollapsed = true;
            const appLayout = document.querySelector('.app-layout');
            const sidebar = document.querySelector('.sidebar');
            
            if (appLayout) {
                appLayout.setAttribute('data-nav-expanded', 'false');
            }
            
            if (sidebar) {
                sidebar.classList.add('collapsed');
            }
        }
    }

    // Clean up event listeners
    destroy() {
        const collapseBtn = document.getElementById('sidebar-collapse-btn');
        if (collapseBtn) {
            collapseBtn.removeEventListener('click', this.toggleCollapse);
        }

        const menuLinks = document.querySelectorAll('.menu-link');
        menuLinks.forEach(link => {
            link.removeEventListener('click', this.handleMenuClick);
        });
    }
}

export default Sidebar;