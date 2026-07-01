# FrontierCRM — Visual Identity Guide

**Version:** 2.0 (proposed refinements)
**Status:** Draft for Review
**Date:** 2026-06-30

---

## 1. Logo

### 1.1 Logo Lockups

Three primary lockups are provided for different contexts:

| Variant | File | Usage |
|---------|------|-------|
| **Full lockup** | `logo.svg` / `logo-full.png` | Primary brand representation — header, landing page, documentation |
| **Mark only** | `logo-mark.svg` / `logo-mark.png` | Favicon, social avatar, app launcher icon, small spaces |
| **Wordmark** | `logo-wordmark.svg` / `logo-wordmark.png` | Situations where mark alone is insufficient but full lockup is too wide |

### 1.2 Logo Mark Anatomy

The FrontierCRM mark is a **compass-forward arrow** symbolizing:

- **Direction** — North arrow pointing forward (growth, progress)
- **Exploration** — Compass circle (discovery, CRM as a map of relationships)
- **Precision** — Center diamond + teal dot (data-driven accuracy)
- **Connectivity** — East/West/South points (360° view of customer relationships)

### 1.3 Clear Space

- **Full lockup:** Minimum clear space = height of the letter "F" on all sides
- **Mark only:** Minimum clear space = 50% of mark width on all sides
- **Wordmark:** Minimum clear space = height of the word "Frontier" on all sides

### 1.4 Minimum Size

| Variant | Digital | Print |
|---------|---------|-------|
| Full lockup | 140px wide | 1.5in wide |
| Mark only | 24px × 24px | 0.25in × 0.25in |
| Wordmark | 100px wide | 1in wide |

### 1.5 Logo Do's and Don'ts

**Do:**
- Use the full-color lockup on light backgrounds (`#FFFFFF`, `#F8FAFC`)
- Use the dark-background lockup on dark backgrounds (`#0B1120`, `#1E293B`)
- Maintain aspect ratio when resizing
- Use component-level SVG where possible for crisp rendering

**Don't:**
- Do not stretch, skew, or rotate the logo
- Do not recolor the logo — use the provided color variants
- Do not place the logo on busy backgrounds or low-contrast surfaces
- Do not add effects (drop shadows, glows) to the logo
- Do not substitute a different icon or symbol for the mark
- Do not use the wordmark without the mark in application icon contexts

---

## 2. Color Application Rules

### 2.1 Primary Color — Blue (`#2563EB`)

| Usage | Token | Notes |
|-------|-------|-------|
| Primary buttons (default) | `bg-brand-600` (`#2563EB`) | WCAG AA 4.9:1 on white |
| Primary buttons (hover) | `bg-brand-700` (`#1D4ED8`) | WCAG AAA 6.2:1 on white |
| Primary buttons (active) | `bg-brand-800` (`#1E40AF`) | WCAG AAA 8.0:1 on white |
| Links | `text-brand-600` | Underline on hover |
| Active nav item (bg) | `bg-brand-50` | Light tint, not for text |
| Active nav item (text) | `text-brand-700` | WCAG AAA 6.2:1 on white |

### 2.2 Color for Text

| Level | Light Mode | Dark mode | Minimum Contrast |
|-------|-----------|-----------|-----------------|
| Primary text | `text-slate-800` (`#1E293B`) | `text-slate-100` (`#F1F5F9`) | 13.5:1 / 12.5:1 (AAA) |
| Secondary text | `text-slate-600` (`#475569`) | `text-slate-400` (`#94A3B8`) | 6.5:1 (AAA) / 3.5:1 |
| Tertiary/placeholder | `text-slate-400` (`#94A3B8`) | `text-slate-500` (`#64748B`) | 3.2:1 / 4.2:1 |
| Inverse text | `text-white` | `text-white` | 12.5:1+ |

**Rule:** Do not use `text-slate-400` for body text or labels — it fails WCAG AA on white. Use `text-slate-600` for all readable secondary content.

### 2.3 Surface Colors

| Surface | Light | Dark | Usage |
|---------|-------|------|-------|
| Page bg | `bg-slate-50` (`#F8FAFC`) | `bg-slate-950` (`#0B1120`) | Default page background |
| Card bg | `bg-white` | `bg-slate-800` (`#1E293B`) | Cards, dropdowns, modals |
| Secondary bg | `bg-slate-100` (`#F1F5F9`) | `bg-slate-800` (`#1E293B`) | Table headers, sidebar |
| Tertiary bg | `bg-slate-200` (`#E2E8F0`) | `bg-slate-700` (`#334155`) | Hover states, active bg |

### 2.4 Border Colors

| Level | Light | Dark | Usage |
|-------|-------|------|-------|
| Default | `border-slate-200` (`#E2E8F0`) | `border-slate-700` (`#334155`) | Card borders, table dividers |
| Light | `border-slate-100` (`#F1F5F9`) | `border-slate-800` (`#1E293B`) | Subtle interior dividers |

### 2.5 Semantic Color Usage

| Status | Token | Usage |
|--------|-------|-------|
| Success | `text-emerald-600` (`#059669`) | Won deal, completed task, active |
| Warning | `text-amber-700` (`#B45309`) | Pending, at-risk, caution |
| Error | `text-red-500` (`#EF4444`) | Lost deal, error message, blocked |
| Info | `text-blue-600` (`#2563EB`) | Informational status |

