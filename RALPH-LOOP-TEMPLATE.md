# RALPH-LOOP-TEMPLATE: Iterative AI Development Prompt

> **What is this?** A template for creating living development documents that guide iterative AI coding loops. Copy this file, rename it `RALPH-LOOP.md`, and customize for your project.

---

## How to Use This Template

1. **Copy** this file to your project root as `RALPH-LOOP.md`
2. **Fill in** the project-specific sections (marked with `{{PLACEHOLDER}}`)
3. **Create** your initial state diagram showing all components
4. **Populate** the Immutable section with already-completed work
5. **Prioritize** tasks in the Mutable section
6. **Point** your AI loop at the file with: *"Read RALPH-LOOP.md first. Follow its instructions."*

---

## Instructions for Ralph-Loop

### On Each Iteration:

1. **Read this file first** - Understand current state before taking action
2. **Update the State Diagram** - Mark completed items with `[x]`, in-progress with `[~]`
3. **Update Proven Solutions** - When you solve a hard problem, document it
4. **Update {{PROJECT_GUIDELINES_FILE}}** - When fundamental patterns/behaviors change, update the project guidelines
5. **Check off completed tasks** - Move items from Mutable → Immutable when done
6. **Add discovered unknowns** - Document blockers and new requirements as they emerge

### File Structure Rules:

| Section | Rule |
|---------|------|
| **Immutable** | Progress tracking only - never remove completed items |
| **Mutable** | Active work - update tasks, add/remove as needed |
| **Proven Solutions** | Hard-won knowledge - only add, never remove |
| **Guidelines Updates** | When you change fundamental behavior, update project docs |

---

## Project Overview

> Fill in your project details

**Project:** {{PROJECT_NAME}}

**One-liner:** {{BRIEF_DESCRIPTION}}

**MVP Goal:** {{WHAT_DOES_DONE_LOOK_LIKE}}

**Key Technologies:** {{TECH_STACK}}

**Guidelines File:** {{PROJECT_GUIDELINES_FILE}} (e.g., CLAUDE.md, CONTRIBUTING.md)

---

## Current State Diagram

> Create an ASCII diagram showing your system architecture and component status.
> Use: `[x]` Complete, `[~]` Partial/In-Progress, `[ ]` Not Started

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         {{PROJECT_NAME}} STATE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LAYER 1: {{LAYER_NAME}}                                                    │
│  ════════════════════════                                                    │
│  [x] Component A - description                                               │
│  [~] Component B - description (partial: what's done, what's left)          │
│  [ ] Component C - description                                               │
│                                                                              │
│  LAYER 2: {{LAYER_NAME}}                                                    │
│  ════════════════════════                                                    │
│  [x] Component D - description                                               │
│  [ ] Component E - description                                               │
│                                                                              │
│  DATA FLOW                                                                   │
│  ═════════                                                                   │
│  [x] Source → Processing → Destination                                       │
│  [ ] Additional flow not yet implemented                                     │
│                                                                              │
│  PERSISTENCE                                                                 │
│  ═══════════                                                                 │
│  [ ] Database schema                                                         │
│  [ ] Storage adapter                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

Legend: [x] Complete  [~] Partial/In-Progress  [ ] Not Started
```

---

## Immutable: Completed Work (Progress Updates Only)

> **Rule:** Only add to this section. Never remove items. Mark completion dates.

### {{EPIC_OR_MILESTONE_1}} ✅
- [x] Task A - completed YYYY-MM-DD
- [x] Task B - completed YYYY-MM-DD

### {{EPIC_OR_MILESTONE_2}} ✅
- [x] Task C - completed YYYY-MM-DD

### Infrastructure ✅
- [x] Initial project setup
- [x] CI/CD pipeline (if applicable)

---

## Mutable: Active Tasks (Update as Work Progresses)

> **Rule:** Update freely. Check off completed items, add new discoveries, reprioritize as needed.

### Priority 1: Critical Path (Blocking)

> Tasks that block other work or are essential for MVP

#### P1.1 {{CRITICAL_FEATURE_1}}
- [ ] Subtask A
  - File: `path/to/file.ext:line_number`
  - Requires: Dependencies or prerequisites
  - Test: How to verify it works
- [ ] Subtask B

#### P1.2 {{CRITICAL_FEATURE_2}}
- [ ] Subtask A
- [ ] Subtask B

### Priority 2: Core Features

> Important but not blocking

#### P2.1 {{FEATURE_AREA_1}}
- [ ] Task A
- [ ] Task B

#### P2.2 {{FEATURE_AREA_2}}
- [ ] Task A
- [ ] Task B

### Priority 3: Polish & Enhancement

> Nice-to-have, do after P1 and P2

- [ ] Enhancement A
- [ ] Enhancement B
- [ ] Performance optimization
- [ ] Error handling improvements

### Discovered Unknowns

> Add blockers and new requirements here as they emerge during development

- [ ] **TBD:** {{UNKNOWN_1}} - discovered during {{CONTEXT}}
- [ ] **TBD:** {{UNKNOWN_2}} - needs investigation

---

## Proven Solutions

> **Rule:** When you solve a hard problem, document it here. This is institutional knowledge that prevents re-solving the same problems.

### {{SOLUTION_TITLE_1}}

**Problem:** {{What was the issue?}}

**Solution:**
```{{language}}
{{Code or configuration that solved it}}
```

**Key insight:** {{Why this works / what to remember}}

---

### {{SOLUTION_TITLE_2}}

**Problem:** {{What was the issue?}}

**Solution:** {{Description or code}}

**Key insight:** {{Why this works}}

---

### Template: Add New Solutions

Copy this template when documenting a new solution:

```markdown
### {{Solution Title}}

