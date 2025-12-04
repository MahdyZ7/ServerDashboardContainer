# Dark Mode Contrast Improvements

**Date:** 2025-12-04
**Status:** Completed

## Overview

This document describes the improvements made to enhance text contrast and readability in dark mode across the Server Monitoring Dashboard.

## Problem Statement

Users reported difficulty reading text in dark mode due to insufficient contrast in:
- Table cells and headers
- Graph labels and axis text
- Tab labels (selected and unselected)
- Metric values and labels
- Dropdown menus

## Solution

### 1. Enhanced Text Colors

Updated CSS color variables for better contrast:

```css
--ku-text-primary: #F3F4F6    /* Increased from #E5E7EB */
--ku-text-secondary: #D1D5DB   /* Increased from #9CA3AF */
--ku-text-muted: #9CA3AF       /* Unchanged, but better differentiated */
```

### 2. Table Improvements

**Headers:**
- Color: Pure white (#FFFFFF)
- Font weight: 600 (bold)
- Background: Enhanced tertiary color

**Cell Text:**
- Color: #E5E9F0 (bright, high contrast)
- Hover state: Pure white with brighter background

**Code Changes:** `srcs/Frontend/assets/dark-mode.css:156-182`

### 3. Graph Enhancements

Added comprehensive styling for Plotly graphs:

**Text Elements:**
- Titles, axis labels, tick labels: #E5E9F0
- Grid lines: Enhanced visibility with proper opacity
- Hover labels: Dark background with bright text

**New Configuration:**
- `DARK_MODE_LAYOUT` in `graph_config.py`
- `DARK_MODE_COLORS` dictionary for consistent theming

**Code Changes:**
- `srcs/Frontend/assets/dark-mode.css:259-282`
- `srcs/Frontend/graph_config.py:327-410`

### 4. Tab Improvements

**Unselected Tabs:**
- Text: #D1D5DB (brighter gray)
- Font weight: 500

**Selected/Hover Tabs:**
- Text: Pure white (#FFFFFF)
- Font weight: 600
- Background: KU Primary blue

**Code Changes:** `srcs/Frontend/assets/dark-mode.css:205-218`

### 5. Metrics & Values

Enhanced contrast for all metric displays:

**Metric Values:**
- Color: #F3F4F6 (very bright)
- Font weight: 600

**Metric Labels:**
- Color: #D1D5DB
- Font weight: 500

**Stat Values (Overview):**
- Color: #60A5FA (brighter blue)
- Font weight: 600

**Code Changes:** `srcs/Frontend/assets/dark-mode.css:91-148`

### 6. Dropdowns

**All States:**
- Default text: #E5E9F0
- Hover text: Pure white
- Selected option: White text on blue background

**Code Changes:** `srcs/Frontend/assets/dark-mode.css:294-325`

### 7. Input Fields

**Enhanced States:**
- Default: #E5E9F0
- Placeholder: #9CA3AF (visible but distinct)
- Focus: Pure white with blue border

**Code Changes:** `srcs/Frontend/assets/dark-mode.css:327-347`

## WCAG Compliance

All text now meets or exceeds WCAG 2.1 Level AA standards:
- **Large text (18pt+):** Minimum 3:1 contrast ✓
- **Normal text:** Minimum 4.5:1 contrast ✓
- **Active UI components:** Minimum 3:1 contrast ✓

## Testing Checklist

- [x] Table text is readable in both light and dark backgrounds
- [x] Graph labels and tick marks are clearly visible
- [x] Tab labels are distinguishable in all states
- [x] Metric values stand out from labels
- [x] Dropdown text is readable in all states
- [x] Input field text is visible and clear
- [x] No color-only indicators (all use text/icons)

## Browser Compatibility

Tested and working in:
- Chrome/Edge (Chromium)
- Firefox
- Safari

## Files Modified

1. `srcs/Frontend/assets/dark-mode.css`
   - Enhanced text color variables
   - Table styling improvements
   - Graph text element styling
   - Tab contrast improvements
   - Metric and value styling
   - Dropdown enhancements
   - Input field improvements

2. `srcs/Frontend/graph_config.py`
   - Added `DARK_MODE_COLORS` dictionary
   - Added `DARK_MODE_LAYOUT` configuration
   - Provides proper graph theming for dark mode

## Usage

The improvements are automatically applied when dark mode is active. No additional configuration required.

To use dark mode graph layouts in your code:

```python
from graph_config import DARK_MODE_LAYOUT, ENHANCED_LAYOUT

# Detect theme (implement theme detection logic)
is_dark_mode = detect_dark_mode()

# Apply appropriate layout
layout = DARK_MODE_LAYOUT if is_dark_mode else ENHANCED_LAYOUT

fig.update_layout(**layout)
```

## Future Enhancements

Consider implementing:
1. Automatic theme detection based on system preferences
2. Dynamic graph layout switching on theme toggle
3. Theme preference persistence in localStorage
4. High contrast mode for accessibility

## References

- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- Color Contrast Checker: https://webaim.org/resources/contrastchecker/
- Dark Mode Best Practices: https://web.dev/prefers-color-scheme/
