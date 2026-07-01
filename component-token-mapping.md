# FrontierCRM — Component Token Mapping

**Date:** 2026-06-30
**Status:** Draft for Review

---

## How to Read This Document

Each component section maps:
1. **Token references** — which design tokens the component uses (colors, spacing, typography, radius, shadow)
2. **Current values** — what's actually in the codebase
3. **Spec alignment** — whether the component matches the design spec
4. **Inconsistencies** — gaps between current implementation and spec

---

## 1. Button (`src/components/atoms/button.tsx`)

### Variants

| Variant | BG Token | Text Token | Border Token | Hover | Active |
|---------|---------|------------|-------------|-------|--------|
| **primary** | `brand-600` (`#2563EB`) | `white` | none | `brand-700` | `brand-800` |
| **secondary** | `surface-secondary` (`#F1F5F9`) | `text-primary` (`#1E293B`) | `border` (`#E2E8F0`) | `surface-tertiary` | `gray-200` |
| **outline** | `transparent` | `text-primary` (`#1E293B`) | `border` 2px | `surface-secondary` + `border-brand-500` | `surface-secondary` |
| **ghost** | `transparent` | `text-primary` (`#1E293B`) | none | `surface-secondary` | `gray-200` |
| **danger** | `red-600` (`#DC2626`) | `white` | none | `red-700` | `red-800` |

### Size Scale

| Token | Class | Height | Padding | Font Size | Gap |
|-------|-------|--------|---------|-----------|-----|
| xs | `h-6 px-2 text-xs` | 24px | 8px x | 12px | 4px |
| sm | `h-8 px-3 text-xs` | 32px | 12px x | 12px | 6px |
| md | `h-10 px-4 text-sm` | 40px | 16px x | 14px | 8px |
| lg | `h-12 px-6 text-base` | 48px | 24px x | 16px | 10px |
| xl | `h-14 px-8 text-lg` | 56px | 32px x | 18px | 12px |

### Radius
- **Current:** `rounded-lg` (8px) ✓ matches spec

### Shadow
- **Primary:** `shadow-sm` ✓
- **Secondary:** `shadow-sm` ✓
- **Outline:** none ✓
- **Ghost:** none ✓
- **Danger:** `shadow-sm` ✓

