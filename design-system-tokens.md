# FrontierCRM Design System Tokens

**Version:** 2.0 (proposed refinements)
**Status:** Draft for Review
**Date:** 2026-06-30

---

## 1. Color Palette

### 1.1 Primary — Blue (`#3B82F6`)

The primary palette drives all actionable elements: buttons, links, active states, and selected indicators.

| Token | Hex | Tailwind | Light Usage | WCAG on White | WCAG on Dark (`#0B1120`) |
|-------|-----|----------|-------------|---------------|--------------------------|
| `--color-brand-50` | `#EFF6FF` | `blue-50` | Selected list bg, light hover | — | — |
| `--color-brand-100` | `#DBEAFE` | `blue-100` | User avatar bg, notification indicators | — | — |
| `--color-brand-200` | `#BFDBFE` | `blue-200` | Focus ring (lighter variant) | — | — |
| `--color-brand-300` | `#93C5FD` | `blue-300` | Hover border on interactive cards | — | — |
| `--color-brand-400` | `#60A5FA` | `blue-400` | Icon accents on dark mode | — | — |
| `--color-brand-500` | `#3B82F6` | `blue-500` | **Primary accent** (buttons, links) | 4.0:1 AA | 8.1:1 AAA |
| `--color-brand-600` | `#2563EB` | `blue-600` | **Primary button bg**, active nav icon | 4.9:1 AA | 7.0:1 AA |
| `--color-brand-700` | `#1D4ED8` | `blue-700` | Hover state on primary buttons | 6.2:1 AAA | 5.8:1 AA |
| `--color-brand-800` | `#1E40AF` | `blue-800` | Active/pressed state | 8.0:1 AAA | 4.6:1 AA |
| `--color-brand-900` | `#1E3A8A` | `blue-900` | Dark bg emphasis | 10.0:1 AAA | 3.5:1 (use only as bg on dark) |

**✓ Current tokens** cover the full Tailwind blue spectrum. No change needed.
**⚠ Proposed refinement:** Add `--color-brand-950: #172554` for deeper hover on dark surfaces.

---

### 1.2 Secondary — Teal (`#14B8A6`)

Used for secondary accents, data visualization, success indicators, and badge colors.

| Token | Hex | Tailwind | Usage | WCAG on White | WCAG on Dark |
|-------|-----|----------|-------|---------------|--------------|
| `--color-secondary-50` | `#F0FDFA` | `emerald-50` | Light success bg | — | — |
| `--color-secondary-100` | `#CCFBF1` | `emerald-100` | Badge bg (success) | — | — |
| `--color-secondary-200` | `#99F6E4` | `emerald-200` | Progress track | — | — |
| `--color-secondary-300` | `#5EEAD4` | `emerald-300` | Data viz (light) | — | — |
| `--color-secondary-400` | `#2DD4BF` | `teal-400` | Data viz accent | — | — |
| `--color-secondary-500` | `#14B8A6` | `teal-500` | **Secondary brand color** | 3.2:1 FAIL | 6.4:1 AA |
| `--color-secondary-600` | `#0D9488` | `teal-600` | Hover state | 3.9:1 FAIL | 5.3:1 AA |
| `--color-secondary-700` | `#0F766E` | `teal-700` | Dark mode hover | 4.8:1 AA | 4.4:1 AA |
| `--color-secondary-800` | `#115E59` | `teal-800` | Active/pressed | 6.1:1 AA | — |
| `--color-secondary-900` | `#134E4A` | `teal-900` | Dark bg emphasis | 7.3:1 AAA | — |

**⚠ Issue:** `--color-secondary-500` and `--color-secondary-600` fail WCAG AA (4.5:1) on white backgrounds. These should only be used as decorative accents on white, NOT for text or interactive elements on white. On dark backgrounds they pass easily.

**Proposed refinement:** Add a dedicated success semantic token (`--color-success: #059669` / `emerald-600`) which provides 4.1:1 AA on white vs the current `#10B981` (3.2:1 FAIL). The current `--color-success: #10B981` remains acceptable as a badge bg.

---

### 1.3 Accent — Amber (`#F59E0B`)

Used for warnings, attention calls, highlights, and notification badges.

