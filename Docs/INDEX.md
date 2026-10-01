# Documentation Index

Welcome to the Server Dashboard Container documentation. This index reflects the current repository layout reviewed on 2026-05-04.

## Current Runtime

The active Docker Compose stack has three services:

| Service | Container | Source |
| --- | --- | --- |
| `postgres` | `postgres` | `docker-compose.yml` |
| `datacollection` | `DataCollection` | `srcs/DataCollection/` |
| `dashboard` | `Dashboard` | `srcs/Backend/` |

There is no active Nginx service and no active `srcs/Frontend/` Dash app in the current directory. The dashboard is a unified Flask app with Jinja templates, static CSS/JS, and Chart.js.

## Documentation Structure

```
Docs/
├── Schema-System/           # Superseded schema-driven plan (history)
├── Monitoring-Analysis/     # System analysis & monitoring improvements
├── Frontend-Improvements/   # Frontend refactoring documentation
├── Project-Overview/        # Project setup, testing, & troubleshooting
```

## 🚀 Quick Start

**New to the project?** Read in this order:

1. [`../CLAUDE.md`](../CLAUDE.md) - Project overview & development guide
2. [`../README.md`](../README.md) - Getting started & setup
3. [`Project-Overview/CODE_REVIEW_FIX_PLAN.md`](Project-Overview/CODE_REVIEW_FIX_PLAN.md) - Current prioritized fix plan
4. [`Project-Overview/AUTO_START.md`](Project-Overview/AUTO_START.md) - Auto-start on boot setup

## 📚 Documentation Categories

### 1. Schema-Driven System (superseded)

**Location:** `Docs/Schema-System/` — kept for history only.

The YAML schema and its generators were removed on 2026-10-01: nothing used them at
runtime and they had drifted from the real tables. Tables and migrations are defined in
`init_db()` in `srcs/DataCollection/backend.py`; the collector review and fix status are in
`srcs/DataCollection/REVIEW.md`.

---

### 2. Monitoring & Analysis

**Location:** `Docs/Monitoring-Analysis/`

System analysis, architecture documentation, and monitoring improvements.

| Document | Description | Use Case |
|----------|-------------|----------|
| [MONITORING_IMPROVEMENTS.md](Monitoring-Analysis/MONITORING_IMPROVEMENTS.md) | 15 new metrics to add + integration guide | Planning improvements |
| [ARCHITECTURE_VISUAL.md](Monitoring-Analysis/ARCHITECTURE_VISUAL.md) | Visual system diagrams & data flow | Understanding architecture |
| [data_flow_analysis.md](Monitoring-Analysis/data_flow_analysis.md) | Complete data flow analysis (77KB) | Deep system understanding |
| [BASH_SCRIPTS_CODE_REVIEW.md](Monitoring-Analysis/BASH_SCRIPTS_CODE_REVIEW.md) | Bash scripts code review | Reviewing monitoring scripts |
| [ANALYSIS_INDEX.md](Monitoring-Analysis/ANALYSIS_INDEX.md) | Quick lookup guide | Finding specific info |
| [ABSOLUTE_FILE_PATHS.md](Monitoring-Analysis/ABSOLUTE_FILE_PATHS.md) | Code locations reference | Locating code |
| [SUMMARY.md](Monitoring-Analysis/SUMMARY.md) | Quick reference summary | Overview |

**What's Inside:**
- Current system analysis (19 metrics tracked)
- Proposed improvements (swap, network I/O, GPU, security)
- Data flow through 9 layers
- Field-by-field breakdown

---

### 3. Frontend Improvements

**Location:** `Docs/Frontend-Improvements/`

Frontend refactoring documentation, improvements, and implementation details for the current Flask/Jinja/static JS dashboard.

