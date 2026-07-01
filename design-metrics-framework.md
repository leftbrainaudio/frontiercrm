# FrontierCRM — Design Metrics Framework

**Date:** 2026-06-30
**Author:** Creative (ALLSTARS Design & Brand Lead)
**Framework:** HEART + Goals-Signals-Metrics (Google, 2010)
**Status:** Baseline estimates · Pre-instrumentation

---

## 1. HEART Framework Applied to FrontierCRM

### Happiness

**Goal:** Users find FrontierCRM pleasant and efficient for daily sales work.
**Signal:** High CSAT in post-task surveys; low complaint volume; repeat daily usage.
**Metric:** CSAT (post-task survey scale 1–5), NPS (quarterly), Support ticket sentiment.

| Category | Current Baseline | Target (90d) | Target (12mo) |
|----------|-----------------|-------------|---------------|
| CSAT (post-task) | Not instrumented | ≥ 4.2 / 5.0 | ≥ 4.5 / 5.0 |
| NPS | Not instrumented | ≥ 30 | ≥ 50 |
| Daily active usage (DAU/MAU) | Inferred from auth | ≥ 60% monthly stickiness | ≥ 75% |

### Engagement

**Goal:** Users actively manage contacts, deals, pipeline, and email inside FrontierCRM.
**Signal:** Frequency and depth of core actions per session.
**Metric:** Actions per session (deal stage changes + contact updates + emails sent), session duration, feature adoption rate.

| Category | Current Baseline | Target (90d) | Target (12mo) |
|----------|-----------------|-------------|---------------|
| Avg. actions per session | Not instrumented | ≥ 8 | ≥ 15 |
| Pipeline page daily visits per user | Not instrumented | ≥ 1.5 | ≥ 3.0 |
| Email compose rate (sends/user/week) | Not instrumented | ≥ 2 | ≥ 5 |
| Feature breadth (% using ≥ 3 modules/week) | Not instrumented | ≥ 40% | ≥ 60% |

### Adoption

**Goal:** New users complete onboarding and adopt core workflows within their first week.
**Signal:** Onboarding completion rate, first deal creation, first contact import.
**Metric:** Time-to-first-action, onboarding step completion rate, Day 7 retention.

| Category | Current Baseline | Target (90d) | Target (12mo) |
|----------|-----------------|-------------|---------------|
| Onboarding completion rate | Not instrumented | ≥ 80% | ≥ 90% |
| Time to first deal created | Not instrumented | ≤ 2 days | ≤ 1 day |
| Day 7 retention (returned ≥ 3×) | Not instrumented | ≥ 60% | ≥ 80% |
| Contact import rate (within 30d) | Not instrumented | ≥ 50% | ≥ 70% |

### Retention

**Goal:** Users keep coming back to FrontierCRM as their daily CRM.
**Signal:** Weekly and monthly returning users, churn rate.
**Metric:** Weekly returning users (D7/D30/D90), monthly churn, feature re-engagement.

| Category | Current Baseline | Target (90d) | Target (12mo) |
|----------|-----------------|-------------|---------------|
| Week 1 → Week 4 retention | Not instrumented | ≥ 50% | ≥ 65% |
| Monthly churn | Unknown | ≤ 8% | ≤ 5% |
| Pipeline re-engagement (users who abandon then return within 30d) | Not instrumented | ≥ 25% | ≥ 40% |

### Task Success

**Goal:** Users complete primary sales tasks without errors, confusion, or wasted time.
**Signal:** Task completion rate, error rate, time-on-task.
**Metric:** Task success rate per flow, time on task, error encounters per session.

| Category | Current Baseline | Target (90d) | Target (12mo) |
|----------|-----------------|-------------|---------------|
| Login → Dashboard (auth flow) | ~8s (measured) | ≤ 5s | ≤ 3s |
| Create a deal (full flow) | Not instrumented | ≥ 85% completion | ≥ 95% |
| Update deal stage (one click) | Not instrumented | ≥ 95% completion | ≥ 99% |
| Compose + send email | Not instrumented | ≥ 80% completion | ≥ 92% |
| Find a contact by name | Not instrumented | ≤ 10s | ≤ 5s |

---

## 2. Business Metrics Influenced by Design

Design quality directly impacts these business metrics:

| Business Metric | UX Driver | Estimated Lift from Good UX | Current Value | Target (12mo) |
|-----------------|-----------|---------------------------|---------------|---------------|
| **User Activation** | Onboarding flow, first-impression UX | +15–25% | Unknown | ≥ 80% activation rate |
| **Monthly Retention** | Task efficiency, satisfaction, trust | +10–20% reduction in churn | Unknown | ≤ 5% churn |
| **Trial → Paid Conversion** | Perceived value in first 14 days | +20–30% | Unknown | ≥ 25% conversion |
| **Support Ticket Volume** | Self-service, clear UI, error prevention | −20–40% in UX-related tickets | Unknown | ≤ 15% of tickets = UX-related |
| **Avg. Revenue Per User (ARPU)** | Feature adoption breadth | +10–15% | Unknown | +15% |
| **NPS** | Overall experience quality | +15–25 points | Unknown | ≥ 50 |
| **Time-to-Value** | Onboarding speed, first deal creation | −40% | Unknown | ≤ 2 days to first deal |

### Connection diagram

```
                    ┌─ Task Success ──→ Error rate ↓, Completion ↑
                    │
Good design ────────┼─ Engagement ────→ Actions/session ↑, Feature breadth ↑ ──→ ARPU ↑
                    │
                    ├─ Adoption ──────→ Activation ↑, Time-to-value ↓ ──→ Revenue ↑
                    │
                    ├─ Retention ─────→ Churn ↓, LTV ↑
                    │
                    └─ Happiness ─────→ NPS ↑, Support tickets ↓
```

