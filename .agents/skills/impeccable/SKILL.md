---
name: impeccable
description: >-
  Use for frontend craft, UI component styling, layout architecture, accessibility (WCAG AA),
  and responsive state design (loading, error, empty, success).
---

# /impeccable (Frontend Craft & UI Polish)

> Design polish, frontend component craftsmanship, accessibility (a11y), and responsive layout rigor.

## Overview
- **Trigger**: Frontend UI components, styling fixes, layout polish, responsive design, animations, or accessibility audits.
- **Pipeline Stage**: `UI Implementation & Polish` (runs after logic TDD / design intelligence)

## The 4 Modes of User Attention
- **Transact**: Forms, checkouts, dashboards. Priority: scanability, native affordances, keyboard accessibility, clear error recovery states.
- **Persuade**: Landing pages, marketing. Priority: distinct brand POV, high visual impact, clear calls to action.
- **Read**: Documentation, changelogs, articles. Priority: typography hierarchy, readable line lengths, clear content structure.
- **Experience**: Showcases, portfolios. Priority: immersive visual presentation.

## Craft Floor Checklist
1. **Accessibility (a11y)**: Semantic HTML, full keyboard navigation, WCAG AA color contrast, screen reader labels.
2. **State Completeness**: Always implement all 4 UI states: `Loading`, `Success`, `Error` (with retry action), and `Empty`.
3. **Typography & Layout**: Strict typographic scale, consistent spatial grid (4px/8px), no horizontal overflow on mobile viewports.
4. **Motion & Feedback**: Micro-interactions for button clicks, hover states, and state transitions (150-250ms).
