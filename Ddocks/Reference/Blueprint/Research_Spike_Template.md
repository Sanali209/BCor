---
id: RS-{{NUMBER}}
parent_goal: GL-{{NUMBER}}
hypothesis: "If we do {{X}}, then {{Y}} because {{Z}}"
verdict: PENDING
created_at: {{ISO_TIMESTAMP}}
revision_count: 1
---

# Research Spike: {{TOPIC}}

## Research Questions
1. {{Core technical question to answer}}
2. {{Risk or unknown to validate}}

## Experiment / POC Plan
{{Describe the minimal experiment to validate or invalidate the hypothesis.}}

## Results
{{Findings from the experiment. What was discovered?}}

## Verdict
- **Decision:** PENDING | SUCCESS | FAILED
- **Justification:** {{Why this verdict was reached.}}

## Impact on Features
- [FT-xxx]({{PATH_TO_FEATURE}}) — `research_required` can now be set to false.

## Technical Justification
{{One paragraph suitable for inclusion in the architectural documentation.}}