| Document | Description | Use Case |
|----------|-------------|----------|
| [UI_UX_ENHANCEMENT_PLAN.md](Frontend-Improvements/UI_UX_ENHANCEMENT_PLAN.md) | Comprehensive UI/UX enhancement plan | Complete enhancement roadmap |
| [UI_UX_ENHANCEMENTS_SUMMARY.md](Frontend-Improvements/UI_UX_ENHANCEMENTS_SUMMARY.md) | Phase 1 implementation summary | What was implemented & how to use |
| [DARK_MODE_COMPLETE.md](Frontend-Improvements/DARK_MODE_COMPLETE.md) | **✨ CONSOLIDATED** Complete dark mode guide | Dark mode implementation & troubleshooting |
| [DARK_MODE_CONTRAST_FIX.md](Frontend-Improvements/DARK_MODE_CONTRAST_FIX.md) | Dark mode contrast fixes | Specific contrast improvements |
| [MOBILE_RESPONSIVE_ENHANCEMENTS.md](Frontend-Improvements/MOBILE_RESPONSIVE_ENHANCEMENTS.md) | Complete mobile responsiveness & touch UX | Mobile optimization reference |
| [TABLE_CARD_ENHANCEMENTS.md](Frontend-Improvements/TABLE_CARD_ENHANCEMENTS.md) | Table/Card UI polish & modern design | Table & card enhancement reference |
| [GRAPH_UX_ENHANCEMENTS.md](Frontend-Improvements/GRAPH_UX_ENHANCEMENTS.md) | Graph UX/UI polish & interactivity | Graph enhancement reference |
| [BRAND_COMPLIANCE_UPDATE.md](Frontend-Improvements/BRAND_COMPLIANCE_UPDATE.md) | KU Brand Guidelines compliance | Brand compliance review |
| [INTER_VS_DIN_NEXT.md](Frontend-Improvements/INTER_VS_DIN_NEXT.md) | Font comparison & justification | Font selection reference |
| [FRONTEND_IMPROVEMENT_PLAN.md](Frontend-Improvements/FRONTEND_IMPROVEMENT_PLAN.md) | Comprehensive improvement roadmap | Planning frontend work |
| [FRONTEND_IMPROVEMENTS_SUMMARY.md](Frontend-Improvements/FRONTEND_IMPROVEMENTS_SUMMARY.md) | Implementation details & metrics | Reviewing changes |

**Topics Covered:**
- **UI/UX Enhancements** - Loading states, dark mode, micro-interactions, animations
- **Mobile Responsiveness** - Touch optimization and adaptive layouts
- **Dark Mode** - Implementation with high-contrast themes
- **Accessibility** - Focus states, ARIA labels, keyboard navigation
- **Component Enhancements** - Tables, cards, graphs with modern design
- **KU Brand Compliance** - Typography, colors, guidelines
- **Code Quality** - Error handling, validation, and planned tests

---

### 4. Project Overview

**Location:** `Docs/Project-Overview/`

Project setup, testing, troubleshooting, and general reference documentation.

| Document | Description | Use Case |
|----------|-------------|----------|
| [CODE_REVIEW_FIX_PLAN.md](Project-Overview/CODE_REVIEW_FIX_PLAN.md) | Prioritized remediation plan from current code review | Planning fixes |
| [QUICK_REFERENCE.md](Project-Overview/QUICK_REFERENCE.md) | Quick commands & tips | Daily reference |
| [AUTO_START.md](Project-Overview/AUTO_START.md) | **✨ CONSOLIDATED** Auto-start configuration | Setting up production auto-start |
| [TROUBLESHOOTING.md](Project-Overview/TROUBLESHOOTING.md) | **✨ NEW** Common issues & solutions | When things go wrong |
| [SSH_KEY_MIGRATION.md](Project-Overview/SSH_KEY_MIGRATION.md) | **📋 PLANNED** SSH key auth migration + user tutorial | Replacing password auth with SSH keys |
| [TESTING_CHECKLIST.md](Project-Overview/TESTING_CHECKLIST.md) | Pre-deployment testing | Before releases |
| [UV_MIGRATION_FIXES_APPLIED.md](Project-Overview/UV_MIGRATION_FIXES_APPLIED.md) | UV migration changes | Understanding UV setup |
| [UV_MIGRATION_TODO.md](Project-Overview/UV_MIGRATION_TODO.md) | UV migration TODOs | Pending tasks |
| [REVIEW_SUMMARY.md](Project-Overview/REVIEW_SUMMARY.md) | Code review summary | Quality checks |

