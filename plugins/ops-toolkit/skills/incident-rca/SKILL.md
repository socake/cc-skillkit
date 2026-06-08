---
name: incident-rca
description: Use when you need to find the root cause of an incident, outage, or regression systematically — reconstruct a timeline, correlate with recent changes, test multiple hypotheses in parallel, and produce an evidence-backed root-cause writeup instead of a guess. For methodical RCA and blameless postmortems, not instant symptom lookup.
---

# incident-rca

A discipline for getting from "something broke" to a *named, evidence-backed root
cause* — and a fix that prevents recurrence. The enemy is the plausible-but-wrong
story: the first explanation that fits is often a symptom, a trigger, or a
coincidence, not the cause. This skill forces the rigor that catches that.

## When to use

- An incident/outage/regression needs a real root cause, not "we restarted it and
  it went away"
- Writing a blameless postmortem
- "Why did this happen?" where the answer isn't obvious and guessing is expensive
- Multiple competing explanations and you need to decide between them with evidence

**When *not* to use:** a known symptom with a known lookup path (use the relevant
triage skill, e.g. `k8s-triage`); or a one-glance fix. RCA is for when the cause is
genuinely unclear.

## The method

Work the steps in order. Don't jump to a fix before the evidence names the cause.

### 1. Frame the incident precisely

One or two sentences: **what** is impacted, **how much** (scope/severity), **since
when** (start time), and **what "normal" looks like** for comparison. A fuzzy frame
produces a fuzzy RCA. Pin the time window — it bounds everything downstream.

### 2. Reconstruct the timeline

Build an ordered list of events around the start time: deploys, config changes,
scaling/autoscaling events, infra changes (cert rotation, DNS, node lifecycle),
dependency incidents, the **first** error/alert (not when someone noticed). Sources:
deploy history, change logs, metrics annotations, alert timestamps, audit logs.

The single most useful question: **what was the first observable symptom, and what
happened in the 15 minutes before it?**

### 3. Correlate with change — "what changed?"

Most incidents are triggered by a change. Before exotic theories, line up the start
time against: code deploys, config/flag changes, scale events, dependency/version
bumps, certificate/credential rotation, traffic shifts. A change whose timestamp
hugs the incident start is your prime suspect — but correlation is a *lead*, not a
verdict; step 4 tests it.

### 4. Generate hypotheses, then test them in parallel

List **at least three** plausible causes — including at least one that isn't the
obvious one. For each, write a falsifiable prediction:

> "If hypothesis H is true, then I should observe E (and should *not* observe F)."

Then go check E/F. Testing predictions in parallel beats serially falling in love
with the first idea. Kill hypotheses fast; the survivor with positive evidence is
your candidate. Keep a one-line **hypothesis matrix** (see references) so you can
see which are confirmed, refuted, or untested.

### 5. Evidence discipline (anti-hallucination)

Non-negotiable for every claim:

- **Cite the evidence.** Each conclusion carries a pointer: a log line, a metric, a
  timestamp, a config diff. No bare assertions.
- **Separate observation from inference.** "Error rate hit 80% at 14:03" (observed)
  vs "therefore the deploy caused it" (inferred — does the timeline support it?).
- **State confidence and what would change it.** "High — the error stops exactly when
  the config is reverted" vs "Medium — correlated, but I haven't reproduced it."
- If you can't point to evidence, say "unknown / needs verification" — don't
  invent a mechanism to close the gap.

### 6. Drill to the mechanism — root cause, not surface

Apply *why* repeatedly until you reach a mechanism you could prevent, not just a
restated symptom. "Pod OOMed" → why → "limit too low for new payload size" → why →
"limit never updated when the feature shipped" → *that's* a root cause you can fix
and guard. Distinguish three things explicitly:

- **Root cause** — the underlying mechanism that, fixed, prevents recurrence
- **Trigger** — what set it off this time (often a change)
- **Contributing factors** — what made it worse / slower to detect / harder to fix

### 7. Remediation & prevention

- **Stop the bleeding** (short-term, reversible) vs **fix the cause** (durable).
- Add the two questions every good postmortem answers: *how do we prevent
  recurrence?* and *how do we detect it faster next time?* (alert, guardrail, test).

## Output: root-cause card

Close with this compact card (full templates, incl. blameless postmortem, in
`references/rca-templates.md`):

```
Incident   : <one line — impact, scope, since when>
Root cause : <mechanism, named>
Trigger    : <what set it off this time>
Evidence   : <the pointer(s) that prove it — log/metric/diff + timestamp>
Contributing: <factors that worsened/hid it>
Fix        : <stop-the-bleeding> | <durable fix>
Prevent/Detect: <guardrail or test> | <new signal/alert>
Confidence : <high|medium — and what would raise it>
```

Blameless throughout: name mechanisms and gaps in the system, not people.
