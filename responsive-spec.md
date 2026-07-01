# FrontierCRM — Responsive Behaviour Spec

**Date:** 2026-06-30  
**Auditor:** Creative (ALLSTARS Design & Visual Specialist)  
**Target breakpoints:** 390px (phone), 768px (tablet portrait), 1280px (desktop), 1920px (large desktop)  
**Framework:** Tailwind v4 with `@custom-variant dark` and responsive prefixes

---

## Breakpoint Strategy

FrontierCRM uses Tailwind's default breakpoints:
| Breakpoint | Min-width | Device |
|-----------|-----------|--------|
| `sm` | 640px | Large phone / small tablet |
| `md` | 768px | Tablet portrait |
| `lg` | 1024px | Tablet landscape / small desktop |
| `xl` | 1280px | Desktop |
| `2xl` | 1536px | Large desktop |

The app uses a **mobile-first** strategy with `sm:`, `md:`, `lg:`, `xl:` prefixes to scale up.

---

## Layout Behaviour by Screen

### 1. Sidebar Navigation

| Property | 390px | 768px | 1280px | 1920px |
|----------|-------|-------|--------|--------|
| State | Hidden overlay | Hidden overlay | Fixed, collapsible | Fixed, collapsible |
| Width | 288px (w-72) when open | 288px (w-72) when open | 240px (w-60) / 64px collapsed | 240px / 64px collapsed |
| Trigger | Hamburger in topbar | Hamburger in topbar | Collapse chevron in sidebar header | Same |
| Overlay | `bg-black/50` backdrop | `bg-black/50` backdrop | None (inline flex) | None |

**Issue:** At 768px, the sidebar uses `lg:flex` (≥1024px) — tablets in portrait (768-1023px) get the overlay drawer. This is correct behaviour per the spec. Prior audit Issue #51 flagged this as a mismatch but **768-1023px as overlay drawer is the right UX** for tablet portrait. The sidebar should animate in from the left.

**Recommendation:** Add slide-in animation from left for the mobile/tablet overlay:
```css
@keyframes slide-in-left {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}
```

### 2. Top Bar

| Property | 390px | 768px | 1280px | 1920px |
|----------|-------|-------|--------|--------|
| Height | 64px (h-16) | 64px | 64px | 64px |
| Padding | `px-4` | `px-4` | `px-4 lg:px-6` | `px-6` |
| Search width | `w-40` (160px) | `w-40 md:w-64` (256px) | `w-64 lg:w-80` (320px) | 320px |
| Hamburger | ✅ Visible | ✅ Visible | ✅ Hidden (`lg:hidden`) | Hidden |
| Theme/Notifications | In "More" dropdown (`md:hidden`) | In "More" dropdown | Inline visible | Inline visible |
| Profile name | Hidden (`md:block` hidden) | ✅ Visible | ✅ Visible | ✅ Visible |

**Issue:** On 390px, the search input is very narrow (160px → `w-40`) with `max-w-[200px] sm:max-w-md`. This is acceptable on mobile — the input expands to `w-full` on focus. However, the `max-w-[200px]` on the container limits the dropdown width.

**Recommendation:** At 390px, make the search expand to full width when focused, and push other actions into the "More" dropdown (already done).

### 3. Dashboard

| Property | 390px | 768px | 1280px | 1920px |
|----------|-------|-------|--------|--------|
| Metric cards | 1 column | 2 columns | 4 columns | 4 columns |
| Chart + sidebar | 1 column (stacked) | 1 column | 3 columns (chart: 2, sidebar: 1) | 3 columns |
| Gradient banner padding | `px-6 py-8` | `px-6 py-8` | `sm:px-8` | `sm:px-8` |

**Issue:** The gradient banner at 390px extends beyond the main content padding. The `AppLayout` main content has `p-3 sm:p-4 lg:p-6` but the banner is inside a child container that doesn't account for the parent's reduced padding on mobile. The banner uses `px-6` which overflows the parent's `p-3` on 390px — the banner has 24px left/right padding while the parent content area only has 12px padding on small screens.

**Recommendation:** Either remove `px-6` from the banner at 390px and let it inherit parent padding, or add `-mx-3` to allow the banner to bleed slightly:
```jsx
<div className="-mx-3 sm:mx-0 rounded-none sm:rounded-xl px-4 py-6 sm:px-8 sm:py-8">
```
Currently the banner has no negative margin, so its rounded corners and padding are contained within the parent. At 390px this looks fine because the parent `p-3` creates 12px gutters. The banner's `rounded-xl` still rounds corners that are touching the edge. **Minor visual inconsistency only.**

