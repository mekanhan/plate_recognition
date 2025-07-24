# Theme System Requirements

## Overview

This document outlines the requirements and implementation guidelines for the theme system in the LPR (License Plate Recognition) application. The theme system should follow modern web development best practices, prioritize user experience, and ensure accessibility compliance.

## Core Requirements

### 1. Three-State Theme Model

The application must support three distinct theme states:

- **`light`** - Explicit light theme with bright backgrounds and dark text
- **`dark`** - Explicit dark theme with dark backgrounds and light text  
- **`auto`** - Automatically follows the user's system preference (`prefers-color-scheme`)

### 2. Theme Priority Chain

The theme resolution must follow this priority order:

1. **User's explicit choice** (stored in localStorage as 'theme')
2. **System preference** (detected via `prefers-color-scheme` media query)
3. **Default fallback** (light mode)

### 3. Performance Requirements

- **No Flash of Wrong Theme (FOUT)**: Theme must be applied before first paint
- **Smooth Transitions**: Theme changes should be visually smooth (≤300ms)
- **Minimal Reflow**: Theme switching should minimize layout recalculations
- **Memory Efficient**: Theme management should not cause memory leaks

## Technical Implementation

### CSS Architecture

#### Base Theme Structure
```css
/* Light theme as default in :root */
:root {
  --bg-primary: #bebec7;
  --bg-secondary: #acaec0;
  --bg-tertiary: #cfd1e4;
  --surface-color: #ffffff;
  --card-bg: #ffffff;
  --text-primary: #1a1d23;
  --text-secondary: #2d3748;
  --text-muted: #4a5568;
  --border-color: #b0b7be;
  /* Additional variables... */
}

/* Dark theme override */
[data-theme="dark"] {
  --bg-primary: #1a202c;
  --bg-secondary: #2d3748;
  --bg-tertiary: #4a5568;
  --surface-color: #334155;
  --card-bg: #1e293b;
  --text-primary: #f7fafc;
  --text-secondary: #e2e8f0;
  --text-muted: #a0aec0;
  --border-color: #4a5568;
  /* Additional variables... */
}

/* System preference fallback */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    --bg-primary: #1a202c;
    --bg-secondary: #2d3748;
    --surface-color: #334155;
    --card-bg: #1e293b;
    /* Mirror dark theme variables */
  }
}
```

#### Variable Organization
- All theme-related CSS variables must be defined in `/frontend/src/styles/base/variables.css`
- No duplicate theme variables in other CSS files
- Variables should follow semantic naming conventions (e.g., `--surface-color` not `--gray-100`)

### JavaScript Theme Management

#### Core Theme Manager Class
```javascript
class ThemeManager {
  constructor() {
    this.themes = ['light', 'dark', 'auto'];
    this.currentTheme = this.getInitialTheme();
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    this.init();
  }

  init() {
    this.applyTheme();
    this.listenForSystemChanges();
  }

  getInitialTheme() {
    const saved = localStorage.getItem('theme');
    return this.themes.includes(saved) ? saved : 'auto';
  }

  applyTheme() {
    const resolvedTheme = this.resolveTheme();
    
    if (resolvedTheme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    
    this.updateToggleButton();
  }

  resolveTheme() {
    if (this.currentTheme === 'auto') {
      return this.mediaQuery.matches ? 'dark' : 'light';
    }
    return this.currentTheme;
  }

  setTheme(theme) {
    if (!this.themes.includes(theme)) return;
    
    this.currentTheme = theme;
    localStorage.setItem('theme', theme);
    this.applyTheme();
    
    // Dispatch theme change event
    window.dispatchEvent(new CustomEvent('themeChanged', {
      detail: { theme: this.currentTheme, resolved: this.resolveTheme() }
    }));
  }

  listenForSystemChanges() {
    this.mediaQuery.addEventListener('change', () => {
      if (this.currentTheme === 'auto') {
        this.applyTheme();
      }
    });
  }
}
```

### Initialization Requirements

#### Order of Operations
1. **Pre-DOM**: Theme detection and initial application
2. **Early App Init**: Theme manager instantiation
3. **Component Initialization**: All UI components render with correct theme
4. **Event Binding**: Theme toggle functionality activation

#### Implementation in Header Component
```javascript
// In Header.js constructor
constructor() {
  this.themeManager = new ThemeManager();
  // Other initialization...
  this.init();
}

init() {
  this.render();
  this.attachEventListeners();
  // Other setup...
}
```

