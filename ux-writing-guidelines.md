# FrontierCRM — UX Writing Guidelines & Copy Audit

**Date:** 2026-06-30  
**Auditor:** Creative (ALLSTARS Design & Visual Specialist)

---

## Part 1: Copy Voice & Tone Guide

### Voice Principles

| Principle | Description | Example |
|-----------|-------------|---------|
| **Clear over clever** | Never sacrifice clarity for wordplay | "Enter your email address" not "The key to unlocking CRM magic" |
| **Action-oriented** | Tell users what they can do, not what they can't | "Update your password in Settings" not "Password cannot be changed here" |
| **Concise** | Fewer words = faster comprehension | "Sign in" not "Sign in to your account" (context already provides the rest) |
| **Human** | Conversational but professional | "We'll send you a link" not "A magic link email will be dispatched to the provided email address" |
| **Consistent** | Same term for same thing everywhere | Always "contacts", never "leads" or "prospects" for the same concept |

### Tone by Context

| Context | Tone | Example |
|---------|------|---------|
| Success messages | Warm, celebratory | "Deal created! 🎉" |
| Error messages | Empathetic, specific | "We couldn't send your email. Check the recipient address and try again." |
| Empty states | Encouraging, instructive | "No contacts yet. Add your first contact to get started." |
| Loading states | Neutral, brief | "Loading contacts..." (with skeleton) |
| Confirmation dialogs | Direct, clear | "Delete this contact? This can't be undone." |
| Guidance / helper text | Helpful, instructive | "Use an email address your teammates will recognize." |

### Dos and Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| "Sign in" | "Log in" / "Login" / "Authenticate" |
| "Sign up" | "Register" / "Create an account" (button says "Create account" — this is OK for the CTA) |
| "Connect Gmail" | "Authorize Gmail OAuth 2.0 Scope" |
| "Try again" | "Retry operation" |
| "Something went wrong" | "An unexpected error has occurred" |
| "Please enter..." | "Input required: ..." |
| "Cancel" | "Abort" / "Dismiss" |
| "Save Changes" | "Submit modifications" |
| "View Reports" | "Navigate to reports section" |
| "No contacts yet" | "No data available" |
| "Use a recovery code instead" | "Switch to recovery code authentication method" |

---

## Part 2: Current Copy Audit

### ☑ Button Labels

| Screen | Current Label | Recommendation | Issue Severity |
|--------|--------------|----------------|----------------|
| Login | "Sign in" | ✅ Correct | — |
| Login | "Continue with Google" | ✅ Correct | — |
| Login | "Continue with Microsoft" | ✅ Correct | — |
| Login | "Continue with SSO" | ✅ Correct | — |
| Login | "Sign in with magic link" | ✅ Correct | — |
| Signup | "Create account" | ⚠️ "Create Account" (title case to match "Sign In") | NIT |
| Signup | "Already have an account? Sign in" | ✅ Correct | — |
| Pipeline | "Add Deal" | ✅ Correct | — |
| Pipeline | "Create Deal" | ✅ Correct | — |
| Activities | "Create Meeting" | ✅ Correct | — |
| Activities | "Load more (X shown)" | ⚠️ "Load more (X loaded)" — "shown" implies the total, not what's been loaded | MINOR |
| Contact List | "Add Contact" | ✅ Correct | — |
| Contact Detail | "Edit" / "Delete" | ✅ Correct | — |
| Settings | "Save Changes" | ✅ Correct | — |
| Reports | "Export CSV" | ✅ Correct | — |
| Reports | "Try again" | ✅ Consistent | — |
| Email | "Connect Gmail" | ✅ Correct | — |
| Email | "Send Invitation" | ⚠️ "Send Invite" (shorter, friendlier) | NIT |
| General | "Try Again" | ✅ Consistent capitalisation | — |

### ☑ Error Messages

