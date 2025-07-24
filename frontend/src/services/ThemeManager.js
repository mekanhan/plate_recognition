/**
 * Theme Management Service
 * Handles theme switching, persistence, and system preference detection
 */
class ThemeManager {
    constructor() {
        // Prevent multiple instances
        if (ThemeManager.instance) {
            return ThemeManager.instance;
        }
        
        this.themes = ['light', 'dark', 'auto'];
        this.currentTheme = this.getInitialTheme();
        this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        ThemeManager.instance = this;
        this.init();
    }

    init() {
        this.applyTheme();
        this.listenForSystemChanges();
        
        // Make available globally for debugging and component access
        window.themeManager = this;
        
        // Update button when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.updateToggleButton());
        } else {
            this.updateToggleButton();
        }
    }

    /**
     * Determine initial theme from localStorage or default to auto
     */
    getInitialTheme() {
        try {
            const saved = localStorage.getItem('theme');
            return this.themes.includes(saved) ? saved : 'auto';
        } catch (error) {
            console.warn('localStorage not available, using auto theme:', error);
            return 'auto';
        }
    }

    /**
     * Apply the current theme to the document
     */
    applyTheme() {
        const resolvedTheme = this.resolveTheme();
        
        if (resolvedTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        
        // Update button with a small delay to ensure DOM is ready
        setTimeout(() => this.updateToggleButton(), 10);
        this.dispatchThemeChangeEvent();
    }

    /**
     * Resolve the actual theme (light/dark) from current setting
     */
    resolveTheme() {
        if (this.currentTheme === 'auto') {
            return this.mediaQuery.matches ? 'dark' : 'light';
        }
        return this.currentTheme;
    }

    /**
     * Set a new theme and persist it
     */
    setTheme(theme) {
        if (!this.themes.includes(theme)) {
            console.warn(`Invalid theme: ${theme}. Valid themes:`, this.themes);
            return;
        }
        
        this.currentTheme = theme;
        
        try {
            localStorage.setItem('theme', theme);
        } catch (error) {
            console.warn('Failed to persist theme preference:', error);
        }
        
        this.applyTheme();
    }

    /**
     * Toggle between light and dark themes (skips auto for manual toggle)
     */
    toggleTheme() {
        const resolved = this.resolveTheme();
        const newTheme = resolved === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    /**
     * Get current theme info
     */
    getThemeInfo() {
        return {
            current: this.currentTheme,
            resolved: this.resolveTheme(),
            isAuto: this.currentTheme === 'auto',
            systemPrefersDark: this.mediaQuery.matches
        };
    }

    /**
     * Listen for system theme preference changes
     */
    listenForSystemChanges() {
        this.mediaQuery.addEventListener('change', (e) => {
            console.log('System theme preference changed to:', e.matches ? 'dark' : 'light');
            
            if (this.currentTheme === 'auto') {
                this.applyTheme();
            }
        });
    }

    /**
     * Update theme toggle button appearance and accessibility
     */
    updateToggleButton() {
        const button = document.getElementById('dark-mode-toggle');
        if (!button) return;

        const icon = button.querySelector('i');
        if (!icon) return;

        const resolved = this.resolveTheme();
        const isAuto = this.currentTheme === 'auto';
        
        // Update icon
        if (isAuto) {
            icon.className = `fas fa-adjust`; // Auto icon
        } else {
            icon.className = `fas ${resolved === 'dark' ? 'fa-sun' : 'fa-moon'}`;
        }
        
        // Update accessibility attributes
        const modeText = isAuto ? 'auto' : resolved;
        const nextMode = resolved === 'dark' ? 'light' : 'dark';
        
        button.setAttribute('aria-label', 
            `Current theme: ${modeText}. Click to switch to ${nextMode} mode`
        );
        button.setAttribute('aria-pressed', resolved === 'dark');
        button.setAttribute('title', 
            isAuto ? `Auto theme (currently ${resolved})` : `${resolved} theme`
        );
    }

    /**
     * Dispatch theme change event for components to listen to
     */
    dispatchThemeChangeEvent() {
        const event = new CustomEvent('themeChanged', {
            detail: {
                theme: this.currentTheme,
                resolved: this.resolveTheme(),
                isAuto: this.currentTheme === 'auto',
                timestamp: Date.now()
            }
        });
        
        window.dispatchEvent(event);
    }

    /**
     * Add CSS transitions for smooth theme switching
     */
    enableTransitions() {
        const style = document.createElement('style');
        style.id = 'theme-transitions';
        style.textContent = `
            * {
                transition: 
                    background-color 0.3s ease,
                    border-color 0.3s ease,
                    color 0.3s ease,
                    box-shadow 0.3s ease !important;
            }
            
            @media (prefers-reduced-motion: reduce) {
                * {
                    transition-duration: 0.01ms !important;
                }
            }
        `;
        
        document.head.appendChild(style);
        
        // Remove transitions after animation completes to avoid performance impact
        setTimeout(() => {
            const transitionStyle = document.getElementById('theme-transitions');
            if (transitionStyle) {
                transitionStyle.remove();
            }
        }, 300);
    }

    /**
     * Destroy theme manager and clean up event listeners
     */
    destroy() {
        this.mediaQuery.removeEventListener('change', this.listenForSystemChanges);
        delete window.themeManager;
    }

    /**
     * Debug method to get all theme information
     */
    debug() {
        return {
            themes: this.themes,
            current: this.currentTheme,
            resolved: this.resolveTheme(),
            systemPrefersDark: this.mediaQuery.matches,
            localStorage: this.getStoredTheme(),
            documentTheme: document.documentElement.getAttribute('data-theme')
        };
    }

    /**
     * Get theme from localStorage (helper for debugging)
     */
    getStoredTheme() {
        try {
            return localStorage.getItem('theme');
        } catch {
            return null;
        }
    }
}

export default ThemeManager;