**Also See:**
- [`../CLAUDE.md`](../CLAUDE.md) - Main project guide (in root)
- [`../README.md`](../README.md) - Project README (in root)

---

## 🎯 Common Tasks

### I want to add a new metric
→ Read: [`Schema-System/SCHEMA_HOWTO.md`](Schema-System/SCHEMA_HOWTO.md)

### I want to understand the architecture
→ Read: [`Monitoring-Analysis/ARCHITECTURE_VISUAL.md`](Monitoring-Analysis/ARCHITECTURE_VISUAL.md)

### I want to improve the frontend
→ Read: [`Frontend-Improvements/FRONTEND_IMPROVEMENT_PLAN.md`](Frontend-Improvements/FRONTEND_IMPROVEMENT_PLAN.md)

### I want to fix the reviewed issues
→ Read: [`Project-Overview/CODE_REVIEW_FIX_PLAN.md`](Project-Overview/CODE_REVIEW_FIX_PLAN.md)

### Something's not working
→ Read: [`Project-Overview/TROUBLESHOOTING.md`](Project-Overview/TROUBLESHOOTING.md)

### I want quick reference commands
→ Read: [`Project-Overview/QUICK_REFERENCE.md`](Project-Overview/QUICK_REFERENCE.md)

### I want to set up auto-start
→ Read: [`Project-Overview/AUTO_START.md`](Project-Overview/AUTO_START.md)

### I want to test before deployment
→ Read: [`Project-Overview/TESTING_CHECKLIST.md`](Project-Overview/TESTING_CHECKLIST.md)

### Dark mode issues
→ Read: [`Frontend-Improvements/DARK_MODE_COMPLETE.md`](Frontend-Improvements/DARK_MODE_COMPLETE.md)

---

## Document Status

| Category | Status |
|----------|--------|
| Root README | Updated to current three-service Flask stack |
| Project Overview | Contains setup, troubleshooting, auto-start, SSH migration, and current fix plan |
| Frontend Improvements | Historical and current UI/UX references for Flask static dashboard |
| Schema System | Superseded; generator and generated docs removed (2026-10-01) |

## Recent Changes

**2026-05-04 - Current-state documentation update:**
- Added `Project-Overview/CODE_REVIEW_FIX_PLAN.md`.
- Updated the root README to describe the active Flask/PostgreSQL/DataCollection stack.
- Updated this index to remove claims about active Nginx, Dash, separate frontend containers, and missing tests.

---

## 🔄 Maintenance

### Updating Documentation

- **Manual docs** - Update as features change
- **This index** - Update when adding new categories

### Adding New Documentation

1. Create markdown file in appropriate category folder
2. Add entry to this index
3. Link from related documents
4. Keep naming consistent (UPPERCASE_WITH_UNDERSCORES.md)

### Documentation Guidelines

- **Be concise** - Remove redundant information
- **Cross-reference** - Link to related docs
- **Consolidate** - Merge similar documents when appropriate
- **Date updates** - Include last updated date in docs
- **Remove temporary docs** - Don't keep single-use process documents

---

## 🆘 Need Help?

1. Check this index for relevant documentation
2. Read [`../CLAUDE.md`](../CLAUDE.md) for project context
3. Check [`Project-Overview/TROUBLESHOOTING.md`](Project-Overview/TROUBLESHOOTING.md) for common issues
4. Check specific category for detailed guides

---

**Last Updated:** 2026-05-04
**Documentation Version:** 2.1 (Current Runtime)
**Project:** Server Dashboard Container
