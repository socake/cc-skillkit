---
name: k8s-triage
description: Use when a Kubernetes workload is unhealthy — pods CrashLoopBackOff / Pending / OOMKilled / ImagePullBackOff, a Deployment won't roll out, or a service returns 5xx after a deploy. Drives a read-only, evidence-first triage in a fixed order (workload → events → logs → scheduling/resources → networking) and reports the root cause, not a log dump.
---

# k8s-triage

Structured, read-only triage for a misbehaving Kubernetes workload. The goal is
to reach a *named root cause* with evidence, fast — not to dump everything and
guess. Optimized for the failure modes that actually bite in production, several
of which look like one thing and are really another.

## When to use

Reach for this whenever someone reports any of:

- a pod stuck in `CrashLoopBackOff`, `Pending`, `OOMKilled`, `ImagePullBackOff`, `ErrImagePull`, `CreateContainerError`
- a `Deployment` / `Statefulset` / `Rollout` that won't progress or is stuck `Degraded`
- a service that started returning `5xx`, timeouts, or "no healthy upstream" after a deploy or scale event
- "it was fine yesterday and now it's down" on a K8s-hosted service

Do **not** use it for cluster-provisioning, Helm authoring, or app-level business
bugs — this is incident triage of a running workload.

## Operating rules

1. **Read-only by default.** `get`, `describe`, `logs`, `top`, `events` only. Never
   `delete`/`patch`/`scale`/`rollout restart` as a *diagnostic* — that destroys the
   evidence and can mask the cause. Propose a fix; let the human apply it.
2. **Confirm the target first.** Which cluster/context and namespace? A surprising
   share of "outages" are someone pointed at the wrong context. State it out loud.
3. **Follow the order below.** Don't jump to logs before you've read events; don't
   blame the app before you've ruled out scheduling and resources.
4. **Report the conclusion, not the dump.** End with: root cause → evidence
   (the one line that proves it) → suggested fix → blast radius.

## Triage order

Work top-down. Stop when the evidence names a cause; don't keep digging past it.

```
0. Orient      → which context + namespace; what is "broken" concretely?
1. Workload    → kubectl get deploy/sts/pod -o wide ; replicas desired vs ready
2. Events      → kubectl describe pod / kubectl get events --sort-by=.lastTimestamp
3. Logs        → current + previous container logs (--previous is where crashes hide)
4. Scheduling  → why Pending? nodeSelector / taints+tolerations / affinity / quota
5. Resources   → requests/limits vs node capacity; OOM; HPA behavior
6. Networking  → Service endpoints, readiness gating, Ingress/Gateway routing
```

The exact commands and the symptom-by-symptom decision trees live in
`references/symptom-playbooks.md`. Open it once you know the symptom — it covers
`Pending`, `CrashLoopBackOff`, `OOMKilled`, `ImagePullBackOff`, stuck rollouts,
and post-deploy `5xx` individually.

## Root causes that are easy to miss

These are the ones that waste the most time because the obvious reading is wrong:

- **`Pending` is usually *unschedulable*, not *out of capacity*.** Before assuming
  the cluster is full, check `nodeSelector` / node `taints` vs pod `tolerations` /
  `affinity`. A pod bound to a dedicated node pool whose taint it doesn't tolerate
  will sit `Pending` forever on a half-empty cluster. `describe pod` spells out
  the reason under Events (`0/N nodes available: … didn't match node selector /
  had untolerated taint`).

- **A rolling update can deadlock on a dedicated/full node pool.** With
  `maxSurge>0` the new pod is created *before* the old one is removed; if the pool
  has no room for the surge replica it goes `Pending`, the rollout stalls, and the
  deploy "times out" even though nothing is crashing. Look at `maxSurge`/
  `maxUnavailable` against available capacity in that pool.

- **Memory-based HPA over-scales steady-memory services.** A service with a large
  constant baseline (JVM heap, cache, model weights) sits near its memory target
  permanently, so a `memory`-Utilization HPA reads "high memory" as "needs more
  replicas" and scales out without bound while CPU is ~0%. If replicas climbed but
  load didn't, suspect the HPA metric, not traffic.

- **`--previous` logs hold the real error.** For `CrashLoopBackOff` the *current*
  container is the fresh restart; the stack trace that killed it is in
  `kubectl logs <pod> --previous`. Reading only current logs shows a healthy boot
  and hides the crash.

- **Transient node churn ≠ app failure.** During node recycling / graceful
  shutdown / spot reclaim, in-flight requests fail briefly and agents emit scary
  errors. Correlate the error timestamp with node lifecycle events before blaming
  the app — a node that went away one second before the error is the cause.

- **Service has zero endpoints because readiness fails.** A `5xx`/"no healthy
  upstream" with pods `Running` often means the readiness probe never passes, so
  the Service has no endpoints. `kubectl get endpoints <svc>` empty + pods Running
  = readiness/probe problem, not the app being down.

## Output template

```
Root cause : <one sentence, named>
Evidence   : <the single command output line that proves it>
Fix        : <concrete, minimal, reversible>
Blast radius: <who/what is affected; is it spreading?>
Confidence : <high | medium — and what would raise it>
```
