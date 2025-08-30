1. Analysis First - Don't Assume
TELL AI:
"Before modifying anything:
1. ANALYZE the existing structure
2. IDENTIFY the current navigation pattern (overlay, push, off-canvas)
3. UNDERSTAND the page routing system
4. CHECK how pages are currently related to navigation
5. DOCUMENT what's working and what's broken"
2. Audit the Current Implementation
AI SHOULD CHECK:
- Where is the navigation component defined?
- Is it rendered at the app level or page level?
- What's the current CSS positioning strategy?
- How are pages wrapped (or not wrapped) by the layout?
- What routing system is being used?
- Are there inconsistencies between pages?
3. Identify the Root Cause
COMMON ISSUES TO LOOK FOR:
1. Navigation only included on some pages
2. Pages rendered outside the layout wrapper
3. Z-index conflicts causing overlays
4. Absolute positioning without proper offsets
5. Missing or incorrect CSS Grid/Flexbox setup
6. Route configuration bypassing the layout
4. Plan the Refactoring Approach
STEP-BY-STEP APPROACH:
1. Create/update the main layout wrapper
2. Ensure navigation is part of this wrapper
3. Update routing to render pages inside wrapper
4. Fix CSS to implement push pattern
5. Test on each page for consistency
6. Handle edge cases (modals, fullscreen, etc.)
5. Specific Instructions for Common Scenarios
Scenario A: Navigation Missing on Some Pages
FIX APPROACH:
"The navigation is missing from the Recordings page. 
1. Check if RecordingsPage is using the same layout wrapper as other pages
2. If not, wrap it with the AppLayout component
3. Ensure the route renders: <AppLayout><RecordingsPage /></AppLayout>
4. Never render pages directly without the layout wrapper"
Scenario B: Navigation Overlaying Content
FIX APPROACH:
"The navigation is overlaying the page content.
1. Remove any 'position: absolute' from main content
2. Change layout from overlay to push pattern:
   - Use CSS Grid: grid-template-columns: [nav-width] 1fr
   - Or Flexbox: display: flex with nav having fixed width
3. Ensure content has no negative margins
4. Remove any z-index from content area"
Scenario C: Inconsistent Behavior Across Pages
FIX APPROACH:
"Different pages behave differently with navigation.
1. Centralize navigation logic in one layout component
2. Remove page-specific navigation code
3. Ensure all routes use the same layout structure
4. Create a consistent page wrapper component"
6. Implementation Checklist for AI
BEFORE STARTING:
□ Backup or version control current code
□ Document current behavior
□ List all affected pages

IMPLEMENTATION:
□ Create/update AppLayout component
□ Move navigation to AppLayout
□ Update all routes to use AppLayout
□ Fix CSS for push pattern
□ Remove page-specific nav code
□ Test each page individually

VERIFICATION:
□ Navigation visible on all pages?
□ Content properly offset when nav expanded?
□ No overlapping elements?
□ Smooth transitions working?
□ Mobile responsiveness maintained?
7. Code Structure AI Should Aim For
javascript// App.js - The goal structure
<App>
  <AppLayout>
    <Sidebar 
      expanded={isExpanded}
      onToggle={handleToggle}
    />
    <MainContent offset={isExpanded ? 250 : 64}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/recordings" element={<Recordings />} />
        <Route path="/cameras" element={<Cameras />} />
        {/* All routes render inside MainContent */}
      </Routes>
    </MainContent>
  </AppLayout>
</App>
8. CSS Architecture to Implement
css/* The goal CSS structure */
.app-layout {
  display: grid;
  grid-template-columns: var(--nav-width) 1fr;
  min-height: 100vh;
  transition: grid-template-columns 300ms ease;
}

.app-layout[data-nav-expanded="true"] {
  --nav-width: 250px;
}

.app-layout[data-nav-expanded="false"] {
  --nav-width: 64px;
}

/* No absolute positioning for main content */
.main-content {
  grid-column: 2;
  overflow-y: auto;
  padding: 20px;
}
9. Migration Strategy
SAFE MIGRATION STEPS:
1. Start with one page (e.g., Dashboard)
2. Implement the new layout for that page
3. Test thoroughly
4. Apply same pattern to other pages one by one
5. Remove old navigation code after all pages migrated
6. Clean up unused CSS
10. What NOT to Do
AI SHOULD AVOID:
- Making assumptions about the current setup
- Changing everything at once
- Using quick fixes like !important in CSS
- Creating page-specific navigation solutions
- Ignoring the mobile experience
- Breaking existing functionality