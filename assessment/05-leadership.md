# Phase 5: Leadership — Collaboration, Decision Logs & Process Templates

**Date:** 2026-06-30
**Skills applied:** cross-functional-collaboration, stakeholder-management, articulating-design-decisions, mentoring-coaching, design-team-leadership

---

## 1. Creative ↔ Builder ↔ Coach Collaboration Workflow

The ALLSTARS agent system (Creative, Builder, Coach) needs a defined handoff process so decisions are traceable and work is not duplicated.

### Handoff Flow

```
┌─────────────┐     Design Spec     ┌─────────────┐     QA Review     ┌─────────────┐
│             │ ──────────────────► │             │ ────────────────► │             │
│  Creative   │                     │   Builder   │                   │   Coach     │
│  (Design)   │ ◄────────────────── │   (Code)    │ ◄──────────────── │   (Review)  │
│             │     UX Feedback     │             │     Bug Report    │             │
└─────────────┘                     └─────────────┘                   └─────────────┘
       │                                   │                                │
       │           Decision Log            │                                │
       └───────────────────────────────────┴────────────────────────────────┘
                    (tracked in kanban comments)
```

### Phase 1: Creative → Builder Handoff

**Trigger:** Creative completes design spec for a feature/fix

**Deliverables:**
- Design spec document (this assessment framework)
- UI mockups or wireframes (as needed)
- UX copy for all new/changed strings
- Token/component naming if new patterns are introduced
- Accessibility checklist completed for the feature

**Handoff Checklist:**
- [ ] Design rationale documented (what changed, why, what evidence)
- [ ] All states specified (default, hover, focus, active, error, disabled, loading, empty)
- [ ] Responsive breakpoints specified (390px, 768px, 1280px, 1920px)
- [ ] Accessibility: skip-to-content, keyboard nav, focus-visible, aria labels, contrast
- [ ] Dark mode variants specified
- [ ] Design tokens used (no hardcoded values)
- [ ] UX copy reviewed (labels, errors, empty states, microcopy)

### Phase 2: Builder → Coach Handoff

**Trigger:** Builder completes implementation

**Deliverables:**
- Working code on a branch
- Tests passing
- Link to preview

**QA Checklist:**
- [ ] Matches design spec visually (pixel-level diff)
- [ ] All states functional (hover, focus, error, loading)
- [ ] Responsive: works at 390px, 768px, 1280px, 1920px
- [ ] Dark mode renders correctly
- [ ] Keyboard navigable (Tab, Enter, Escape, Arrow keys)
- [ ] Screen reader announces all dynamic changes
- [ ] Touch targets ≥ 44×44px on mobile
- [ ] No console errors
- [ ] Design tokens used (no hardcoded values)

### Phase 3: Coach → Creative Feedback Loop

**Trigger:** Coach identifies issues

**Format:** `kanban_comment` with structured feedback

**Feedback template:**
```
## QA Review — [Feature Name]
**Date:** YYYY-MM-DD
**Severity level per issue**

### 🔴 Blocker (must fix before merge)
- [ ] Issue description | Location | Expected behaviour

### 🟠 Major (fix this sprint)
- [ ] Issue description | Location | Expected behaviour

### 🟢 Minor (fix when convenient)
- [ ] Issue description | Location | Expected behaviour
```

---

## 2. Design Decision Log Template

Every design change should be logged so decisions are traceable and not re-litigated. Use this template in `kanban_comment` or a shared decision log.

```markdown
## Design Decision — [ID]

**Date:** YYYY-MM-DD
**Author:** [Creative / Builder / Coach]
**Area:** [e.g. Email page, Pipeline sidebar, Settings layout]

### Context
What problem are we solving? What user need or evidence drives this?

### Decision
What did we decide to do?

### Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|-------------|
| Option A | ... | ... | ... |
| Option B | ... | ... | ✓ Selected |

### Evidence
- User research: [link or summary]
- Analytics: [metric before/after]
- Heuristic: [which heuristic, severity]
- Accessibility: [WCAG criterion addressed]

### Impact
- Files changed: [list]
- Design system: [new tokens, new components]
- Tests needed: [yes/no, which]
- Risks: [regression risk, dependencies]

### Approval
- [ ] Creative sign-off
- [ ] Builder sign-off
- [ ] Coach sign-off
```

---

## 3. Stakeholder Comms Template

For leadership updates, use this concise template:

```markdown
## Design Update — [Week/Month]

### What we shipped
- [Item] — [one-line impact, e.g. "Email page crash fixed — 25% of app now usable"]
- [Item] — [impact]
- [Item] — [impact]

### What we're working on
- [Item] — [ETA, e.g. "Next week"]
- [Item] — [ETA]

### Key metrics
| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Sidebar link reliability | 75% | [new value] | 100% |
| Email page error rate | 100% | [new value] | 0% |
| Deal creation rate | 0% | [new value] | 30% |

### Blockers
- [Blocker] — [what we need from leadership]

### Next steps
- [Item] — [owner, date]
- [Item] — [owner, date]
```

---

## 4. Design Review Process

### When to Review
- Every new page or major component
- Every significant redesign of an existing component
- Every change that introduces new design tokens
- Every change that affects keyboard navigation or screen reader behaviour

### Review Cadence