| Screen | Current Error | Recommendation | Severity |
|--------|--------------|---------------|----------|
| Login | "Invalid credentials" | "The email or password you entered is incorrect." Tell users what *to do*, not just what *went wrong*. | **MAJOR** |
| Login | "No SSO configured for this domain. Please sign in with email and password." | ✅ Clear, actionable | — |
| Login | "Failed to initiate SSO login." | "We couldn't start SSO. Please try again or sign in with your email and password." | MINOR |
| Signup | "Signup failed. Please try again." | "We couldn't create your account. {{ details }} Please try again or contact support." Include the actual server error. | **MAJOR** |
| Signup | Field-level: "First name is required", "Password is required" | ✅ Clear, specific | — |
| Signup | Password mismatch | "Passwords don't match" (add apostrophe) vs current "Passwords do not match" | NIT |
| Pipeline | Toast: "Failed to create deal" | "We couldn't create this deal. Check the form and try again." | MINOR |
| Email | Toast: "Failed to send email. Please try again." | ✅ Good — specific failure + action | — |
| Email | "Cancel" (while sending) | Button is disabled during send — replace with disable + "Sending..." (already done) | — |
| Calendar | Toast: "Title is required" | ✅ Clear | — |
| General | API error toast: "Something went wrong" | ✅ Acceptable default; also show error detail when available | — |

### ☑ Empty States

| Screen | Current Copy | Recommendation | Severity |
|--------|-------------|----------------|----------|
| Contacts | "No contacts yet" + "Get started by adding your first contact." | ✅ Excellent — title + guidance + CTA button | — |
| Dashboard | "No pipeline data yet" (chart empty state) | ✅ Adequate for a data-dependent view | — |
| Dashboard | "No recent activity" + inline illustration | ✅ Good — includes branded illustration | — |
| Dashboard | "No tasks due" | ⚠️ "All caught up! No tasks due." (friendly, positive) | NIT |
| Pipeline | "No deals" in column | ❌ **Poor** — "Drag a deal here or click [+ Add Deal] to get started." | **MAJOR** |
| Activity Timeline | "No activity yet" + "Start by creating a deal or contacting someone — activity will appear here automatically." | ✅ Excellent — instructive + specific | — |
| Email (Inbox) | "No emails yet" + "Your inbox is empty. Connect an email account to get started." | ✅ Good | — |
| Email (Sent) | "No sent emails" + "Sent emails will appear here once you compose your first message." | ✅ Good | — |
| Email (Starred) | "No starred emails" + "Star important emails to find them quickly." | ✅ Good | — |
| Email (Not connected) | "Connect your Gmail" + full guidance with Gmail button | ✅ Excellent — call-to-action driven empty state | — |
| Settings (Team) | "No team members yet. Invite someone to get started." | ✅ Good | — |
| Reports | "No forecast data available. Select a quarter and configure scenarios above." | ✅ Good | — |

### ☑ Helper Text & Labels

| Screen | Current Text | Recommendation | Severity |
|--------|-------------|----------------|----------|
| Login | "or sign in with email" (divider) | ⚠️ "or sign in with email and password" (more specific) | NIT |
| Login | Email placeholder: "you@company.com" | ✅ Good | — |
| Login | Password placeholder: "Enter your password" | ⚠️ "••••••••" or leave empty — placeholder text is redundant for password fields | NIT |
| Signup | Organization placeholder: "Your Company Inc" | ✅ Good | — |
| Signup | No helper text on password field | ⚠️ Add: "At least 8 characters" below password input | MINOR |
| Signup | Email placeholder: "you@company.com" | ✅ Consistent | — |
| Add Deal | "Deal Name" label, placeholder: "e.g. Enterprise Contract" | ✅ Good | — |
| Add Deal | "Value ($)" label, placeholder: "e.g. 50000" | ✅ Good | — |
| Calendar Event | "Title" label, placeholder: "e.g. Q3 Review with Alice" | ✅ Good | — |
| Calendar Event | "Date" + "Start Time" + "Duration (min)" | ✅ Good | — |
| Calendar Event | "Description" placeholder: "Meeting agenda, notes, or additional details..." | ✅ Good | — |
| Settings | Profile "Email" helper text: "Email cannot be changed" | ✅ Clear | — |
| Settings | Profile "Phone" placeholder: "+1 (555) 000-0000" | ✅ Good | — |
| Search | Placeholder: "Search contacts, deals..." | ✅ Good | — |
| Search | "Type at least 2 characters to search" | ✅ Good | — |
| Search | No results: "No results for &ldquo;{{query}}&rdquo;" + "Try a different search term" | ✅ Excellent | — |

