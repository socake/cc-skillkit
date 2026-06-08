# Symptom playbooks

Open the section matching the observed symptom. Each is a short decision tree with
exact read-only commands. Placeholders: `<ns>` namespace, `<pod>`, `<deploy>`,
`<svc>`. Add `-n <ns>` to every command (omitted below for brevity).

A useful first command for almost any symptom:

```bash
kubectl get pod <pod> -o wide
kubectl describe pod <pod> | sed -n '/Events:/,$p'   # the Events block is gold
```

---

## Pending — pod never schedules

```bash
kubectl describe pod <pod> | sed -n '/Events:/,$p'
```

Read the scheduler message under Events. It tells you exactly why:

- `didn't match node selector` / `had untolerated taint {…}` →
  scheduling constraint, **not** capacity. Compare:
  ```bash
  kubectl get pod <pod> -o jsonpath='{.spec.nodeSelector}{"\n"}{.spec.tolerations}{"\n"}'
  kubectl get nodes --show-labels
  kubectl get nodes -o json | jq '.items[].spec.taints'
  ```
  Fix: add the missing toleration / correct the nodeSelector, or schedule onto a
  pool that matches.

- `Insufficient cpu` / `Insufficient memory` → genuine capacity. Check requests
  vs allocatable:
  ```bash
  kubectl get pod <pod> -o jsonpath='{.spec.containers[*].resources}{"\n"}'
  kubectl describe nodes | grep -A5 'Allocated resources'
  kubectl top nodes
  ```
  Fix: lower requests, add nodes, or wait for autoscaler. If a cluster-autoscaler/
  Karpenter is present, check its logs — it may be refusing to scale (no matching
  nodepool, limits hit).

- `pod has unbound immediate PersistentVolumeClaims` → storage. See the PVC:
  ```bash
  kubectl get pvc ; kubectl describe pvc <pvc>
  ```

- `node(s) had volume node affinity conflict` → PV is zone-locked to a node the
  pod can't land on.

---

## CrashLoopBackOff — container keeps dying

The crash reason is in the **previous** container, not the current one:

```bash
kubectl logs <pod> --previous --tail=100
kubectl describe pod <pod> | sed -n '/Last State:/,/Ready:/p'   # exit code + reason
```

- Exit code `137` = SIGKILL, usually **OOMKilled** (see that section) or liveness
  probe killing a slow starter.
- Exit code `1`/`2` with a stack trace = application boot error — missing config,
  bad env var, failed dependency connection. Read the trace.
- `Reason: Error` immediately after start + healthy-looking logs = the process
  exits 0/non-0 too fast; check the entrypoint/command.
- Liveness probe too aggressive for startup time → container is healthy but killed
  before it finishes booting. Compare `initialDelaySeconds` to real boot time:
  ```bash
  kubectl get pod <pod> -o jsonpath='{.spec.containers[*].livenessProbe}{"\n"}'
  ```
  Fix: raise `initialDelaySeconds` or add a `startupProbe`.

---

## OOMKilled

```bash
kubectl describe pod <pod> | grep -i -A3 'Last State'   # shows OOMKilled
kubectl top pod <pod> --containers
```

- Container limit too low for real usage → raise `resources.limits.memory`, but
  first confirm it's not a leak (memory climbs monotonically until the limit).
- Node-level OOM (whole node under pressure) vs container-level (this container hit
  its cgroup limit) are different problems — `describe` says which. Node pressure
  shows as evictions across many pods.

---

## ImagePullBackOff / ErrImagePull

```bash
kubectl describe pod <pod> | grep -i -A2 'Failed'
```

- `not found` / `manifest unknown` → wrong tag or image never pushed. Verify the
  tag exists in the registry.
- `unauthorized` / `pull access denied` → missing/expired `imagePullSecret`:
  ```bash
  kubectl get pod <pod> -o jsonpath='{.spec.imagePullSecrets}{"\n"}'
  kubectl get secret <secret> -o jsonpath='{.type}{"\n"}'   # want kubernetes.io/dockerconfigjson
  ```
- timeout pulling → registry reachability from the node (firewall, regional
  mirror). Long-running pods on the same node can mask this because the image is
  already cached locally — a fresh node exposes it.

---

## Rollout stuck / Deployment won't progress

```bash
kubectl rollout status deploy/<deploy> --timeout=10s   # will report what's blocking
kubectl get rs -l app=<deploy> -o wide                 # old vs new ReplicaSet
kubectl describe deploy <deploy> | sed -n '/Conditions:/,/Events:/p'
```

- New ReplicaSet has `Pending` pods → jump to the **Pending** playbook. The classic
  trap: `maxSurge>0` needs a surge replica the node pool can't fit.
- New pods `CrashLoopBackOff` → the new image is broken; rollout correctly refuses
  to proceed. Triage the new pod as a crash.
- `ProgressDeadlineExceeded` → it gave up; the underlying reason is in the new
  pods' events.
- Surge math: with a dedicated/full pool, set `maxSurge: 0` + `maxUnavailable: 1`
  so it removes-then-creates instead of needing extra room.

---

## Post-deploy 5xx / timeouts / "no healthy upstream"

Pods can be `Running` and the service still be down. Check the chain endpoint-out:

```bash
kubectl get endpoints <svc>            # EMPTY endpoints = readiness failing
kubectl get pod -l <selector> -o wide  # are pods Ready (not just Running)?
kubectl describe pod <pod> | grep -i -A3 'Readiness'
```

- Endpoints empty + pods Running → **readiness probe never passes**, so the Service
  routes to nothing. Fix the probe or the thing it checks; the app may be fine.
- Endpoints present but still 5xx → look one layer up: Ingress/Gateway/HTTPRoute
  routing, or the app genuinely erroring (read its logs).
- 5xx started exactly at deploy time + new pods Ready → likely the new build; check
  whether a rollback restores service, and read new-pod logs for the error.
- Single-replica critical pods (ingress gateways, controllers) are a SPOF: if one
  is `Pending` after a node event the whole service drops. Verify replica count and
  PodDisruptionBudgets for anything on the request path.

---

## Wrap-up

Whatever the symptom, close with the output template from `SKILL.md`: named root
cause, the one line of evidence, a minimal reversible fix, and the blast radius.
Resist proposing the fix until the evidence names the cause.
