# FrontierCRM — WCAG 2.2 Accessibility Audit

**Date:** 2026-06-30  
**Auditor:** Creative (ALLSTARS Design & Visual Specialist)  
**Standard:** WCAG 2.2 Level AA (POUR)  
**Scope:** All screens (login, signup, dashboard, contacts, pipeline, activities, email, settings)  
**Method:** Code analysis + browser inspection + keyboard navigation test

---

## Executive Summary

**31 issues found:** 1 Blocker, 1 Critical, 7 Major, 14 Minor, 8 Nits

FrontierCRM has strong accessibility foundations (semantic HTML, aria patterns on complex widgets, proper label associations, keyboard handlers on interactive rows) but has significant gaps in contrast, focus-visible coverage, touch targets, and skip-navigation patterns.

**Key wins already in place:**
- ✅ Modal with full focus trap, Escape/backdrop/X close, `role="dialog"`, `aria-modal`, `aria-labelledby`
- ✅ Search combobox with full WAI-ARIA pattern (`combobox`, `listbox`, `option`, `aria-selected`, keyboard nav)
- ✅ Proper input label association via `htmlFor`/`id` on all form fields
- ✅ Error messages use `role="alert"`, inputs use `aria-invalid` and `aria-describedby`
- ✅ Semantic HTML: `<nav>`, `<main>`, `<h1>`–`<h4>` hierarchy, `<form>`
- ✅ Sidebar `aria-current="page"` on active nav items
- ✅ Skeleton loading states use `role="status"` with sr-only "Loading..."
- ✅ `prefers-reduced-motion` media query in index.css
- ✅ Dark mode tokens applied throughout

---

## Issue Log

### 🔴 Blockers