---

## Part 3: Terminology Glossary

| Term | Use | Don't Use |
|------|-----|-----------|
| Sign in | ✅ Throughout | Log in, Login, Authenticate |
| Sign up | ✅ Throughout | Register, Create account (but "Create account" is OK as button label) |
| Sign out | ✅ Throughout | Logout, Disconnect |
| Deal | ✅ Pipeline object | Opportunity, Lead (if pre-qualified) |
| Contact | ✅ Person record | Lead, Prospect, Customer |
| Account | ✅ Company record | Organization, Company (when referring to CRM entity) |
| Pipeline | ✅ Sales stages | Funnel, Workflow |
| Stage | ✅ Pipeline step | Phase, Step |
| Activity | ✅ Timeline entry | Event, Action, Log entry |
| Timeline | ✅ Activity feed | Activity log, History |
| Dashboard | ✅ Main overview | Home, Overview |
| Reports | ✅ Analytics section | Analytics, Insights |
| Settings | ✅ Configuration | Preferences, Account |
| Team | ✅ User group | Organization (when referring to people) |
| Integration | ✅ Third-party connection | Connector, Plugin |
| Sync | ✅ Data sync | Synchronize |
| Connect | ✅ OAuth link | Authorize, Link account |
| Delete | ✅ Destructive action | Remove (when irreversible) |
| Remove | ✅ Non-destructive removal | Delete (when reversible) |

---

## Part 4: Empty State Improvement Blueprint

### Current "No deals" empty state (Pipeline column)
**Current:** "No deals" — plain text, no guidance, no action

**Proposed:**
```
┌─────────────────────────┐
│   [Arrow pointing down]  │
│   No deals yet           │
│                          │
│   Click [+ Add Deal]     │
│   or drag a deal here    │
│                          │
│   [Add Deal button]      │
└─────────────────────────┘
```
**Implementation:** Use the `EmptyState` component with a Deal-specific icon and action prop.

### Empty State Component Usage Map

| Screen | Component | Empty State Component? | Action Button? |
|--------|-----------|----------------------|----------------|
| Contacts List | `EmptyState` (local) | ✅ Yes (local component) | ✅ "Add Contact" |
| Pipeline Column | Text "No deals" | ❌ No | ❌ None |
| Activity Timeline | `EmptyState` (shared) | ✅ Yes | ❌ No (instructional text only) |
| Dashboard Activity | `ActivityEmptyState` (local) | ✅ Yes (SVG illustration) | ❌ None |
| Dashboard Tasks | `EmptyState` (local) | ✅ Yes | ❌ None |
| Dashboard Chart | `EmptyState` (local) | ✅ Yes | ❌ None |
| Email (tabs) | `EmptyState` (local) | ✅ Yes | ❌ None (varies by tab) |
| Email (not connected) | `NotConnectedState` (local) | ✅ Yes | ✅ "Connect Gmail" |
| Settings Team | `EmptyState` (local) | ✅ Yes | ✅ Via page-level button |
| Settings Custom Fields | Via `EmptyState` | ✅ Yes | ❌ None |
| Reports Forecast | Local div | ⚠️ Text-only | ❌ None |

**Recommendation:** Standardise all empty states to use the shared `EmptyState` component for visual consistency. Only the pipeline column and forecast report currently diverge.

---

## Part 5: Priority Copy Fixes

### Immediate
1. **UX-01**: Login error "Invalid credentials" → "The email or password you entered is incorrect."
2. **UX-02**: Signup error "Signup failed. Please try again." → include server error details
3. **UX-03**: Pipeline column "No deals" → Use EmptyState with guidance and Add Deal button

### Short-term
4. **UX-04**: All "Try again" error buttons → Ensure they always have `onRetry` connected (most already do)
5. **UX-05**: Activity timeline "Load more (X shown)" → "Load more (X loaded)"
6. **UX-06**: Settings "Send Invitation" → "Send Invite"

### Backlog
7. **UX-07**: "Passwords do not match" → "Passwords don't match"
8. **UX-08**: "No tasks due" → "All caught up! No tasks due."
9. **UX-09**: Password helper text on signup → "At least 8 characters"
10. **UX-10**: Reports forecast empty state → Use shared `EmptyState` component
