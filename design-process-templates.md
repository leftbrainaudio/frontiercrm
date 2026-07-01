# FrontierCRM — Design Process Templates

**Date:** 2026-06-30
**Author:** Creative (ALLSTARS Design & Brand Lead)

---

## Table of Contents

1. [Design Critique Checklist (for Builder self-review before PR)](#1-design-critique-checklist)
2. [Design Decision Log (ADR for UX)](#2-design-decision-log-template)
3. [Stakeholder Communication Template](#3-stakeholder-communication-template)
4. [Cross-Functional Collaboration Workflow](#4-cross-functional-collaboration-workflow)

---

## 1. Design Critique Checklist

### Purpose

A lightweight self-review checklist for Builder (or any non-design contributor) to run before opening a PR, so the design review catches structural issues, not pixel-level nits. Use this BEFORE requesting a review from Creative.

### Instructions

For each UI change, go through the checklist items. If any item is marked **FAIL**, fix it before requesting review. If the item is **N/A**, explain why in a comment.

### Checklist

```
## Design Critique — Pre-PR Self-Review

**Feature/Patch:** __________________________________
**Reviewer (Builder):** _____________________________
**Date:** __________________________________________

### 1. Layout & Spacing
- [ ] PASS / FAIL / N/A — Layout uses the 4px spacing scale (Tailwind: p-1, p-2, p-3, p-4, p-5, p-6, p-8)
- [ ] PASS / FAIL / N/A — Content area uses correct responsive padding:
  - mobile:  p-4
  - tablet:  sm:p-6
  - desktop: lg:p-8
- [ ] PASS / FAIL / N/A — No horizontal overflow at 390px, 768px, or 1280px viewport
- [ ] PASS / FAIL / N/A — Elements align to a consistent grid/gutter (no arbitrary `left: 37px`)

### 2. Typography
- [ ] PASS / FAIL / N/A — Body text uses Inter font (via `font-sans` class)
- [ ] PASS / FAIL / N/A — Heading hierarchy respects spec: H1=28px, H2=24px, H3=20px, H4=16px
- [ ] PASS / FAIL / N/A — Body text is 14px default, labels are 14px, small text is 12px
- [ ] PASS / FAIL / N/A — Line-height: body=1.5, headings=1.25
- [ ] PASS / FAIL / N/A — No text overflow or truncation without `...` indicator

### 3. Color & Tokens
- [ ] PASS / FAIL / N/A — Colors use theme tokens, not hardcoded hex values
  - INCORRECT: `text-[#3b82f6]` → CORRECT: `text-brand-500`
  - INCORRECT: `bg-[#f8fafc]` → CORRECT: `bg-surface`
- [ ] PASS / FAIL / N/A — Dark mode variant exists for every color token
- [ ] PASS / FAIL / N/A — Text contrast ≥ 4.5:1 for body text, ≥ 3:1 for large text (18px+ bold)
- [ ] PASS / FAIL / N/A — Error states use `red-500`/`red-600`; success uses `emerald-500`/`emerald-600`

### 4. Interactive Elements
- [ ] PASS / FAIL / N/A — Every interactive element has `focus-visible` ring style
  - Format: `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2`
- [ ] PASS / FAIL / N/A — All buttons use the shared Button component (or explain why custom)
- [ ] PASS / FAIL / N/A — All inputs use the shared Input component
- [ ] PASS / FAIL / N/A — Touch targets ≥ 44×44 CSS pixels on mobile (390px viewport)
- [ ] PASS / FAIL / N/A — Hover states exist on all clickable elements
- [ ] PASS / FAIL / N/A — Disabled states have `opacity-50` + `cursor-not-allowed`
- [ ] PASS / FAIL / N/A — Loading states show spinner (or skeleton) — no blank area

### 5. Accessibility
- [ ] PASS / FAIL / N/A — All images have meaningful `alt` text (or `role="presentation"` if decorative)
- [ ] PASS / FAIL / N/A — All form inputs have associated `<label>` (via `htmlFor`/`id`)
- [ ] PASS / FAIL / N/A — Error messages use `role="alert"` and inputs use `aria-invalid={true}`
- [ ] PASS / FAIL / N/A — Semantic HTML: `<nav>`, `<main>`, `<h1>`–`<h4>`, `<button>`, `<form>`
- [ ] PASS / FAIL / N/A — Modal dialogs: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- [ ] PASS / FAIL / N/A — Tab order is logical (no tabindex > 0)
- [ ] PASS / FAIL / N/A — `aria-current="page"` on active nav items
- [ ] PASS / FAIL / N/A — `prefers-reduced-motion` respected (no animations when reduced)

### 6. Responsive
- [ ] PASS / FAIL / N/A — Layout works at 390px (mobile)
- [ ] PASS / FAIL / N/A — Layout works at 768px (tablet)
- [ ] PASS / FAIL / N/A — Layout works at 1280px+ (desktop)
- [ ] PASS / FAIL / N/A — Tables have horizontal scroll on mobile (no overflow hidden cropping data)
- [ ] PASS / FAIL / N/A — Sidebar/collapse behaviour matches spec breakpoints

### 7. States
- [ ] PASS / FAIL / N/A — Loading state: skeleton or spinner shown
- [ ] PASS / FAIL / N/A — Empty state: contextual message + CTA (not just "No data")
- [ ] PASS / FAIL / N/A — Error state: user-friendly message + retry action
- [ ] PASS / FAIL / N/A — Success state: toast or confirmation message

### 8. Design System Compliance
- [ ] PASS / FAIL / N/A — Uses existing components where possible (Button, Input, Card, Modal, Table)
- [ ] PASS / FAIL / N/A — No new component created without checking if one exists
- [ ] PASS / FAIL / N/A — Spacing uses Tailwind scale (p-1 through p-8), not arbitrary values

### Summary
- [ ] PASS — All items passed or N/A. Ready for Creative review.
- [ ] FAIL — Items marked FAIL above. Fix before requesting review.

**Notes for reviewer:** __________________________________
```

---

## 2. Design Decision Log Template

### Purpose

Document significant design decisions so they are explicit, auditable, and won't be re-litigated in future sprints. Every design decision with trade-offs, cross-functional impact, or user-facing change should get an entry.

### Structure

```
DDL-XXX: [Title]
────────────────────────────────────────────────────

**Date:**       YYYY-MM-DD
**Author:**     Creative / Builder / Coach
**Status:**     Proposed | Accepted | Deprecated | Rejected
**Stakeholders:** List of people who were involved or should be informed

### Context
What was the problem we were solving? What user need or business goal does this serve?

### Decision
What did we decide? Be specific about the design direction, component choice, or interaction pattern.

### Alternatives Considered
| Option | Pros | Cons | Why Not Chosen |
|--------|------|------|----------------|
| A      | ...  | ...  | ...            |
| B      | ...  | ...  | ...            |

### Rationale
- User research or data that informed this decision
- Design principles or heuristics that apply
- Business constraints that shaped the choice
- Trade-offs we accepted (and why)

### Impact
- **Components affected:** [list of components/files]
- **Pages affected:** [list of routes]
- **Accessibility:** [any WCAG considerations]
- **Performance:** [any perf trade-offs]
- **Future considerations:** [what this enables or blocks]

### Evidence
- Links to prototypes, research findings, or metrics
- Screenshot/diagram of the chosen design

### Review Notes
- What feedback was received during review?
- How was it incorporated?

### Revisit On
- [Date or trigger condition for revisiting this decision]
```

### Example Entry

```
DDL-001: Sidebar Breakpoint — Collapsible Drawer at 768–1023px
────────────────────────────────────────────────────────────────

**Date:**       2026-06-30
**Author:**     Creative
**Status:**     Proposed
**Stakeholders:** Builder, PM

### Context
At 768–1023px (tablet portrait), the sidebar is currently fixed/visible
(hidden md:flex). This wastes vertical space and leaves less room for
content on a 768px-wide viewport. User research shows tablet users
expect a collapsible drawer pattern.

### Decision
Replace hidden lg:flex with hidden md:flex. At 768–1023px,
the sidebar is hidden by default and shown via hamburger toggle
as a slide-out overlay (same as <768px behaviour).

### Alternatives Considered
| Option | Pros | Cons | Why Not Chosen |
|--------|------|------|----------------|
| Keep current (fixed at 768+) | Simple, no change | Wastes space, non-standard | — |
| Mini sidebar at 768–1023px | Shows nav icons | Too different from mobile pattern | — |
| Drawer (chosen) | Consistent with mobile pattern | Copy-paste mobile overlay logic | — |

### Rationale
- Consistent UX: same drawer pattern from 0–1023px
- Avoids a third layout variant (mini sidebar)
- Matches user expectation from other SaaS tools (Linear, Notion)

### Impact
- **Components affected:** sidebar.tsx, app-layout.tsx
- **Pages affected:** All app pages (Dashboard, Contacts, Pipeline, etc.)
- **Accessibility:** Mobile overlay already has aria-label, focus trap
- **Performance:** No impact
- **Future considerations:** Enables responsive sidebar collapse toggle animation

### Revisit On
- After user testing with 3 tablet users, or if stakeholders report a
  significant drop in sidebar navigation usage.
```

---

## 3. Stakeholder Communication Template

### Purpose

A consistent format for sharing design updates with stakeholders (PM, engineering lead, Coach, leadership). Use for:
- Weekly design progress updates
- Design review invitations
- Major milestone announcements
- Change proposals

### Weekly Design Update

```
## Design Update — Week of [DATE]

**From:** Creative
**To:** [Stakeholders]

### What shipped this week
- [Feature/component] — [status, link to PR]
- [Fix] — [status]

### What's in review
- [Feature/component] — [link to Figma/PR]
- Expected decision by: [date]

### What's next
- [Next item] — [planned start date]
- [Next item] — [planned start date]

### Blockers (if any)
- [Blocker description] — [what we need to unblock]

### Metrics this week
| Metric | Current | Trend | Target |
|--------|---------|-------|--------|
| UX audit issues resolved | 12/56 | ↑ | 56 |
| Components documented | 5/10 | ↑ | 10 |
| A11y axe violations | 3 | ↓ | 0 |
```

### Design Review Invitation

```
## Design Review: [Feature Name]

**When:** [Date, Time, Duration]
**Who:** [Stakeholders + team]
**Where:** [Link to Figma / PR / Meeting]

### What we'll cover
1. Problem statement & user need
2. Design exploration (2–3 alternatives shown)
3. Recommended direction with rationale
4. Open questions for the group

### Pre-reading (5 min)
- [Link to Figma prototype]
- [Link to design decision log entry]

### Expected outcome
- Decision on [specific question]
- Feedback on [area of concern]
- Approval to proceed to [next phase]
```

### Design Milestone Announcement

```
## Design Milestone: [Title]

**Date:** [DATE]

### What was accomplished
[2–3 sentence summary of what shipped and why it matters]

### What changed for users
- [Before/After description or screenshot]

### Key metrics
- [Metric improved]
- [Before value → After value]

### What's next
[Brief preview of the next phase]

### Thanks
[Shoutout to Builder, Coach, PM, or anyone who contributed]
```

---

## 4. Cross-Functional Collaboration Workflow

### Purpose

Define how Creative, Builder, and Coach work together on design delivery, so every contributor knows when to hand off, when to review, and what to expect.

### The Three Roles

| Role | Who | What they own |
|------|-----|---------------|
| **Creative** | Design & Brand Lead | Design direction, UI mockups, brand identity, design tokens, accessibility, UX quality gate |
| **Builder** | Frontend Engineer | Component implementation, CSS/Tailwind, React code, PR creation, dev tooling |
| **Coach** | Product Lead / PM | Requirements, priorities, stakeholder management, user research scheduling, acceptance criteria |

### Workflow by Phase

#### Phase: Discovery (Creative + Coach)

```
Coach:  "We need to [solve problem] for [user type]."
Creative:  Researches, sketches, writes design brief.
Coach:  Reviews brief, confirms direction.
Output: Design brief (1-pager) + user need statement.
```

**Artifact:** Design brief with problem statement, constraints, user need, and success criteria.

#### Phase: Design (Creative leads, Builder + Coach reviews)

```
Creative:  Produces 2–3 mockup variants in Figma.
Creative:  Runs self-critique against checklist.
Creative:  Invites Builder + Coach for async review.
Builder:  Reviews for technical feasibility, component compatibility.
Coach:  Reviews for product fit, priority alignment.
Creative:  Incorporates feedback, selects direction.
Creative:  Writes DDL entry with rationale.
Output: Approved mockup + DDL entry.
```

**Timebox:** 2–3 days for most features. If longer, break into smaller chunks.

#### Phase: Build (Builder leads, Creative reviews)

```
Builder:  Implements approved design using component library.
Builder:  Runs self-review against Design Critique Checklist.
Builder:  Opens PR with checklist results.
Creative:  Reviews PR within 24 hours (design review — not code review).
Creative:  Checks: layout, spacing, typography, tokens, accessibility, responsive.
Builder:  Fixes design review comments.
Builder:  Merges after Creative approval.
Output: Shipped PR with design sign-off.
```

**PR design review SLA:** 24 hours for standard items, 4 hours for blockers.

#### Phase: Final Review (Creative + Coach)

```
Coach:  Validates against acceptance criteria.
Creative:  Final visual QA on staging.
Creative:  Updates metrics baseline if applicable.
Output: Acceptance confirmed, metrics updated.
```

### Communication Channels

| Channel | Purpose | Frequency |
|---------|---------|-----------|
| #design Slack channel | Async reviews, questions, design links | Daily |
| Biweekly design critique | Structured feedback on work-in-progress | Every 2 weeks |
| Sprint demo | Shipped work shown to broader team | Per sprint |
| Design decision log | Permanent record of decisions | Per decision |
| Weekly design update | Stakeholder newsletter | Weekly |

### Escalation Path

When creative direction and technical constraints collide:

1. **Creative ↔ Builder** — Try to find a shared solution (e.g., acceptable visual compromise that Builder can ship cheaply)
2. **Creative + Builder → Coach** — If no compromise, escalate to Coach for product-level prioritisation
3. **Coach** — Makes the final call based on ship date, user impact, and resource constraints

### Rules of Engagement

- **Creative does not commit code** — Builder handles all PRs
- **Builder does not ship UI without design review** — PRs must have Creative approval
- **Coach does not change scope mid-sprint** — Changes go through the next sprint planning
- **Everyone participates in critique** — critique is about the work, not the person
- **No surprises** — If a deadline is at risk, surface it before the sprint ends

### Pre-Design Kickoff Checklist

Before starting any design work, confirm:

- [ ] Problem statement is clear and user-centred
- [ ] Success criteria are defined (outcome, not output)
- [ ] Constraints are understood (tech, timeline, budget)
- [ ] Existing components have been checked for reuse
- [ ] Stakeholder list is known
- [ ] Design critique session is scheduled