**Badge backgrounds:**
- Success badge: `bg-emerald-50` + `text-emerald-700`
- Warning badge: `bg-amber-50` + `text-amber-700`
- Error badge: `bg-red-50` + `text-red-700`
- Info badge: `bg-blue-50` + `text-blue-700`

---

## 3. Typography Hierarchy

### 3.1 Headings

```
H1 — Page Title (28px / 36px line-height / 700 weight / -0.02em tracking)
  Example: Dashboard, Contacts, Pipeline

H2 — Section Header (24px / 32px line-height / 700 weight / -0.015em tracking)
  Example: Pipeline by Stage, Recent Activity

H3 — Card Title (20px / 28px line-height / 600 weight / -0.01em tracking)
  Example: Deal Value, Contact Name

H4 — Small Section (18px / 28px line-height / 600 weight / -0.005em tracking)
  Example: Filter Section, Stats Group
```

### 3.2 Body & UI

```
Body — (14px / 20px line-height / 400 weight)
  Example: All paragraph text, form labels, table cells

Small — (12px / 16px line-height / 400 or 500 weight)
  Example: Captions, table headers, sidebar nav, timestamps

Caption — (11px / 14px line-height / 500 weight / 0.05em uppercase tracking)
  Example: Table column headers (as `text-xs font-semibold uppercase tracking-wider`)
```

### 3.3 Code & Data

```
Code — (13px / 18px line-height / 400 weight / JetBrains Mono)
  Example: API endpoints, IDs, monetary values, keyboard shortcuts (kbd: 10px)
```

---

## 4. Spacing Principles

### 4.1 Grid System

FrontierCRM uses Tailwind's default 4px unit grid:
- **1 unit** = 4px
- Standard spacing increments: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64px

### 4.2 Content Padding

| Container | Mobile (<640px) | Tablet (640-1024px) | Desktop (>1024px) |
|-----------|----------------|--------------------|-------------------|
| Page content | 16px (p-4) | 24px (p-6) | 32px (p-8) |
| Card body | 16px (p-4) | 20px (p-5) | 20px (p-5) |
| Modal body | 24px (px-6 py-3) | 24px | 24px |

### 4.3 Component Spacing

- **Between form fields:** 16px (`space-y-4`)
- **Button groups:** 8px (`gap-2`)
- **List items:** 4px (`space-y-1`)
- **Section divider:** 24px (`mb-6 mt-6`)

---

## 5. Imagery & Illustration Style

### 5.1 Style Guidelines

- **Format:** Geometric abstractions with curved and angled elements
- **Colors:** Brand blue (`#2563EB`), secondary teal (`#14B8A6`), subtle accent amber (`#F59E0B`) on dark navy (`#0B1120`) backgrounds
- **Tone:** Professional, data-forward, clean — not cartoonish or overly playful
- **Theme:** CRM-related metaphors — pipelines, data flows, connected nodes, growth charts, kanban columns
- **Background:** Dark navy (`#0B1120`) or transparent — illustrations should work on the app's dark surface

### 5.2 Image Types

| Type | Purpose | Format |
|------|---------|--------|
| Hero/Banner | Landing page, marketing | 16:9 PNG, dark theme |
| Feature illustration | Empty states, feature pages | Square or 4:3 PNG |
| Data visualization | Charts, reports | In-app (React/Chart.js) — not illustration |
| Iconography | UI elements | Lucide React icons (already in use) |

### 5.3 Illustration Do's and Don'ts

**Do:**
- Use brand color palette exclusively
- Keep compositions clean with ample negative space
- Use subtle glow/lighting effects on brand-500 elements

**Don't:**
- Don't use stock photography
- Don't mix illustration styles (geometric + organic)
- Don't place text inside illustrations
- Don't use rasterized icons that could be SVG

---

## 6. Application Icon & Favicon

| Size | Format | Usage |
|------|--------|-------|
| 32×32 | PNG | Favicon (browser tab) |
| 192×192 | PNG | PWA home screen icon |
| 512×512 | PNG | PWA splash screen |
| SVG | SVG | Application toolbar icon |

The app icon uses the **mark-only** variant centered on a brand-600 (`#2563EB`) rounded square background.

---

## 7. Dark Mode Principles

Dark mode inversions should be designed as **color-aware transformations**, not simple luminance flips:

| Element | Principle |
|---------|-----------|
| Surfaces | Scale: `white → slate-800 → slate-950` for depth hierarchy |
| Borders | `slate-200 → slate-700` (maintain 1px weight) |
| Text | `slate-800 → slate-100` (maintain contrast) |
| Brand colors | `brand-600 → brand-500` (brighter on dark) |
| Shadows | Use `black/10` to `black/15` opacity — not gray |
| Saturation | Reduce saturation on semantic colors to avoid eye strain |

Dark mode is applied via the `.dark` class on `<html>` using `@custom-variant dark (&:where(.dark, .dark *));` in `index.css`. ✓

---

*FrontierCRM Design System · Visual Identity Guide v2.0*