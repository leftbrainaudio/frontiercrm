# FrontierCRM — UX Maturity Assessment & Growth Plan

**Date:** 2026-06-30
**Author:** Creative (ALLSTARS Design & Brand Lead)
**Model:** NN/g 6-Stage UX Maturity Model
**Factors:** Strategy, Culture, Process, Outcomes

---

## Executive Summary

FrontierCRM currently sits at **Stage 3 — Emergent** on the NN/g 6-stage UX maturity model, with clear indicators of **Stage 4 — Structured** beginning to form in the frontend component library and design token system. The project has strong foundations (well-structured components, dark mode, accessibility patterns) but lacks formal UX process, user research, design leadership, and outcome measurement.

**Target:** Stage 4 — Structured (within 6 months) → Stage 5 — Integrated (within 12 months)

---

## 1. NN/g Maturity Model Overview

| Stage | Name | Description | FrontierCRM? |
|-------|------|-------------|-------------|
| 1 | Absent | UX is not done or acknowledged | — |
| 2 | Limited | Sporadic UX work, no dedicated role | — |
| 3 | **Emergent** | UX activities exist but are reactive, inconsistent, and not resourced | **CURRENT** |
| 4 | Structured | UX process is systematic, resourced, and integrated into delivery | **TARGET (6mo)** |
| 5 | Integrated | UX is embedded across the org; decisions are user-centred by default | **TARGET (12mo)** |
| 6 | User-driven | User research drives strategy; the org learns continuously | — |

---

## 2. Current State Assessment (Stage 3 — Emergent)

### 2.1 Strategy — Mixed

| Indicator | Finding | Score |
|-----------|---------|-------|
| User-centred objectives | Not explicitly stated in planning docs. Feature analysis exists but is competitive-focused, not user-need-focused. | 1/5 |
| Design vision | No north-star narrative or experience vision document. Brand identity is defined (logos, colours, typography) but not narrated as an experience. | 1/5 |
| UX in planning | UX is not represented in roadmap planning (this document is the first design roadmap). Features are driven by engineering and product. | 1/5 |
| Stakeholder understanding | AUDIT_REPORT.md shows a security-first mindset. Stakeholders value quality but may not distinguish UX from visual polish. | 2/5 |

**Strategy score: 1.3/5**

### 2.2 Culture — Moderate

| Indicator | Finding | Score |
|-----------|---------|-------|
| Cross-functional collaboration | Builder and Creative work together on PRs. The design critique checklist template formalises a review culture. | 3/5 |
| Leadership buy-in | Design artifacts (logos, tokens, component library) exist and are used. The project invested in a Pro Max compliance audit. | 3/5 |
| User empathy | No user research has been conducted (no usability tests, no interviews, no personas). Design decisions are intuition-based. | 1/5 |
| Shared language | Design tokens (brand, surface, text, dark) are documented in index.css. Components use consistent naming. | 3/5 |

**Culture score: 2.5/5**

### 2.3 Process — Developing

| Indicator | Finding | Score |
|-----------|---------|-------|
| Design system | Component library (Button, Input, Card, Modal, Table) with dark mode, Tailwind v4 @theme token system. Well-structured but not formally documented. | 3/5 |
| UX process | No formal design process — work happens in response to feature requests. No design review cadence. No design decision log. | 2/5 |
| Accessibility process | Audit found 56 issues (2 blocker, 12 major). Some patterns are correct (aria, semantic HTML, focus trap) but no systematic a11y testing. | 2/5 |
| Design critique | No critique cadence. The design critique checklist template (produced in this session) would be a first step. | 1/5 |
| User research process | None. No research repository, no testing cadence, no participant recruitment pipeline. | 0/5 |

**Process score: 1.6/5**

### 2.4 Outcomes — Minimal

| Indicator | Finding | Score |
|-----------|---------|-------|
| UX metrics | No UX metrics exist. The design-metrics-framework.md produced in this session is the first attempt. | 0/5 |
| Business metrics tied to UX | No connection between design decisions and business outcomes. No A/B testing capability. | 0/5 |
| Measuring design impact | No instrumentation. No analytics events for UX flows. | 0/5 |
| Reporting | No design dashboards, no UX KPI reports. | 0/5 |

**Outcomes score: 0/5**

### Overall Maturity Score

