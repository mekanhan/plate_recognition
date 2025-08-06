# Instructions for Fixing Camera Info Card Styling

## Current Issues to Address:
1. **Inconsistent alignment** - Location and Connection fields are centered while other fields are left-aligned
2. **Missing consistent styling** - Recording Status section lacks the same card-style formatting as Location/Connection
3. **No collapse/expand functionality** - The Recording Status section should be collapsible

## Required Changes:

### 1. Standardize Field Layout
- Apply consistent styling to ALL information fields
- Use the same layout pattern as Location and Connection fields:
  ```
  [Label]:                    [Value]
  ```
- Ensure proper spacing and alignment across all fields

### 2. Apply Card-Style Formatting
Convert the Recording Status section to match the card style:
- Add proper background/container styling
- Apply consistent padding and margins
- Use the same font sizes and colors as Location/Connection

### 3. Implement Collapse/Expand Functionality
Add collapsible sections for better organization:
- Add expand/collapse toggle button (▼/▶) next to "Recording Status" header
- Allow users to hide/show the recording details
- Maintain state persistence (remember collapsed/expanded state)

### 4. Specific Field Formatting Requirements:

**Recording Status Section:**
```
▼ Recording Status
├─ Status:           Stopped ▼
├─ Connection:       ❌ disconnected  
├─ FFmpeg PID:       439961
├─ Segments:         47 (last: 11:47:30 PM)
├─ Storage:          0 B
└─ Uptime:           17m
```

**Styling Guidelines:**
- Use consistent indentation for sub-items
- Align colons vertically
- Right-align values or left-align with consistent spacing
- Apply the same color scheme throughout

### 5. Button Styling
- Ensure "Start Recording" and "Refresh" buttons match the overall theme
- Apply consistent hover states and transitions
- Use appropriate spacing between buttons

### 6. Visual Hierarchy
- Make section headers slightly larger/bolder
- Use subtle separators between sections if needed
- Ensure proper contrast ratios for accessibility

## Implementation Checklist:
- [ ] Align all field labels and values consistently
- [ ] Apply card-style container to Recording Status section
- [ ] Add collapse/expand functionality to sections
- [ ] Standardize typography (fonts, sizes, weights)
- [ ] Ensure consistent spacing/padding throughout
- [ ] Match the color scheme of Location/Connection fields
- [ ] Test responsive behavior
- [ ] Verify accessibility standards

## Example CSS Structure:
```css
.info-section {
  background: [match existing card background];
  padding: [consistent padding];
  margin-bottom: [consistent spacing];
  border-radius: [match existing radius];
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: [consistent vertical padding];
}

.info-label {
  font-weight: [consistent weight];
  color: [match existing label color];
}

.info-value {
  text-align: right;
  color: [match existing value color];
}
```

## Additional Notes:
- Maintain the existing dark theme aesthetic
- Preserve the "Online" status indicator styling
- Keep the Reolink logo/branding consistent
- Ensure all interactive elements have appropriate feedback