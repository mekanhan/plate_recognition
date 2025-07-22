/**
 * LPR Framework - Core Application JavaScript
 */

class LPRApp {
	constructor() {
		this.theme = localStorage.getItem('theme') || 'light';
		this.sidebarOpen = false;
		this.websockets = new Map();
		this.init();
	}

	init() {
		this.setupTheme();
		this.setupMobileMenu();
		this.setupTooltips();
		this.setupModals();
		this.setupNotifications();
		this.startSystemMonitoring();
		
		// Initialize any page-specific components
		if (typeof this.initPage === 'function') {
			this.initPage();
		}
		
		console.log('LPR App initialized');
	}

	// Theme Management
	setupTheme() {
		document.documentElement.setAttribute('data-theme', this.theme);
		
		const themeToggle = document.querySelector('.theme-toggle');
		if (themeToggle) {
			themeToggle.addEventListener('click', () => this.toggleTheme());
		}
	}

	toggleTheme() {
		this.theme = this.theme === 'light' ? 'dark' : 'light';
		document.documentElement.setAttribute('data-theme', this.theme);
		localStorage.setItem('theme', this.theme);
		
		// Update theme toggle icon
		this.updateThemeToggleIcon();
	}

	updateThemeToggleIcon() {
		const themeToggle = document.querySelector('.theme-toggle');
		if (themeToggle) {
			const icon = themeToggle.querySelector('svg') || themeToggle.querySelector('.icon');
			if (icon) {
				icon.className = this.theme === 'light' ? 'icon-moon' : 'icon-sun';
			}
		}
	}

	// Mobile Menu Management
	setupMobileMenu() {
		const toggle = document.querySelector('.mobile-menu-toggle');
		const sidebar = document.querySelector('.app-sidebar');
		const overlay = document.querySelector('.sidebar-overlay');

		if (toggle && sidebar) {
			toggle.addEventListener('click', () => this.toggleSidebar());
		}

		if (overlay) {
			overlay.addEventListener('click', () => this.closeSidebar());
		}

		// Close sidebar on window resize if mobile menu is not needed
		window.addEventListener('resize', () => {
			if (window.innerWidth > 768 && this.sidebarOpen) {
				this.closeSidebar();
			}
		});
	}

	toggleSidebar() {
		this.sidebarOpen = !this.sidebarOpen;
		const sidebar = document.querySelector('.app-sidebar');
		const overlay = document.querySelector('.sidebar-overlay');

		if (sidebar) {
			sidebar.classList.toggle('open', this.sidebarOpen);
		}
		
		if (overlay) {
			overlay.classList.toggle('show', this.sidebarOpen);
		}
	}

	closeSidebar() {
		this.sidebarOpen = false;
		const sidebar = document.querySelector('.app-sidebar');
		const overlay = document.querySelector('.sidebar-overlay');

		if (sidebar) {
			sidebar.classList.remove('open');
		}
		
		if (overlay) {
			overlay.classList.remove('show');
		}
	}

	// Modal Management
	setupModals() {
		// Close modal when clicking outside
		document.addEventListener('click', (e) => {
			if (e.target.classList.contains('modal')) {
				this.closeModal(e.target);
			}
		});

		// Close modal with escape key
		document.addEventListener('keydown', (e) => {
			if (e.key === 'Escape') {
				const openModal = document.querySelector('.modal.show');
				if (openModal) {
					this.closeModal(openModal);
				}
			}
		});

		// Setup modal triggers
		document.addEventListener('click', (e) => {
			const trigger = e.target.closest('[data-modal-target]');
			if (trigger) {
				const targetId = trigger.getAttribute('data-modal-target');
				const modal = document.getElementById(targetId);
				if (modal) {
					this.openModal(modal);
				}
			}

			const closeBtn = e.target.closest('[data-modal-close]');
			if (closeBtn) {
				const modal = closeBtn.closest('.modal');
				if (modal) {
					this.closeModal(modal);
				}
			}
		});
	}