| Factor | Score | Weight |
|--------|-------|--------|
| Strategy | 1.3/5 | 25% |
| Culture | 2.5/5 | 25% |
| Process | 1.6/5 | 25% |
| Outcomes | 0.0/5 | 25% |
| **Weighted Total** | **1.35/5** | **100%** |

**Stage: Stage 3 — Emergent** (clear signs of Stage 4 foundations in component library, but no process, research, or measurement)

---

## 3. Growth Plan: Stage 3 → Stage 4 (Structured) in 6 Months

### 3.1 Strategy — Move from 1.3 → 3.0

| Action | Effort | Timeline | Success Criterion |
|--------|--------|----------|-------------------|
| Write a north-star experience vision (1-page narrative describing what FrontierCRM feels like for a user in 12 months) | 1 day | Month 1 | Vision document exists, referenced in sprint planning |
| Establish user-centred objectives for each sprint (e.g., "Improve deal creation task success rate") | 0.5 day setup | Month 1 | Sprint goals include UX outcomes |
| Include design lead in roadmap/planning meetings | Ongoing | Month 1 | Design lead attends all sprint planning sessions |
| Present design roadmap to stakeholders (this document) | 0.5 day | Month 1 | Stakeholders have seen and acknowledged the roadmap |
| Create a 60-second UX elevator pitch for leadership | 0.5 day | Month 2 | Leadership can articulate why UX matters for FrontierCRM |

### 3.2 Culture — Move from 2.5 → 3.5