### Toggle Button Implementation

#### Button States
- **Light Mode Active**: Moon icon (`fa-moon`) - "Switch to dark mode"
- **Dark Mode Active**: Sun icon (`fa-sun`) - "Switch to light mode"
- **Auto Mode**: Adaptive icon showing current resolved state with auto indicator

#### Accessibility Requirements
```javascript
updateToggleButton() {
  const button = document.getElementById('dark-mode-toggle');
  const icon = button.querySelector('i');
  const resolvedTheme = this.resolveTheme();
  
  // Update icon
  icon.className = `fas ${resolvedTheme === 'dark' ? 'fa-sun' : 'fa-moon'}`;
  
  // Update accessibility attributes
  button.setAttribute('aria-label', 
    `Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`
  );
  button.setAttribute('aria-pressed', resolvedTheme === 'dark');
}
```

## User Experience Requirements

### 1. Persistence
- User theme preference must persist across browser sessions
- Theme state must survive browser restarts and tab navigation
- localStorage must be gracefully handled when unavailable

### 2. Responsiveness
- Theme changes must be immediate (no loading states)
- All UI elements must transition smoothly between themes
- No visual artifacts during theme switching

### 3. Discoverability
- Theme toggle must be easily discoverable in the UI
- Current theme state must be visually clear
- Toggle should provide appropriate hover/focus states

## Accessibility Requirements

### 1. WCAG Compliance
- Theme toggle must be keyboard accessible (Tab, Enter, Space)
- Proper ARIA labels and states must be maintained
- Color contrast ratios must meet WCAG AA standards in both themes

### 2. Reduced Motion Support
```css
@media (prefers-reduced-motion: reduce) {
  * {
    transition-duration: 0.01ms !important;
  }
}
```

### 3. High Contrast Support
```css
@media (prefers-contrast: high) {
  :root {
    --border-color: #000000;
    --text-muted: #000000;
  }
  
  .card, .button {
    border: 2px solid currentColor;
  }
}
```

## Integration Points

### 1. Component Architecture
- All components must use CSS custom properties for theme values
- No hardcoded colors in component styles
- Theme-aware components should listen for `themeChanged` events

### 2. Application State
- Theme state should be available to all application components
- Global theme manager instance should be accessible via `window.themeManager`
- Theme changes should trigger re-evaluation of conditional styling

### 3. External Libraries
- Third-party components should inherit theme styles where possible
- Custom theme overrides should be documented and maintainable
- Chart libraries and data visualizations should adapt to theme changes

## Testing Requirements

### 1. Functional Testing
- Theme persistence across sessions
- System preference detection and response
- Toggle button functionality in all states
- localStorage error handling

### 2. Visual Testing
- No flash of unstyled content (FOUC)
- Smooth transitions between themes
- Proper contrast ratios in both themes
- Component styling consistency

### 3. Accessibility Testing
- Keyboard navigation of theme controls
- Screen reader compatibility
- Color contrast validation
- Reduced motion compliance

## Migration Strategy

### Phase 1: Foundation
1. Consolidate CSS variables in `variables.css`
2. Remove duplicate theme definitions from `main.css`
3. Implement core `ThemeManager` class

### Phase 2: Integration
1. Update `Header` component to use `ThemeManager`
2. Add system preference detection
3. Implement proper initialization order

### Phase 3: Enhancement
1. Add smooth transitions and animations
2. Implement accessibility improvements
3. Add comprehensive testing coverage

### Phase 4: Optimization
1. Performance optimization and monitoring
2. Advanced features (theme scheduling, custom themes)
3. Documentation and developer guidelines

## Success Criteria

- ✅ Theme switching works reliably in all browsers
- ✅ No visual artifacts or flashing during theme changes
- ✅ System preferences are respected and responded to automatically
- ✅ Theme state persists across browser sessions
- ✅ All accessibility requirements are met
- ✅ Performance impact is minimal (< 50ms for theme switches)
- ✅ Code is maintainable and well-documented

## Future Considerations

### Extensibility
- Support for custom theme creation
- Theme scheduling based on time of day
- Integration with user preference APIs
- Multi-brand theme support

### Advanced Features
- Theme preview without applying
- Gradual theme transitions based on ambient light
- Component-level theme overrides
- Theme analytics and usage tracking