	openModal(modal) {
		modal.classList.add('show');
		document.body.style.overflow = 'hidden';
		
		// Focus first focusable element
		const focusable = modal.querySelector('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
		if (focusable) {
			focusable.focus();
		}
	}

	closeModal(modal) {
		modal.classList.remove('show');
		document.body.style.overflow = '';
	}

	// Tooltip Setup
	setupTooltips() {
		const tooltips = document.querySelectorAll('[data-tooltip]');
		tooltips.forEach(element => {
			this.createTooltip(element);
		});
	}

	createTooltip(element) {
		let tooltip = null;

		element.addEventListener('mouseenter', () => {
			const text = element.getAttribute('data-tooltip');
			const position = element.getAttribute('data-tooltip-position') || 'top';

			tooltip = document.createElement('div');
			tooltip.className = `tooltip tooltip-${position}`;
			tooltip.textContent = text;
			document.body.appendChild(tooltip);

			const rect = element.getBoundingClientRect();
			const tooltipRect = tooltip.getBoundingClientRect();

			let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
			let top = rect.top - tooltipRect.height - 8;

			if (position === 'bottom') {
				top = rect.bottom + 8;
			} else if (position === 'left') {
				left = rect.left - tooltipRect.width - 8;
				top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
			} else if (position === 'right') {
				left = rect.right + 8;
				top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
			}

			tooltip.style.left = `${left}px`;
			tooltip.style.top = `${top}px`;
			tooltip.style.opacity = '1';
		});

		element.addEventListener('mouseleave', () => {
			if (tooltip) {
				tooltip.remove();
				tooltip = null;
			}
		});
	}

	// Notification System
	setupNotifications() {
		this.createNotificationContainer();
	}

	createNotificationContainer() {
		if (!document.querySelector('.notification-container')) {
			const container = document.createElement('div');
			container.className = 'notification-container';
			document.body.appendChild(container);
		}
	}

	showNotification(message, type = 'info', duration = 5000) {
		const container = document.querySelector('.notification-container');
		if (!container) return;

		const notification = document.createElement('div');
		notification.className = `notification notification-${type}`;
		notification.innerHTML = `
			<div class="notification-content">
				<span class="notification-message">${message}</span>
				<button class="notification-close" aria-label="Close">&times;</button>
			</div>
		`;

		container.appendChild(notification);

		// Show notification
		setTimeout(() => notification.classList.add('show'), 10);

		// Auto remove
		const autoRemove = setTimeout(() => this.removeNotification(notification), duration);

		// Manual close
		const closeBtn = notification.querySelector('.notification-close');
		closeBtn.addEventListener('click', () => {
			clearTimeout(autoRemove);
			this.removeNotification(notification);
		});
	}

	removeNotification(notification) {
		notification.classList.remove('show');
		setTimeout(() => notification.remove(), 300);
	}

	// WebSocket Management
	createWebSocket(url, options = {}) {
		const ws = new WebSocket(url);
		const wsId = options.id || url;

		ws.onopen = () => {
			console.log(`WebSocket connected: ${wsId}`);
			this.updateConnectionStatus(wsId, 'connected');
			if (options.onOpen) options.onOpen();
		};

		ws.onmessage = (event) => {
			if (options.onMessage) {
				try {
					const data = JSON.parse(event.data);
					options.onMessage(data);
				} catch (e) {
					options.onMessage(event.data);
				}
			}
		};

		ws.onclose = () => {
			console.log(`WebSocket disconnected: ${wsId}`);
			this.updateConnectionStatus(wsId, 'disconnected');
			if (options.onClose) options.onClose();
			
			// Auto-reconnect after 3 seconds
			if (options.autoReconnect !== false) {
				setTimeout(() => this.createWebSocket(url, options), 3000);
			}
		};

		ws.onerror = (error) => {
			console.error(`WebSocket error: ${wsId}`, error);
			this.updateConnectionStatus(wsId, 'error');
			if (options.onError) options.onError(error);
		};

		this.websockets.set(wsId, ws);
		return ws;
	}

	updateConnectionStatus(wsId, status) {
		const statusElements = document.querySelectorAll(`[data-connection-status="${wsId}"]`);
		statusElements.forEach(element => {
			element.className = `status status-${status}`;
			element.innerHTML = `
				<span class="status-dot"></span>
				<span class="status-text">${status}</span>
			`;
		});
	}

	// System Monitoring
	startSystemMonitoring() {
		this.updateSystemStats();
		setInterval(() => this.updateSystemStats(), 10000); // Update every 10 seconds
	}

	async updateSystemStats() {
		try {
			const response = await fetch('/api/system/health');
			if (response.ok) {
				const data = await response.json();
				this.updateSystemMetrics(data);
			}
		} catch (error) {
			console.error('Failed to fetch system stats:', error);
		}
	}

	updateSystemMetrics(data) {
		// Update CPU usage
		const cpuElement = document.querySelector('[data-metric="cpu"]');
		if (cpuElement && data.cpu) {
			cpuElement.textContent = `${data.cpu}%`;
			const progressBar = cpuElement.closest('.metric-card')?.querySelector('.progress-bar');
			if (progressBar) {
				progressBar.style.width = `${data.cpu}%`;
			}
		}

		// Update Memory usage
		const memoryElement = document.querySelector('[data-metric="memory"]');
		if (memoryElement && data.memory) {
			memoryElement.textContent = `${data.memory}%`;
			const progressBar = memoryElement.closest('.metric-card')?.querySelector('.progress-bar');
			if (progressBar) {
				progressBar.style.width = `${data.memory}%`;
			}
		}

		// Update GPU usage (if available)
		const gpuElement = document.querySelector('[data-metric="gpu"]');
		if (gpuElement && data.gpu) {
			gpuElement.textContent = `${data.gpu}%`;
			const progressBar = gpuElement.closest('.metric-card')?.querySelector('.progress-bar');
			if (progressBar) {
				progressBar.style.width = `${data.gpu}%`;
			}
		}

		// Update detection stats
		if (data.detections) {
			const totalElement = document.querySelector('[data-metric="total-detections"]');
			if (totalElement) {
				totalElement.textContent = data.detections.total || 0;
			}

			const todayElement = document.querySelector('[data-metric="today-detections"]');
			if (todayElement) {
				todayElement.textContent = data.detections.today || 0;
			}

			const accuracyElement = document.querySelector('[data-metric="accuracy"]');
			if (accuracyElement) {
				accuracyElement.textContent = `${data.detections.accuracy || 0}%`;
			}
		}
	}

	// Utility Methods
	formatDate(date) {
		return new Intl.DateTimeFormat('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		}).format(new Date(date));
	}

	formatFileSize(bytes) {
		const sizes = ['B', 'KB', 'MB', 'GB'];
		if (bytes === 0) return '0 B';
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
	}

	debounce(func, delay) {
		let timeoutId;
		return (...args) => {
			clearTimeout(timeoutId);
			timeoutId = setTimeout(() => func.apply(this, args), delay);
		};
	}
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
	window.lprApp = new LPRApp();
});

// Global utility functions
window.LPRUtils = {
	showNotification: (message, type, duration) => {
		if (window.lprApp) {
			window.lprApp.showNotification(message, type, duration);
		}
	},
	
	openModal: (modalId) => {
		const modal = document.getElementById(modalId);
		if (modal && window.lprApp) {
			window.lprApp.openModal(modal);
		}
	},
	
	closeModal: (modalId) => {
		const modal = document.getElementById(modalId);
		if (modal && window.lprApp) {
			window.lprApp.closeModal(modal);
		}
	}
};