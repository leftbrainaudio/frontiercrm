# FrontierCRM — Design Roadmap

**Date:** 2026-06-30
**Author:** Creative (ALLSTARS Design & Brand Lead)
**Driven by:** UI/UX Pro Max Compliance Audit, Security Audit (AUDIT_REPORT.md), Feature Analysis report, Changelog v1.3.0

---

## Overview

A phased design roadmap grounded in FrontierCRM's current state: a multi-tenant CRM with React 19 / Tailwind 4 frontend, established component library (Button, Input, Card, Modal, Table), SVG brand identity (compass-forward arrow), and 56 UX issues discovered during the Pro Max audit. Phasing follows Lean UX (Discovery → Alpha → Beta → Live), treating every work item as an outcome hypothesis.

---

## Phase 1 — Now (Sprint 1–4, July 2026)

**Theme:** Critical UX fixes, brand identity rollout, accessibility blockers
**Duration:** ~4 weeks · 2 designers → 1 design lead
**Framing:** Remove barriers that degrade perceived quality and block accessibility compliance.

### 1.1 Font & Typography Rollout

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| Apply Inter font to body via CSS base layer | S | HIGH | None | Inter renders on all text; no font flash on page load |
| Standardise heading hierarchy (H1=28px, H2=24px, H3=20px, H4=16px) | M | HIGH | Font fix complete | All pages use consistent heading scale; no manual `<text-2xl>` for H1 |
| Add `<link rel="preconnect">` for Google Fonts + `font-display: swap` | XS | MEDIUM | None | Lighthouse font-display score ≥ 90 |

### 1.2 Accessibility Blockers

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| Add `focus-visible` rings to all auth page buttons (OAuth, SSO, magic link) | S | HIGH | None | Tab through login/signup — every interactive element has visible ring |
| Add `focus-visible` to native `<select>` elements in AddDealModal | S | HIGH | None | Tab through modal selects → visible focus ring |
| Add `focus-visible` to `<Link>` router elements (sign-up, magic link) | S | MEDIUM | None | Tab through auth page links → visible focus ring |
| Add `prefers-reduced-motion` query to disable excess animations | XS | MEDIUM | None | `prefers-reduced-motion: reduce` stops `.animate-fade-in` / `.animate-slide-up` |
| Add `aria-label` to sidebar collapse toggle and mobile close button | XS | MEDIUM | None | axe DevTools audit passes for aria-label on sidebar controls |
| Raise touch targets to 44×44px minimum on mobile | M | MEDIUM | None | All interactive elements ≥ 44×44 CSS px at 390px viewport |

### 1.3 Brand Identity Rollout

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| Replace "F" placeholder in sidebar logo with actual SVG logo-mark | S | HIGH | Logos exist at `frontend/public/logos/` | Sidebar shows compass-forward arrow mark |
| Add SVG logo to login/signup pages | S | MEDIUM | Logo-mark in place | Auth pages display branded mark |
| Set `<title>` and `og:title` to use brand name consistently | XS | LOW | None | `<title>FrontierCRM</title>` on all pages |
| Add brand favicon (SVG) and `apple-touch-icon` | XS | LOW | — | Browser tab shows compass mark, iOS shows icon |

### 1.4 Visual Polish — Highest-Impact Fixes

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| Fix table row selection: add 3px primary-500 left border | S | HIGH | None | Selected row shows 3px left border indicator |
| Fix sidebar breakpoint: 768–1023px as collapsible drawer | M | HIGH | None | Resize from 1280→768: sidebar hides, hamburger appears |
| Fix Card component border-radius from 12px to 8px | XS | MEDIUM | None | Cards render with `rounded-lg` (8px) |
| Fix Modal overlay color to `neutral-900/60` | XS | MEDIUM | None | Modal backdrop is neutral-900/60, not black/50 |
| Fix Modal body `max-h` from 60vh to 85vh | XS | MEDIUM | None | Modal body scroll extends to 85vh |
| Fix Input border-radius from 8px to 6px | XS | LOW | None | Input fields show `rounded-md` (6px) |
| Fix Button focus ring from 2px to 3px | XS | LOW | None | Button focus-visible shows 3px ring |

### 1.5 Foundation — Design System Docs

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| Document current component API surface (Button, Input, Card, Modal, Table) | M | MEDIUM | None | DESIGN.md spec file published in repo |
| Document all design tokens (colors, spacing, typography, shadows) | M | MEDIUM | None | Token reference covers all 4 categories |
| Export design tokens as JSON for cross-referencing | S | MEDIUM | Token docs exist | `design-tokens.json` consumed by Builder in component work |

---

## Phase 2 — Next (Sprint 5–8, August–September 2026)