### 4. Contacts List

| Property | 390px | 768px | 1280px | 1920px |
|----------|-------|-------|--------|--------|
| Layout | Full-width table | Full-width table | Full-width table | Full-width table |
| Header | Stacked (flex-col) | Side-by-side (sm:flex-row) | Side-by-side | Side-by-side |
| Search | `max-w-md` (448px) | `max-w-md` | `max-w-md` | `max-w-md` |
| Pagination | Full width, stacked | Full width, stacked | Inline | Inline |

**Issue:** The contact table uses `overflow-x-auto` which works well — on 390px the table scrolls horizontally. However, there's no visual indicator (fade gradient or shadow) that the table can scroll horizontally on narrow screens.

**Recommendation:** Add a subtle horizontal scroll indicator:
```css
.overflow-x-auto {
  background: linear-gradient(to right, transparent 95%, rgba(0,0,0,0.03) 100%);
}
```

### 5. Pipeline (Kanban)

| Property | 390px | 768px | 1280px | 1920px |
|----------|-------|-------|--------|--------|
| Layout | Vertical stack (`flex-col`) | Vertical stack | Horizontal scroll (`flex-row`) | Horizontal scroll |
| Column width | `w-full` | `w-full md:w-[280px]` | `w-[280px]` | `w-[280px]` |
| Columns visible | 1 | 1-2 | 3-4 | 4+ |

**Issue:** The transition from vertical stack (`flex-col`) to horizontal scroll (`md:flex-row`) happens at 768px. But at 768-900px, with the sidebar as overlay, there's about 768px of content width. A column width of 280px means 2 columns fit with 20px gaps ≈ 580px. Users see 2 columns and a partial 3rd, which is fine for horizontal scroll. However, the `md:flex-row` (≥768px) combined with `md:w-[280px]` means at 768px exactly, the sidebar overlay + content forces the kanban into horizontal scroll mode with insufficient width. **The sidebar overlay already solves this** (sidebar opens on demand at <1024px), so at 768px the kanban has the full 768px to work with.

**Recommendation:** Move the flex-direction breakpoint to `lg:flex-row` (1024px) so tablets get the vertical stacked layout:
```diff
- <div className="flex flex-col md:flex-row ...">
+ <div className="flex flex-col lg:flex-row ...">
```
This aligns with the sidebar overlay breakpoint (`lg:flex`).

### 6. Activities / Timeline

| Property | 390px | 768px | 1280px | 1920px |
|----------|-------|-------|--------|--------|
| Layout | Centered `max-w-3xl` | Centered 768px | Centered 768px | Centered 768px |
| Padding | `px-4 py-6` | `sm:px-6` | `sm:px-6 lg:px-8` | `lg:px-8` |
| Create Meeting button | Full-width on mobile? | Normal button | Normal button | Normal button |

**Issue:** The timeline is constrained to `max-w-3xl` (768px max). On 1280px and 1920px, this creates large gutters — the timeline card uses only ~60% of available width on a 1920px display. While this is intentional (reading-comfort line length), the timeline feels empty on large screens.

**Recommendation:** Increase to `max-w-4xl` (896px) on large screens:
```jsx
className="mx-auto max-w-3xl px-4 py-6 sm:px-6 lg:px-8 xl:max-w-4xl"
```

### 7. Email

| Property | 390px | 768px | 1280px | 1920px |
|----------|-------|-------|--------|--------|
| Layout | Single column | Split (list + detail) | Split (list + detail) | Split (list + detail) |
| Detail back button | ✅ Visible | ✅ Visible (`lg:hidden` shown at <1024px) | Hidden | Hidden |
| Connection status badge | Hidden | `hidden sm:flex` | Visible | Visible |

**Issue:** The email page uses a single-column layout with conditional rendering — when an email is selected on mobile, the list is hidden and the detail view takes over. The back button (line 232, `lg:hidden`) is always visible on screens <1024px. **This is correct behaviour.**

### 8. Reports

| Property | 390px | 768px | 1280px | 1920px |
|----------|-------|-------|--------|--------|
| Metric cards | 1 column | 2 columns | 3 columns | 6 columns |
| Chart layouts | Stacked | 2-col grid | 3-col grid | 3-col grid |
| Tab navigation | Scrollable tabs | Full tabs | Full tabs | Full tabs |
| Padding | `p-3` | `p-3 sm:p-6` | `sm:p-6` | `sm:p-6` |

