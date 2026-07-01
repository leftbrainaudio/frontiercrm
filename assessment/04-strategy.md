# Phase 4: Strategy — Roadmap, Measurement Framework & UX Maturity

**Date:** 2026-06-30
**Skills applied:** design-strategy, roadmap-prioritisation, measuring-design-impact, ux-maturity-advocacy
**Reference:** Synthesises all findings from assessment/01-foundation.md, 02-craft.md, 03-methods.md

---

## 1. Design Vision Statement

> **FrontierCRM will be the CRM that sales teams *want* to use — not one they're forced to.**
>
> In 12 months, a sales rep should be able to go from signup to first closed deal in under 10 minutes. Every interaction should feel crafted, not assembled. The product should anticipate the next action and remove friction from every flow.

### North-Star Principles

1. **Workflows over chrome** — every pixel should help the user close deals faster. If it doesn't serve a sales task, cut or defer it.
2. **Crafted, not assembled** — consistent design tokens, intentional spacing, bespoke micro-interactions that feel premium.
3. **Inclusive by default** — every new page must pass WCAG 2.2 AA before shipping. Accessibility is not a polish phase.
4. **Data-informed, not data-driven** — analytics show *what*; user research reveals *why*. Both are required.

---

## 2. Prioritised Design Roadmap

### Effort × Impact Matrix

```
                      HIGH IMPACT
                         │
                         │
   P0 ─ Crash fixes ─────┼──── P1 ─ Seed data
        Error boundaries  │        Responsive sidebar
        Skip-to-content   │        Keyboard a11y
        Inter font fix    │        Dark mode tokens
                         │
    LOW EFFORT ──────────┼───────── HIGH EFFORT
                         │
   P1 ─ Focus ring tokens│    P2 ─ Confirmation dialogs
        Motion pref       │         Select component
        Touch targets     │         Dashboard charts responsive
        UX copy polish    │         Analytics instrumentation
                         │
                         │    P3 ─ Breadcrumbs
                         │         Keyboard shortcuts
                         │         Auto-save forms
                         │         Global search (Cmd+K)
                         │         DatePicker component
                      LOW IMPACT
```

### P0 — Blocker Fixes (Start Here)

| # | Item | Effort | Impact | Skills | Dependencies | Rationale |
|---|------|--------|--------|--------|-------------|-----------|
| S1 | **Fix Email page crash** (`connections?.find` error) | 1 day | 🔴 Critical | front-end-fluency, error-prevention | API sync fix | Crash blocks entire Email workflow — 25% of app broken |
| S2 | **Fix Slack/Users/Audit Log 404 pages** | 1 day | 🔴 Critical | front-end-fluency, information-architecture | Backend endpoints | 3 sidebar links lead to errors |
| S3 | **Add global React Error Boundary** | 0.5 day | 🔴 Critical | interaction-design, accessibility-wcag | None | Prevents raw stack traces reaching users |
| S4 | **Add skip-to-content link** | 0.5 day | 🔴 Critical | accessibility-wcag, front-end-fluency | None | Keyboard-first navigation essential for WCAG A |
| S5 | **Apply Inter font to body** | 0.25 day | 🟠 Major | front-end-fluency, visual-ui-design | None | Brand typography — carried from prior audit |

### P1 — Core UX Improvements (Next Sprint)

| # | Item | Effort | Impact | Skills | Dependency |
|---|------|--------|--------|--------|------------|
| S6 | **Seed demo data for new users** | 2 days | 🟠 Major | user-research, data-informed-design | None |
| S7 | **Fix sidebar breakpoint (768-1023px drawer)** | 1 day | 🟠 Major | responsive-design, interaction-design | None |
| S8 | **Respect prefers-reduced-motion** | 0.5 day | 🟠 Major | accessibility-wcag, front-end-fluency | None |
| S9 | **Increase touch targets to 44×44px min** | 1 day | 🟠 Major | accessibility-wcag, responsive-design | None |
| S10 | **Tokenize focus ring (3px + token)** | 0.5 day | 🟢 Minor | design-systems, front-end-fluency | Done in index.css by replacing `ring-2` with `ring-[length]` |
| S11 | **Standardise Select component** | 2 days | 🟠 Major | design-systems, front-end-fluency | Component audit (item M5 in craft) |
| S12 | **UX copy polish (10 items)** | 0.5 day | 🟢 Minor | ux-writing | Audit items C1-C10 |
| S13 | **Add confirmation dialogs for destructive actions** | 2 days | 🟠 Major | interaction-design, design-systems | Modal component already built |

