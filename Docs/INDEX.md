# Documentation Index

Welcome to the Server Dashboard Container documentation. All project documentation is organized here by category.

---

## 📁 Documentation Structure

```
Docs/
├── Schema-System/           # Schema-driven architecture
├── Monitoring-Analysis/     # System analysis & monitoring improvements
├── Frontend-Improvements/   # Frontend refactoring documentation
├── Project-Overview/        # Project setup, testing, & troubleshooting
└── generated/              # Auto-generated docs from schema
```

---

## 🚀 Quick Start

**New to the project?** Read in this order:

1. [`../CLAUDE.md`](../CLAUDE.md) - Project overview & development guide
2. [`../README.md`](../README.md) - Getting started & setup
3. [`Project-Overview/AUTO_START.md`](Project-Overview/AUTO_START.md) - Auto-start on boot setup
4. [`Schema-System/SCHEMA_HOWTO.md`](Schema-System/SCHEMA_HOWTO.md) - Daily workflow (if using schema system)

---

## 📚 Documentation Categories

### 1. Schema-Driven System

**Location:** `Docs/Schema-System/`

The schema-driven architecture reduces adding metrics from 10+ files to 1 file!

| Document | Description | When to Use |
|----------|-------------|-------------|
| [SCHEMA_HOWTO.md](Schema-System/SCHEMA_HOWTO.md) | **START HERE** - Daily usage guide | Every time you add a metric |
| [SCHEMA_REFACTORING_SUMMARY.md](Schema-System/SCHEMA_REFACTORING_SUMMARY.md) | Overview & benefits | Understanding the system |
| [SCHEMA_DRIVEN_REFACTORING_PLAN.md](Schema-System/SCHEMA_DRIVEN_REFACTORING_PLAN.md) | Complete technical specification | Deep dive into architecture |
| [SCHEMA_MIGRATION_GUIDE.md](Schema-System/SCHEMA_MIGRATION_GUIDE.md) | Step-by-step migration guide | Integrating with existing code |

**Key Features:**
- ✅ Single YAML schema drives everything
- ✅ Auto-generates SQL, Python, TypeScript, validators, parsers, docs
- ✅ 85% faster metric addition (15-30 min vs 2-4 hours)
- ✅ Zero synchronization bugs

**Quick Command:**
```bash
cd schema/generators
uv run python generate_all.py  # Generate all code from schema
```

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

Frontend refactoring documentation, improvements, and implementation details.

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
- **Mobile Responsiveness** - 320px-4K support, touch optimization, adaptive layouts
- **Dark Mode** - Complete implementation with high-contrast themes
- **Accessibility** - Focus states, ARIA labels, keyboard navigation
- **Component Enhancements** - Tables, cards, graphs with modern design
- **KU Brand Compliance** - Typography, colors, guidelines
- **Code Quality** - Error handling, validation, testing (103 tests)

---

### 4. Project Overview

**Location:** `Docs/Project-Overview/`

Project setup, testing, troubleshooting, and general reference documentation.

| Document | Description | Use Case |
|----------|-------------|----------|
| [QUICK_REFERENCE.md](Project-Overview/QUICK_REFERENCE.md) | Quick commands & tips | Daily reference |
| [AUTO_START.md](Project-Overview/AUTO_START.md) | **✨ CONSOLIDATED** Auto-start configuration | Setting up production auto-start |
| [TROUBLESHOOTING.md](Project-Overview/TROUBLESHOOTING.md) | **✨ NEW** Common issues & solutions | When things go wrong |
| [TESTING_CHECKLIST.md](Project-Overview/TESTING_CHECKLIST.md) | Pre-deployment testing | Before releases |
| [UV_MIGRATION_FIXES_APPLIED.md](Project-Overview/UV_MIGRATION_FIXES_APPLIED.md) | UV migration changes | Understanding UV setup |
| [UV_MIGRATION_TODO.md](Project-Overview/UV_MIGRATION_TODO.md) | UV migration TODOs | Pending tasks |
| [REVIEW_SUMMARY.md](Project-Overview/REVIEW_SUMMARY.md) | Code review summary | Quality checks |

**Also See:**
- [`../CLAUDE.md`](../CLAUDE.md) - Main project guide (in root)
- [`../README.md`](../README.md) - Project README (in root)

---

### 5. Generated Documentation

**Location:** `Docs/generated/`

Auto-generated documentation from schema (updated when you run `generate_all.py`).

| Document | Description | Auto-Updated |
|----------|-------------|--------------|
| [DATABASE_SCHEMA.md](generated/DATABASE_SCHEMA.md) | Database tables & columns | ✅ Yes |
| [API_DOCUMENTATION.md](generated/API_DOCUMENTATION.md) | API endpoints reference | ✅ Yes |
| [QUICK_REFERENCE.md](generated/QUICK_REFERENCE.md) | Field formats & validation | ✅ Yes |

