# SKILL ADAPTER: IMPECCABLE

> High-craft frontend design, visual hierarchy, UI/UX refinement, and accessibility.

## Overview
- **Trigger**: Any user-facing interface work: components, forms, dashboards, typography, motion, responsive layout, dark mode, or design systems.
- **Pipeline Stage**: `UI / UX Design & Refinement`
- **Scope Restriction**: Not for backend-only logic, data pipelines, or server configurations.

## Modes of Design
- **Operate**: App UI, dashboards, tools, forms. Priority: scanability, native affordances, keyboard accessibility, clear error recovery states.
- **Persuade**: Landing pages, marketing. Priority: distinct brand POV, high visual impact, clear calls to action.
- **Read**: Documentation, changelogs, articles. Priority: typography hierarchy, readable line lengths, clear content structure.
- **Experience**: Showcases, portfolios. Priority: immersive visual presentation.

## Craft Floor Checklist
1. **Accessibility (a11y)**: Semantic HTML, full keyboard navigation, WCAG AA color contrast, screen reader labels.
2. **State Completeness**: Always implement all 4 UI states: `Loading`, `Success`, `Error` (with retry action), and `Empty`.
3. **Typography & Layout**: Strict typographic scale, consistent spatial grid (4px/8px), no horizontal overflow on mobile viewports.
4. **Motion & Feedback**: Micro-interactions for button clicks, hover states, and state transitions (150-250ms).

## Execution
```bash
# If CLI tool installed:
impeccable context --target <component-path>
# Or adhere directly to the craft floor rules during UI edits
```
