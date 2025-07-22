# Frontend Architecture & Component Organization Guide

**Version:** 1.0  
**Date:** 2025-01-09  
**Authors:** Frontend Architecture Team  
**Status:** Active Development  

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Industry Best Practices](#industry-best-practices)
4. [Recommended File Structure](#recommended-file-structure)
5. [Component Architecture](#component-architecture)
6. [Development Guidelines](#development-guidelines)
7. [Build System & Tools](#build-system--tools)
8. [Testing Strategy](#testing-strategy)
9. [Migration Plan](#migration-plan)

## Executive Summary

This document outlines the transformation of the current monolithic frontend (prototype6.html) into a modern, maintainable, and scalable component-based architecture following industry best practices for enterprise web applications.

### Key Objectives

- **Modularity**: Break down monolithic structure into reusable components
- **Maintainability**: Improve code organization and readability
- **Scalability**: Enable easy addition of new features and components
- **Performance**: Optimize loading times and resource usage
- **Developer Experience**: Enhance development workflow and debugging capabilities

## Current State Analysis

### Current Issues with Monolithic Structure

#### Single File Problems
```html
<!-- Current structure - prototype6.html (2000+ lines) -->
<!DOCTYPE html>
<html>
<head>
    <!-- All CSS imports in one place -->
    <link rel="stylesheet" href="/static/css/styles.css">
    <link rel="stylesheet" href="/static/css/ip_camera_modal.css">
    <link rel="stylesheet" href="/static/css/dark_theme.css">
</head>
<body>
    <!-- All HTML structure in one file -->
    <nav class="sidebar">...</nav>
    <main class="main-content">
        <section id="dashboard">...</section>
        <section id="cameras">...</section>
        <section id="detections">...</section>
        <!-- ... more sections -->
    </main>
    <!-- All JavaScript in separate files but monolithic structure -->
    <script src="/static/js/script.js"></script>
    <script src="/static/js/camera_modal.js"></script>
</body>
</html>
```

#### Problems Identified
- **Long Files**: Single HTML file with 2000+ lines
- **Mixed Concerns**: HTML, CSS, and JS logic scattered
- **Poor Reusability**: Components cannot be reused easily
- **Difficult Debugging**: Hard to locate specific component issues
- **Merge Conflicts**: Multiple developers working on same file
- **Performance**: Loading entire UI even when only parts are needed

## Industry Best Practices

### Modern Frontend Architecture Principles

#### 1. Component-Based Architecture
```
Components should be:
✅ Single Responsibility - One purpose per component
✅ Reusable - Can be used in multiple contexts
✅ Composable - Can be combined to create complex UIs
✅ Self-contained - Include their own styles and logic
✅ Testable - Easy to unit test in isolation
```

#### 2. Separation of Concerns
```
Structure:
├── HTML Templates (Structure)
├── CSS Modules (Styling)
├── JavaScript Modules (Behavior)
└── Assets (Images, Icons, Fonts)
```

#### 3. File Naming Conventions
```
kebab-case for files: dashboard-metrics.component.js
PascalCase for classes: DashboardMetrics
camelCase for variables: dashboardController
UPPER_CASE for constants: API_ENDPOINTS
```

#### 4. Module System
```javascript
// ES6 Modules
import { DashboardController } from './controllers/dashboard.controller.js';
import { CameraService } from './services/camera.service.js';
import './components/camera-grid/camera-grid.component.js';
```

## Recommended File Structure

### Project Organization
```
lpr-frontend/
├── public/                           # Static public files
│   ├── index.html                   # Main entry point
│   ├── favicon.ico
│   └── manifest.json
├── src/                             # Source code
│   ├── components/                  # Reusable UI components
│   │   ├── common/                  # Shared components
│   │   │   ├── sidebar/
│   │   │   │   ├── sidebar.component.js
│   │   │   │   ├── sidebar.component.css
│   │   │   │   └── sidebar.component.html
│   │   │   ├── header/
│   │   │   │   ├── header.component.js
│   │   │   │   ├── header.component.css
│   │   │   │   └── header.component.html
│   │   │   ├── modal/
│   │   │   │   ├── modal.component.js
│   │   │   │   ├── modal.component.css
│   │   │   │   └── modal.component.html
│   │   │   └── notification/
│   │   │       ├── notification.component.js
│   │   │       ├── notification.component.css
│   │   │       └── notification.component.html
│   │   ├── dashboard/               # Dashboard specific components
│   │   │   ├── metrics-card/
│   │   │   │   ├── metrics-card.component.js
│   │   │   │   ├── metrics-card.component.css
│   │   │   │   └── metrics-card.component.html
│   │   │   ├── camera-grid/
│   │   │   │   ├── camera-grid.component.js
│   │   │   │   ├── camera-grid.component.css
│   │   │   │   └── camera-grid.component.html
│   │   │   ├── recent-detections/
│   │   │   │   ├── recent-detections.component.js
│   │   │   │   ├── recent-detections.component.css
│   │   │   │   └── recent-detections.component.html
│   │   │   └── system-health/
│   │   │       ├── system-health.component.js
│   │   │       ├── system-health.component.css
│   │   │       └── system-health.component.html
│   │   ├── cameras/                 # Camera management components
│   │   │   ├── camera-card/
│   │   │   │   ├── camera-card.component.js
│   │   │   │   ├── camera-card.component.css
│   │   │   │   └── camera-card.component.html
│   │   │   ├── camera-modal/
│   │   │   │   ├── camera-modal.component.js
│   │   │   │   ├── camera-modal.component.css
│   │   │   │   └── camera-modal.component.html
│   │   │   └── camera-filters/
│   │   │       ├── camera-filters.component.js
│   │   │       ├── camera-filters.component.css
│   │   │       └── camera-filters.component.html
│   │   ├── detections/              # Detection management components
│   │   │   ├── detection-table/
│   │   │   │   ├── detection-table.component.js
│   │   │   │   ├── detection-table.component.css
│   │   │   │   └── detection-table.component.html
│   │   │   ├── detection-filters/
│   │   │   │   ├── detection-filters.component.js
│   │   │   │   ├── detection-filters.component.css
│   │   │   │   └── detection-filters.component.html
│   │   │   └── detection-modal/
│   │   │       ├── detection-modal.component.js
│   │   │       ├── detection-modal.component.css
│   │   │       └── detection-modal.component.html
│   │   └── analytics/               # Analytics components
│   │       ├── charts/
│   │       │   ├── line-chart/
│   │       │   ├── bar-chart/
│   │       │   └── pie-chart/
│   │       └── reports/
│   ├── pages/                       # Page-level components
│   │   ├── dashboard/
│   │   │   ├── dashboard.page.js
│   │   │   ├── dashboard.page.css
│   │   │   └── dashboard.page.html
│   │   ├── cameras/
│   │   │   ├── cameras.page.js
│   │   │   ├── cameras.page.css
│   │   │   └── cameras.page.html
│   │   ├── detections/
│   │   │   ├── detections.page.js
│   │   │   ├── detections.page.css
│   │   │   └── detections.page.html
│   │   └── analytics/
│   │       ├── analytics.page.js
│   │       ├── analytics.page.css
│   │       └── analytics.page.html
│   ├── services/                    # Business logic services
│   │   ├── api/
│   │   │   ├── api.service.js
│   │   │   ├── camera.api.js
│   │   │   ├── detection.api.js
│   │   │   └── analytics.api.js
│   │   ├── camera.service.js
│   │   ├── detection.service.js
│   │   ├── notification.service.js
│   │   └── websocket.service.js
│   ├── utils/                       # Utility functions
│   │   ├── date.utils.js
│   │   ├── validation.utils.js
│   │   ├── export.utils.js
│   │   └── theme.utils.js
│   ├── store/                       # State management
│   │   ├── app.store.js
│   │   ├── camera.store.js
│   │   ├── detection.store.js
│   │   └── user.store.js
│   ├── styles/                      # Global styles
│   │   ├── globals.css
│   │   ├── variables.css
│   │   ├── themes.css
│   │   └── responsive.css
│   ├── assets/                      # Static assets
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   ├── config/                      # Configuration files
│   │   ├── app.config.js
│   │   └── api.config.js
│   └── main.js                      # Application entry point
├── tests/                           # Test files
│   ├── components/
│   ├── services/
│   ├── utils/
│   └── e2e/
├── docs/                           # Documentation
├── build/                          # Build configuration
│   ├── webpack.config.js
│   ├── vite.config.js
│   └── rollup.config.js
├── package.json
├── package-lock.json
└── README.md
```

## Component Architecture

### Base Component Class
```javascript
// src/components/base/base.component.js
export class BaseComponent {
    constructor(selector, props = {}) {
        this.selector = selector;
        this.props = props;
        this.element = null;
        this.state = {};
        this.eventListeners = [];
    }

    async init() {
        await this.loadTemplate();
        await this.loadStyles();
        this.render();
        this.bindEvents();
    }

    async loadTemplate() {
        const templatePath = this.getTemplatePath();
        const response = await fetch(templatePath);
        this.template = await response.text();
    }

    async loadStyles() {
        const stylePath = this.getStylePath();
        if (!document.querySelector(`link[href="${stylePath}"]`)) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = stylePath;
            document.head.appendChild(link);
        }
    }

    render() {
        const container = document.querySelector(this.selector);
        if (container) {
            container.innerHTML = this.processTemplate(this.template);
            this.element = container;
            this.afterRender();
        }
    }

    processTemplate(template) {
        // Simple template processing
        return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return this.props[key] || this.state[key] || '';
        });
    }

    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.render();
    }

    bindEvents() {
        // Override in child components
    }

    afterRender() {
        // Override in child components
    }

    destroy() {
        this.eventListeners.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this.eventListeners = [];
    }

    addEventListener(element, event, handler) {
        element.addEventListener(event, handler);
        this.eventListeners.push({ element, event, handler });
    }

    getTemplatePath() {
        const className = this.constructor.name.toLowerCase();
        return `/src/components/${className}/${className}.component.html`;
    }

    getStylePath() {
        const className = this.constructor.name.toLowerCase();
        return `/src/components/${className}/${className}.component.css`;
    }
}
```

### Sample Component Implementation
```javascript
// src/components/dashboard/metrics-card/metrics-card.component.js
import { BaseComponent } from '../../base/base.component.js';

export class MetricsCard extends BaseComponent {
    constructor(selector, props) {
        super(selector, props);
        this.state = {
            value: props.value || 0,
            label: props.label || '',
            trend: props.trend || 'neutral',
            icon: props.icon || 'fas fa-chart-line'
        };
    }

    bindEvents() {
        if (this.props.clickable) {
            this.addEventListener(this.element, 'click', () => {
                this.props.onClick && this.props.onClick(this.props);
            });
        }
    }

    updateValue(newValue, trend = 'neutral') {
        this.setState({
            value: newValue,
            trend: trend
        });
    }

    afterRender() {
        // Add animation classes
        this.element.classList.add('metric-card-animated');
    }
}
```

### Component Template
```html
<!-- src/components/dashboard/metrics-card/metrics-card.component.html -->
<div class="metric-card {{trend}}" data-testid="metrics-card">
    <div class="metric-icon">
        <i class="{{icon}}"></i>
    </div>
    <div class="metric-content">
        <h3 class="metric-value">{{value}}</h3>
        <p class="metric-label">{{label}}</p>
        <span class="metric-trend">{{trendText}}</span>
    </div>
</div>
```

### Component Styles
```css
/* src/components/dashboard/metrics-card/metrics-card.component.css */
.metric-card {
    background: var(--card-background);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.5rem;
    transition: all 0.3s ease;
    cursor: pointer;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-card-animated {
    animation: slideInUp 0.5s ease-out;
}

@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.metric-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1rem;
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
    color: var(--primary-text);
}

.metric-label {
    color: var(--secondary-text);
    margin: 0.5rem 0;
    font-size: 0.9rem;
}

.metric-trend {
    font-size: 0.8rem;
    font-weight: 600;
}

.metric-card.positive .metric-trend {
    color: var(--success-color);
}

.metric-card.negative .metric-trend {
    color: var(--danger-color);
}

.metric-card.neutral .metric-trend {
    color: var(--warning-color);
}
```

## Development Guidelines

### Coding Standards

#### 1. JavaScript Standards
```javascript
// Use ES6+ features
const apiService = new ApiService();

// Destructuring
const { cameras, detections } = state;

// Arrow functions for short operations
const filterCameras = (cameras) => cameras.filter(c => c.status === 'online');

// Async/await for promises
async function fetchDetections() {
    try {
        const response = await apiService.getDetections();
        return response.data;
    } catch (error) {
        console.error('Failed to fetch detections:', error);
        throw error;
    }
}

// Use meaningful variable names
const activeCameraCount = cameras.filter(camera => camera.status === 'active').length;

// Constants in UPPER_CASE
const API_ENDPOINTS = {
    CAMERAS: '/api/cameras',
    DETECTIONS: '/api/detections'
};
```

#### 2. CSS Standards
```css
/* Use CSS custom properties for theming */
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --success-color: #10b981;
    --danger-color: #ef4444;
    --warning-color: #f59e0b;
}

/* BEM methodology for class naming */
.camera-card { /* Block */
    display: flex;
    flex-direction: column;
}

.camera-card__header { /* Element */
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
}

.camera-card--offline { /* Modifier */
    opacity: 0.6;
    border-color: var(--danger-color);
}

/* Mobile-first responsive design */
.detection-table {
    width: 100%;
    overflow-x: auto;
}

@media (min-width: 768px) {
    .detection-table {
        overflow-x: visible;
    }
}
```

#### 3. HTML Standards
```html
<!-- Semantic HTML5 elements -->
<main class="main-content">
    <section class="dashboard-section">
        <header class="section-header">
            <h1 class="section-title">Dashboard</h1>
        </header>
        <article class="metrics-container">
            <!-- Content -->
        </article>
    </section>
</main>

<!-- Accessibility attributes -->
<button 
    class="camera-action-btn" 
    aria-label="View camera details"
    data-testid="camera-view-btn"
    role="button"
    tabindex="0">
    <i class="fas fa-eye" aria-hidden="true"></i>
    View Details
</button>

<!-- Progressive enhancement -->
<form class="camera-form" novalidate>
    <input 
        type="text" 
        name="cameraName" 
        required 
        aria-describedby="camera-name-help">
    <div id="camera-name-help" class="form-help">
        Enter a descriptive name for the camera
    </div>
</form>
```

### State Management

#### Simple Store Pattern
```javascript
// src/store/app.store.js
class AppStore {
    constructor() {
        this.state = {
            cameras: [],
            detections: [],
            currentPage: 'dashboard',
            user: null,
            loading: false,
            notifications: []
        };
        this.subscribers = [];
    }

    getState() {
        return { ...this.state };
    }

    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.notifySubscribers();
    }

    subscribe(callback) {
        this.subscribers.push(callback);
        return () => {
            this.subscribers = this.subscribers.filter(sub => sub !== callback);
        };
    }

    notifySubscribers() {
        this.subscribers.forEach(callback => callback(this.state));
    }

    // Action methods
    async loadCameras() {
        this.setState({ loading: true });
        try {
            const cameras = await cameraService.getCameras();
            this.setState({ cameras, loading: false });
        } catch (error) {
            this.setState({ loading: false });
            throw error;
        }
    }

    addNotification(notification) {
        const notifications = [...this.state.notifications, {
            id: Date.now(),
            timestamp: new Date(),
            ...notification
        }];
        this.setState({ notifications });
    }
}

export const appStore = new AppStore();
```

### Error Handling

#### Global Error Handler
```javascript
// src/utils/error-handler.js
class ErrorHandler {
    constructor() {
        this.setupGlobalHandlers();
    }

    setupGlobalHandlers() {
        window.addEventListener('error', (event) => {
            this.handleError({
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                stack: event.error?.stack
            });
        });

        window.addEventListener('unhandledrejection', (event) => {
            this.handleError({
                message: 'Unhandled Promise Rejection',
                promise: event.promise,
                reason: event.reason
            });
        });
    }

    handleError(error) {
        console.error('Application Error:', error);
        
        // Log to external service in production
        if (process.env.NODE_ENV === 'production') {
            this.logToService(error);
        }

        // Show user-friendly notification
        this.showUserNotification(error);
    }

    logToService(error) {
        // Send to logging service
        fetch('/api/logs/error', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(error)
        }).catch(console.error);
    }

    showUserNotification(error) {
        const notification = {
            type: 'error',
            title: 'Something went wrong',
            message: 'Please try again or contact support if the problem persists.',
            duration: 5000
        };
        
        // Use notification service
        notificationService.show(notification);
    }
}

export const errorHandler = new ErrorHandler();
```

## Build System & Tools

### Modern Build Setup with Vite

#### Package.json
```json
{
    "name": "lpr-frontend",
    "version": "1.0.0",
    "type": "module",
    "scripts": {
        "dev": "vite",
        "build": "vite build",
        "preview": "vite preview",
        "test": "vitest",
        "test:ui": "vitest --ui",
        "lint": "eslint src --ext .js",
        "lint:fix": "eslint src --ext .js --fix",
        "format": "prettier --write src/**/*.{js,css,html}"
    },
    "devDependencies": {
        "vite": "^5.0.0",
        "eslint": "^8.0.0",
        "prettier": "^3.0.0",
        "vitest": "^1.0.0",
        "@vitest/ui": "^1.0.0",
        "jsdom": "^23.0.0"
    },
    "dependencies": {
        "chart.js": "^4.0.0",
        "date-fns": "^3.0.0"
    }
}
```

#### Vite Configuration
```javascript
// vite.config.js
import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
    root: 'src',
    publicDir: '../public',
    build: {
        outDir: '../dist',
        rollupOptions: {
            input: {
                main: resolve(__dirname, 'src/index.html')
            }
        }
    },
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true
            },
            '/ws': {
                target: 'ws://localhost:8000',
                ws: true
            }
        }
    },
    css: {
        modules: {
            localsConvention: 'camelCaseOnly'
        }
    }
});
```

## Testing Strategy

### Unit Testing with Vitest

#### Component Testing
```javascript
// tests/components/metrics-card/metrics-card.test.js
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MetricsCard } from '../../../src/components/dashboard/metrics-card/metrics-card.component.js';

describe('MetricsCard Component', () => {
    let container;
    let component;

    beforeEach(() => {
        container = document.createElement('div');
        container.innerHTML = '<div id="test-container"></div>';
        document.body.appendChild(container);
    });

    it('should render with correct props', async () => {
        const props = {
            value: 1247,
            label: 'Active Cameras',
            trend: 'positive',
            icon: 'fas fa-video'
        };

        component = new MetricsCard('#test-container', props);
        await component.init();

        const element = container.querySelector('.metric-card');
        expect(element).toBeTruthy();
        expect(element.textContent).toContain('1247');
        expect(element.textContent).toContain('Active Cameras');
        expect(element.classList.contains('positive')).toBe(true);
    });

    it('should handle click events when clickable', async () => {
        const onClick = vi.fn();
        const props = {
            value: 100,
            label: 'Test',
            clickable: true,
            onClick
        };

        component = new MetricsCard('#test-container', props);
        await component.init();

        const element = container.querySelector('.metric-card');
        element.click();

        expect(onClick).toHaveBeenCalledWith(props);
    });

    it('should update value and trend', async () => {
        component = new MetricsCard('#test-container', {
            value: 100,
            label: 'Test'
        });
        await component.init();

        component.updateValue(200, 'positive');

        const valueElement = container.querySelector('.metric-value');
        expect(valueElement.textContent).toBe('200');
        expect(container.querySelector('.metric-card').classList.contains('positive')).toBe(true);
    });
});
```

#### Service Testing
```javascript
// tests/services/camera.service.test.js
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { CameraService } from '../../src/services/camera.service.js';

// Mock the API service
vi.mock('../../src/services/api/camera.api.js', () => ({
    CameraApi: {
        getCameras: vi.fn(),
        createCamera: vi.fn(),
        updateCamera: vi.fn(),
        deleteCamera: vi.fn()
    }
}));

describe('CameraService', () => {
    let cameraService;

    beforeEach(() => {
        cameraService = new CameraService();
        vi.clearAllMocks();
    });

    it('should get cameras with proper transformation', async () => {
        const mockApiResponse = {
            data: [
                { id: '1', name: 'Camera 1', status: 'online' },
                { id: '2', name: 'Camera 2', status: 'offline' }
            ]
        };

        CameraApi.getCameras.mockResolvedValue(mockApiResponse);

        const cameras = await cameraService.getCameras();

        expect(cameras).toHaveLength(2);
        expect(cameras[0]).toMatchObject({
            id: '1',
            name: 'Camera 1',
            status: 'online'
        });
    });

    it('should handle camera creation with validation', async () => {
        const newCamera = {
            name: 'New Camera',
            ipAddress: '192.168.1.100',
            location: 'Entrance'
        };

        CameraApi.createCamera.mockResolvedValue({
            data: { id: '3', ...newCamera }
        });

        const result = await cameraService.createCamera(newCamera);

        expect(CameraApi.createCamera).toHaveBeenCalledWith(newCamera);
        expect(result.id).toBe('3');
    });
});
```

### E2E Testing with Playwright

#### E2E Test Example
```javascript
// tests/e2e/dashboard.spec.js
import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should display dashboard metrics', async ({ page }) => {
        await expect(page.locator('.metrics-grid')).toBeVisible();
        await expect(page.locator('.metric-card')).toHaveCount(4);
        
        const firstMetric = page.locator('.metric-card').first();
        await expect(firstMetric.locator('.metric-value')).toContainText(/\d+/);
    });

    test('should navigate to cameras page', async ({ page }) => {
        await page.click('[data-page="cameras"]');
        await expect(page.locator('#cameras')).toBeVisible();
        await expect(page.locator('.page-title')).toContainText('Cameras');
    });

    test('should open detection modal', async ({ page }) => {
        await page.click('[data-page="detections"]');
        await page.click('.detection-table tbody tr:first-child .view-details-btn');
        
        await expect(page.locator('#detection-details-modal')).toBeVisible();
        await expect(page.locator('.modal-title')).toContainText('Detection Details');
    });

    test('should filter detections', async ({ page }) => {
        await page.click('[data-page="detections"]');
        await page.fill('#smart-search', 'ABC');
        await page.click('#apply-filters-btn');
        
        // Check that filtered results are displayed
        const tableRows = page.locator('.detection-table tbody tr');
        await expect(tableRows).toHaveCountGreaterThan(0);
    });
});
```

## Migration Plan

### Phase 1: Setup and Foundation (Week 1-2)

#### 1.1 Project Structure Setup
```bash
# Create new project structure
mkdir lpr-frontend
cd lpr-frontend

# Initialize package.json
npm init -y

# Install development dependencies
npm install -D vite eslint prettier vitest @vitest/ui jsdom playwright

# Install runtime dependencies
npm install chart.js date-fns

# Create directory structure
mkdir -p src/{components,pages,services,utils,store,styles,assets,config}
mkdir -p src/components/{common,dashboard,cameras,detections,analytics}
mkdir -p public docs tests build
```

#### 1.2 Development Environment
```javascript
// .eslintrc.js
module.exports = {
    env: {
        browser: true,
        es2021: true,
    },
    extends: ['eslint:recommended'],
    parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
    },
    rules: {
        'no-unused-vars': 'warn',
        'no-console': 'warn',
        'prefer-const': 'error',
        'no-var': 'error',
    },
};

// .prettierrc
{
    "semi": true,
    "trailingComma": "es5",
    "singleQuote": true,
    "printWidth": 100,
    "tabWidth": 4
}
```

### Phase 2: Component Migration (Week 3-4)

#### 2.1 Extract Core Components
Priority order for component extraction:

1. **BaseComponent** - Foundation class
2. **Header/Sidebar** - Navigation components
3. **MetricsCard** - Dashboard metrics
4. **CameraGrid** - Camera display
5. **DetectionTable** - Detection results

#### 2.2 Migration Script
```javascript
// tools/migrate-component.js
import fs from 'fs/promises';
import path from 'path';

class ComponentMigrator {
    constructor(componentName, componentType) {
        this.componentName = componentName;
        this.componentType = componentType;
        this.basePath = `src/components/${componentType}/${componentName}`;
    }

    async createComponent() {
        // Create component directory
        await fs.mkdir(this.basePath, { recursive: true });

        // Generate component files
        await this.createJavaScriptFile();
        await this.createHTMLFile();
        await this.createCSSFile();
        await this.createTestFile();

        console.log(`✅ Component ${this.componentName} created successfully`);
    }

    async createJavaScriptFile() {
        const jsContent = this.generateJSTemplate();
        await fs.writeFile(`${this.basePath}/${this.componentName}.component.js`, jsContent);
    }

    async createHTMLFile() {
        const htmlContent = this.generateHTMLTemplate();
        await fs.writeFile(`${this.basePath}/${this.componentName}.component.html`, htmlContent);
    }

    async createCSSFile() {
        const cssContent = this.generateCSSTemplate();
        await fs.writeFile(`${this.basePath}/${this.componentName}.component.css`, cssContent);
    }

    async createTestFile() {
        const testContent = this.generateTestTemplate();
        await fs.writeFile(`tests/components/${this.componentName}.test.js`, testContent);
    }

    generateJSTemplate() {
        return `import { BaseComponent } from '../../base/base.component.js';

export class ${this.pascalCase(this.componentName)} extends BaseComponent {
    constructor(selector, props = {}) {
        super(selector, props);
        this.state = {
            ...this.state,
            // Add component-specific state
        };
    }

    bindEvents() {
        // Add event listeners
    }

    afterRender() {
        // Post-render logic
    }

    // Add component-specific methods
}
`;
    }

    generateHTMLTemplate() {
        return `<div class="${this.kebabCase(this.componentName)}" data-testid="${this.kebabCase(this.componentName)}">
    <!-- Component template -->
    <div class="${this.kebabCase(this.componentName)}__content">
        {{content}}
    </div>
</div>
`;
    }

    generateCSSTemplate() {
        return `.${this.kebabCase(this.componentName)} {
    /* Component styles */
}

.${this.kebabCase(this.componentName)}__content {
    /* Content styles */
}

/* Responsive styles */
@media (max-width: 768px) {
    .${this.kebabCase(this.componentName)} {
        /* Mobile styles */
    }
}
`;
    }

    generateTestTemplate() {
        return `import { describe, it, expect, beforeEach } from 'vitest';
import { ${this.pascalCase(this.componentName)} } from '../src/components/${this.componentType}/${this.componentName}/${this.componentName}.component.js';

describe('${this.pascalCase(this.componentName)} Component', () => {
    let container;
    let component;

    beforeEach(() => {
        container = document.createElement('div');
        container.innerHTML = '<div id="test-container"></div>';
        document.body.appendChild(container);
    });

    it('should render successfully', async () => {
        component = new ${this.pascalCase(this.componentName)}('#test-container');
        await component.init();

        const element = container.querySelector('.${this.kebabCase(this.componentName)}');
        expect(element).toBeTruthy();
    });

    // Add more tests
});
`;
    }

    pascalCase(str) {
        return str.replace(/(^\w|[-_]\w)/g, (match) => match.replace(/[-_]/, '').toUpperCase());
    }

    kebabCase(str) {
        return str.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase();
    }
}

// Usage: node tools/migrate-component.js metrics-card dashboard
const [componentName, componentType] = process.argv.slice(2);
if (componentName && componentType) {
    const migrator = new ComponentMigrator(componentName, componentType);
    migrator.createComponent();
} else {
    console.log('Usage: node migrate-component.js <component-name> <component-type>');
}
```

### Phase 3: Service Layer (Week 5-6)

#### 3.1 API Service Architecture
```javascript
// src/services/api/api.service.js
class ApiService {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options,
        };

        // Add authentication token if available
        const token = this.getAuthToken();
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new ApiError(
                    `HTTP ${response.status}: ${response.statusText}`,
                    response.status,
                    await response.json()
                );
            }

            const contentType = response.headers.get('Content-Type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new ApiError('Network error', 0, { originalError: error.message });
        }
    }

    get(endpoint, params = {}) {
        const url = new URL(endpoint, this.baseURL);
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== null) {
                url.searchParams.append(key, params[key]);
            }
        });
        
        return this.request(url.pathname + url.search, { method: 'GET' });
    }

    post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    getAuthToken() {
        return localStorage.getItem('authToken');
    }
}

class ApiError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
    }
}

export const apiService = new ApiService();
```

#### 3.2 Domain-Specific Services
```javascript
// src/services/camera.service.js
import { apiService } from './api/api.service.js';
import { appStore } from '../store/app.store.js';

export class CameraService {
    constructor() {
        this.apiEndpoint = '/cameras';
    }

    async getCameras(filters = {}) {
        try {
            const response = await apiService.get(this.apiEndpoint, filters);
            const cameras = this.transformCameraData(response.data || response);
            
            // Update global state
            appStore.setState({ cameras });
            
            return cameras;
        } catch (error) {
            console.error('Failed to fetch cameras:', error);
            throw new Error('Unable to load cameras. Please try again.');
        }
    }

    async createCamera(cameraData) {
        try {
            // Validate camera data
            this.validateCameraData(cameraData);
            
            const response = await apiService.post(this.apiEndpoint, cameraData);
            const newCamera = this.transformCameraData([response.data || response])[0];
            
            // Update global state
            const currentCameras = appStore.getState().cameras;
            appStore.setState({ 
                cameras: [...currentCameras, newCamera] 
            });
            
            return newCamera;
        } catch (error) {
            console.error('Failed to create camera:', error);
            throw new Error('Unable to create camera. Please check your input and try again.');
        }
    }

    async updateCamera(cameraId, updates) {
        try {
            const response = await apiService.put(`${this.apiEndpoint}/${cameraId}`, updates);
            const updatedCamera = this.transformCameraData([response.data || response])[0];
            
            // Update global state
            const currentCameras = appStore.getState().cameras;
            const updatedCameras = currentCameras.map(camera => 
                camera.id === cameraId ? updatedCamera : camera
            );
            appStore.setState({ cameras: updatedCameras });
            
            return updatedCamera;
        } catch (error) {
            console.error('Failed to update camera:', error);
            throw new Error('Unable to update camera. Please try again.');
        }
    }

    async deleteCamera(cameraId) {
        try {
            await apiService.delete(`${this.apiEndpoint}/${cameraId}`);
            
            // Update global state
            const currentCameras = appStore.getState().cameras;
            const filteredCameras = currentCameras.filter(camera => camera.id !== cameraId);
            appStore.setState({ cameras: filteredCameras });
            
            return true;
        } catch (error) {
            console.error('Failed to delete camera:', error);
            throw new Error('Unable to delete camera. Please try again.');
        }
    }

    async testCameraConnection(connectionData) {
        try {
            const response = await apiService.post(`${this.apiEndpoint}/test-connection`, connectionData);
            return response.data || response;
        } catch (error) {
            console.error('Camera connection test failed:', error);
            throw new Error('Camera connection test failed. Please check your settings.');
        }
    }

    transformCameraData(cameras) {
        if (!Array.isArray(cameras)) return [];
        
        return cameras.map(camera => ({
            id: camera.id,
            name: camera.name || '',
            ipAddress: camera.ip_address || camera.ipAddress || '',
            location: camera.location || '',
            status: camera.status || 'unknown',
            configuration: camera.configuration || {},
            healthMetrics: camera.health_metrics || camera.healthMetrics || {},
            createdAt: camera.created_at || camera.createdAt || new Date(),
            updatedAt: camera.updated_at || camera.updatedAt || new Date(),
        }));
    }

    validateCameraData(cameraData) {
        if (!cameraData.name || cameraData.name.trim().length === 0) {
            throw new Error('Camera name is required');
        }
        
        if (!cameraData.ipAddress || !this.isValidIpAddress(cameraData.ipAddress)) {
            throw new Error('Valid IP address is required');
        }
        
        if (!cameraData.location || cameraData.location.trim().length === 0) {
            throw new Error('Camera location is required');
        }
    }

    isValidIpAddress(ip) {
        const ipRegex = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return ipRegex.test(ip);
    }
}

export const cameraService = new CameraService();
```

### Phase 4: State Management (Week 7)

#### 4.1 Advanced Store Implementation
```javascript
// src/store/base.store.js
export class BaseStore {
    constructor(initialState = {}) {
        this.state = { ...initialState };
        this.subscribers = new Map();
        this.middleware = [];
    }

    getState() {
        return { ...this.state };
    }

    setState(newState, actionType = 'SET_STATE') {
        const previousState = { ...this.state };
        
        // Apply middleware
        const action = { type: actionType, payload: newState, previousState };
        this.middleware.forEach(middleware => {
            middleware(action, this.state);
        });
        
        this.state = { ...this.state, ...newState };
        this.notifySubscribers(actionType, this.state, previousState);
    }

    subscribe(callback, selector = null) {
        const id = Date.now() + Math.random();
        this.subscribers.set(id, { callback, selector });
        
        return () => this.subscribers.delete(id);
    }

    notifySubscribers(actionType, currentState, previousState) {
        this.subscribers.forEach(({ callback, selector }) => {
            if (selector) {
                const currentValue = selector(currentState);
                const previousValue = selector(previousState);
                
                if (currentValue !== previousValue) {
                    callback(currentValue, actionType);
                }
            } else {
                callback(currentState, actionType);
            }
        });
    }

    addMiddleware(middleware) {
        this.middleware.push(middleware);
    }

    // Action creators
    createAction(type, payloadCreator = (payload) => payload) {
        return (payload) => {
            const actionPayload = payloadCreator(payload);
            this.setState(actionPayload, type);
        };
    }
}

// Logging middleware
export const loggingMiddleware = (action, state) => {
    if (process.env.NODE_ENV === 'development') {
        console.group(`🔄 Store Action: ${action.type}`);
        console.log('Previous State:', action.previousState);
        console.log('Action Payload:', action.payload);
        console.log('New State:', state);
        console.groupEnd();
    }
};

// Persistence middleware
export const persistenceMiddleware = (persistKey) => (action, state) => {
    try {
        localStorage.setItem(persistKey, JSON.stringify(state));
    } catch (error) {
        console.warn('Failed to persist state:', error);
    }
};
```

#### 4.2 Feature-Specific Stores
```javascript
// src/store/camera.store.js
import { BaseStore, loggingMiddleware } from './base.store.js';

class CameraStore extends BaseStore {
    constructor() {
        super({
            cameras: [],
            selectedCamera: null,
            filters: {
                status: '',
                location: '',
                search: ''
            },
            loading: false,
            error: null,
            lastUpdated: null
        });

        this.addMiddleware(loggingMiddleware);
        
        // Define actions
        this.actions = {
            setCameras: this.createAction('SET_CAMERAS', (cameras) => ({
                cameras,
                lastUpdated: new Date(),
                error: null
            })),
            
            addCamera: this.createAction('ADD_CAMERA', (camera) => ({
                cameras: [...this.state.cameras, camera],
                lastUpdated: new Date()
            })),
            
            updateCamera: this.createAction('UPDATE_CAMERA', ({ cameraId, updates }) => ({
                cameras: this.state.cameras.map(camera => 
                    camera.id === cameraId ? { ...camera, ...updates } : camera
                ),
                lastUpdated: new Date()
            })),
            
            removeCamera: this.createAction('REMOVE_CAMERA', (cameraId) => ({
                cameras: this.state.cameras.filter(camera => camera.id !== cameraId),
                selectedCamera: this.state.selectedCamera?.id === cameraId ? null : this.state.selectedCamera,
                lastUpdated: new Date()
            })),
            
            selectCamera: this.createAction('SELECT_CAMERA', (camera) => ({
                selectedCamera: camera
            })),
            
            setFilters: this.createAction('SET_FILTERS', (filters) => ({
                filters: { ...this.state.filters, ...filters }
            })),
            
            setLoading: this.createAction('SET_LOADING', (loading) => ({ loading })),
            
            setError: this.createAction('SET_ERROR', (error) => ({ error }))
        };
    }

    // Selectors
    get activeCameras() {
        return this.state.cameras.filter(camera => camera.status === 'active');
    }

    get filteredCameras() {
        const { cameras, filters } = this.state;
        
        return cameras.filter(camera => {
            if (filters.status && camera.status !== filters.status) return false;
            if (filters.location && camera.location !== filters.location) return false;
            if (filters.search) {
                const searchLower = filters.search.toLowerCase();
                return camera.name.toLowerCase().includes(searchLower) ||
                       camera.ipAddress.toLowerCase().includes(searchLower);
            }
            return true;
        });
    }

    getCameraById(id) {
        return this.state.cameras.find(camera => camera.id === id);
    }

    // Async actions
    async loadCameras() {
        this.actions.setLoading(true);
        try {
            const cameras = await cameraService.getCameras();
            this.actions.setCameras(cameras);
        } catch (error) {
            this.actions.setError(error.message);
        } finally {
            this.actions.setLoading(false);
        }
    }
}

export const cameraStore = new CameraStore();
```

### Phase 5: Integration & Testing (Week 8)

#### 5.1 Component Integration
```javascript
// src/pages/dashboard/dashboard.page.js
import { MetricsCard } from '../../components/dashboard/metrics-card/metrics-card.component.js';
import { CameraGrid } from '../../components/dashboard/camera-grid/camera-grid.component.js';
import { RecentDetections } from '../../components/dashboard/recent-detections/recent-detections.component.js';
import { SystemHealth } from '../../components/dashboard/system-health/system-health.component.js';
import { appStore } from '../../store/app.store.js';
import { cameraStore } from '../../store/camera.store.js';
import { detectionStore } from '../../store/detection.store.js';

export class DashboardPage {
    constructor() {
        this.components = {};
        this.subscriptions = [];
    }

    async init() {
        await this.initializeComponents();
        this.subscribeToStores();
        await this.loadData();
    }

    async initializeComponents() {
        // Initialize metrics cards
        this.components.activeCameras = new MetricsCard('.metric-card[data-metric="cameras"]', {
            value: 0,
            label: 'Active Cameras',
            icon: 'fas fa-video text-blue',
            clickable: true,
            onClick: () => this.navigateToPage('cameras')
        });

        this.components.detectionsToday = new MetricsCard('.metric-card[data-metric="detections"]', {
            value: 0,
            label: 'Detections Today',
            icon: 'fas fa-car text-green',
            clickable: true,
            onClick: () => this.navigateToPage('detections')
        });

        // Initialize dashboard components
        this.components.cameraGrid = new CameraGrid('.camera-grid', {
            maxCameras: 4,
            showControls: true
        });

        this.components.recentDetections = new RecentDetections('.recent-detections-list', {
            maxDetections: 10
        });

        this.components.systemHealth = new SystemHealth('.health-metrics');

        // Initialize all components
        await Promise.all(
            Object.values(this.components).map(component => component.init())
        );
    }

    subscribeToStores() {
        // Subscribe to camera store changes
        this.subscriptions.push(
            cameraStore.subscribe(
                (cameras) => this.updateCameraMetrics(cameras),
                (state) => state.cameras
            )
        );

        // Subscribe to detection store changes
        this.subscriptions.push(
            detectionStore.subscribe(
                (detections) => this.updateDetectionMetrics(detections),
                (state) => state.detections
            )
        );

        // Subscribe to app store changes
        this.subscriptions.push(
            appStore.subscribe(
                (systemHealth) => this.components.systemHealth?.updateHealth(systemHealth),
                (state) => state.systemHealth
            )
        );
    }

    async loadData() {
        try {
            // Load data concurrently
            await Promise.all([
                cameraStore.loadCameras(),
                detectionStore.loadTodayDetections(),
                appStore.loadSystemHealth()
            ]);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showErrorMessage('Failed to load dashboard data');
        }
    }

    updateCameraMetrics(cameras) {
        const activeCameras = cameras.filter(camera => camera.status === 'active');
        this.components.activeCameras?.updateValue(activeCameras.length, 'positive');
        this.components.cameraGrid?.updateCameras(cameras.slice(0, 4));
    }

    updateDetectionMetrics(detections) {
        const today = new Date().toDateString();
        const todayDetections = detections.filter(detection => 
            new Date(detection.timestamp).toDateString() === today
        );
        
        this.components.detectionsToday?.updateValue(todayDetections.length, 'positive');
        this.components.recentDetections?.updateDetections(detections.slice(0, 10));
    }

    navigateToPage(pageName) {
        window.dispatchEvent(new CustomEvent('navigate', { detail: { page: pageName } }));
    }

    showErrorMessage(message) {
        // Use notification service or show error UI
        console.error(message);
    }

    destroy() {
        // Clean up subscriptions
        this.subscriptions.forEach(unsubscribe => unsubscribe());
        this.subscriptions = [];

        // Destroy components
        Object.values(this.components).forEach(component => {
            component.destroy?.();
        });
    }
}
```

## Implementation Timeline

### Complete Migration Schedule

| Phase | Duration | Deliverables | Resources |
|-------|----------|-------------|-----------|
| **Phase 1: Foundation** | 2 weeks | - Project setup<br>- Build system<br>- Base components | 2 developers |
| **Phase 2: Core Components** | 2 weeks | - Navigation<br>- Dashboard components<br>- Camera components | 3 developers |
| **Phase 3: Services** | 2 weeks | - API services<br>- Business logic<br>- Error handling | 2 developers |
| **Phase 4: State Management** | 1 week | - Store implementation<br>- Data flow<br>- Integration | 2 developers |
| **Phase 5: Testing & Polish** | 1 week | - Unit tests<br>- E2E tests<br>- Documentation | 3 developers |
| **Total** | **8 weeks** | Complete modernized frontend | **Team of 3-4** |

### Success Metrics

#### Technical Metrics
- **Bundle Size**: < 1MB total (vs current ~2MB)
- **Load Time**: < 2 seconds initial load
- **Component Reusability**: 80%+ components reused across pages
- **Test Coverage**: 90%+ unit test coverage
- **Accessibility**: WCAG 2.1 AA compliance

#### Developer Experience
- **Build Time**: < 30 seconds development builds
- **Hot Reload**: < 1 second component updates
- **Code Maintainability**: Cyclomatic complexity < 10 per function
- **Documentation**: 100% component documentation

This comprehensive frontend architecture guide provides a clear roadmap for transforming the monolithic prototype into a modern, maintainable, and scalable component-based architecture. The modular approach ensures better developer experience, easier testing, and improved maintainability while following industry best practices.