| Type | Participants | Duration | Frequency |
|------|-------------|----------|-----------|
| **Design critique** | Creative + Builder + Coach | 30 min | Weekly |
| **Stakeholder review** | Creative + Product + Leadership | 30 min | Bi-weekly |
| **Sprint demo** | All | 15 min | Per sprint |

### Remote Collaboration Guidelines

1. **Design specs** are written in markdown, stored in `assessment/` or `design-docs/`
2. **Mockups** are added as images to `assessment/images/` or linked from the spec
3. **All feedback** is tracked as kanban comments on the relevant task card
4. **Decisions** are logged using the Decision Log template above
5. **Every handoff** includes the checklist from Section 1

---

## 5. Design Competency Framework (for mentoring)

As the design function grows, these competencies define what "good" looks like at each level:

| Competency | Junior | Mid | Senior | Lead |
|------------|--------|-----|--------|------|
| **Craft** | Can build components from system tokens | Designs new patterns within existing system | Creates new system patterns | Sets system direction |
| **User research** | Conducts supervised tests | Plans and runs studies independently | Synthesises multi-study insights | Sets research strategy |
| **Accessibility** | Follows checklists | Identifies gaps proactively | Advocates and trains others | Sets a11y standards |
| **Cross-functional** | Takes feedback well | Runs design critiques | Facilitates workshops | Aligns multiple teams |
| **Business impact** | Ships on time | Prioritises user vs business needs | Ties design to metrics | Drives outcomes |

---

## 6. Onboarding a New Designer (Template)

```
## Designer Onboarding — [Name]

### Week 1
- [ ] Read project README.md
- [ ] Set up dev environment (frontend + backend)
- [ ] Browse all app screens (note: some crash currently)
- [ ] Read existing audit (ui-ux-pro-max-audit.md)
- [ ] Read complete assessment suite (assessment/)
- [ ] Review component library (frontend/src/components/)

### Week 2
- [ ] Fix two minor UX issues from the audit
- [ ] Attend design critique session
- [ ] Run one usability test session
- [ ] Understand Creative ↔ Builder ↔ Coach workflow

### Week 3
- [ ] Lead design for one new feature/fix
- [ ] Document design decisions in decision log
- [ ] Present to stakeholder review
```

---

## 7. Running Effective Design Critiques

### Format (30 min)

| Time | Activity | Facilitator |
|------|----------|-------------|
| 0-3 min | Context: what are we reviewing, what stage, what decisions are needed | Designer |
| 3-10 min | Walkthrough: designer shows work and explains rationale | Designer |
| 10-25 min | Feedback: structured, goal-based, aimed at work not person | All |
| 25-30 min | Summary: what's happening next, action items captured | Facilitator |

### Rules
1. Feedback must start with the design goal, not personal preference
2. "I don't like it" → reframe as "This doesn't achieve [goal] because..."
3. All feedback goes in the kanban comment thread
4. Designer closes the loop: what changed, what didn't, and why

---

## 8. Accessibility Standards Document

### Mandatory Checks (Every PR)

- [ ] Semantic HTML: nav, main, aside, h1-h6, button, form
- [ ] All interactive elements keyboard-operable
- [ ] `focus-visible` ring on all interactive elements
- [ ] `aria-label` on icon-only buttons
- [ ] `aria-current="page"` on active nav
- [ ] `aria-expanded` on expandable elements
- [ ] `role="alert"` on dynamic error messages
- [ ] `aria-invalid` on inputs with errors
- [ ] `htmlFor`/`id` on all label-input pairs
- [ ] Color contrast ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- [ ] Touch targets ≥ 44×44px
- [ ] `prefers-reduced-motion` respected
- [ ] Skip-to-content link as first focusable element
- [ ] Error boundary wraps the page

### Tools
- axe DevTools (browser extension)
- Lighthouse Accessibility audit
- WAVE browser extension
- Screen reader: VoiceOver (macOS) or NVDA (Windows)
- Colour contrast analyser

---

## 9. Decision Log — This Assessment

| ID | Date | Decision | Author | Rationale |
|----|------|----------|--------|-----------|
| D001 | 2026-06-30 | Email crash fix is P0 priority | Creative | Blocks 25% of app; heuristic H1/H9 severity 4 |
| D002 | 2026-06-30 | Fix sidebar 404s before building new pages | Creative | 3 sidebar links broken; IA issue |
| D003 | 2026-06-30 | Add error boundaries before any new features | Creative | Prevents user-facing stack traces |
| D004 | 2026-06-30 | Use existing Modal component for confirmation dialogs | Creative | Modal already has focus trap, aria, Escape pattern |
| D005 | 2026-06-30 | Seed demo data in Sprint 2 after crash fixes | Creative | First-value experience requires populated data |
| D006 | 2026-06-30 | Instrument analytics in Sprint 3 | Creative | Need baseline metrics before any A/B testing |
| D007 | 2026-06-30 | Skip-to-content is P0 accessibility fix | Creative | WCAG 2.4.1 Bypass Blocks (A) — keyboard-first navigation |
| D008 | 2026-06-30 | Remove `/timeline` duplicate route | Creative | Same component as `/activities` — confuses IA |
| D009 | 2026-06-30 | Move Slack/Users/Audit Log to Settings sub-nav | Creative | Primary sidebar should not contain admin links |
| D010 | 2026-06-30 | Dark mode tokens need consolidation | Creative | Inconsistent use of `--dark-*` vs inline `dark:` variants |