---

## 3. A/B Testing Opportunities

### What to test, how to measure, and minimum sample size

| # | Hypothesis | Primary Metric | Min. Sample (per variant, p<0.05, 80% power) | Duration | Priority |
|---|-----------|----------------|----------------------------------------------|----------|----------|
| 1 | **Pipeline kanban vs table view**: Table view improves deal management speed for users with >20 deals | Actions per session (pipeline), task completion time | ~200 users | 2–3 weeks | HIGH |
| 2 | **Inline email compose vs modal**: Inline compose (below thread) reduces abandonment vs modal overlay | Email send completion rate | ~300 users | 2–4 weeks | HIGH |
| 3 | **Simplified signup (3 fields) vs current**: Fewer fields increase signup completion | Signup completion rate | ~500 events | 1–2 weeks | HIGH |
| 4 | **Onboarding wizard variant A vs B**: Progressive disclosure vs step-by-step wizard | Onboarding completion rate | ~100 users | 2–3 weeks | MEDIUM |
| 5 | **Dashboard layout**: Sidebar KPIs vs top-row summary cards | Dashboard session duration, KPI click-through | ~200 users | 2 weeks | MEDIUM |
| 6 | **Search placement**: Global search bar vs per-page search | Search usage rate, time-to-find | ~150 users | 1–2 weeks | LOW |
| 7 | **Navigation label test**: Icon-only vs icon+label in sidebar | Navigation task success rate | ~100 users | 1 week | LOW |

### A/B Testing Checklist

Before launching any A/B test, confirm:

- [ ] Hypothesis documented with expected direction and rationale
- [ ] Primary metric defined and instrumented in advance
- [ ] Assignment strategy: random user-level bucketing (server-side preferred)
- [ ] Minimum sample size calculated (use formula above, accounting for expected effect size)
- [ ] Run duration determined (minimum 1 full business cycle = 7 days; avoid launching during holidays)
- [ ] Qualitative research paired with test (post-test interviews with 3–5 users per variant)
- [ ] Decision rule stated: "If variant lifts primary metric ≥ X% with p < 0.05, ship"
- [ ] Guardrail metrics defined (no negative impact on secondary metrics > 5%)

### A/B Testing Workflow

```
Hypothesis → Instrument → Randomise → Run (min duration) → 
  → Collect qual → Analyse → Decide: Ship / Iterate / Kill
```

---

## 4. Current Baseline Estimates

Since FrontierCRM does not yet have a UX instrumentation layer, the baselines below are **engineering-derived estimates** where possible, and **assumed industry benchmarks** otherwise. Each should be verified within the first instrumentation sprint.

| Metric | How to Measure | Current (Est.) | Source |
|--------|---------------|----------------|--------|
| Login-to-dashboard time | Frontend Perf API (`performance.now`) | ~8s (includes API calls) | DevTools trace |
| Signup completion rate | Backend: signups ÷ started auth pages | Unknown (no page-view tracking) | Need analytics |
| Onboarding step completion | Backend: DB rows per user | Unknown | Need instrumentation |
| Deal creation time | Frontend: opened modal → deal created | Unknown | Need RUM |
| Email send success | Backend: SENT status count ÷ SENDING status | Unknown | Backend logs exist |
| Error rate per session | Frontend: caught errors + React error boundaries | Unknown | Need Sentry breadcrumbs |
| Pipeline page load time | Frontend Perf API | Unknown | Need RUM |
| Keyboard tab coverage | Manual axe DevTools walkthrough | ~85% of interactive elements | Audit data |
| Lighthouse performance score | Lighthouse CI | Unknown | Run vendor check |
| Dark mode toggle usage | Frontend state + localStorage | Unknown | Need analytics |
| Mobile (390px) usage share | User-agent detection or analytics | Unknown (PWA supports install) | Need analytics |

### Recommended First Instrumentation (Sprint 1)

Minimum viable instrumentation to close the baseline gap — implement in priority order:

1. **PostHog** (or equivalent privacy-first analytics) — page views, event tracking, session recordings
2. **RUM (Real User Monitoring)** — Lighthouse field data, CLS, LCP, FID/INP
3. **Tracing events** for core flows: deal creation, email send, contact search, pipeline stage change
4. **CSAT survey** — 1-question post-task survey (paper.js or in-app modal) on 3 key flows
5. **NPS survey** — quarterly in-app prompt (standard 0–10 scale + "why?" followup)

---

## 5. Metrics Review Cadence

| Cadence | When | Who | What |
|---------|------|-----|------|
| Weekly | Sprint demo | Designer + Builder | Check instrumented metrics vs targets; flag regressions |
| Monthly | Design review | Design lead + PM | Review all HEART categories; adjust targets |
| Quarterly | Leadership review | Design lead + stakeholders | Present NPS, retention, ARPU impact; update roadmap |
| Per experiment | After A/B test | Design lead + Builder + PM | Analyse result; decide ship/iterate/kill; log in design decision log |

---

## 6. Tooling Recommendations

| Tool | Purpose | Cost | Priority |
|------|---------|------|----------|
| PostHog (self-hosted or cloud) | Product analytics, session recording, feature flags, A/B testing | Free tier / $0-100/mo | P0 — Instrumentation |
| Hotjar or equivalent | Session replays, heatmaps, feedback widgets | Free tier (limited recordings) | P1 — Qualitative insights |
| Lighthouse CI | Performance & accessibility regression tracking | Free | P1 — CI gate |
| DCMatrix / Google Optimize | A/B test assignment and tracking | Free (Optimize sunset → use PostHog) | P2 — When scaling experiments |
| Figma Dev Mode | Design-spec sync for developers | Included in Figma plan | P0 — Handoff |