| Action | Effort | Timeline | Success Criterion |
|--------|--------|----------|-------------------|
| Invite Builder and Coach to observe one usability test session | 0.5 day | Month 2 | Builder and Coach have observed real users struggling/winning |
| Host a "UX 101" lunch & learn for the team (30 min: what UX is, why it matters, how we'll do it) | 0.5 day prep | Month 2 | Team can articulate what UX means for FrontierCRM |
| Share user research findings in sprint demos | 0.5 day/month | Month 3 | Research clips appear in demos; team discusses user behaviour |
| Celebrate design wins publicly (metrics improvements, shipped components) | 0.25 day/month | Ongoing | Slack or standup includes design wins alongside eng wins |

### 3.3 Process — Move from 1.6 → 3.5

| Action | Effort | Timeline | Success Criterion |
|--------|--------|----------|-------------------|
| **Design critique checklist** (this document) is adopted as mandatory PR gate | 0.5 day training | Month 1 | Every UI PR includes checklist; Builder runs it before requesting review |
| **Design decision log** (this document) is created and first 3 entries written | 1 day | Month 1 | DDL has ≥ 3 entries covering sidebar, font, and one other decision |
| **Biweekly design critique** cadence established (30 min, async or sync) | 0.5 day setup | Month 1 | Critique runs on schedule for 2 consecutive months |
| Complete Pro Max audit fixes (Phase 1 of roadmap) | 4 weeks | Month 1–2 | Zero blocker + major issues from audit |
| **Design system documentation** published (component API + token reference) | 2 weeks | Month 2 | DESIGN.md at repo root; tokens exported as JSON |
| **Component library v2** (Select, Skeleton, Badge, DropdownMenu, Toast, EmptyState) | 6 weeks | Month 2–3 | All Phase 2.1 components shipped and documented |
| **First usability test** (3 users, 5 core tasks, moderated, remote) | 2 weeks | Month 3 | Test report with ≥ 3 actionable findings |
| **User research repository** established (findings, recordings, personas) | 1 week | Month 3 | Repo exists with first test results; template for future tests |
| **Full WCAG 2.2 AA pass** (axe DevTools + manual keyboard + screen reader) | 2 weeks | Month 4 | Zero axe violations on all 8 major screens |

### 3.4 Outcomes — Move from 0.0 → 2.5

| Action | Effort | Timeline | Success Criterion |
|--------|--------|----------|-------------------|
| **Instrument analytics** (PostHog or equivalent) — page views, events, session recordings | 1 week (eng) | Month 1 | Events firing for all core flows |
| Establish UX metric baselines (task success, time on task, error rate) for 3 key flows | 1 week | Month 2 | Baseline values published for login, deal creation, email send |
| Set up CSAT survey on 3 key flows (post-task prompt) | 0.5 day | Month 2 | CSAT data streaming for deal creation, email send, contact search |
| First A/B experiment (pipeline kanban vs table) | 2 weeks | Month 3 | Experiment launched; results analysed within 4 weeks |
| Design impact report to leadership (quarterly) | 1 day | Month 3 | First report delivered with HEART metrics + business impact |
| Set up NPS survey (quarterly in-app) | 0.5 day | Month 3 | NPS baseline established |

### 3.5 Milestone Map

```
Month 1                  Month 2                  Month 3                  Month 4–6
────────                 ────────                 ────────                 ─────────
Strategy:
  Vision doc             UX elevator pitch
  Roadmap presented      Design lead in planning
  Sprint UX goals

Culture:
  UX 101 lunch & learn   Builder observes test     Research in demos
                          Coach observes test

Process:
  Critique checklist  →  DS documentation      →  Component v2 done     →  WCAG 2.2 AA pass
  DDL created            First usability test      Research repository
  Biweekly critique      Phase 1 fixes done
  Phase 1 (audit fixes)

Outcomes:
  Analytics instrum.  →  Baselines published    →  First A/B test        →  NPS baseline
                          CSAT live                 First impact report
```

---

## 4. Resource Requirements

### Current Resources

| Role | Headcount | Status |
|------|-----------|--------|
| Creative (Design Lead) | 1 | Active |
| Builder (Frontend Engineer) | 1 | Active (part-time for design work) |
| Coach (Product Lead) | 1 | Active |

### Gaps

| Need | Why | When | Estimated Cost |
|------|-----|------|----------------|
| UX Researcher (part-time or freelance) | To run usability tests, user interviews, and maintain research repository | Month 3 onward | $5–10K/month (contractor) |
| Analytics tool (PostHog Cloud) | Product analytics, session recording, A/B testing | Month 1 | $0–100/month (free tier covers needs) |
| User testing participant pool | Recruit 3–5 users per month for testing | Month 2 | $50–100 per session (gift cards) |
| Figma Professional (or equivalent) | Design system management, prototyping, handoff | Already owned | — |

### Ongoing Commitment

| Activity | Time per sprint (2 weeks) | Who |
|----------|--------------------------|-----|
| Design critique (biweekly) | 2 hours | Creative + Builder + Coach |
| Sprint planning + UX goals | 1 hour | Creative |
| PR design reviews | 2–4 hours | Creative |
| Usability testing (monthly) | 8 hours (setup + run + analyse) | Creative + freelance researcher |
| Metrics review | 1 hour | Creative |
| DDL maintenance | 0.5 hour | Creative |
| Weekly design update | 0.5 hour | Creative |

---

## 5. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| No dedicated UX researcher available | Medium | High | Start with moderated remote tests run by Creative; use tools like UserTesting.com for unmoderated tests |
| Analytics instrumentation competes with feature work | High | Medium | Start with lightweight PostHog snippet (15 min install); full event taxonomy can follow |
| Stakeholders see UX work as "nice to have" not essential | Medium | High | Tie every UX activity to a business outcome in the metrics framework; use the 60-sec elevator pitch |
| Design process overhead slows down Builder | Low | Medium | The critique checklist is designed to be lightweight (5 min self-review); time savings from fewer rework cycles should offset |
| Regression in maturity after initial push | Low | Medium | Treat maturity as a living system (NN/g: "tend it, it can regress"). Quarterly re-assessment with the 4-factor model |

---

## 6. Maturity Re-Assessment Cadence

| When | Who | What |
|------|-----|------|
| Quarterly | Creative | Re-run the 4-factor assessment against this baseline; update scorecard |
| 6 months | Creative + Coach | Check if Stage 4 (Structured) indicators are met; adjust plan for Stage 5 |
| 12 months | Creative + Coach + Stakeholders | Full maturity review; decide on next growth cycle |

---

## 7. Stage 5 (Integrated) Preview

Once Stage 4 is achieved (6 months), the next horizon is Stage 5 — Integrated, where user-centred practice is embedded in how the entire organisation operates:

| Indicator | What it looks like at Stage 5 |
|-----------|-------------------------------|
| Strategy | UX is a core part of the product strategy; design lead reports to C-level |
| Culture | Everyone (eng, PM, support) considers user impact in their decisions |
| Process | User research is a standard input to every sprint; no feature ships without a user need |
| Outcomes | Design metrics are part of the company dashboard alongside revenue and churn |

**Estimated effort to Stage 5:** 12 months from today, with a second designer and a dedicated researcher. The design-metrics-framework.md and design-process-templates.md produced in this session are the foundational investments for reaching Stage 5 — they build the measurement and process infrastructure that makes user-centred practice sustainable.