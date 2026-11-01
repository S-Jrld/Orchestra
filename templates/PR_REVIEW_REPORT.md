# PULL REQUEST REVIEW REPORT

> Mandatory format for Orchestra PR reviews. Conventional Comments enforced.

## 1. Metadata
- **PR**: #{{pr_number}} — {{pr_title}}
- **Author**: @{{author}}
- **Branch**: `{{head_ref}}` $\to$ `{{base_ref}}`
- **Verdict**: {{verdict}}

## 2. Executive Summary
{{executive_summary}}

## 3. Terminal Verification Scorecard
| Step | Command | Exit Code | Duration | Status |
|---|---|---|---|---|
{{verification_scorecard_rows}}

## 4. Impacted Dependencies
| Modified File | Upstream Importers |
|---|---|
{{impacted_dependency_rows}}

## 5. Review Findings (Conventional Comments)
{{findings_markdown}}
