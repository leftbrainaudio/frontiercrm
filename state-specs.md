# FrontierCRM — Component State Documentation

**Date:** 2026-06-30  
**Auditor:** Creative (ALLSTARS Design & Visual Specialist)

---

## Table of Contents

1. [State Architecture Overview](#1-state-architecture-overview)
2. [Screen-by-Screen State Map](#2-screen-by-screen-state-map)
3. [Loading Patterns](#3-loading-patterns)
4. [Empty State Patterns](#4-empty-state-patterns)
5. [Error State Patterns](#5-error-state-patterns)
6. [Success & Feedback Patterns](#6-success--feedback-patterns)
7. [Edge Cases](#7-edge-cases)
8. [Implementation Guidance](#8-implementation-guidance)

---

## 1. State Architecture Overview

FrontierCRM uses **React Query (TanStack Query)** for server state management. Every data-fetching hook returns:
- `data` — the response payload
- `isLoading` — true during the initial fetch (no cached data)
- `isFetching` — true during any fetch (including background refetches)
- `isError` — true if the request failed
- `error` — the error object
- `refetch` — manually trigger a re-fetch

### State Matrix

Every data view goes through these states:

```
[isLoading]
    ↓
[isError] ──→ ErrorState (with retry)
    ↓
[data is null/empty] ──→ EmptyState (with action guidance)
    ↓
[data has results] ──→ Normal content (Table/List/Chart)
```

---

## 2. Screen-by-Screen State Map

### 2.1 Login Page

| State | Implementation | UI Pattern | Notes |
|-------|---------------|------------|-------|
| **Loading** (form submit) | Button `loading` prop | Spinner replaces button text, button disabled | `aria-busy="true"` on Button |
| **Error** (validation) | `fieldErrors` state | Red border on input, `role="alert"` error text below | Per-field validation ✓ |
| **Error** (API failure) | `error` state | Red banner with `role="alert"` above form | Generic "Invalid credentials" — should be more specific (see UX-01) |
| **Success** | Auth redirect | Redirects to `/dashboard` or onboarding | No success toast needed |
| **SSO loading** | `ssoLoading` state | Spinner + "Redirecting to SSO..." text | Button disabled during loading |
| **2FA flow** | `isAwaiting2FA` flag | Replaces entire page with `TwoFactorChallenge` component | Good — clean state transition |

### 2.2 Signup Page

| State | Implementation | UI Pattern | Notes |
|-------|---------------|------------|-------|
| **Loading** (submit) | Button `loading` prop | Spinner | ✓ |
| **Error** (field validation) | `fieldErrors` state | Per-field error on First name, Last name, Email, Password | ✅ Implemented |
| **Error** (API failure) | `error` state | Red banner at top | Could show field-specific errors from API |
| **Success** | Auth redirect | Redirects to `/onboarding` or `/dashboard` | ✓ |
| **Confirm password** mismatch | Client-side check | "Passwords do not match" error (only on submit) | ⚠️ Should also validate in real-time |

### 2.3 Dashboard

| State | Implementation | UI Pattern | Notes |
|-------|---------------|------------|-------|
| **Loading** | `isLoading` from `useDashboardReport` | Skeletons in all 4 MetricCards + chart skeleton in each section | Good — skeleton per card, not one big spinner |
| **Empty** (no data) | `report?.summary.active_deals === 0` | MetricCards show "No data" badge, chart shows EmptyState "No pipeline data yet" | ✅ Graceful degredation |
| **Empty** (no activities) | `activities.length === 0` | `ActivityEmptyState` with SVG line chart illustration | ✅ Branded illustration |
| **Empty** (no tasks) | `tasks.length === 0` | `EmptyState` with "No tasks due" text | ⚠️ Could be more friendly |
| **Error** | Via toast from API call | Toast notification only — no inline ErrorState | ⚠️ Inline ErrorState would be better for the full page |
| **Stale deals warning** | `staleDeals` data | Red/orange banner with action button | ✅ Good — proactive alert |
| **Success** (data loaded) | Report data available | Charts, metric cards, activity list, task list all rendered | ✅ |
| **Partial loading** | Individual subqueries can still be loading while others show data | Skeleton for the loading section, content for loaded sections | ✅ Good approach |

### 2.4 Contacts List

| State | Implementation | UI Pattern | Notes |
|-------|---------------|------------|-------|
| **Loading** | `isLoading` from `useContacts` | Table skeleton (8 rows) via `Table loading` prop | ✅ |
| **Empty** (no results) | `contacts.length === 0 && !isLoading` | `EmptyState` with UserPlus icon, "No contacts yet", "Get started by adding your first contact." + Add Contact button | ✅ Excellent |
| **Empty** (search no results) | Table `emptyContent="No contacts found."` | Table renders empty row with "No contacts found." | ⚠️ Could include "Try a different search term" guidance |
| **Error** | `isError === true` | Card wraps `ErrorState` with "Failed to load contacts" + Retry button (calls `refetch()`) | ✅ Good |
| **Pagination** | `page` state + `totalPages` | Page numbers with ellipsis, Previous/Next buttons | ✅ Good |
| **Success** | Data returned | Contact table with avatar, name, email, phone, job title, account, created date | ✅ |

### 2.5 Contact Detail

| State | Implementation | UI Pattern | Notes |
|-------|---------------|------------|-------|
| **Loading** | From `useContact` | `DetailSkeleton` — full page skeleton with breadcrumb, header card, tabs, content grid | ✅ Comprehensive |
| **Error** | `isError` | `ErrorState` with retry | ✅ |
| **Empty** (not found) | Via 404 API response | Error state with "Contact not found" | ⚠️ Should handle 404 specifically |
| **Edit mode** | `isEditing` state | Inline inputs replace DetailRow values, Save/Cancel buttons appear | ✅ |
| **Save loading** | `saving` state | Button spinner | ✅ |
| **Save error** | Catch handler | Toast error message | ⚠️ Could also show inline error |
| **Tab switching** | `activeTab` state | Content swaps without page reload | ✅ |
| **Tab loading** | Per-tab API loading | Card skeleton for tab content | ✅ |

### 2.6 Pipeline / Kanban

| State | Implementation | UI Pattern | Notes |
|-------|---------------|------------|-------|
| **Loading** | `isLoading` from data hooks | `DealCardSkeleton` (3 per column), columns rendered with color bars | ✅ |
| **Empty** (no deals in column) | `deals.length === 0` | "No deals" text centered in column | ❌ **POOR** — should use CTA to add deal |
| **Drag start** | `DragStartEvent` | Original card dims (opacity 0.4), DragOverlay shown with `scale-105 rotate-3` | ✅ |
| **Drag over** | `isOver` state | Column gets `ring-2 ring-brand-500/50` highlight + background tint | ✅ |
| **Drag end** | `DragEndEvent` | API call to update deal stage, invalidate queries, toast "Deal updated" | ✅ |
| **Error** (API) | Catch on mutation | Toast error via `react-hot-toast` | ⚠️ No inline error state for failures |
| **Add Deal modal open** | `showAddDeal` state | `AddDealModal` renders as modal overlay | ✅ |
| **Form validation** | `errors` state | Per-field error messages on inputs, form-level error banner | ✅ |
| **Submit loading** | `createDeal.isPending` | Button spinner | ✅ |
| **Deal detail modal** | `selectedDeal` state | `DealDetailModal` with edit/view modes | ✅ |
| **Status change** (won/lost) | `changeStatus` mutation | Toast success, modal closes, queries invalidated | ✅ |

### 2.7 Activity Timeline

| State | Implementation | UI Pattern | Notes |
|-------|---------------|------------|-------|
| **Loading** (initial) | `isLoading && page === 1` | `TimelineSkeleton` — 5 rows with circular avatars + text lines | ✅ |
| **Loading** (more) | `isLoading && page > 1` | Button shows "Loading..." with spinner | ✅ |
| **Empty** | `allEntries.length === 0` | `TimelineEmptyState` using shared EmptyState component | ✅ |
| **Error** | `isError` | `TimelineErrorState` with message + "Try again" button (calls `refetch()`) | ✅ |
| **Filter active** | `filters` state + URL params | Context banner showing filter scope + "Clear filter" link | ✅ |
| **Load more** | `hasMore` state | "Load more (X shown)" button, scrolls new results in | ✅ |
| **All loaded** | `!hasMore && allEntries.length > 0` | "Showing all X activities" text | ✅ |
| **Create meeting modal** | `showCreateMeeting` state | `CreateCalendarEventModal` renders as modal | ✅ |

### 2.8 Email

| State | Implementation | UI Pattern | Notes |
|-------|---------------|------------|-------|
| **Loading** (list) | `isLoading` from `useEmails` | `EmailListSkeleton` — 6 rows with avatar + text lines | ✅ |
| **Empty** (connected, no emails) | `emails.length === 0` | `EmptyState` per tab (Inbox/Sent/Starred) with context-appropriate messages | ✅ |
| **Not connected** | No Gmail connection | `NotConnectedState` with "Connect your Gmail" heading, explanation, and CTA button | ✅ Excellent |
| **Error** | `isError` | `ErrorState` with "Try again" button | ✅ |
| **Email detail** (mobile) | `selectedEmailId` + `lg:hidden` | Detail replaces list view, back button in header | ✅ |
| **Email detail** (desktop) | Selected state | Split view: list on left, detail on right | ✅ |
| **Compose modal** | `composeOpen` state | Modal with form fields | ✅ |
| **Sending** | `composeSending` state | Button shows spinner, "Cancel" disabled, 28s timeout shown | ✅ |
| **Send success** | API response `status === 'sent'` | Toast "Email sent", modal closes, form resets | ✅ |
| **Send failure** | API error | Error message in compose modal + "Try again" / "Save Draft" buttons | ✅ |
| **Timeout** | 28s timer | "Still sending..." message below button | ✅ |
| **Tab switch** | `activeTab` state | List refreshes with new filter params | ✅ |

### 2.9 Reports

| State | Implementation | UI Pattern | Notes |
|-------|---------------|------------|-------|
| **Loading** | `reportLoading` | Subcomponent-level loading (MetricCardsRow, PipelineValueChart all have loading prop) | ✅ |
| **Empty** (no report data) | `!report || report.summary.active_deals === 0` | Chart shows empty state | ✅ |
| **Forecast loading** | `forecastLoading` | `ForecastSummaryCards` shows loading, spinner shown separately | ✅ |
| **Forecast empty** | No forecast data | "No forecast data available. Select a quarter and configure scenarios above." | ✅ |
| **Error** | Via toast | Toast notification | ⚠️ Could add inline error state |
| **Tab switch** | `activeTab` state | Dashboard ↔ Forecast | ✅ |
| **Export** | Export button clicks | Download initiated | ✅ |

### 2.10 Settings

| State | Implementation | UI Pattern | Notes |
|-------|---------------|------------|-------|
| **Loading** (profile) | `saving` state | Button spinner | ✅ |
| **Save success** | API success | Toast "Profile updated" | ✅ |
| **Save error** | API failure | Toast error | ✅ |
| **Team loading** | `isLoading` from `useMemberships` | `TabSkeleton` — 4 skeleton rows | ✅ |
| **Team error** | `isError` | `ErrorState` with message | ✅ |
| **Team empty** | `members.length === 0` | `EmptyState` "No team members yet. Invite someone to get started." | ✅ |
| **Invite modal** | `inviteOpen` state | Modal with email + role fields | ✅ |
| **Invite loading** | `inviteMember.isPending` | Button spinner | ✅ |
| **Integration connect** | Popup OAuth flow | Popup window, polling for close, toast feedback | ⚠️ Edge case — popup could be blocked |

---

## 3. Loading Patterns

### Skeleton Loading (Preferred)
**Used for:** Dashboard, Contacts List, Contact Detail, Activities, Email, Settings

```tsx
// Shared Skeleton component — atoms/skeleton.tsx
<Skeleton variant="text" width="60%" />   // Text line
<Skeleton variant="circular" width={32} height={32} />  // Avatar
<Skeleton variant="rectangular" width={240} height={180} />  // Chart/Image area
<Skeleton count={3} />  // Multiple text lines
```

**Best practices already in use:**
- Skeletons match the layout shape of the real content ✅
- Each skeleton has `role="status"` with sr-only "Loading..." ✅
- `noAnimation` prop available for print or reduced-motion ✅
- Pulses use Tailwind `animate-pulse` which is controlled by `prefers-reduced-motion` ✅

### Spinner Loading
**Used for:** Button loading states, inline operations, full-page auth redirects

```tsx
// Button loading: spinner replaces icon/children
<Button loading>Create Deal</Button>
// → renders Loader2 spinner + visually hidden children

// Inline spinner: used sparingly
<div className="animate-spin h-6 w-6 border-2 border-brand-500 border-t-transparent rounded-full" />
```

**Rule of thumb:** Use **skeletons** for initial content load (tells users the *structure* of what's coming). Use **spinners** for button/inline operations where the content won't change shape.

### Full-Page Loading
```tsx
// Used in AppLayout for auth check
<Spinner fullPage />
```

**Only used during authentication verification** — never for data loading. ✅

---

## 4. Empty State Patterns

### Shared EmptyState Component
```tsx
<EmptyState
  icon={<Inbox className="h-8 w-8" />}   // Optional — defaults to Inbox icon
  title="No emails yet"                     // Required
  description="Your inbox is empty."        // Optional
  action={{                                 // Optional — CTA button
    label: "Connect Gmail",
    onClick: handleConnect,
  }}
  illustration={<CustomSVG />}             // Optional — replaces icon
/>
```

**Current component renders:**
1. Icon (48px circle in surface-secondary bg) or Illustration
2. Title (h3, text-base, font-semibold)
3. Description (p, text-sm, max-w-sm centered)
4. Action button (primary variant, md size, mt-6)

### Empty State Checklist

| Element | Required? | Current Coverage |
|---------|-----------|------------------|
| Icon/Illustration | ✅ Yes — visual cue | ✅ All have icons or illustrations |
| Title | ✅ Yes — what's missing | ✅ All have titles |
| Description | ✅ Yes — guidance text | ✅ Most have descriptions |
| Action button | ⚠️ When an action is available | ❌ Missing on Pipeline column empty state |
| Fallback (no permission) | ✅ When user can't act | ✅ Handled by role gates |

### Empty State Quick Reference

| View | Title | Description | Action |
|------|-------|-------------|--------|
| Contacts | "No contacts yet" | "Get started by adding your first contact." | ✅ "Add Contact" |
| Contacts (search) | — | "No contacts found." (table emptyContent) | ❌ "Try a different search" hint |
| Pipeline column | "No deals" ❌ | Missing — see UX-03 fix | ❌ Missing |
| Dashboard chart | "No pipeline data yet" | — | ❌ N/A |
| Dashboard tasks | "No tasks due" | — | ❌ N/A |
| Dashboard activity | Line chart illustration | "No recent activity" badge | ❌ N/A |
| Timeline | "No activity yet" | Full instructional description | ❌ N/A |
| Email inbox | "No emails yet" | Instructional text | ❌ N/A |
| Email (not connected!) | "Connect your Gmail" | Full OAuth guidance | ✅ "Connect Gmail" |
| Team members | "No team members yet..." | Instructional text | ✅ Via page btn |

---

## 5. Error State Patterns

### Shared ErrorState Component
```tsx
<ErrorState
  title="Something went wrong"              // Optional — defaults to this
  description="An unexpected error occurred." // Optional with good default
  errorDetail="ERR_401"                     // Optional — error code (shown in muted mono)
  onRetry={() => refetch()}                 // Optional — retry button
/>
```

**Current component renders:**
1. AlertTriangle icon (red circle background)
2. Title (h3)
3. Description (p, max-w-sm)
4. Error detail (code, pre-like, muted)
5. "Try Again" button (secondary, with optional onClick)

### Error Recovery Flows

| Error Type | Pattern | Recovery |
|-----------|---------|----------|
| **Network failure** | Inline ErrorState | "Try Again" calls `refetch()` |
| **API validation error** | Per-field error messages | User corrects fields |
| **API general error** | Toast notification | "Try again" (no action) |
| **Auth error** | Redirect to login | Automatic redirect |
| **2FA failure** | Error text in 2FA form | User retries code entry |
| **Mutation error** | Toast + button re-enable | User can retry action |
| **Send timeout** | Timeout UI in compose modal | Retry or save as draft |
| **OAuth popup blocked** | Toast "Popup blocked" | Manual instruction to allow popups |

---

## 6. Success & Feedback Patterns

### Toast Notifications
Uses `react-hot-toast` for ephemeral feedback:

| Type | Duration | Used For |
|------|----------|----------|
| `toast.success(msg)` | 4s (default) | Mutation success (deal created, email sent, profile updated, contact saved) |
| `toast.error(msg)` | 4s (default) | Mutation failure, network errors |

**All toasts appear in the top-right corner** (default position). No custom positioning.

### Success States Without Toast

| Interaction | Feedback | Notes |
|-------------|----------|-------|
| Form submit → redirect | Redirect happens — no toast needed | 💡 Could add brief toast on landing page: "Welcome back!" |
| Tab switch | Instant content swap | ✅ No loading flash thanks to React Query cache |
| Theme toggle | Instant visual change | ✅ Smooth CSS transition |
| Sidebar collapse | Smooth width animation | ✅ 200ms transition |

---

## 7. Edge Cases

| Edge Case | Current Handling | Recommendation |
|-----------|-----------------|----------------|
| **Backend offline** | Toast on every failed API call via react-query error handler or per-query error state | Add global query error boundary that shows "Service unavailable" instead of multiple toasts |
| **Slow network (3G)** | Skeletons show immediately, no timeout | ✅ Good — no timeout spinner on slow connections |
| **Empty search** | "Type at least 2 characters" | ✅ |
| **Row with no clickable data** | Columns show '-' or '—' for empty values | ✅ |
| **Long names / text** | Truncation via `truncate` class | ✅ |
| **Drag on mobile** | `PointerSensor` with distance=5 means long-press activates drag | ⚠️ May conflict with scroll. Test on real device. |
| **Rapid form clicks** | `disabled` state immediately after first click via `loading` prop | ✅ |
| **Session expiry during use** | API 401 → auth redirect via axios interceptor | ✅ |
| **Pagination overflow** | `generatePageNumbers` handles ellipsis for 7+ pages | ✅ |
| **Many activities (1000+)** | "Load more" pagination with 25 per page | ✅ |
| **Email OAuth popup blocked** | Toast "Popup blocked. Please allow popups for this site." | ✅ |
| **Dark mode flash on load** | Theme persisted in localStorage, applied on app init | ✅ |
| **Calendar event reminder > duration** | Reminder defaults to 15min, independent of event duration | ⚠️ Should validate: "Reminder can't be longer than event" |
| **Delete confirmation required** | Via toast warning (no explicit confirm dialog for most actions) | ⚠️ Add "Are you sure?" confirm dialog for destructive actions |

---

## 8. Implementation Guidance

### Adding a New Data View

1. **Loading state**: Use the `Skeleton` component matching the layout shape. Wrap in `<div role="status">` with sr-only text.
2. **Empty state**: Use the shared `EmptyState` component with:
   - An icon matching the data type (from lucide-react)
   - Title: what's missing
   - Description: what to do about it
   - Action button: primary action if user can take one
3. **Error state**: Use the shared `ErrorState` component with:
   - `onRetry` connected to the query's `refetch()`
   - Human-readable error message (not raw API text)
4. **Success state**: Default rendering. Add toast for mutations only.

### Pattern Code
```tsx
const { data, isLoading, isError, error, refetch } = useQuery(...);

if (isLoading) return <MySkeleton />;
if (isError) {
  const msg = (error as any)?.message || 'Something went wrong';
  return <ErrorState message={msg} onRetry={() => refetch()} />;
}
if (!data || data.length === 0) {
  return (
    <EmptyState
      icon={<MyIcon className="h-8 w-8" />}
      title="Nothing here yet"
      description="Start by doing X to populate this view."
      action={{ label: 'Do X', onClick: handleAction }}
    />
  );
}
return <NormalView data={data} />;
```

### Gap Summary

| Gap | Location | Severity | Fix |
|-----|----------|----------|-----|
| Pipeline column "No deals" — no action | `pipeline-page.tsx` | **High** | Replace text with EmptyState + Add Deal button |
| No inline error state for pipeline page | `pipeline-page.tsx` | Medium | Add ErrorState wrapper for the kanban |
| Dashboard error handled by toast only | `dashboard-page.tsx` | Medium | Add ErrorState for full-page errors |
| Reports error handled by toast only | `reports-page.tsx` | Medium | Add ErrorState for report loading failures |
| Empty search results could be more helpful | `contact-list.tsx` | Low | Add "Try a different search term" guidance |
| Forecast empty state uses raw div (not EmptyState) | `reports-page.tsx` | Low | Switch to shared EmptyState component |
| 404 contact detail not explicitly handled | `contact-detail.tsx` | Medium | Check error status for 404 → "Contact not found" |
| Destructive actions lack confirmation dialog | Multiple | Medium | Add `<Modal>` for delete confirmations |
