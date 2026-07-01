# Phase 2: Craft — Components, Visuals, Interactions & Accessibility

**Date:** 2026-06-30
**Skills applied:** interaction-design, visual-ui-design, wireframing, prototyping, design-systems, responsive-design, ux-writing, accessibility-wcag, ux
**Reference:** Builds on ui-ux-pro-max-audit.md (56 issues documented)

---

## 1. Design System & Token Analysis

The app uses Tailwind v4 with custom `@theme` tokens in `index.css`. The token architecture follows a solid pattern with named semantic tokens.

### Token Coverage

| Category | Tokens | Notes |
|----------|--------|-------|
| Primary (Brand) | brand-50 through brand-900 | ✅ Blue scale (#3B82F6 primary) |
| Secondary | secondary-50 through secondary-900 | ✅ Teal scale — used sparingly |
| Accent | accent-50 through accent-900 | ✅ Amber scale — used sparingly |
| Surface | surface, surface-secondary, surface-tertiary | ✅ Semantic names |
| Text | text-primary, text-secondary, text-tertiary, text-inverse | ✅ Semantic names |
| Border | border, border-light | ✅ Semantic names |
| Dark mode | dark-surface, dark-surface-secondary, dark-surface-tertiary, dark-border, dark-border-light, dark-text-primary/secondary/tertiary | ⚠️ Inconsistent naming — uses hyphen prefix instead of standard Tailwind dark: handling |
| Error/Success | error (#EF4444), success (#10B981) | ✅ |
| Typography | font-family-sans (Inter), font-family-mono (JetBrains Mono) | ❌ Inter not applied to body |

### Token Issues (New Findings Beyond Prior Audit)

1. **Dark mode tokens use custom `--dark-*` variants instead of Tailwind's standard `dark:` modifier** — the codebase has defined `--dark-surface`, `--dark-border`, etc. but many components still use inline `dark:bg-slate-900` / `dark:border-slate-700` which bypass the design tokens. This creates inconsistency — some components use token values, others use raw Tailwind values.

2. **`--color-surface-tertiary` (#F3F4F6) is nearly identical to `--color-surface-secondary` (#F1F5F9)** — the 2-shade difference is barely visible. This creates false semantic separation.

3. **No focus ring token** — focus rings are hardcoded as `ring-2 ring-brand-500` with no tokenized `--focus-ring` value. The prior audit flagged this as a nit (spec says 3px, code uses 2px).

4. **No motion/transition tokens** — transition durations are hardcoded (`transition-all duration-150`, `transition-colors duration-200`, `300ms ease`). No centralized motion scale.

5. **`--color-border-light` used but not consistently** — some places use `gray-200`/`slate-200` instead.

6. **No elevation/shadow tokens** — shadows are Tailwind defaults (`shadow-sm`, `shadow-xl`). No tokenized elevation scale.

### Component Library Assessment

| Component | File | States | Status |
|-----------|------|--------|--------|
| Button | `atoms/button.tsx` | Default, hover, active, disabled, loading, focus-visible | ✅ Well-implemented — 5 variants, 5 sizes |
| Input | `atoms/input.tsx` | Default, focus, error, disabled, read-only | ✅ Good — variant system, iconLeft/iconRight, label association |
| Card | `molecules/card.tsx` | Default | ⚠️ Missing interactive variant — cards used as clickable items lack proper button semantics |
| Modal | `molecules/modal.tsx` | Open, close, sizes (sm/md/lg) | ✅ Excellent — focus trap, aria, Escape/click-outside, 3 sizes |
| Table | `ui/table.tsx` | Sortable, row selection, hover | ✅ Good — aria-sort, keyboard nav, responsive horizontal scroll |
| Badge | `atoms/badge.tsx` | Multiple variants | ✅ Used throughout |
| Avatar | `atoms/avatar.tsx` | Initials, sizes | ✅ Used throughout |
| Skeleton | `atoms/skeleton.tsx` | Text, circular, rectangular | ✅ Loading state coverage |

### Missing Components

- **Select/Dropdown** — Some pages use native `<select>` (Add Deal modal, Settings) while others use custom comboboxes (Search bar). No standardized Select component.
- **Toggle** — Dark mode toggle is a button with Sun/Moon icons, not a formal Toggle component.
- **Breadcrumbs** — Not present anywhere. Needed for deep navigation.
- **Toast/Snackbar** — Uses `react-hot-toast` library. Functional but no custom styling that matches the design system.
- **Pagination** — Built inline in contacts page, not as a reusable component.
- **DatePicker** — Not present. Dates entered manually or via native `<input type="date">`.
- **Empty State** — Separate `ui/empty-state.tsx` component exists and is used consistently.

---

## 2. Accessibility Audit (WCAG 2.2 AA)

### Existing Good Practices (From Prior Audit + New Verification)

- ✅ Semantic HTML: `<nav>`, `<main>`, `<h1>`-`<h4>` hierarchy, `<form>` elements
- ✅ Sidebar: `aria-current="page"` on active nav items
- ✅ Topbar search: Full WAI-ARIA combobox pattern (`combobox`, `listbox`, `option`, `aria-selected`, keyboard navigation)
- ✅ Modal: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, focus trap, Escape/click-outside/X close
- ✅ Color contrast: body text 6.5:1 (above 4.5:1 minimum)
- ✅ Input labels: `htmlFor`/`id` association
- ✅ Error messages: `role="alert"` on error messages, `aria-invalid` on inputs
- ✅ Dark mode: comprehensive dark theme tokens
- ✅ Keyboard navigation: Tab works through interactive elements

### New Accessibility Issues Found

| # | Issue | Location | WCAG Criterion | Severity |
|---|-------|----------|----------------|----------|
| A1 | **No skip-to-content link** | All pages | 2.4.1 Bypass Blocks (A) | **Critical** — Keyboard users must tab through all 12 sidebar links before reaching main content |
| A2 | **`prefers-reduced-motion` not respected** | `index.css` body has hardcoded `transition: background-color 300ms ease, color 300ms ease` | 1.4.4 Resize text / 2.3.3 Animation from interactions | **Major** — All transitions fire regardless of user motion preference |
| A3 | **Touch targets below 44x44px** | Email row star buttons (32px), Select stage dropdown arrows, Inline filter chips (Activities page) | 2.5.8 Target Size (AA, WCAG 2.2) | **Major** — Multiple touch targets below 44x44px minimum |
| A4 | **No `aria-label` on sidebar collapse toggle** | `sidebar.tsx` line 65 (has aria-label ✅ — verified) | 4.1.2 Name, Role, Value (A) | ✅ Fixed since prior audit |
| A5 | **Email page detail close button lacks focus-visible on mobile** | `email-page.tsx` line 232 | 2.4.7 Focus Visible (AA) | **Major** — Custom close button with no explicit focus indicator |
| A6 | **`dangerouslySetInnerHTML` with DOMPurify** — mitigated | `email-page.tsx` line 294 uses `DOMPurify.sanitize()` ✅ | 1.1.1 Non-text Content (A) | ✅ Fixed (DOMPurify now applied) |
| A7 | **Slack/Users/Audit Log page crashes leave users stranded** — no error boundary | These pages throw "404 Not Found" with no back button or navigation recovery | 3.2.1 On Focus (A) | **Critical** — Runtime errors break the application with no recovery path |
| A8 | **Email page crash is unhandled** — React error boundary not implemented anywhere | `email-page.tsx` line 335 `connections?.find` fails | 4.1.1 Parsing (A) | **Critical** — Uncaught TypeError crashes entire page |
| A9 | **Activities timeline filter buttons** — no `aria-pressed` on toggle filters (All types, Notes, Calls, etc.) | Timeline page filters | 4.1.2 Name, Role, Value (A) | **Minor** — Filter buttons act as toggles but aren't marked as such |
| A10 | **Compose Modal "To" field** uses `type="email"` but no visible label association (floating label pattern) | `email-page.tsx` line 696-704 | 1.3.1 Info and Relationships (A) | **Minor** — Input has label via Input component, verified: uses `htmlFor`/`id` |
| A11 | **Notification bell has no unread count announced** | `topbar.tsx` | 4.1.2 Name, Role, Value (A) | **Minor** — Dot has visual presence but aria-label doesn't convey count |
| A12 | **No landmark regions beyond `<nav>`** — `<main>` is present but no `<aside>` for sidebar (uses `<aside>` — ✅ verified) | sidebar.tsx uses `<aside>` semantic element | 1.3.1 Info and Relationships (A) | ✅ Correct |

### Accessibility Summary

| Severity | Count | New | Carried from Prior Audit |
|----------|-------|-----|-------------------------|
| **Critical** | 3 | A1, A7, A8 | 0 |
| **Major** | 3 | A2, A3, A5 | 5 from prior audit (focus-visible gaps, sidebar breakpoint, table selection) |
| **Minor** | 3 | A9, A11, A12 | 26 from prior audit |
| **Nits** | 0 | — | 16 from prior audit |
| **Total** | 3 new critical issues (page crashes + skip-to-content) | **44 total a11y issues (16 new + carried)** | |

---

## 3. UX Copy Audit

### Existing Good Practices

- ✅ Consistent button labels: "Add Contact", "Add Deal", "Save Changes", "Export CSV"
- ✅ Error messages use `role="alert"` and describe the problem
- ✅ Page titles are clear: "Dashboard", "Sales Pipeline", "Contacts", "Activity Timeline"
- ✅ Empty states provide guidance ("Get started by adding your first contact")
- ✅ "Sign in" / "Sign up" / "Create account" — action-oriented labels

### UX Copy Issues

| # | Location | Current Text | Issue | Recommendation |
|---|----------|-------------|-------|---------------|
| C1 | Onboarding page | "Set up your company — Tell us about your business so we can tailor the experience." | Vague — "tailor the experience" is a non-promise | "Set up your company — This helps us customise your pipeline stages and default fields." |
| C2 | Contacts empty state | "Get started by adding your first contact." | Generic | "Add your first contact — or import from a CSV to get started faster." |
| C3 | Pipeline empty state | "No deals yet" | Generic empty state | "No deals yet — Create your first deal or import from CSV." |
| C4 | Activities filter "System" | Button labelled "System" | Unclear what "System" means to a user | "System events" |
| C5 | Email compose "Discard" button | "Discard" | Negative connotation — implies permanence | "Cancel" |
| C6 | Forecast page heading | "Next 3 Months · 2026-06-01 – 2026-09-28· Scenario: Most Likely" | Hardcoded hyphen-separated date range; inconsistent spacing around · | "Next 3 months · Jun 1 – Sep 28, 2026 · Scenario: Most Likely" |
| C7 | Email page "Connect your Gmail" | "You'll be redirected to Google to authorize access." | Passive voice | "We'll redirect you to Google to grant access. Your data stays encrypted." |
| C8 | Dashboard metric cards | "No data" badge when value is $0 | Better to contextualise | "No data yet — start adding deals" |
| C9 | Settings Profile section | Labels: "First Name", "Last Name", "Email" | Standard inputs but no hint that they're editable | + "Save Changes" button is clear ✅ |
| C10 | Error page (crash) | "Unexpected Application Error!" | React default error message — no user-friendly wrapper | Implement error boundary with: "Something went wrong — Try refreshing the page or contact support." |

---

## 4. Responsive Audit

| Breakpoint | Good | Issues |
|------------|------|--------|
| **1920px+** (wide desktop) | ✅ Sidebar collapsible, max width containers constrain content, multi-column layouts work | ⚠️ No max-width on main content — dashboards stretch across full width, line lengths can exceed 120 chars on metric cards |
| **1280px** (desktop) | ✅ All layouts functional, sidebars visible, kanban horizontal, reports charts visible | ⚠️ Sidebar breakpoint: prior audit says 768-1023 should be collapsible drawer, not fixed |
| **768px** (tablet) | ✅ Auth pages stack vertically, kanban stacks vertically, contacts grid collapses | ❌ **Sidebar is fixed at 768px+** — prior audit flags this (Issue #51). Tablet users lose screen real estate to a permanently open sidebar. |
| **390px** (mobile) | ✅ Mobile sidebar overlay works, forms full-width, tables horizontal-scroll | ❌ Small touch targets (star buttons, filter chips), hamburger menu accessible |

### New Responsive Findings

1. **Email page provides excellent responsive layout** — transitions from split-pane (desktop) to single-pane (mobile) with `hidden lg:flex` pattern. This is the best responsive implementation in the app.
2. **Pipeline kanban** — responsive with `flex-col md:flex-row` but the columns don't have a minimum width, making them squeeze too thin on tablet.
3. **Dashboard charts** — Recharts charts don't resize well below 768px, with axis labels overlapping.
4. **Modal sizes** — `max-w-sm` (384px) on mobile is appropriate but the modal doesn't go fullscreen below 480px.

---

## 5. Interaction Design Analysis

### Flows That Work Well

- **Login → Onboarding → Dashboard** — smooth auth guard, onboarding guard, redirect to dashboard
- **Pipeline kanban drag-and-drop** — uses `@dnd-kit/core` with keyboard sensor support, aria-compatible
- **Modal interaction patterns** — consistent Escape/click-outside/X close, focus trap, body scroll lock
- **Search combobox** — full keyboard navigation with arrow keys, debounced search, group results by type

### Interaction Design Issues

| # | Issue | Location | Severity |
|---|-------|----------|----------|
| I1 | **No confirmation on destructive actions** — deleting a contact or deal has no confirmation dialog | All CRUD pages | **Major** — Violates Nielsen's "User control and freedom" heuristic |
| I2 | **Errors don't persist after page navigation** — no toast or persistent notification for background failures | All pages | **Major** — toast disappears after 4 seconds |
| I3 | **No loading skeleton on Profile/Settings save** — "Save Changes" button shows loading state but form doesn't show which fields are being saved | Settings page | **Minor** |
| I4 | **Activities timeline filters** — clicking a filter button replaces the active filter without visual transition; no way to select multiple types | Activities page | **Minor** |
| I5 | **No auto-save on long forms** — Compose email, Settings profile, Custom fields all require manual save with no draft recovery | Multiple pages | **Minor** |
| I6 | **Dashboard metric cards** — Trend arrows (▲▼) show "vs last month" but there's no way to change the comparison period | Dashboard | **Minor** |

---

## 6. UI State Coverage

### Loading States
- ✅ Skeletons used throughout (dashboard metrics, email list, contacts table, timeline)
- ✅ Spinner component for auth loading and full-page loading
- ✅ Button loading spinners with `aria-busy`

### Empty States
- ✅ Custom empty states with icon, title, description, and CTA button for most pages
- ⚠️ Forecast and Reports use raw text ("No monthly breakdown data for this period") instead of the consistent Empty State component

### Error States
- ✅ Error states with icon, message, and "Try Again" button for contacts, email, timeline
- ❌ **No global error boundary** — page crashes (Email, Slack, Users, Audit Log) show React raw error screen
- ⚠️ Error messages are inconsistent — some use `role="alert"`, others don't

### Edge States

| State | Coverage |
|-------|----------|
| First-time user | ✅ Onboarding wizard |
| Empty (no data) | ✅ Most pages |
| Filtered (no results) | ⚠️ Not clearly tested — search returns empty dropdown but no "No results" inline message |
| Loading | ✅ Skeleton components |
| Partial failure | ❌ Not handled — individual section failures can block whole page |
| Offline | ❌ Not handled — no offline indicator or queuing |
| Rate limited | ❌ Not handled |
| 404 (crash) | ❌ Pages that don't load show React error boundary fallthrough |

---

## 7. Craft Recommendations (Prioritised)

### P0 — Must Fix
1. **Add React Error Boundary** — wrap each page route to catch crashes gracefully and show user-friendly recovery UI
2. **Add skip-to-content link** as first focusable element for keyboard users
3. **Respect `prefers-reduced-motion`** — disable transitions when user has motion sensitivity
4. **Increase touch targets to 44x44px minimum** (email star buttons, filter chips)

### P1 — Should Fix
5. **Standardize select/dropdown component** — replace native `<select>` in Add Deal modal
6. **Add confirmation dialogs** for destructive actions (delete contact, delete deal)
7. **Implement toast notification system** with proper styling matching the design system
8. **Apply Inter font to body** (carried from prior audit — blocker)

### P2 — Nice to Fix
9. **Tokenize focus ring width** to match spec (3px not 2px)
10. **Create consistent empty state component usage** in Reports/Forecast
11. **Add breadcrumbs** to deep pages (Contacts > Detail, Email > Templates)
12. **Eliminate hardcoded Tailwind colors** — use design tokens everywhere

### P3 — Future
13. **Create standard Select component** with typeahead, keyboard nav, and dropdown
14. **Build DatePicker component** that fits the design system
15. **Add pagination component** that can be reused across tables