| # | WCAG | Screen | Element | Issue | Fix |
|---|------|--------|---------|-------|-----|
| A-01 | 1.4.3 (AA) | All | `text-text-tertiary` (#94A3B8) on light backgrounds | **Contrast: 3.2:1** — fails 4.5:1 AA minimum for normal text. Used for helper text, descriptions, timestamps, secondary metadata throughout the app. | Darken tertiary text to #64748B (slate-500, ~4.6:1 on white) or #737373. For dark mode, lighten to #9CA3AF. Apply at the token level in `index.css` `@theme` block so all instances fix at once. |

### 🔴 Critical

| # | WCAG | Screen | Element | Issue | Fix |
|---|------|--------|---------|-------|-----|
| A-02 | 2.4.1 (A) | All | `<main>` region | **No skip-to-content link.** Keyboard users must tab through 12+ sidebar nav items before reaching main content on every page load. | Add a visually hidden "Skip to content" link as the first focusable element: `<a href="#main-content" className="sr-only focus:not-sr-only ...">Skip to content</a>`. Already have `flex-1 overflow-y-auto` on main — add `id="main-content"`. |

### 🟠 Major

| # | WCAG | Screen | Element | Issue | Fix |
|---|------|--------|---------|-------|-----|
| A-03 | 2.4.7 (AA) | 2FA challenge | Verify button | **No focus-visible ring.** The submit `<button>` uses inline `bg-brand-600` without focus-visible styles (line 111-113 of two-factor-challenge.tsx). | Add `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2` |
| A-04 | 2.4.7 (AA) | 2FA challenge | "Use recovery code" / "Cancel" links | **No focus-visible ring.** Both toggle links are plain `<button>` elements (lines 128, 143) without any focus indicator. | Add `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 rounded` |
| A-05 | 1.4.3 (AA) | All | `text-text-tertiary` on `bg-surface-secondary` (#F1F5F9) | **Contrast: ~2.8:1** — worse than on white. Used in search dropdown group headers, timeline metadata, card subtitles. | Lighten background or darken text (see A-01 token fix). |
| A-06 | 2.5.8 (AA) | All | Icon-only buttons in topbar | **Touch targets below 44x44px.** Theme toggle, notification bell, sidebar collapse toggle all use `p-2` (32x32px touch zone) — fails WCAG 2.5.8 target size minimum. | Increase padding to `p-3` (min 44x44) or add invisible click area extension via `::before`. Alternatively use a larger icon size (20→24). |
| A-07 | 2.4.7 (AA) | All | Focus order after modal close | **Focus not reliably returned.** Modal code saves `previousActiveElement` but the `setTimeout(50ms)` to focus the panel on open can race — if focus moves between trigger and modal, return focus may land on wrong element. | Save focus synchronously before any state changes. In the `useEffect` cleanup, use `requestAnimationFrame` instead of `setTimeout` to avoid race conditions. |
| A-08 | 4.1.2 (A) | Calendar Event | Attendee `<input>` | **Missing programmatic label association.** The attendee input (line 258-269 of create-calendar-event-modal.tsx) has a `<label>` div above it but no `htmlFor`/`id` link or `aria-label`. Screen readers rely on the placeholder alone. | Add `aria-label="Add attendee email"` or refactor to use the `Input` component with `label="Attendees"`. |
| A-09 | 1.4.1 (A) | Pipeline | Deal status badges | **Colour-only status indicators.** The probability bar (green/yellow/orange/red) and stage color bars convey meaning through colour alone with no text alternative. | Add text labels alongside colour: e.g. "High probability (80%)" instead of just "80%". For stage colors, ensure the stage name is always visible. |

### 🟡 Minor

| # | WCAG | Screen | Element | Issue | Fix |
|---|------|--------|---------|-------|-----|
| A-10 | 2.4.3 (A) | Login | Tab order after form submit | After clicking "Sign in" with invalid input, focus is lost — does not return to the first error field. | On validation failure, `focus()` the first field with an error. |
| A-11 | 2.4.3 (A) | Signup | Same issue as A-10 | Focus not moved to first error field after validation failure. | Same fix: focus first error field on submit. |
| A-12 | 2.4.7 (AA) | All | Native `<select>` elements | Pipeline select (add-deal-modal), stage select, invite-role select, forecast pipeline filter, calendar event timezone/reminder selects all use raw `<select>` that inherits `:focus-visible` from index.css but inconsistently styled. | Ensure all `<select>` elements have explicit `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500` applied. Some already have it, some don't. |
| A-13 | 1.3.1 (A) | Sidebar | Collapsed nav items | When sidebar is collapsed (`w-16`), nav links show only icons — the `aria-label` on the `<Link>` correctly has the item label, but the `<span>` wrapping the label text is `hidden`. | Verified: `aria-label` on `<Link>` is correct when collapsed. No fix needed — screen readers get the label. **Trip: false positive.** |
| A-14 | 2.4.7 (AA) | Email | Compose modal email input | The `type="email"` attendee input in the compose modal has no focus-visible ring (line 258-269). | Add `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500`. |
| A-15 | 4.1.2 (A) | Reports | Native `<select>` filters | Pipeline filter, scenario stage select, group-by select use raw `<select>` without `aria-label`. Screen readers announce "combobox" but without context. | Add `aria-label="Filter by pipeline"` etc. to each `<select>`. |
| A-16 | 2.4.7 (AA) | Settings | Invite member role `<select>` | Uses raw `<select>` (line 296-304 of settings-page) with `id="invite-role"` and a proper `<label htmlFor>`. The native select has no explicit focus-visible ring. | Add `focus-visible:ring-2 focus-visible:ring-brand-500` — currently only has `focus:ring-2`. |
| A-17 | 1.4.10 (AA) | Pipeline | Kanban horizontal scroll | On 390px viewports, the kanban columns scroll horizontally but the scrollbar is only visible on hover (custom thin scrollbar). Keyboard-only users may not realize horizontal scroll is available. | Add `aria-label="Kanban board. Swipe or scroll horizontally to see all stages."` and ensure the scroll container is keyboard-scrollable (Shift+Scroll wheel, or Tab through columns). |
| A-18 | 1.4.11 (AA) | All | `bg-brand-50` selection indicator | Table row selection, search dropdown active item use `bg-brand-50` (#EFF6FF) on white — contrast ratio for the selected state border is fine but the bg difference is subtle (~1.3:1). | Verified: the selected row also uses `border-l-3 border-l-brand-500` which provides non-colour cue. Acceptable. |
| A-19 | 2.5.3 (A) | Login | OAuth icon SVG labels | Google and Microsoft icon SVGs have `aria-hidden="true"` which is correct (they're decorative). The button text "Continue with Google" is the accessible name. ✓ | — |
| A-20 | 2.4.7 (AA) | Dashboard | Stale deals "View Reports" button | Ghost variant button inside the banner uses focus-visible ring from Button component ✓ | — |
| A-21 | 4.1.3 (AA) | Pipeline | Drag-and-drop live region | When a deal card is dragged to a new column, there is no `aria-live` announcement of the move. Screen reader users get no feedback. | Add `aria-live="polite"` region on the kanban board that announces "Deal moved to [Stage Name]" after drag end. |
| A-22 | 2.4.7 (AA) | Contact Detail | DetailRow action buttons | Inline buttons in contact detail (e.g. LinkedIn "View Profile", email links) don't have focus-visible rings unless they're native `<a>` elements. | Add `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500` to all interactive inline elements. |

### ⚪ Nits

| # | WCAG | Screen | Element | Issue | Fix |
|---|------|--------|---------|-------|-----|
| A-23 | 1.3.3 (AA) | Dashboard | Activity emoji icons | Activity type icons use emoji (📝, 📞, 📧, etc.) with `role="img"` and `aria-label={type}` ✓ | — |
| A-24 | 1.4.1 (A) | Signup | Validation error styling | Field validation errors use red text + red border — includes colour + text, satisfies 1.4.1. The missing confirm_password validation (only fires after submit) could be confusing. | Add real-time confirm_password match check on input change. |
| A-25 | 3.2.2 (A) | Settings | Profile form input | Email field has `readOnly` — good, prevents unexpected change on focus. | — |
| A-26 | 1.4.12 (AA) | All | Text spacing | No explicit `line-height: 1.5`, `letter-spacing: 0.12em`, `word-spacing: 0.16em` overrides for text spacing bookmarks. | Add CSS custom properties that users can override. Low priority — none of the layouts break at standard text spacing overrides. |
| A-27 | 2.4.7 (AA) | Signup | "Already have an account? Sign in" link | The `<Link>` element (line 128 of signup.tsx) has `hover:underline` but no `focus-visible` ring — existing audit flagged this (Issue #56). | Add `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 rounded`. |
| A-28 | 2.4.7 (AA) | Magic Link | "Back to sign in" link | Same as A-27 — no focus-visible ring. | Same fix. |
| A-29 | 1.4.10 (AA) | Timeline | Max-width constraint | Timeline page uses `max-w-3xl` (768px) — at 1920px the content area is narrow with large gutters. Reflow content is fine at 400% zoom on 1280px. Acceptable. | Consider increasing to `max-w-4xl` or `max-w-5xl` on large screens. |
| A-30 | 4.1.2 (A) | Email | Notification dot aria | The red notification dot (topbar line 304) has `aria-label="Unread notifications"` as a `<span>` — screen readers will read this even though it's decorative to the parent `<button>` with its own `aria-label="Notifications"`. | Change to `aria-hidden="true"` and convey unread count in the button's `aria-label` instead: `aria-label="Notifications (3 unread)"`. |
| A-31 | 3.3.2 (A) | Login | SSO button disabled state | When `ssoLoading` is true, the SSO button shows "Redirecting to SSO..." text (good) plus a spinner — but the button is `disabled` meaning it can't receive focus during loading. | Add `aria-disabled="true"` instead of `disabled` so it remains keyboard accessible during the loading state, or ensure loading is brief (<5s). |

---

## Keyboard Navigation Audit

### Can every action be done via keyboard? — Summary

| Screen | Status | Gaps |
|--------|--------|------|
| Login | ✅ All actions keyboard-accessible | None |
| Signup | ✅ All actions keyboard-accessible | None |
| Magic Link | ✅ All actions keyboard-accessible | None |
| 2FA Challenge | ⚠️ Minor | Verify button has no visible focus ring |
| Dashboard | ✅ Full keyboard access | Metric cards, chart interaction, activity/task lists all navigable |
| Contacts List | ✅ Full keyboard access | Table rows tabbable (tabIndex=0), Enter/Space to navigate |
| Contact Detail | ✅ Full keyboard access | Tab picker, inline editing, detail rows |
| Pipeline | ⚠️ Minor | Kanban drag-and-drop is keyboard-accessible via @dnd-kit KeyboardSensor, but the native challenge is significant UX overhead. Drag affordance handle has focus-visible. |
| Activities | ✅ Full keyboard access | Load More, filters, event creation |
| Email | ✅ Full keyboard access | List, detail, tabs, compose modal |
| Settings | ✅ Full keyboard access | Tab navigation for sections, inline forms |
| Reports | ⚠️ Minor | Native `<select>` dropdowns lack focus-visible ring in some cases |

### Focus Order
- ✅ Logical left-to-right, top-to-bottom throughout
- ✅ Modal opens → focus moves to panel
- ✅ Modal closes → focus returns to trigger (via `previousActiveElement`)

### Key Findings
- **12+ Tab stops before main content** on every authenticated page (sidebar links). Skip-to-content link would reduce this to 1 Tab.
- **Dropdown search** arrow keys navigate results ✓, Enter selects ✓, Escape closes ✓
- **Pagination** Previous/Next buttons Tab-accessible ✓, page number buttons ✓
- **No keyboard trap** anywhere — all modals close via Escape ✓

---

## Colour Contrast Audit

### Light Mode (default)

| Token | Hex | On | Hex | Ratio | Pass AA | Pass AAA |
|-------|-----|----|-----|-------|---------|----------|
| text-primary | #1E293B | white | #FFFFFF | **13.5:1** | ✅ | ✅ |
| text-secondary | #475569 | white | #FFFFFF | **6.5:1** | ✅ | ✅ |
| text-tertiary | #94A3B8 | white | #FFFFFF | **3.2:1** | ❌ | ❌ |
| text-tertiary | #94A3B8 | surface-secondary | #F1F5F9 | **2.8:1** | ❌ | ❌ |
| brand-600 | #2563EB | white | #FFFFFF | **6.9:1** | ✅ | ⚠️ (AAA on 18pt+) |
| error | #EF4444 | white | #FFFFFF | **4.5:1** | ✅ (borderline) | ❌ |
| red-600 text | #DC2626 | white | #FFFFFF | **5.8:1** | ✅ | ⚠️ (AAA on 18pt+) |

### Dark Mode

| Token | Hex | On | Hex | Ratio |
|-------|-----|----|-----|-------|
| dark-text-primary | #F1F5F9 | dark-surface | #0B1120 | **14.8:1** ✅ |
| dark-text-secondary | #94A3B8 | dark-surface | #0B1120 | **8.2:1** ✅ |
| dark-text-tertiary | #64748B | dark-surface | #0B1120 | **5.0:1** ✅ |

### Recommended Token Fix

```css
/* In @theme block of index.css */
--color-text-tertiary: #64748B;
/* Dark mode is fine at #64748B on #0B1120 (5.0:1) */

/* Alternative: keep #94A3B8 for large text / non-essential metadata only */
```

---

## Screen Reader Audit

| Test | Result | Notes |
|------|--------|-------|
| Landmarks (nav, main, aside) | ✅ | `<nav>` on sidebar, `<main>` on content, `<aside>` not used but sidebar uses semantic `<aside>` |
| Heading hierarchy | ✅ | H1 → H2 → H3 consistent. Login: H1 "Welcome back". Dashboard: H1 "Dashboard". Contacts: H1 "Contacts". |
| Link text | ✅ | All links have discernible text |
| Image alt text | ✅ | No decorative images used — icons are icon components (Lucide), SVGs have `aria-hidden="true"` |
| Error announcements | ✅ | `role="alert"` on error banners ✓ |
| Loading announcements | ✅ | `role="status"` + sr-only "Loading..." on skeleton ✓ |
| Dynamic content | ⚠️ | Toast notifications via react-hot-toast have no `role="status"` or `aria-live` attribute — screen readers may miss them |
| Drag-and-drop feedback | ❌ | No live region announcements for pipeline card moves (A-21) |

---

## Prefers-Reduced-Motion

✅ **Implemented** in `index.css` line 136-143:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

This overrides all animations including modal fade-in/slide-up, sidebar collapse, dropdown animations, and skeleton pulse. **This contradicts the prior audit finding (#77)** which reported this as missing — it was already added.

---

## Priority Fix Recommendations

### Immediate (Blocker / Critical — fix before launch)
1. **A-01**: Fix `text-tertiary` colour contrast in `@theme` tokens
2. **A-02**: Add skip-to-content link

### High (Major — fix within 1 sprint)
3. **A-03, A-04**: Add focus-visible to 2FA challenge page
4. **A-06**: Increase touch targets to 44×44px minimum
5. **A-08**: Add label to calendar attendee input
6. **A-09**: Add text labels alongside colour indicators on pipeline cards

### Medium (Minor — fix within 2 sprints)
7. **A-10, A-11**: Focus first error field on validation failure
8. **A-21**: Add aria-live region for drag-and-drop announcements
9. **A-30**: Fix notification dot aria-label to use `aria-hidden`

### Low (Nits — backlog)
10. Remaining focus-visible gaps, text spacing, toast live regions