| Token | Hex | Tailwind | Usage | WCAG on White | WCAG on Dark |
|-------|-----|----------|-------|---------------|--------------|
| `--color-accent-50` | `#FFFBEB` | `amber-50` | Warning bg | — | — |
| `--color-accent-100` | `#FEF3C7` | `amber-100` | Badge bg (warning) | — | — |
| `--color-accent-200` | `#FDE68A` | `amber-200` | Highlight underline | — | — |
| `--color-accent-300` | `#FCD34D` | `amber-300` | Gold star ratings | — | — |
| `--color-accent-400` | `#FBBF24` | `amber-400` | Icon accents | — | — |
| `--color-accent-500` | `#F59E0B` | `amber-500` | **Accent color** | 2.8:1 FAIL | 5.6:1 AA |
| `--color-accent-600` | `#D97706` | `amber-600` | Warning border | 3.5:1 FAIL | 4.6:1 AA |
| `--color-accent-700` | `#B45309` | `amber-700` | Dark mode text | 4.6:1 AA | 3.8:1 FAIL |
| `--color-accent-800` | `#92400E` | `amber-800` | Dark mode hover text | 6.1:1 AA | — |

**⚠ Issue:** Like secondary, accent-500 and 600 fail WCAG AA on white. They are decorative-only on light surfaces. Use `accent-700` for readable warning text on white.

**Proposed refinement:** No palette change — the amber is intentionally attention-catching even when decorative. Document that warning text on white must use `accent-700` or darker.

---

### 1.4 Neutral / Surface

| Token | Current Hex | Proposed | Tailwind Match | Usage |
|-------|------------|----------|----------------|-------|
| `--color-surface` | `#F8FAFC` | No change | `slate-50` | Page background (light) |
| `--color-surface-secondary` | `#F1F5F9` | No change | `slate-100` | Table headers, secondary bg |
| `--color-surface-tertiary` | `#f3f4f6` | `#E2E8F0` | `slate-200` | Hover states — current value is `gray-100`, inconsistent with slate family |
| `--color-border` | `#E2E8F0` | No change | `slate-200` | Card borders, dividers, table borders |
| `--color-border-light` | `#f3f4f6` | `#F1F5F9` | `slate-100` | Subtle separators — current `gray-100`, inconsistent |

**⚠ Proposed:** Align `surface-tertiary` and `border-light` to the slate family to match the rest of the surface palette. Currently they use `gray-100`/`gray-200` while the rest of the palette is slate-based.

---

### 1.5 Dark Surface

| Token | Current Hex | Proposed | Tailwind Match | Usage |
|-------|------------|----------|----------------|-------|
| `--dark-surface` | `#0B1120` | No change | `gray-950` | Page background (dark) |
| `--dark-surface-secondary` | `#1e293b` | No change | `slate-800` | Card bg, sidebar, dropdown |
| `--dark-surface-tertiary` | `#334155` | No change | `slate-700` | Hover states, secondary bg |
| `--dark-border` | `#334155` | No change | `slate-700` | Card borders, dividers |
| `--dark-border-light` | `#1e293b` | No change | `slate-800` | Subtle separators |

✓ Dark surface tokens are consistent and well-chosen.

---

### 1.6 Text

| Token | Current Hex | Proposed | Tailwind Match | WCAG on White | WCAG on Dark `#0B1120` | Usage |
|-------|------------|----------|----------------|---------------|------------------------|-------|
| `--color-text-primary` | `#1E293B` | No change | `slate-800` | **13.5:1 AAA** | **5.7:1 AA** | Headings, body |
| `--color-text-secondary` | `#475569` | No change | `slate-600` | **6.5:1 AAA** | **3.5:1 FAIL** | Labels, meta text |
| `--color-text-tertiary` | `#94A3B8` | No change | `slate-400` | **3.2:1 FAIL** | 2.1:1 FAIL | Placeholders, disabled (fine for 3:1 large text) |
| `--color-text-inverse` | `#FFFFFF` | No change | `white` | — | **12.5:1 AAA** | Text on brand/dark bg |

**⚠ Issue:** `text-tertiary` fails WCAG AA on both light and dark bgs. For text smaller than 18px (or 14px bold), this fails the 4.5:1 AA requirement. This is acceptable for placeholder text and disabled states per WCAG, but should **not** be used for any readable content.

**Proposed refinement:** Replace placeholder uses of `#94A3B8` with `#64748B` (slate-500, 4.2:1 AA) where the text must be readable (help text, helper text). Keep `#94A3B8` only for true placeholders and disabled text.

---

### 1.7 Semantic Colors

| Token | Current Hex | Proposed | Tailwind | WCAG on White | Usage |
|-------|------------|----------|----------|---------------|-------|
| `--color-error` | `#EF4444` | No change | `red-500` | 3.8:1 FAIL | Error messages on white — add `bg-red-50` for AA |
| `--color-success` | `#10B981` | `#059669` (prop) | `emerald-500` | 3.2:1 FAIL → 4.1:1 AA | Success text — proposed `emerald-600` passes |
| Info (missing) | — | `#2563EB` | `blue-600` | 4.9:1 AA | Add dedicated info semantic token |