### Focus Ring
- **Current:** `focus-visible:ring-2 focus-visible:ring-offset-2` with brand-500 ring color
- **Spec says:** 3px ring
- **Inconsistency:** ⚠ Ring width is 2px, spec calls for 3px (audit #17 — NIT)

### Loading State
- Uses `Loader2` spinner icon from lucide-react, replaces children
- `aria-busy` set when loading ✓
- `disabled:opacity-50` + `disabled:pointer-events-none` ✓ (audit #16 ✓)

### Dark Mode
- Primary: `dark:bg-brand-500 dark:hover:bg-brand-600` (brighter variant — good)
- Secondary: `dark:bg-dark-surface-secondary dark:text-dark-text-primary dark:hover:bg-dark-surface-tertiary dark:border-dark-border` ✓
- Danger: `dark:bg-red-500 dark:hover:bg-red-600` ✓

**Overall alignment: Strong.** Minor nit on ring width. All dark mode variants properly mapped.

---

## 2. Input (`src/components/atoms/input.tsx`)

### Size Scale

| Token | Height | Padding | Font Size |
|-------|--------|---------|-----------|
| sm | 32px (`h-8`) | `px-2.5` (10px) | 12px |
| md | 40px (`h-10`) | `px-3` (12px) | 14px |

### Variants

| Variant | BG | Border | Focus Border |
|---------|-----|--------|-------------|
| **outline** | `bg-white` | `border-border` (`#E2E8F0`) | `border-brand-500` |
| **filled** | `bg-surface-secondary` (`#F1F5F9`) | `transparent` | `border-brand-500` |

### Radius
- **Current:** `rounded-md` (6px) 
- **Spec says:** 6px ✓

### Focus Ring
- **Current:** `focus:ring-2 focus:ring-brand-500/20`
- **Spec says:** primary-500 + 3px primary-200 ring
- **Inconsistency:** ⚠ The spec mentions a 3px primary-200 ring; current implementation uses a 20% opacity brand-500 ring. The current approach is cleaner and is actually better practice (no doubled ring). No change recommended.

### Error State
- Border: `border-red-500` (`#EF4444`) ✓
- `aria-invalid` set on input ✓
- Error message with `role="alert"` ✓
- Label associated via `htmlFor` ✓

### Dark Mode
- Outline: `dark:bg-transparent dark:border-dark-border dark:text-dark-text-primary dark:focus:border-brand-400` ✓
- Filled: `dark:bg-dark-surface-secondary dark:text-dark-text-primary dark:focus:bg-dark-surface` ✓

### Label Typography
- `text-sm font-medium text-text-primary` (14px, 500 weight, #1E293B) ✓
- Bottom margin: `mb-1.5` (6px) ✓

### Helper Text
- `text-xs text-text-tertiary` (12px, #94A3B8) 
- **Inconsistency:** ⚠ Help text uses `text-tertiary` which is `#94A3B8` (3.2:1 AA FAIL for 12px text). Should use `text-text-secondary` (`#475569`, 6.5:1) for readable helper text.

**Overall alignment: Good.** Minor issue with helper text contrast. All dark mode variants present.

---

## 3. Card (`src/components/molecules/card.tsx`)

### Variants

| Variant | BG | Border | Shadow |
|---------|-----|--------|--------|
| **default** | `bg-white` | `border-border` | `shadow-sm` |
| **elevated** | `bg-white` | `border-border` | `shadow-md` |
| **outline** | `transparent` | `border-border` | none |
| **interactive** | `bg-white` | `border-border` | `shadow-sm` → `shadow-md` on hover + `border-brand-300` |

### Radius
- **Current:** `rounded-lg` (8px) 
- **Spec says:** 8px ✓

### Padding

| Token | Class | Value |
|-------|-------|-------|
| none | — | 0 |
| sm | `p-3` | 12px |
| md | `p-4 sm:p-5` | 16px → 20px |
| lg | `p-6 sm:p-8` | 24px → 32px |

### Header/Footer
- Header: `border-b border-border` + padding variant ✓
- Footer: `border-t border-border` + padding variant ✓
- Title: `text-base font-semibold text-text-primary` (16px 600 #1E293B) ✓
- Subtitle: `text-sm text-text-secondary` (14px #475569) ✓

### Dark Mode
- Default: `dark:bg-dark-surface dark:border-dark-border` ✓
- Elevated: `dark:bg-dark-surface dark:border-dark-border dark:shadow-lg dark:shadow-black/10` ✓
- Interactive: `dark:bg-dark-surface dark:border-dark-border dark:hover:border-brand-600 dark:hover:shadow-lg dark:hover:shadow-black/10` ✓

**Overall alignment: Strong.** No inconsistencies. Dark mode variants thorough.

---

## 4. Modal (`src/components/molecules/modal.tsx`)

### Size Scale

| Token | Width Class | Pixels | Spec | Match? |
|-------|------------|--------|------|--------|
| sm | `max-w-sm` | 384px | 400px | ⚠ 16px off |
| md | `max-w-lg` | 512px | 480px | ⚠ 32px off |
| lg | `max-w-2xl` | 672px | 640px | ⚠ 32px off |
| xl | `max-w-4xl` | 896px | — | N/A |
| full | `max-w-[95vw]` | 95vw | — | N/A |

**Inconsistency:** ⚠ Modal widths use Tailwind's `max-w-*` breakpoints which don't match the spec's exact pixel values (audit #36-38). Proposed fix: Use custom CSS class with exact pixel values or add `w-[400px]` for sm, `w-[480px]` for md, `w-[640px]` for lg.

### Backdrop
- **Current:** `bg-black/60 backdrop-blur-sm` — black at 60% opacity
- **Spec says:** `bg-neutral-900/60`
- **Inconsistency:** ⚠ (audit #40 — MINOR). Functionally identical effect.

### Panel
- **Current:** `bg-white shadow-xl` (light) / `dark:bg-dark-surface dark:border dark:border-dark-border`
- **Radius:** `rounded-t-xl sm:rounded-xl` (12px rounded top corners on mobile, full 12px on desktop)
- **Spec says:** 8px for cards, but modal gets 12px asymmetric rounding for mobile sheet behavior — this is intentional ✓

### Body Max Height
- **Current:** `max-h-[85vh]` 
- **Previous spec (audit #39):** Was `max-h-[60vh]`, now changed to 85vh in current code. ✓ Fixed.

### Animation
- Backdrop: `animate-fade-in` ✓
- Panel: `animate-slide-up` ✓
- **Spec says:** "fade scale 200ms ease-out"
- **Inconsistency:** ⚠ (audit #41 — MINOR). Current animation is slide-up (translateY 8px) not scale. Proposed: add `scale(0.95→1)` to slide-up animation for more polished entrance.

### Focus Management
- Focus trap implemented (Tab + Shift+Tab cycling) ✓ (audit #43 ✓)
- TabIndex on panel for initial focus ✓
- Previous active element restored on close ✓
- Body scroll locked while open ✓
- Escape key: calls `onClose` ✓ (audit #42 ✓)
- Click-outside: calls `onClose` via backdrop click ✓
- Close button: X icon with `aria-label="Close dialog"` ✓

### Dark Mode
- Panel: `dark:bg-dark-surface dark:border dark:border-dark-border` ✓
- Title: `dark:text-dark-text-primary` ✓
- Description: `dark:text-dark-text-secondary` ✓
- Close button: `dark:text-dark-text-tertiary dark:hover:text-dark-text-primary dark:hover:bg-dark-surface-secondary` ✓
- Footer border: `dark:border-dark-border` ✓

**Overall alignment: Strong.** Minor quirks on width values and animation.

---

## 5. Badge (`src/components/` — not yet a standalone component)

**Status: No dedicated Badge component found.** Badge patterns are implemented inline:

- **Sidebar nav:** Active badge via `bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300` on the nav link itself
- **User avatar:** Brand initials in `bg-brand-100 dark:bg-brand-900/50 text-brand-700 dark:text-brand-300`
- **Table status indicators:** Inline classes in pages (not always consistent)
- **Notification dot:** Inline `w-2 h-2 rounded-full bg-red-500` in topbar

**Inconsistency:** ⚠ Missing a dedicated Badge/Tag component. Badge patterns are scattered across the codebase without consistent:
- Size variants (default, sm, lg)
- Color schemes (neutral, brand, success, warning, error, secondary)
- Semantic role mapping (`role="status"`)
- Consistent border radius (some use `rounded`, some `rounded-full`, some `rounded-md`)

**Proposed:** Extract a reusable `Badge` atom with variants: `neutral`, `brand`, `success`, `warning`, `error`, `secondary` — plus outline variants.

---

## 6. Tag (`src/components/` — not yet a standalone component)

**Status: No dedicated Tag component found.** Similar to Badge — tags/chips are applied inline where needed.

**Proposed:** A `Tag` component with:
- `variant`: neutral, brand, success, warning, error
- `size`: sm, md
- `removable` prop: shows X button, fires `onRemove`
- `icon` prop: leading icon
- Radius: `rounded-md` (6px) for default, `rounded-full` for pill variant

---

## 7. Table (`src/components/ui/table.tsx`)

### Container
- **Current:** `rounded-lg border border-border` (8px radius, #E2E8F0 border)
- **Spec:** same ✓

### Header Row
- **Current:** `bg-surface-secondary` (`#F1F5F9`), `border-b border-border`
- **Spec says:** `neutral-50` (`#F8FAFC`)
- **Inconsistency:** ⚠ Header bg is `slate-100` vs spec's `slate-50` (audit #30 — NIT)

### Header Text
- **Current:** `text-xs font-semibold uppercase tracking-wider text-text-secondary` (12px, 600 weight, #475569, uppercase)
- **Spec says:** `neutral-500 caption-bold`
- **Match:** ✓ Functionally identical. `text-text-secondary` is `#475569` which is `slate-600` — spec says `slate-500` (#64748B). MINOR shade difference.

### Row Height
- **Current:** `py-2.5` (10px vertical padding = ~36px + content)
- **Spec says:** 52px fixed height
- **Inconsistency:** ⚠ (audit #31 — MINOR). Current rows are shorter than spec. Use `py-3.5` for ~44px or add explicit `h-[52px]`.

### Row Selection
- **Current:** `bg-brand-50 dark:bg-brand-900/20` + `border-l-3 border-l-brand-500`
- **Spec says:** primary-50 bg + 3px primary-500 left border
- **Match:** ✓ **Looks like the `border-l-3 border-l-brand-500` was already added** (visible in audit #33 and in current `table.tsx` line 262). The left border indicator is now present. ✓

### Row Hover
- **Current:** `hover:bg-surface-tertiary` (`#f3f4f6`)
- **Spec says:** `neutral-50` (`#F8FAFC`)
- **Inconsistency:** ⚠ Hover uses `gray-100` level; spec wants `slate-50`. Minor.

### Sort Indicators
- `aria-sort` on sortable headers ✓
- Sorting icons: ChevronUp/ChevronDown for active sort, ChevronsUpDown for unsorted ✓
- Keyboard navigation on rows (Enter/Space) ✓

### Selection Checkboxes
- Checkbox: `rounded border-border text-brand-600` ✓
- Select all checkbox in header ✓
- `aria-label` on checkboxes ✓

### Empty State
- Centered text `text-text-tertiary` in 48px vertical padding ✓

### Dark Mode
- Container: `dark:border-dark-border` ✓
- Header: `dark:bg-dark-surface-secondary dark:border-dark-border` ✓
- Header text: `dark:text-dark-text-secondary` ✓
- Body divider: `dark:divide-dark-border` ✓
- Selected row: `dark:bg-brand-900/20` ✓

**Overall alignment: Good.** Minor height and bg shade inconsistencies. The selection border indicator is now correctly implemented.

---

## 8. Sidebar (`src/components/organisms/sidebar.tsx`)

### Width
- **Current (expanded):** `w-60` (240px) 
- **Spec says:** 240px fixed sidebar
- **Match:** ✓ Correct value

### Width (Collapsed)
- **Current:** `w-16` (64px)
- **Spec:** 64px ✓

### Breakpoint Behavior
- **Current:** `hidden lg:flex` → visible from 1024px+ as fixed sidebar
- **Spec (audit #51):** 768-1023px should be collapsible drawer (hidden, toggled via hamburger)
- **Match:** ✓ **This is already correct** in the current code — `hidden lg:flex` means the sidebar is hidden below 1024px, which aligns with the spec. The audit was based on earlier code that used `md:flex`.

### Background
- **Current:** `bg-white dark:bg-slate-900` + `border-r border-gray-200 dark:border-slate-700` ✓

### Nav Items
- Width: `rounded-lg` (8px) ✓
- Padding: `px-3 py-2.5` (12px x 10px) ✓
- Font: `text-sm font-medium` (14px, 500) ✓
- Active bg: `bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300` ✓
- Inactive text: `text-gray-600 dark:text-slate-400 dark:hover:bg-slate-700`
- **Inconsistency:** ⚠ Inactive text on light uses `text-gray-600` (`#4B5563`) instead of `text-text-secondary` (`slate-600`/`#475569`). Minor shade discrepancy — should use the design token.

### Chevron Toggle
- `aria-label` set dynamically: "Collapse sidebar" / "Expand sidebar" ✓
- Icon: ChevronLeft when expanded, ChevronRight when collapsed ✓
- Visibility: `hidden lg:flex` — desktop only ✓

### Mobile Overlay
- `fixed inset-0 z-50 lg:hidden` ✓
- Overlay bg: `bg-black/50` ✓
- Mobile aside: `w-72` (288px) — wider than desktop for touch targets ✓
- Close button: X icon with `aria-label="Close menu"` ✓

### User Area
- **Current:** Uses initials in `bg-brand-100 dark:bg-brand-900/50 text-brand-700 dark:text-brand-300` ✓
- User name: `text-sm font-medium text-gray-900` (should be `text-text-primary`) — ⚠ minor
- Email: `text-xs text-gray-500 dark:text-slate-400` ✓

**Overall alignment: Strong.** Breakpoint behavior corrected. Minor token usage inconsistency on nav item text.

---

## 9. Topbar (`src/components/organisms/topbar.tsx`)

### Height & Spacing
- **Current:** `h-16` (64px), `px-4 lg:px-6` ✓

### Search Input
- Width: `w-40 md:w-64 lg:w-80` (responsive step) ✓
- Border: `border border-gray-200 dark:border-slate-600` — inconsistent with `border` token
- **Inconsistency:** ⚠ Uses `gray-200` / `slate-600` instead of surface/border tokens. Should use `border-border` (`slate-200`/`slate-700`).
- Focus ring: `focus:ring-2 focus:ring-brand-500` ✓
- WAI-ARIA: `combobox`, `listbox`, `option`, `aria-selected` — full pattern ✓

### Search Dropdown
- Width: `left-0 right-0 top-full` — full width ✓
- BG: `bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700` ✓
- Result items: hover = `hover:bg-gray-50 dark:hover:bg-slate-700/50`, selected = `bg-brand-50 dark:bg-brand-900/20` ✓
- Selected item driven by keyboard nav with `data-idx` ✓

### Theme Toggle
- `aria-label="Toggle theme"` ✓
- Icon: Sun when dark, Moon when light ✓
- `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500` ✓
- **Inconsistency:** ⚠ Theme toggle uses `p-2 rounded-lg` (8px radius) but no explicit `hover:bg-surface-secondary` design token — uses `hover:bg-gray-100` instead.

### Notification Bell
- `aria-label="Notifications"` ✓
- Dot: `aria-label` on dot reads "Unread notifications" ✓ (audit #72 fix applied)
- **Inconsistency:** ⚠ Hard-coded red dot color `bg-red-500` (same as `error-500`) vs a dedicated notification dot token.

### Profile Dropdown
- User icon: `bg-brand-100 dark:bg-brand-900/50 text-brand-700 dark:text-brand-300` ✓
- Dropdown: `bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700` ✓
- Items: `px-4 py-2 text-sm text-gray-700 dark:text-slate-300` ✓
- Sign out: `text-red-600` ✓

**Overall alignment: Good.** Minor token naming inconsistency in search border.

---

## 10. Misc. Inconsistency Summary

| # | Component | Issue | Token(s) Affected | Severity |
|---|-----------|-------|-------------------|----------|
| 1 | **Body** | `font-sans` not applied to body (`font-sans` missing from `@apply`) | `--font-family-sans` | **Blocker** |
| 2 | **All** | `gray-*` used alongside `slate-*` throughout components | Naming convention | Minor |
| 3 | **Sidebar** | Inactive nav text uses `text-gray-600` instead of `text-text-secondary` | `--color-text-secondary` | Minor |
| 4 | **Input** | Helper text uses `text-text-tertiary` (`#94A3B8`, 3.2:1 contrast) | `--color-text-tertiary` | Minor |
| 5 | **Table** | Header bg is `slate-100` vs spec `slate-50` | `--color-surface-secondary` | Nit |
| 6 | **Table** | Row height not fixed at spec 52px | spacing | Minor |
| 7 | **Modal** | Width values use Tailwind breakpoints instead of spec px values | spacing | Minor |
| 8 | **Modal** | Animation uses slide-up instead of scale+fade | animation | Minor |
| 9 | **Badge** | No dedicated Badge component — scattered inline classes | n/a | Minor |
| 10 | **Tag** | No dedicated Tag component — scattered inline classes | n/a | Nit |
| 11 | **Button** | Focus ring width is 2px (spec: 3px) | focus style | Nit |
| 12 | **Search input** | Border uses `gray-200` instead of `border-border` | `--color-border` | Nit |
| 13 | **Card** | Radius is `rounded-xl` (12px) — spec says `rounded-lg` (8px) | radius | Minor |

### Where Gray vs Slate Mixup Occurs

These files use `gray-*` classes instead of the `slate-*` / design tokens family:

| File | Classes Used | Should Use |
|------|-------------|------------|
| `index.css` body | `text-gray-900`, `bg-gray-300/400`, `border-gray-200` | `text-text-primary`, surface/border tokens |
| `sidebar.tsx` | `text-gray-600/900`, `bg-gray-100/200`, `border-gray-200`, `hover:bg-gray-200` | `text-text-primary/secondary`, `border-border` |
| `topbar.tsx` | `text-gray-400/500/700/900`, `bg-gray-50/100`, `border-gray-100/200/300` | design token equivalents |
| `button.tsx` (active states) | `active:bg-gray-200` | `active:bg-surface-tertiary` or `active:bg-slate-200` |

This inconsistency is primarily cosmetic — `gray-200` and `slate-200` are visually close — but it undermines token-based theming. A targeted cleanup would bring everything to the design system.

---

## Priority Fix Recommendations

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| **P0** | Apply `font-sans` to body tag | 1 line | Inter brand font across entire app |
| **P1** | Extract Badge and Tag components | Moderate (2 new files) | Consistent status display |
| **P1** | Fix helper text contrast in Input | 1 token change | WCAG AA compliance for help text |
| **P2** | Clean up gray→slate inconsistency | Across multiple files | Token purity, easier theming |
| **P2** | Align Table row height to 52px | CSS change | Spec compliance |
| **P2** | Fix Card radius from 12px→8px | 1 token change in card.tsx | Spec compliance |
| **P3** | Add scale to modal animation | CSS keyframes | Polished UX |
| **P3** | Use exact pixel values for modal widths | CSS classes | Spec pixel accuracy |
| **P3** | Switch button focus ring to 3px | 1 token change | Spec compliance |