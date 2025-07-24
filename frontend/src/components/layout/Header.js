/**
 * Top Header Component
 * Handles system status, notifications, and user actions
 */
class Header {
    constructor() {
        this.systemStatus = {
            online: true,
            uptime: '15d 4h 23m',
            lastUpdate: new Date()
        };
        this.notifications = [];
        
        this.init();
        this.loadTheme();
    }

    init() {
        this.render();
        this.attachEventListeners();
        this.startStatusUpdates();
        this.loadNotifications();
    }

    render() {
        const headerContainer = document.querySelector('.top-header') || this.createHeaderContainer();
        headerContainer.innerHTML = this.getTemplate();
        
        // Update theme button after rendering
        this.updateThemeButton();
    }

    createHeaderContainer() {
        const header = document.createElement('header');
        header.className = 'top-header';
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.insertBefore(header, mainContent.firstChild);
        }
        return header;
    }

    getTemplate() {
        return `
            <div class="header-left">
                <button class="sidebar-toggle">
                    <i class="fas fa-bars"></i>
                </button>
            </div>
            
            <div class="header-right">
                <div class="system-status">
                    <span class="status-indicator ${this.systemStatus.online ? 'online' : 'offline'}"></span>
                    <span>System ${this.systemStatus.online ? 'Online' : 'Offline'}</span>
                    <span class="uptime">Uptime: ${this.systemStatus.uptime}</span>
                    <span class="last-update">Last Update: <span id="last-update-time">${this.formatTime(this.systemStatus.lastUpdate)}</span></span>
                </div>
                <div class="header-actions">
                    <button class="header-btn" id="refresh-btn" title="Refresh Data">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                    <div class="notification-menu">
                        <button class="header-btn" id="notifications-btn" title="Notifications">
                            <i class="fas fa-bell"></i>
                            ${this.notifications.length > 0 ? '<span class="notification-dot"></span>' : ''}
                        </button>
                        <div class="notification-dropdown" id="notification-dropdown">
                            <div class="notification-header">
                                <h4>Notifications</h4>
                                <button class="mark-all-read" id="mark-all-read">Mark all read</button>
                            </div>
                            <div class="notification-list" id="notification-list">
                                ${this.renderNotifications()}
                            </div>
                            <div class="notification-footer">
                                <a href="#alerts" class="view-all-notifications">View all alerts</a>
                            </div>
                        </div>
                    </div>
                    <button class="header-btn" id="dark-mode-toggle" title="Toggle Theme">
                        <i class="fas fa-moon"></i>
                    </button>
                    <button class="header-btn" id="fullscreen-btn" title="Fullscreen">
                        <i class="fas fa-expand"></i>
                    </button>
                    <div class="user-menu">
                        <button class="header-btn user-avatar">
                            <i class="fas fa-user"></i>
                        </button>
                        <div class="user-dropdown">
                            <a href="#profile">Profile</a>
                            <a href="#preferences">Preferences</a>
                            <hr>
                            <a href="#logout">Logout</a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderNotifications() {
        if (this.notifications.length === 0) {
            return '<div class="no-notifications">No new notifications</div>';
        }

        return this.notifications.map(notification => `
            <div class="notification-item ${notification.read ? 'read' : 'unread'}" data-id="${notification.id}">
                <div class="notification-icon ${notification.type}">
                    <i class="fas ${this.getNotificationIcon(notification.type)}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${this.getRelativeTime(notification.timestamp)}</div>
                </div>
                <button class="notification-dismiss" data-id="${notification.id}">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }

    attachEventListeners() {
        // Sidebar toggle
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }

        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        // Notifications
        const notificationsBtn = document.getElementById('notifications-btn');
        if (notificationsBtn) {
            notificationsBtn.addEventListener('click', () => this.toggleNotifications());
        }

        // Mark all read
        const markAllRead = document.getElementById('mark-all-read');
        if (markAllRead) {
            markAllRead.addEventListener('click', () => this.markAllNotificationsRead());
        }

        // Theme toggle - simple direct approach
        const themeToggle = document.getElementById('dark-mode-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleDarkMode());
        }

        // Fullscreen toggle
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        }

        // User menu
        const userAvatar = document.querySelector('.user-avatar');
        if (userAvatar) {
            userAvatar.addEventListener('click', () => this.toggleUserMenu());
        }

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => this.closeDropdowns(e));
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');
        
        if (sidebar && mainContent) {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('sidebar-collapsed');
        }

        // Trigger sidebar component if it exists
        if (window.sidebar) {
            window.sidebar.toggleCollapse();
        }
    }

    refreshData() {
        const refreshBtn = document.getElementById('refresh-btn');
        const icon = refreshBtn.querySelector('i');
        
        // Add spinning animation
        icon.classList.add('fa-spin');
        refreshBtn.disabled = true;

        // Simulate refresh operation
        setTimeout(() => {
            icon.classList.remove('fa-spin');
            refreshBtn.disabled = false;
            this.updateSystemStatus();
            this.showToast('Data refreshed successfully', 'success');
        }, 1500);

        // Trigger global refresh event
        window.dispatchEvent(new CustomEvent('dataRefresh'));
    }

    toggleNotifications() {
        const dropdown = document.getElementById('notification-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('show');
        }
    }

    markAllNotificationsRead() {
        this.notifications = this.notifications.map(n => ({ ...n, read: true }));
        this.updateNotificationBadge();
        this.render();
    }

    toggleDarkMode() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        
        if (currentTheme === 'dark') {
            this.enableLightMode();
        } else {
            this.enableDarkMode();
        }
    }
    
    enableDarkMode() {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        this.updateThemeButton();
    }
    
    enableLightMode() {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
        this.updateThemeButton();
    }
    
    updateThemeButton() {
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) {
            const icon = darkModeToggle.querySelector('i');
            const currentTheme = document.documentElement.getAttribute('data-theme');
            
            if (icon) {
                if (currentTheme === 'dark') {
                    icon.className = 'fas fa-sun';
                    darkModeToggle.title = 'Switch to Light Mode';
                } else {
                    icon.className = 'fas fa-moon';
                    darkModeToggle.title = 'Switch to Dark Mode';
                }
            }
        }
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }

    toggleUserMenu() {
        const dropdown = document.querySelector('.user-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('show');
        }
    }

    closeDropdowns(e) {
        // Close notification dropdown
        const notificationDropdown = document.getElementById('notification-dropdown');
        const notificationBtn = document.getElementById('notifications-btn');
        if (notificationDropdown && !notificationBtn.contains(e.target) && !notificationDropdown.contains(e.target)) {
            notificationDropdown.classList.remove('show');
        }

        // Close user dropdown
        const userDropdown = document.querySelector('.user-dropdown');
        const userAvatar = document.querySelector('.user-avatar');
        if (userDropdown && !userAvatar.contains(e.target) && !userDropdown.contains(e.target)) {
            userDropdown.classList.remove('show');
        }
    }

    startStatusUpdates() {
        // Update time every minute
        setInterval(() => {
            this.systemStatus.lastUpdate = new Date();
            const timeElement = document.getElementById('last-update-time');
            if (timeElement) {
                timeElement.textContent = this.formatTime(this.systemStatus.lastUpdate);
            }
        }, 60000);
    }

    updateSystemStatus() {
        // Simulate system status check
        this.systemStatus.lastUpdate = new Date();
        this.systemStatus.online = true; // This would come from actual system check
        this.render();
    }

    loadNotifications() {
        // This would typically load from API
        this.notifications = [
            {
                id: 1,
                type: 'warning',
                title: 'Camera Offline',
                message: 'Camera 3 at parking lot is not responding',
                timestamp: new Date(Date.now() - 15 * 60 * 1000),
                read: false
            },
            {
                id: 2,
                type: 'info',
                title: 'System Update',
                message: 'LPR accuracy improved to 98.5%',
                timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
                read: false
            }
        ];
        this.updateNotificationBadge();
    }

    updateNotificationBadge() {
        const unreadCount = this.notifications.filter(n => !n.read).length;
        const badge = document.querySelector('.notification-dot');
        const btn = document.getElementById('notifications-btn');
        
        if (unreadCount > 0) {
            if (!badge && btn) {
                btn.innerHTML += '<span class="notification-dot"></span>';
            }
        } else {
            if (badge) {
                badge.remove();
            }
        }
    }

    getNotificationIcon(type) {
        const icons = {
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle',
            info: 'fa-info-circle',
            success: 'fa-check-circle'
        };
        return icons[type] || 'fa-bell';
    }

    formatTime(date) {
        return date.toLocaleTimeString('en-US', { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    getRelativeTime(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`;
        return `${Math.floor(minutes / 1440)}d ago`;
    }

    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
        `;

        const container = document.getElementById('toast-container') || document.body;
        container.appendChild(toast);

        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // Public methods
    addNotification(notification) {
        this.notifications.unshift({
            id: Date.now(),
            timestamp: new Date(),
            read: false,
            ...notification
        });
        this.updateNotificationBadge();
        this.render();
    }

    setSystemStatus(status) {
        this.systemStatus = { ...this.systemStatus, ...status };
        this.render();
    }

    loadTheme() {
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme === 'dark') {
            this.enableDarkMode();
        } else if (savedTheme === 'light') {
            this.enableLightMode();
        } else if (prefersDark) {
            // Respect system preference if no saved preference
            this.enableDarkMode();
        } else {
            this.enableLightMode();
        }
    }
}

export default Header;