# RCA templates

Fill-in scaffolds for the `incident-rca` method. Copy the one you need.

---

## Hypothesis matrix

Keep this visible while investigating. One row per hypothesis; update Status as
evidence comes in. Forces parallel testing instead of tunnel vision.

| # | Hypothesis | Prediction if true (E) | Counter-evidence (F) | Status | Notes |
|---|-----------|------------------------|----------------------|--------|-------|
| 1 | <cause A> | <what you'd see>       | <what would refute>  | untested / confirmed / refuted | <pointer> |
| 2 | <cause B> | …                      | …                    | … | … |
| 3 | <non-obvious cause> | …            | …                    | … | … |

Rule: a hypothesis isn't "confirmed" until you've seen its positive evidence **and**
failed to find its counter-evidence.

---

## Timeline scaffold

Reconstruct around the incident start. Use real timestamps; mark the first symptom.

```
T-…   <recent deploy / config change / scale event / cert rotation>
T-…   <dependency event / traffic shift>
T0    <FIRST observable symptom — error/alert, not human notice>   ← anchor
T+…   <escalation / spread>
T+…   <mitigation applied>
T+…   <recovery confirmed>
```

The 15 minutes before T0 is where the trigger usually hides.

---

## Root-cause card

```
Incident   : <one line — impact, scope, since when>
Root cause : <underlying mechanism, named — not a restated symptom>
Trigger    : <what set it off this time>
Evidence   : <log line / metric / config diff + timestamp that prove it>
Contributing: <factors that worsened it or delayed detection/fix>
Fix        : <stop-the-bleeding, reversible> | <durable fix of the cause>
Prevent/Detect: <guardrail/test to prevent> | <signal/alert to detect faster>
Confidence : <high | medium> — <what evidence would raise it>
```

---

## Blameless postmortem

```
# Postmortem: <incident title>

## Summary
<2–3 sentences: what happened, impact, duration, resolution.>

## Impact
- Users/services affected: <…>
- Severity & duration: <…>
- Quantified blast radius: <requests failed / revenue / SLO burn>

## Timeline
<from the timeline scaffold, with timestamps>

## Root cause
- Root cause: <mechanism>
- Trigger: <what set it off>
- Contributing factors: <…>
(Describe systems and gaps, never individuals.)

## What went well / what went poorly
- Detection: <how long to detect; was the alert good?>
- Response: <what helped, what slowed us>

## Action items
| Action | Type (prevent/detect/mitigate) | Owner | Priority |
|--------|--------------------------------|-------|----------|
| <fix the cause> | prevent | <…> | P1 |
| <add guardrail/test> | prevent | <…> | P2 |
| <add/raise alert> | detect | <…> | P2 |

## Lessons
<what the system should learn — durable, not "be more careful">
```

---

## Anti-patterns to refuse

- "Restarted and it's fine" filed as a root cause — that's mitigation, cause unknown.
- A single hypothesis, confirmed by the absence of disproof — confirmation bias.
- Correlation reported as causation without a tested prediction.
- A mechanism asserted with no evidence pointer — if unknown, say so.
- Blame on a person instead of the system gap that let it happen.
