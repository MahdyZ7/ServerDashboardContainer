# Documentation Index

Welcome to the Server Dashboard Container documentation. All project documentation is organized here by category.

---

## 📁 Documentation Structure

```
Docs/
├── Schema-System/           # Schema-driven architecture (NEW!)
├── Monitoring-Analysis/     # System analysis & monitoring improvements
├── Frontend-Improvements/   # Frontend refactoring documentation
├── Project-Overview/        # Project setup & references
└── generated/              # Auto-generated docs from schema
```

---

## 🚀 Quick Start

**New to the project?** Read in this order:

1. [`../CLAUDE.md`](../CLAUDE.md) - Project overview & development guide
2. [`../README.md`](../README.md) - Getting started & setup
3. [`Schema-System/SCHEMA_HOWTO.md`](Schema-System/SCHEMA_HOWTO.md) - Daily workflow (if using schema system)

---

## 📚 Documentation Categories

### 1. Schema-Driven System (NEW!)

**Location:** `Docs/Schema-System/`

The new schema-driven architecture that reduces adding metrics from 10+ files to 1 file!

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
| [data_flow_analysis.md](Monitoring-Analysis/data_flow_analysis.md) | Complete data flow analysis (77KB!) | Deep system understanding |
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
| [FRONTEND_IMPROVEMENT_PLAN.md](Frontend-Improvements/FRONTEND_IMPROVEMENT_PLAN.md) | Comprehensive improvement roadmap | Planning frontend work |
| [FRONTEND_IMPROVEMENTS_SUMMARY.md](Frontend-Improvements/FRONTEND_IMPROVEMENTS_SUMMARY.md) | Implementation details & metrics | Reviewing changes |
| [IMPLEMENTATION_COMPLETE_SUMMARY.md](Frontend-Improvements/IMPLEMENTATION_COMPLETE_SUMMARY.md) | Completion summary | What was done |
| [MINIMAL_IMPROVEMENTS.md](Frontend-Improvements/MINIMAL_IMPROVEMENTS.md) | Quick improvements guide | Fast wins |

**Topics Covered:**
- Error handling & toast notifications
- Safe DataFrame operations
- Input validation
- Component modularity
- Testing infrastructure (103 tests)

---

### 4. Project Overview

**Location:** `Docs/Project-Overview/`

Project setup, testing, and general reference documentation.

| Document | Description | Use Case |
|----------|-------------|----------|
| [QUICK_REFERENCE.md](Project-Overview/QUICK_REFERENCE.md) | Quick commands & tips | Daily reference |
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

### I want quick reference commands
→ Read: [`Project-Overview/QUICK_REFERENCE.md`](Project-Overview/QUICK_REFERENCE.md)

### I want to migrate to schema-driven system
→ Read: [`Schema-System/SCHEMA_MIGRATION_GUIDE.md`](Schema-System/SCHEMA_MIGRATION_GUIDE.md)

### I want to test before deployment
→ Read: [`Project-Overview/TESTING_CHECKLIST.md`](Project-Overview/TESTING_CHECKLIST.md)

---

## 📊 Document Statistics

| Category | Documents | Total Size |
|----------|-----------|------------|
| Schema System | 4 files | ~150 KB |
| Monitoring Analysis | 7 files | ~210 KB |
| Frontend Improvements | 4 files | ~100 KB |
| Project Overview | 5 files | ~50 KB |
| Generated (Auto) | 3 files | ~20 KB |
| **Total** | **23 files** | **~530 KB** |

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
4. Update category statistics

---

## 🆘 Need Help?

1. Check this index for relevant documentation
2. Read [`../CLAUDE.md`](../CLAUDE.md) for project context
3. Review generated docs for latest API/schema info
4. Check specific category for detailed guides

---

**Last Updated:** 2025-11-05
**Documentation Version:** 1.0
**Project:** Server Dashboard Container