**Problem:** {{What was the issue?}}

**Solution:**
\`\`\`{{language}}
{{Code or configuration}}
\`\`\`

**Key insight:** {{Why this works / what to remember}}
```

---

## Guidelines Update Triggers

> When these situations occur, update your project guidelines file ({{PROJECT_GUIDELINES_FILE}})

| Trigger | Section to Update |
|---------|-------------------|
| New service/component added | Architecture diagram |
| New communication pattern | Data flow documentation |
| New CLI command or make target | Developer workflow |
| New environment variable | Configuration section |
| New API endpoint pattern | API documentation |
| New testing pattern | Testing guidelines |
| New dependency | Dependencies section |

### Guidelines Update Template

When updating {{PROJECT_GUIDELINES_FILE}}, use this pattern:
```markdown
### [Section Name]

**Change:** [What changed]
**Reason:** [Why it changed]
**Impact:** [What developers need to know]
```

---

## Success Criteria Checklist

> Define what "done" looks like. Update status as criteria are met.

| Criterion | Target | Status |
|-----------|--------|--------|
| {{CRITERION_1}} | {{Measurable target}} | ⬜ |
| {{CRITERION_2}} | {{Measurable target}} | ⬜ |
| {{CRITERION_3}} | {{Measurable target}} | ⬜ |
| {{CRITERION_4}} | {{Measurable target}} | ⬜ |
| {{CRITERION_5}} | {{Measurable target}} | ⬜ |
| All tests pass | `{{test_command}}` succeeds | ⬜ |
| Documentation complete | README updated | ⬜ |

Status legend: ✅ Done | ⬜ Not started | 🔄 In progress

---

## Quick Commands Reference

> Add your project's common commands here

```bash
# Development
{{COMMAND_1}}          # {{Description}}
{{COMMAND_2}}          # {{Description}}

# Testing
{{TEST_COMMAND}}       # {{Description}}

# Build
{{BUILD_COMMAND}}      # {{Description}}

# Other
{{OTHER_COMMAND}}      # {{Description}}
```

---

## Session Log (Optional)

> Track major decisions and progress across sessions

| Date | Session | Key Accomplishments | Next Steps |
|------|---------|---------------------|------------|
| YYYY-MM-DD | Initial | Set up RALPH-LOOP | Begin P1.1 |
| | | | |

---

## Notes for AI Loop Configuration

### Recommended Prompt Prefix

```
Read RALPH-LOOP.md first. Follow its instructions.

Your workflow:
1. Check the Current State Diagram for context
2. Work on the highest-priority uncompleted task in the Mutable section
3. Update the state diagram and task lists as you complete work
4. When you discover new patterns or solve hard problems, add to Proven Solutions
5. When you change fundamental behavior, update both RALPH-LOOP.md and {{PROJECT_GUIDELINES_FILE}}

Focus on: {{CURRENT_FOCUS_AREA}}
```

### Context Files to Include

Always include these files in the AI context:
- `RALPH-LOOP.md` (this file)
- `{{PROJECT_GUIDELINES_FILE}}` (project standards)
- `{{OTHER_IMPORTANT_FILE}}` (if applicable)

---

*Template Version: 1.0*
*Created: 2026-01-07*