### P2 — Foundation Building (Next Quarter)

| # | Item | Effort | Impact | Skills |
|---|------|--------|--------|--------|
| S14 | **Instrument analytics (PostHog/Amplitude)** | 3 days | 🟠 Major | data-informed-design, measuring-design-impact |
| S15 | **Add breadcrumbs to deep pages** | 2 days | 🟢 Minor | information-architecture, visual-ui-design |
| S16 | **Consolidate dark mode token usage** | 1 day | 🟢 Minor | design-systems, front-end-fluency |
| S17 | **Implement toast notification system** | 1 day | 🟡 Medium | interaction-design, visual-ui-design |
| S18 | **Dashboard charts responsive below 768px** | 1 day | 🟢 Minor | responsive-design, visual-ui-design |

### P3 — Delight & Power Features (Future)

| # | Item | Effort | Impact | Skills |
|---|------|--------|--------|--------|
| S19 | **Add keyboard shortcuts (Cmd+K search, g+d/g+c/g+p/g+e)** | 3 days | 🟡 Medium | interaction-design, front-end-fluency |
| S20 | **Auto-save on long forms** | 3 days | 🟡 Medium | interaction-design, front-end-fluency |
| S21 | **Floating action button for quick activity logging** | 2 days | 🟡 Medium | interaction-design, visual-ui-design |
| S22 | **Build DatePicker component** | 3 days | 🟡 Medium | design-systems, interaction-design |
| S23 | **Pagination reusable component** | 1 day | 🟢 Minor | design-systems |
| S24 | **User onboarding with demo data flow** | 4 days | 🟠 Major | ux-writing, journey-mapping |

---

## 3. Measurement Framework

### HEART Goals-Signals-Metrics

#### Goal 1: Fix Broken Workflows (Immediate, Wk 1-2)

| Category | Goal | Signal | Metric | Baseline | Target |
|----------|------|--------|--------|----------|--------|
| Task Success | Users can access all sidebar routes without errors | No 404/500 errors on any route | % of sidebar links that load correctly | 75% (9/12 work) | 100% |
| Task Success | Users can reach Email page without crash | Email page renders without error boundary | Email page error rate | 100% crash rate | 0% crash rate |
| Happiness | Recovered users see helpful error messages | Non-technical error text | Error message readability score | 0/10 | 8/10 |

#### Goal 2: First-Value Experience (Near-term, Wk 3-6)

| Category | Goal | Signal | Metric | Baseline | Target |
|----------|------|--------|--------|----------|--------|
| Adoption | New users create a deal within first session | Deal created in first 30 min | % of signups who create ≥1 deal | 0% (no data path) | 30% |
| Engagement | Users log activities regularly | Activities logged per user/week | Avg activities/user/week | 0 | 5 |
| Task Success | Users complete email connection from Settings | Connection success rate | % of attempts that succeed | 0% (crash) | 80% |

#### Goal 3: Power-User Efficiency (Medium-term, Wk 7-12)

| Category | Goal | Signal | Metric | Baseline | Target |
|----------|------|--------|--------|----------|--------|
| Engagement | Users return at least weekly | Weekly returning users | % weekly active / total | 0% | 40% |
| Retention | Users stay beyond 14 days | D14 retention rate | % of signups active on D14 | 0% | 25% |
| Happiness | Users rate the app positively | NPS/CSAT survey response | Net Promoter Score | — | +30 |

### Instrumentation Priority

1. **Page views** — every route fires a page event
2. **Key actions** — create_deal, move_deal, send_email, add_contact, export_csv, connect_email
3. **Error tracking** — all ErrorBoundary catches → Sentry/analytics
4. **Performance** — LCP, FID, CLS on dashboard and pipeline

---

## 4. UX Maturity Assessment

### Current Stage: **Stage 2 — Limited**

Using the NN/g 6-Stage UX Maturity Model:

| Factor | Current State | Stage | Target (6 months) |
|--------|--------------|-------|-------------------|
| **Strategy** | No formal UX strategy; design decisions are implementation-driven | Limited | **Emergent** |
| **Culture** | Design system exists but isn't consistently used; accessibility is checked post-hoc | Limited | **Structured** |
| **Process** | No user research process; no testing; no error boundary pattern | Limited | **Emergent** |
| **Outcomes** | No metrics tracked; no analytics; no design KPIs | Limited | **Emergent** |

**Evidence for "Limited" classification:**
- A design system exists (Tailwind tokens, component library) — this moves it past "Absent"
- But 3 pages crash at runtime, indicating no user testing or QA process
- No analytics instrumentation — impossible to measure UX impact
- Accessibility checked only in audits, not baked into Dev process
- No user research conducted (as far as evidence shows)
- No design review process visible in code/process

### Path to Stage 3 (Emergent)

| Action | Timeframe | What Changes |
|--------|-----------|-------------|
| Fix page crashes (S1-S3) | Sprint 1 | Users can access all features |
| Add error boundaries (S3) | Sprint 1 | No more stack traces reaching users |
| Apply Inter font (S5) | Sprint 1 | Brand consistency across all pages |
| Seed demo data (S6) | Sprint 2 | Users see populated CRM on first visit |
| Instrument analytics (S14) | Sprint 3 | Start measuring UX metrics |
| Schedule first user test | Sprint 3 | Establish research cadence |
| Formalise design review process | Sprint 4 | Design changes reviewed before dev |

### Stage 3 (Emergent) Exit Criteria

- ✅ All pages render without errors
- ✅ Analytics active on all key actions
- ✅ At least one user test conducted with findings documented
- ✅ Design system used consistently across >80% of new code
- ✅ Accessibility checklist part of every PR review
- ✅ UX metrics visible on a team dashboard

---

## 5. Design Strategy — Principles to Implementation

### Principle 1: Fix What's Broken Before Building New

The app has 3 crashing pages, 56 documented UI/UX issues from the prior audit, and 44 accessibility issues from this assessment. **No new screens should be built until the Email page is fixed**, all sidebar links work, and an error boundary pattern is established.

### Principle 2: Make Every Screen Pass the First-Time Test

A first-time user should be able to:
1. Sign up (✅ works)
2. Complete onboarding (✅ works)
3. See demo data (❌ not yet)
4. Create a deal (⚠️ works but shows empty state)
5. Connect email (❌ crashes)
6. View reports (⚠️ works but shows $0)
7. See all sidebar pages (❌ 3 crash)

### Principle 3: Accessibility Is Not a Phase

Every new screen must include before shipping:
- Skip-to-content link
- Full keyboard navigation
- Visible focus indicators
- Screen reader announcements
- WCAG 2.2 AA contrast ratios
- `prefers-reduced-motion` support

### Principle 4: Measure Before You Optimise

No A/B testing or UX optimisation should start until:
- Analytics instrumentation is live on all key actions
- A baseline HEART score is established
- At least one user test has been conducted

---

## 6. Sprint Recommendations

### Sprint 1: Stabilise (Week 1)

| Day | Work |
|-----|------|
| Mon | Fix Email page crash (type guard on `connections?.find` or API shape fix) |
| Tue | Fix Slack/Users/Audit Log 404s (fix frontend routing or add missing pages/endpoints) |
| Wed | Add global React Error Boundary; add skip-to-content link |
| Thu | Apply Inter font; fix focus ring tokens; respect prefers-reduced-motion |
| Fri | Touch target audit (44×44px); UX copy polish |

### Sprint 2: Foundation (Week 2)

| Day | Work |
|-----|------|
| Mon | Seed demo data creation flow |
| Tue | Seed demo data creation flow (cont.) |
| Wed | Sidebar breakpoint fix (768-1023px drawer) |
| Thu | Standardise Select component |
| Fri | Confirmation dialogs for destructive actions |

### Sprint 3: Instrumentation (Week 3)

| Day | Work |
|-----|------|
| Mon | Analytics instrumentation (PostHog/Amplitude) |
| Tue | Analytics instrumentation (cont.) |
| Wed | Dashboard chart responsive improvements |
| Thu | First moderated usability test (3-5 participants) |
| Fri | Test analysis and prioritisation