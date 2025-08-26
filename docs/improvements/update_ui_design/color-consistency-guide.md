# Color Consistency Guide - LPR Web UI

## 🎨 Color System Overview

Our unified color system ensures consistency across all pages by providing:
- **5 shades** for each color (50-900) for flexibility
- **Semantic naming** that clearly indicates usage
- **Consistent hover/active states**
- **Proper contrast ratios** for accessibility
- **Dark theme support** with adjusted values

## 📋 Color Usage Rules

### 1. **Primary Actions & Interactive Elements**

```css
/* Primary buttons */
.btn-primary {
    background: var(--primary);
    color: var(--text-inverse);
}
.btn-primary:hover {
    background: var(--primary-hover);
}

/* Links */
a {
    color: var(--text-link);
}
a:hover {
    color: var(--text-link-hover);
}

/* Active navigation */
.nav-item.active {
    background: var(--primary-bg);
    color: var(--primary);
}
```

### 2. **Status Indicators (Consistent Everywhere)**

```css
/* Camera status */
.camera-status.online,
.status-dot.online,
.metric-status.online {
    background: var(--status-online);
    color: var(--status-online);
}

.camera-status.offline,
.status-dot.offline,
.metric-status.offline {
    background: var(--status-offline);
    color: var(--status-offline);
}

/* Alert badges */
.badge-success { 
    background: var(--badge-success-bg);
    color: var(--badge-success-text);
}
.badge-error {
    background: var(--badge-error-bg);
    color: var(--badge-error-text);
}
```

### 3. **Backgrounds & Surfaces**

```css
/* Page hierarchy */
body {
    background: var(--bg-base);        /* White/main background */
}

.section {
    background: var(--bg-subtle);      /* Light gray sections */
}

.card {
    background: var(--card-bg);        /* Card surfaces */
    border: 1px solid var(--card-border);
}

.sidebar {
    background: var(--sidebar-bg);     /* Dark sidebar */
}
```

### 4. **Text Hierarchy**

```css
/* Consistent text colors */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary);        /* Main headings */
}

p, .body-text {
    color: var(--text-primary);        /* Body text */
}

.subtitle, .description {
    color: var(--text-secondary);      /* Secondary info */
}

.hint, .help-text {
    color: var(--text-tertiary);       /* Muted hints */
}

.disabled {
    color: var(--text-disabled);       /* Disabled state */
}
```

### 5. **Borders & Dividers**

```css
/* Border hierarchy */
.card {
    border: 1px solid var(--border-subtle);    /* Subtle borders */
}

.table th {
    border-bottom: 2px solid var(--border-default);  /* Stronger borders */
}

input:focus {
    border-color: var(--border-focus);         /* Focus state */
}
```

## 🚨 Common Inconsistencies to Fix

### ❌ **Before** (Inconsistent)
```css
/* Different pages using different colors */
.dashboard .status-online { color: #00ff00; }
.cameras .status-online { color: #48bb78; }
.settings .status-online { color: green; }

/* Hard-coded colors */
.error-message { color: #ff0000; }
.success-badge { background: rgb(0, 255, 0); }
```

### ✅ **After** (Consistent)
```css
/* All pages use the same variable */
.status-online { color: var(--status-online); }

/* Semantic variables */
.error-message { color: var(--error); }
.success-badge { background: var(--success-bg); }
```

## 📐 Component-Specific Rules

### **Dashboard**
- Metric cards: `var(--card-bg)` with `var(--border-subtle)`
- Positive changes: `var(--success)`
- Negative changes: `var(--error)`
- Chart colors: Use primary scale `--primary-300` to `--primary-700`

### **Camera Management**
- Online cameras: `var(--status-online)` + `var(--status-online-bg)`
- Offline cameras: `var(--status-offline)` + `var(--status-offline-bg)`
- Error states: `var(--status-error)` + `var(--status-error-bg)`

### **Tables**
- Header background: `var(--table-header-bg)`
- Row hover: `var(--table-row-hover)`
- Selected row: `var(--table-row-selected)`
- Borders: `var(--border-subtle)`

### **Forms**
- Input borders: `var(--border-default)`
- Focus state: `var(--border-focus)`
- Error state: `var(--error)` border with `var(--error-bg)` background
- Success state: `var(--success)` border with `var(--success-bg)` background

### **Modals**
- Overlay: `var(--surface-overlay)`
- Modal background: `var(--card-bg)`
- Modal border: `var(--border-subtle)`
- Shadow: `var(--shadow-modal)`

## 🔄 Migration Checklist

### Phase 1: Core Variables
- [ ] Replace `variables.css` with unified color system
- [ ] Update all hard-coded colors to use variables
- [ ] Test dark theme compatibility

### Phase 2: Component Updates
- [ ] Update button colors across all pages
- [ ] Standardize status indicators
- [ ] Unify form input styles
- [ ] Consistent table styling

### Phase 3: Page-Specific
- [ ] Dashboard: Update metric cards and charts
- [ ] Cameras: Consistent status colors
- [ ] Settings: Form validation states
- [ ] Recordings: Timeline and player controls

## 🎯 Benefits of Consistency

1. **User Experience**: Users learn color meanings once
2. **Maintenance**: Change colors in one place
3. **Accessibility**: Guaranteed contrast ratios
4. **Brand Identity**: Professional, cohesive appearance
5. **Dark Mode**: Automatic theme switching

## 🚀 Quick Implementation

```css
/* Add to your main.css after importing variables */
@import './base/variables.css';

/* Utility classes for quick fixes */
.status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.status-indicator.online { background: var(--status-online); }
.status-indicator.offline { background: var(--status-offline); }
.status-indicator.error { background: var(--status-error); }
.status-indicator.warning { background: var(--status-warning); }

/* Consistent card styles */
.card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: var(--radius-card);
    padding: var(--spacing-md);
}

.card:hover {
    border-color: var(--border-hover);
}
```

## 📝 Notes

- Always use semantic color names (`--success`) not color names (`--green`)
- Test both light and dark themes when making changes
- Use the color scale (50-900) for variations, not opacity
- Maintain WCAG AA contrast ratios (4.5:1 for normal text)