**Theme:** Design System v2, user flow improvements, responsive polish
**Duration:** ~8 weeks · 2 designers + occasional Builder pairing

### 2.1 Design System v2

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| Add `Select` component (standardised dropdown with focus-visible, aria) | M | HIGH | Phase 1.2 accessibility fixes | Pipeline/stage selects use shared Select component |
| Add `Skeleton` component library (already exists as atoms — document + polish) | S | LOW | — | Skeleton variants documented with Loading/Error/Empty pattern |
| Add `Badge` / `Tag` component | S | MEDIUM | — | Status, priority, and tag badges use Badge component (consistent styling) |
| Add `DropdownMenu` (popper-based) | M | MEDIUM | — | All dropdown menus share consistent positioning, keyboard nav, close behaviour |
| Add `Toast` notification system | S | MEDIUM | — | Success/error/info toasts appear consistently; configurable duration, dismiss, stack |
| Add `EmptyState` component | S | LOW | — | All "no data" states render via shared EmptyState with icon, title, action slot |
| v2 component docs + Storybook-style usage examples | M | HIGH | All v2 components done | Every component has a code example + props table in repo docs |

### 2.2 User Flow Improvements

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| Onboarding wizard UX audit + polish (error states, progress indicators) | M | HIGH | Phase 1.2 a11y fixes | Onboarding steps are keyboard-navigable; errors shown inline |
| Signup flow field-level validation (each field validates individually) | S | MEDIUM | — | Signup shows per-field errors, not a single general error |
| Pipeline kanban loading/empty state polish | S | MEDIUM | — | Empty pipeline shows illustrative empty state + CTA |
| Contact detail page: responsive layout at 768px | S | MEDIUM | Phase 1.4 sidebar fix | Contact detail doesn't break when sidebar collapses |
| Activity timeline: date range picker usability pass | S | LOW | — | Date picker is keyboard-accessible, shows clear presets |
| Forecast page: mobile layout pass | M | LOW | — | Forecast table scrolls horizontally on 390px without overlap |
| Email compose modal: compact mode for small screens | M | MEDIUM | — | Compose modal uses full viewport at <640px, no truncation |

### 2.3 Responsive Polish

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| Audit all pages at 390px, 768px, 1280px (regression check) | M | HIGH | Phase 1.4 sidebar fix | Every page renders without overflow or broken layout at all 3 breakpoints |
| Fix main content padding to match spec: `p-4 sm:p-6 lg:p-8` | S | MEDIUM | — | AppLayout content area uses correct padding scale |
| Fix table row height to fixed 52px spec | S | MEDIUM | — | Table rows are exactly 52px tall |
| Fix modal widths to spec (sm=400px, md=480px, lg=640px) | S | LOW | — | Modal width classes match spec dimensions |
| Fix sidebar width from 256px to 240px | XS | LOW | — | Sidebar is exactly 240px when expanded |

### 2.4 Accessibility — Deep Pass

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| Full keyboard navigation audit (axe DevTools + manual tab test) | M | HIGH | Phase 1.2 fixes | Zero axe violations on all 8 major screens |
| Screen reader pass (VoiceOver / NVDA) on 3 critical flows | M | HIGH | — | Login → Dashboard → View Contact announces correctly |
| Color contrast audit on custom components (interactive cards, badges) | S | MEDIUM | — | All text meets 4.5:1 (normal) or 3:1 (large) contrast ratios |
| Add skip-to-content link | XS | MEDIUM | — | First tab on any page shows "Skip to content" link |
| WCAG 2.2 AA compliance statement published | S | LOW | All a11y items done | Compliance statement in repo/docs |

---

## Phase 3 — Later (Sprint 9+, October–December 2026)

**Theme:** Advanced features, experimentation framework, design maturity
**Duration:** ~12 weeks · 2–3 designers · ongoing

### 3.1 Experimentation Framework

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| Define A/B test hypothesis template for design changes | XS | MEDIUM | Phase 2 UX metrics baseline | Template published, used for first 2 tests |
| Instrument first test: pipeline kanban vs table view engagement | M | HIGH | Engineering instrumentation support | Statistically significant result within 2 weeks of launch |
| Instrument second test: email compose flow variant (inline vs modal) | M | MEDIUM | First test infrastructure built | Measurable improvement in email send completion rate |
| Build experiment results dashboard (or use existing analytics) | L | HIGH | Both tests launched | Team references experiment results in weekly sprint planning |