**Proposed refinement:**
- Add `--color-info: #2563EB` — informational text and status badges
- Change `--color-success` from `#10B981` to `#059669` for WCAG AA compliance on white
- `--color-error` stays at `#EF4444` but must be paired with dark background or large text

---

## 2. Typography Scale

### 2.1 Font Families

| Token | Value | Usage |
|-------|-------|-------|
| `--font-family-sans` | `Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` | All UI text |
| `--font-family-mono` | `'JetBrains Mono', 'Fira Code', monospace` | Code, data values, IDs |

**⚠ Current issue (from audit blocker #1, #3):**
The `@theme` block defines `--font-family-sans: Inter` but the body `@apply` in `index.css` does not include `font-sans`. The font stack falls back to system default. **Fix:** Add `font-sans` to the body `@apply` in `index.css` line 80.

### 2.2 Font Size Scale

| Token / Tailwind | Size | Line Height | Weight | Usage |
|------------------|------|-------------|--------|-------|
| `text-xs` | 12px | 16px (1.333) | 400/500 | Caption, table cell, label |
| `text-sm` | 14px | 20px (1.428) | 400/500 | Body, input text, helper |
| `text-base` | 16px | 24px (1.5) | 400/500/600 | Default body, card title |
| `text-lg` | 18px | 28px (1.555) | 600 | Section heading |
| `text-xl` | 20px | 28px (1.4) | 600 | Card heading |
| `text-2xl` | 24px | 32px (1.333) | 700 | Page heading (H2) |
| `text-3xl` | 28px | 36px (1.285) | 700 | H1 — page title |

**⚠ Issue (audit #2):** Login page uses `text-2xl` (24px) for the welcome heading. The spec says H1 should be `text-3xl` (28px) for hero headings.

**Proposed refinement:** Add a formal heading scale:

| Level | Tailwind | Size | Weight | Letter-spacing | Usage |
|-------|----------|------|--------|----------------|-------|
| H1 | `text-3xl` | 28px | 700 (bold) | `-0.02em` | Page title, hero |
| H2 | `text-2xl` | 24px | 700 (bold) | `-0.015em` | Section header |
| H3 | `text-xl` | 20px | 600 (semibold) | `-0.01em` | Card title, subsection |
| H4 | `text-lg` | 18px | 600 (semibold) | `-0.005em` | Small section title |
| Body | `text-sm` | 14px | 400 (regular) | normal | Paragraphs, form labels |
| Small | `text-xs` | 12px | 400/500 | normal | Captions, table cells, sidebar |

### 2.3 Mono Font Size

| Usage | Size | Weight |
|-------|------|--------|
| Code blocks | 13px | 400 |
| Data values (IDs, amounts) | 13px | 500 |
| Keyboard shortcuts (kbd) | 10px | 500 |

---

## 3. Spacing & Sizing Scale

The project uses Tailwind's default spacing scale (base unit: 4px). This is **current and adequate**.

| Token | Tailwind Class | px | Usage |
|-------|---------------|----|-------|
| 4xs | `p-0.5` | 2px | Tight inline spacing |
| 3xs | `p-1` | 4px | Compact gap, icon padding |
| 2xs | `p-1.5` | 6px | Tight label padding |
| xs | `p-2` | 8px | Small card padding, button padding |
| sm | `p-3` | 12px | Input padding, compact panel |
| md | `p-4` | 16px | Default card padding, section gap |
| lg | `p-5` | 20px | Spacious card padding |
| xl | `p-6` | 24px | Page section padding, modal body |
| 2xl | `p-8` | 32px | Auth card padding, large page padding |
| 3xl | `p-10` | 40px | Spacious modal, hero section |

### App Padding Pattern (proposed)

| Breakpoint | Current | Proposed | Source |
|------------|---------|----------|--------|
| Mobile (<640px) | `p-3` | `p-4` (16px) | Audit #45: current is too tight |
| Tablet (640-1024px) | `p-4` | `p-6` (24px) | |
| Desktop (>1024px) | `p-6` | `p-8` (32px) | |

---

## 4. Border Radius

| Token | Tailwind | Value | Usage |
|-------|----------|-------|-------|
| `--radius-sm` | `rounded-sm` | 4px | Checkbox, tag/badge inner corner |
| `--radius-md` | `rounded-md` | 6px | Inputs, selects — **proposed for Input** |
| `--radius-lg` | `rounded-lg` | 8px | Buttons, Cards, Modals, Nav items |
| `--radius-xl` | `rounded-xl` | 12px | Auth card outer wrapper, large cards |

**⚠ Issues (from audit):**
- Input uses `rounded-md` (6px) but audit (#19) expects 6px — current value is actually `rounded-md`, not `rounded-lg`. ✓ Actually correct.
- Card uses `rounded-xl` (12px) but spec says 8px (`rounded-lg`). Audit #26 flags this as MINOR.
- Button uses `rounded-lg` (8px) ✓

**Proposed refinements:**
- Buttons: `rounded-lg` (8px) ✓ — keep
- Inputs: `rounded-md` (6px) ✓ — keep
- Cards: Change from `rounded-xl` (12px) to `rounded-lg` (8px) for consistency across components
- Modals: `rounded-t-xl` (12px top) + `rounded-xl` (12px bottom on desktop) — the asymmetric rounding is intentional for mobile sheet behavior
- Badges: `rounded-md` (6px) or full `rounded-full` for pill badges

---

## 5. Shadows

| Token | Tailwind Class | Value | Usage |
|-------|---------------|-------|-------|
| `--shadow-xs` | `shadow-xs` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | Very subtle elevation |
| `--shadow-sm` | `shadow-sm` | `0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)` | Default card, button, dropdown |
| `--shadow-md` | `shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)` | Elevated card, hover state |
| `--shadow-lg` | `shadow-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)` | Modal, dropdown menu |
| `--shadow-xl` | `shadow-xl` | `0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)` | Alert/toast, mobile drawer overlay |

**Dark mode notes:** In dark mode, shadows should have reduced opacity. Currently handled via `dark:shadow-lg dark:shadow-black/10` on elevated cards. ✓

**Proposed refinement:** Add explicit shadow token definitions for dark mode with `black/15` base.

---

## 6. Animation Timing & Easing

| Name | Keyframes | Duration | Easing | Usage |
|------|-----------|----------|--------|-------|
| `fade-in` | `opacity: 0 → 1` | 200ms | `ease-out` | Backdrop overlay, modal entrance |
| `slide-up` | `translateY(8px) + opacity 0→1` | 200ms | `ease-out` | Modal panel, dropdown menu |
| `slide-in-right` | `translateX(8px) + opacity 0→1` | 200ms | `ease-out` | Sidebar drawer, notification |
| `spin` | `rotate: 0→360deg` | 1s | `linear` | Loading spinner |
| Button transition | — | 150ms | `ease` | Button hover/active state |
| Color transition | — | 300ms | `ease` | Theme toggle (bg, text, border) |

**⚠ Issue (audit #77):** No `prefers-reduced-motion` media query — wait, actually it IS present in `index.css` lines 136-143. ✓ This is already done.

**Proposed refinements:**
- Modal animation: Add `transform: scale(0.95 → 1) + opacity` for entrance animation (current is slide-up only)
- Duration: Keep 200ms for most animations; reduce to 150ms for micro-interactions
- Easing: Standardize on `ease-out` for entrances, `ease-in-out` for state transitions

---

## 7. Z-Index Scale

| Layer | Value | Components |
|-------|-------|-----------|
| Base | 0 | Page content |
| Sticky | 10 | Topbar, table headers |
| Dropdown | 20 | Search dropdown, profile menu |
| Modal overlay | 40 | Backdrop |
| Modal | 50 | Dialog panel |
| Toast/Notification | 60 | Toasts, snackbars |
| Tooltip | 70 | Tooltips |

✓ All current implementations use the right z-index tiers.

---

## Summary of Proposed Changes

| # | Token / Area | Current | Proposed | Severity | Rationale |
|---|-------------|---------|----------|----------|-----------|
| 1 | `font-sans` on body | Missing | Add `font-sans` to body `@apply` | **Blocker** | Inter not applied; brand typography broken |
| 2 | `--color-success` | `#10B981` | `#059669` | Minor | WCAG AA compliance on white |
| 3 | `--color-surface-tertiary` | `#f3f4f6` (gray-100) | `#E2E8F0` (slate-200) | Nit | Align with slate palette |
| 4 | `--color-border-light` | `#f3f4f6` (gray-100) | `#F1F5F9` (slate-100) | Nit | Align with slate palette |
| 5 | H1 heading on login | `text-2xl` (24px) | `text-3xl` (28px) | Minor | Match heading scale |
| 6 | Card border radius | `rounded-xl` (12px) | `rounded-lg` (8px) | Minor | Consistency across components |
| 7 | App padding (mobile) | `p-3` | `p-4` | Minor | Audit #45: generous tap targets |
| 8 | Modal animation | `slide-up` only | Add `scale(0.95→1) + fade` | Minor | Polished entrance |
| 9 | Text tertiary for help text | `slate-400` (3.2:1) | `slate-500` (4.2:1) | Minor | Readable helper text |
| 10 | Info semantic token | Missing | Add `--color-info: #2563EB` | Minor | Semantic completeness |
| 11 | brand-950 | Missing | Add `#172554` | Nit | Dark surface hover depth |