**Note:** These files are auto-generated. Do not edit manually!

---

## 🎯 Common Tasks

### I want to add a new metric
→ Read: [`Schema-System/SCHEMA_HOWTO.md`](Schema-System/SCHEMA_HOWTO.md)

### I want to understand the architecture
→ Read: [`Monitoring-Analysis/ARCHITECTURE_VISUAL.md`](Monitoring-Analysis/ARCHITECTURE_VISUAL.md)

### I want to improve the frontend
→ Read: [`Frontend-Improvements/FRONTEND_IMPROVEMENT_PLAN.md`](Frontend-Improvements/FRONTEND_IMPROVEMENT_PLAN.md)

### Something's not working
→ Read: [`Project-Overview/TROUBLESHOOTING.md`](Project-Overview/TROUBLESHOOTING.md)

### I want quick reference commands
→ Read: [`Project-Overview/QUICK_REFERENCE.md`](Project-Overview/QUICK_REFERENCE.md)

### I want to set up auto-start
→ Read: [`Project-Overview/AUTO_START.md`](Project-Overview/AUTO_START.md)

### I want to migrate to schema-driven system
→ Read: [`Schema-System/SCHEMA_MIGRATION_GUIDE.md`](Schema-System/SCHEMA_MIGRATION_GUIDE.md)

### I want to test before deployment
→ Read: [`Project-Overview/TESTING_CHECKLIST.md`](Project-Overview/TESTING_CHECKLIST.md)

### Dark mode issues
→ Read: [`Frontend-Improvements/DARK_MODE_COMPLETE.md`](Frontend-Improvements/DARK_MODE_COMPLETE.md)

---

## 📊 Document Statistics

| Category | Documents | Status |
|----------|-----------|--------|
| Schema System | 4 files | ✅ Organized |
| Monitoring Analysis | 7 files | ✅ Organized |
| Frontend Improvements | 11 files | ✅ Consolidated (was 14) |
| Project Overview | 7 files | ✅ Enhanced |
| Generated (Auto) | 3 files | ✅ Auto-updated |
| **Total** | **32 files** | **✅ Clean & Organized** |

---

## 🔄 Recent Changes

**2025-12-04 - Documentation Consolidation:**
- ✅ Consolidated 6 dark mode docs → 1 comprehensive guide
- ✅ Merged auto-start docs → single unified guide
- ✅ Created new TROUBLESHOOTING.md with all common issues
- ✅ Removed 11 temporary/duplicate files
- ✅ Reorganized Frontend-Improvements folder
- ✅ Updated this index with clearer navigation

**Removed Files (Consolidated):**
- `DARK_MODE_CONTRAST_SUMMARY.md` → merged into `DARK_MODE_COMPLETE.md`
- `DARK_MODE_FIXES_SUMMARY.md` → merged into `DARK_MODE_COMPLETE.md`
- `DARK_MODE_FIX_COMPLETE.md` → merged into `DARK_MODE_COMPLETE.md`
- `DARK_MODE_QUICK_REF.md` → merged into `DARK_MODE_COMPLETE.md`
- `GRAPH_DARK_MODE_FIX.md` → merged into `DARK_MODE_COMPLETE.md`
- `FINAL_GRAPH_FIX.md` → merged into `DARK_MODE_COMPLETE.md`
- `AUTO_START_GUIDE.md` → moved to `Project-Overview/AUTO_START.md`
- `AUTOSTART_QUICK_REFERENCE.md` → merged into `AUTO_START.md`
- `PORT_CONFLICT_SOLUTION.md` → merged into `TROUBLESHOOTING.md`
- `PERFORMANCE_FIX_FINAL.md` → merged into `TROUBLESHOOTING.md`
- `ORGANIZATION_SUMMARY.md` → no longer needed
- `QUICK_START_NEW_FEATURES.md` → redundant with UI_UX_ENHANCEMENTS_SUMMARY
- `MINIMAL_IMPROVEMENTS.md` → outdated, covered by other docs
- `IMPLEMENTATION_COMPLETE_SUMMARY.md` → merged into FRONTEND_IMPROVEMENTS_SUMMARY

---

## 🔄 Maintenance

### Updating Documentation

- **Schema docs** - Auto-updated when running `generate_all.py`
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
4. Review generated docs for latest API/schema info
5. Check specific category for detailed guides

---

**Last Updated:** 2025-12-04
**Documentation Version:** 2.0 (Consolidated)
**Project:** Server Dashboard Container