### 3.2 Advanced Components

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| `DatePicker` component (calendar popover, keyboard nav, min/max) | L | HIGH | Phase 2.1 DropdownMenu | DatePicker used consistently across filters, forms, timeline |
| `Combobox` component (searchable select with async options) | M | MEDIUM | Phase 2.1 Select component | Topbar search, filter dropdowns, user picker use Combobox |
| `DataTable` (sort, filter, column toggle, virtual scroll) | XL | HIGH | Phase 2 components stable | Contact/pipeline tables support column config and virtual scroll |
| `SplitButton` (primary action + dropdown variants) | S | LOW | — | Used where two-tier action makes sense (Save + Save & New) |
| `FileUpload` (drag-drop, preview, progress, validation) | M | MEDIUM | — | File upload shows preview, progress bar, and type/size validation |
| `CommandPalette` (⌘K quick actions) | L | MEDIUM | Phase 2.1 Toast notification | Users can ⌘K to navigate pages and trigger common actions |

### 3.3 Design Maturity — Team & Process

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| Establish design critique cadence (biweekly internal, monthly cross-functional) | — | HIGH | Team > 1 designer | Critique runs on schedule; artifacts improve visibly between iterations |
| Run first cross-functional design workshop (Creative + Builder + Coach) | M | HIGH | Cadence established | Workshop produces shared artifacts (journey map, priority list) |
| Publish design decision log (ADR for UX — see process-templates) | S | MEDIUM | Phase 2 design docs complete | ADR log has ≥ 5 entries from recent decisions |
| Create user research repository (findings, recordings, personas) | M | HIGH | — | Repository exists with ≥ 3 user sessions documented |
| Conduct first usability test session (3 users, 5 tasks, moderated) | L | HIGH | Research repository ready | Test identifies ≥ 3 usability issues; all logged for prioritisation |
| Present design impact metrics to leadership | S | HIGH | Phase 2 metrics baseline | Leadership review includes UX metrics alongside business KPIs |

### 3.4 Innovation — Differentiators

| Item | Effort | Impact | Dependencies | Success Metric |
|------|--------|--------|--------------|----------------|
| "Deal CPR" dashboard (deals at risk / stalled / healthy) | L | HIGH | Pipeline analytics stable | Dashboard surfaces deals needing attention with clear colour-coding |
| Pipeline velocity tracking (avg days-in-stage, bottleneck alerts) | M | HIGH | Deal stage data complete | Velocity dashboard shows time-in-stage per pipeline stage |
| Smart empty states (contextual, actionable, not generic) | M | MEDIUM | EmptyState component done | Empty states guide user to next action, not just "No data" |
| AI-powered natural-language reporting POC | XL | TRANSFORMATIVE | Experimentation framework active | "Show me deals over $50K stuck for 30 days" returns a chart |

---

## Dependency Map

```
Phase 1            Phase 2            Phase 3
───────            ───────            ───────
1.1 Font           ──>  2.1 DS v2     ──>  3.2 Advanced components
1.2 A11y blockers  ──>  2.4 Deep a11y ──>
1.3 Brand roll     ──>                ──>
1.4 Visual polish  ──>  2.3 Responsive──>
                      ──>  2.2 Flows  ──>  3.4 Innovation
                                        ──>  3.1 Experimentation
                                        ──>  3.3 Maturity
```

No Phase 3 item should start until Phase 2 accessibility pass (2.4) is complete and the first A/B test infrastructure (3.1) is scaffolded.

---

## Resource Plan

| Phase | Designers | Builder pairing (hrs/wk) | Coach review cadence |
|-------|-----------|------------------------|----------------------|
| 1     | 1 lead + 1 IC | 5 hrs/wk | Biweekly |
| 2     | 1 lead + 1 IC | 10 hrs/wk | Weekly |
| 3     | 1 lead + 1–2 IC | 10–15 hrs/wk | Weekly |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Font rollout breaks existing layouts | Low | Medium | Test on staging first; CSS override is scoped to `body` |
| Sidebar breakpoint change breaks nav | Low | High | Add feature flag for 768–1023px drawer; test all 12 nav items render |
| Phase 1 scope creep into visual nits | Medium | Medium | Strictly prioritise blocker + major from audit; defer nits to Phase 2 |
| A/B tests underpowered (insufficient user base) | High | Medium | Start with engagement metrics (higher sample); plan for 4-week minimum run |
| Builder unavailable for component work | Medium | High | Document component specs fully; pair with another IC designer |

---

## Success Criteria (Overall)

- **Phase 1:** Zero UI blocker + major issues from pro-max audit; Inter font rendering; sidebar breakpoints match spec; all interactive elements focus-visible
- **Phase 2:** Component library documented and v2 components shipped; responsive layouts pass at 390/768/1280; WCAG 2.2 AA reported
- **Phase 3:** A/B test framework operational; ≥2 experiments run; design critique cadence established; UX metrics presented to leadership