**Issue:** The forecast section uses `grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4` for controls — on 390px these stack in one column which is correct but the select dropdowns become full-width, which is also correct.

### 9. Settings

| Property | 390px | 768px | 1280px | 1920px |
|----------|-------|-------|--------|--------|
| Tab navigation | Horizontal scroll or full-width pills | Side tabs | Side tabs | Side tabs |

**Recommendation:** Settings tabs should switch to a horizontal scrollable tab bar at 390px. Currently they use a side tab layout on all screens. On mobile, consider switching to a `<select>` dropdown or horizontal tabs.

---

## Touch vs Mouse Interaction Patterns

| Interaction | Touch (390px) | Mouse (1280px) |
|-------------|---------------|-----------------|
| Row click | Tap selects | Click selects |
| Row hover | No hover state (OK — using `active:` state) | `hover:bg-surface-tertiary` on rows |
| Drag-and-drop (pipeline) | Long-press activates drag (PointerSensor: `activationConstraint.distance=5`) | Click-drag with visible drag handle |
| Dropdown menus | Tap to toggle, tap outside to close | Hover + click, click outside to close |
| Tooltips | Not applicable (no hover) | Hover triggers |
| Modals | Bottom sheet style (`items-end sm:items-center`) | Centered dialog |
| Pagination | Tap to navigate | Click to navigate |
| Search dropdown | Tap result to navigate, keyboard opens automatically | Keyboard nav + enter |

All touch targets should be ≥44×44px per WCAG 2.5.8. Current smallest targets:
- Sidebar collapse chevron: 32×32px (❌)
- Topbar icon buttons: 36×36px (❌ with `p-2`)
- Notification bell: 36×36px (❌)
- Search dropdown close/hint buttons: 36×36px (❌)

---

## Responsive Pattern Library (Code-Level Guidance)

### Pattern 1: Responsive Page Header
```tsx
// Current pattern — correct
<div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
  <div>
    <h1 className="text-2xl font-bold">Title</h1>
    <p className="text-sm text-text-secondary">Description</p>
  </div>
  <div className="flex items-center gap-2">
    {/* actions */}
  </div>
</div>
```

### Pattern 2: Responsive Grid
```tsx
// Current pattern — correct
<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
  {/* Cards */}
</div>
```

### Pattern 3: Responsive Padding
```tsx
// Current pattern — correct
<main className="p-3 sm:p-4 lg:p-6">
```

### Pattern 4: Modal on Mobile
```tsx
// Current pattern — bottom sheet on mobile, centered on desktop
className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
```
✅ Correct — bottom sheet mobile pattern is the right UX choice.

### Pattern 5: Table Horizontal Scroll
```tsx
// Current pattern — correct
<div className="w-full overflow-x-auto rounded-lg border border-border">
  <table className="w-full text-left text-sm">
```

---

## Spec Compliance Summary

| Aspect | Status |
|--------|--------|
| Fluid grids (relative units) | ✅ Tailwind uses rem throughout |
| Flexible images | ✅ No fixed-width images |
| Content-driven breakpoints | ⚠️ Sidebar breakpoint at md(768px) conflicts with content at 900px |
| Mobile-first strategy | ✅ ✅ |
| Touch targets ≥44px | ❌ Several below standard |
| No horizontal overflow | ⚠️ Some pages have hidden overflow on very small screens |
| Readable line lengths | ✅ max-w-prose / max-w-3xl on reading content |
| Responsive navigation | ✅ Overlay drawer on mobile |

---

## Priority Fixes

### High Priority
1. **RS-01**: Move kanban flex-direction breakpoint from `md:flex-row` to `lg:flex-row` (align with sidebar overlay at 1024px)
2. **RS-02**: Increase touch targets to 44×44px minimum (topbar icons: `p-2` → `p-3`, sidebar collapse: add invisible expansion)
3. **RS-03**: Increase timeline `max-w-3xl` → `max-w-4xl` on large screens

### Medium Priority
4. **RS-04**: Add horizontal scroll indicator to tables on mobile
5. **RS-05**: Convert settings tabs to horizontal scroll on 390px
6. **RS-06**: Add slide-in-left animation for mobile sidebar overlay

### Low Priority
7. **RS-07**: Consider responsive search expansion on mobile
8. **RS-08**: Audit banner padding overflow on mobile
