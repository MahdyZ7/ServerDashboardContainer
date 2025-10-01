# Server Monitoring Dashboard UI Design Guidelines
## Design Philosophy: Data-First Minimalism

### Core Principles
1. **Maximum Data Density**: Display comprehensive information without overwhelming users
2. **Visual Hierarchy**: Critical metrics prominently displayed, secondary data subtly accessible
3. **Monochromatic Base**: KU Blue (#0057B8) as primary with strategic accent colors for alerts
4. **Zero Visual Clutter**: Remove decorative elements, focus on functional design
5. **Instant Readability**: 3-second rule for understanding server status

---

## Color System

### Primary Palette (Khalifa University Guidelines)
```css
--ku-primary: #0057B8;        /* Main brand color - used sparingly */
--ku-primary-dark: #003A7A;   /* Header gradients, active states */
--ku-neutral-100: #FFFFFF;    /* Background primary */
--ku-neutral-200: #F8F9FA;    /* Background secondary */
--ku-neutral-300: #E9ECEF;    /* Borders, dividers */
--ku-neutral-400: #DEE2E6;    /* Inactive elements */
--ku-neutral-500: #ADB5BD;    /* Muted text */
--ku-neutral-600: #6C757D;    /* Secondary text */
--ku-neutral-700: #495057;    /* Primary text */
--ku-neutral-800: #343A40;    /* Headers */
--ku-neutral-900: #212529;    /* Critical text */
```

### Functional Colors (Status Indicators)
```css
--status-healthy: #0057B8;    /* Normal operation (KU Blue) */
--status-warning: #FF8F1C;    /* Warning state (KU Orange) */
--status-critical: #DC3545;   /* Critical/Error state */
--status-offline: #6C757D;    /* Offline/Inactive state */
--status-info: #00A9CE;       /* Informational (KU Undergraduate Blue) */
```

### Data Visualization Colors
```css
--chart-primary: #0057B8;
--chart-secondary: #00A9CE;
--chart-tertiary: #78D64B;
--chart-quaternary: #6F5091;
--chart-gradient-start: rgba(0, 87, 184, 0.1);
--chart-gradient-end: rgba(0, 87, 184, 0.3);
```

---

## Typography Hierarchy

### Font Stack
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### Type Scale
```css
--text-xs: 11px;     /* Micro labels, timestamps */
--text-sm: 12px;     /* Secondary info, table cells */
--text-base: 13px;   /* Body text, default */
--text-md: 14px;     /* Emphasized content */
--text-lg: 16px;     /* Section headers */
--text-xl: 18px;     /* Card titles */
--text-2xl: 20px;    /* Dashboard title */
--text-3xl: 24px;    /* Key metrics */
```

### Font Weights
```css
--font-normal: 400;   /* Body text */
--font-medium: 500;   /* Labels, secondary headers */
--font-semibold: 600; /* Primary headers, metrics */
--font-bold: 700;     /* Critical alerts, key numbers */
```

---

## Layout Structure

### Grid System
```
Dashboard Container
├── Compact Header (48px fixed)
│   ├── Logo + Title (left)
│   ├── Global Status Indicators (center)
│   └── Quick Actions + Time (right)
├── Alert Bar (40px when active, collapsible)
├── Main Content Area
│   ├── Summary Strip (80px)
│   │   └── 8-10 key metrics in horizontal scroll
│   ├── Server Grid (auto-height)
│   │   └── Compact server cards (2-4 per row)
│   └── Data Tables (collapsible sections)
└── Status Footer (32px fixed)
```

### Spacing System
```css
--space-1: 4px;   /* Tight spacing within components */
--space-2: 8px;   /* Default padding */
--space-3: 12px;  /* Section spacing */
--space-4: 16px;  /* Card padding */
--space-5: 20px;  /* Major sections */
--space-6: 24px;  /* Page margins */
```

---

## Component Specifications

### 1. Compact Header
- **Height**: 48px fixed
- **Background**: Solid #FFFFFF with bottom border
- **Logo**: 32px height, monochrome
- **Elements**: Inline, horizontally aligned
- **Shadow**: None (clean edge)

### 2. Summary Strip
- **Layout**: Horizontal scroll, no wrap
- **Metric Cards**:
  - Size: 120px × 60px
  - Padding: 8px
  - Border: 1px solid #E9ECEF
  - Hover: Background #F8F9FA
- **Content**:
  - Number: 24px bold
  - Label: 11px uppercase, #6C757D
  - Trend: Inline sparkline (optional)

### 3. Server Cards (Compact)
- **Dimensions**: Min 280px wide, auto height
- **Layout**: CSS Grid, responsive
- **Structure**:
  ```
  ┌─────────────────────────────┐
  │ ServerName        ● Online  │ <- 14px, status dot
  ├─────────────────────────────┤
  │ CPU  RAM  DISK  CONN  USERS │ <- Inline metrics
  │ 2.5  45%  67%   125    8    │ <- Values only
  ├─────────────────────────────┤
  │ ▁▂▄▆█▄▂▁ CPU Load (24h)    │ <- Mini sparkline
  └─────────────────────────────┘
  ```
- **Colors**:
  - Background: #FFFFFF
  - Metrics above threshold: Color-coded
  - Border: 1px solid #E9ECEF
  - Status indicator: 6px dot, color-coded

### 4. Data Tables
- **Row Height**: 32px (compressed)
- **Header**: Sticky, #F8F9FA background
- **Borders**: Horizontal only, #E9ECEF
- **Hover**: Background #F8F9FA
- **Selection**: Left border 3px #0057B8
- **Typography**: 12px regular, 13px for primary column

### 5. Inline Visualizations
- **Sparklines**: 60px × 20px, no axes
- **Progress Bars**: 4px height, rounded
- **Status Dots**: 6px diameter, inline
- **Micro Charts**: 40px × 40px max

### 6. Alert Bar
- **Height**: 40px when active
- **Position**: Below header, pushes content down
- **Animation**: Slide down 200ms ease
- **Content**: Icon (14px) + Message (13px) + Action button
- **Dismiss**: Right-aligned X, click to hide

---

## Interaction Patterns

### Hover States
- **Cards**: Elevation change (0 → 2px shadow)
- **Buttons**: Background darken 10%
- **Tables**: Row background #F8F9FA
- **Links**: Underline on hover only

### Click/Active States
- **Cards**: Border color #0057B8
- **Buttons**: Scale 0.98, instant
- **Tabs**: Bottom border 2px #0057B8

### Transitions
```css
--transition-fast: 150ms ease;
--transition-base: 200ms ease;
--transition-slow: 300ms ease;
```

### Loading States
- **Skeleton**: #F8F9FA animated gradient
- **Spinner**: 16px, #0057B8, minimal
- **Progress**: Linear, 2px height

---

## Responsive Breakpoints

```css
--mobile: 320px - 767px;    /* Single column, stacked */
--tablet: 768px - 1023px;   /* 2 columns */
--desktop: 1024px - 1439px; /* 3 columns */
--wide: 1440px+;            /* 4+ columns */
```

### Mobile Adaptations
- Server cards stack vertically
- Summary strip: 2 rows of metrics
- Tables: Horizontal scroll
- Navigation: Hamburger menu

---

## Status Indicator System

### Server Status Logic
```javascript
if (offline) return 'offline';        // Gray
if (cpu > 8 || ram > 95) return 'critical';  // Red
if (cpu > 5 || ram > 85) return 'warning';   // Orange
return 'healthy';                      // Blue
```

### Visual Indicators
- **Dot**: 6px, solid color
- **Badge**: Rounded rectangle, text + background
- **Bar**: Horizontal fill, 4px height
- **Icon**: FontAwesome, 14px, color-coded

---

## Performance Guidelines

### Optimization Targets
- Initial Load: < 2 seconds
- Data Refresh: < 500ms
- Interaction Response: < 100ms
- Animation FPS: 60fps minimum

### Data Display Limits
- Server cards: 20 visible max (pagination)
- Table rows: 50 initial (virtual scroll)
- Charts: 100 data points (sampling)
- Metrics refresh: 15 seconds minimum

---

## Accessibility Standards

### WCAG 2.1 Level AA
- Color contrast: 4.5:1 minimum
- Focus indicators: 2px outline
- Keyboard navigation: Full support
- Screen reader: ARIA labels
- Font size: 11px minimum

### Interaction Targets
- Buttons: 32px × 32px minimum
- Links: 24px × 24px minimum
- Form inputs: 40px height

---

## Implementation Priority

### Phase 1: Core Structure
1. Compact header with status
2. Summary metrics strip
3. Basic server cards
4. Essential data tables

### Phase 2: Enhancements
1. Inline sparklines
2. Collapsible sections
3. Advanced filtering
4. Keyboard shortcuts

### Phase 3: Polish
1. Micro-animations
2. Dark mode support
3. Custom themes
4. Export functionality

---

## Code Examples

### Server Card HTML Structure
```html
<div class="server-card" data-status="healthy">
  <div class="server-card-header">
    <span class="server-name">KU-Server-01</span>
    <span class="server-status-indicator"></span>
  </div>
  <div class="server-metrics-row">
    <div class="metric-inline">
      <span class="metric-value">2.5</span>
      <span class="metric-label">CPU</span>
    </div>
    <!-- More metrics... -->
  </div>
  <div class="server-sparkline">
    <canvas width="280" height="30"></canvas>
  </div>
</div>
```

### CSS Variables for Theming
```css
:root {
  --card-bg: #FFFFFF;
  --card-border: #E9ECEF;
  --card-shadow: 0 1px 3px rgba(0,0,0,0.1);
  --card-radius: 4px;
  --card-padding: 16px;
}
```

---

## Do's and Don'ts

### Do's
- ✓ Use monochromatic palette with accent colors for alerts only
- ✓ Maintain consistent 4px spacing grid
- ✓ Display raw numbers before percentages
- ✓ Group related metrics horizontally
- ✓ Use system fonts for performance

### Don'ts
- ✗ Add gradients or shadows for decoration
- ✗ Use more than 3 font sizes per view
- ✗ Display redundant information
- ✗ Animate without user interaction
- ✗ Use icons without text labels

---

## Testing Checklist

- [ ] 3-second comprehension test for server status
- [ ] Color blind safe (use patterns + color)
- [ ] Mobile responsive (320px minimum)
- [ ] Keyboard navigable
- [ ] 60fps scrolling performance
- [ ] Sub-500ms data updates
- [ ] Clear visual hierarchy
- [ ] Consistent interaction patterns