---
name: ack-triage
description: Use when an Alibaba Cloud ACK / Serverless-ACK cluster has problems specific to ACK rather than generic Kubernetes — ECI/virtual-node pods stuck pulling images (cross-border registry timeouts, needing a regional mirror), node-pool scaling not firing, Terway CNI ENI/IP issues, CCM-managed SLB with no targets or wrong listeners, ECI cold-start latency, or ACK-vs-upstream behavioral gaps. Read-only `kubectl` + `aliyun` CLI triage that names the Alibaba-Cloud-layer root cause.
---

# ack-triage

ACK (Alibaba Cloud Container Service for Kubernetes) is mostly upstream Kubernetes,
but the things that page you live in the Alibaba-Cloud seam: ECI/Serverless virtual
nodes, the Terway CNI, the Cloud Controller Manager (CCM) wiring Services to SLB, RAM
permissions, and — the single most common one — **cross-border image pulls timing
out** because the manifest points at a registry that's slow or blocked from the
mainland region. Those don't surface in a plain `kubectl describe`; you cross into the
`aliyun` API to see them. This skill drives that crossing read-only and reports the
**Alibaba-Cloud-layer root cause**.

Use `k8s-triage` for pure-Kubernetes symptoms. Use **this** when the problem smells
like Alibaba Cloud underneath: a Serverless pod that never finishes `ContainerCreating`,
an SLB with zero healthy targets, a node pool that won't grow.

## When to use

Reach for this on an ACK cluster when someone reports:

- a **Serverless-ACK / ECI / virtual-node pod stuck `ContainerCreating`** on image
  pull, `failed to pull image` / `context deadline exceeded` / very slow pulls
- **node pool not scaling** (managed node pool / autoscaler not adding ECS nodes)
- **Terway CNI** problems: pods stuck on ENI/IP allocation, `failed to alloc eni`
- a **`type: LoadBalancer` Service with no/unhealthy SLB targets**, wrong listeners,
  or no inbound traffic (CCM not reconciling)
- **ECI cold-start** latency: bursty Serverless pods taking minutes to become Ready
- **cross-border slowness**: pulls/registry/API to an out-of-region endpoint timing out
- behavior that differs from upstream K8s because it's **ACK-managed** (CCM annotations,
  Terway IPAM, virtual-kubelet limitations)

**When *not* to use:** app-level crashes, probe misconfig, OOM, or anything inside the
container — that's `k8s-triage`.

## Operating rules

1. **Read-only by default.** `kubectl get/describe/logs` and `aliyun ... Describe* /
   List* / Get*` only. Never mutate (`kubectl delete/patch/scale`, `aliyun ...
   Create/Modify/Delete`) as a *diagnostic*. Propose the fix; a human applies it.
2. **Confirm the target first.** Which cluster, region, and account? ACK clusters are
   region-bound and the `aliyun` CLI defaults a region — `aliyun cs DescribeClusterDetail`
   + the kube-context. Cross-region access is itself a frequent root cause.
3. **Suspect the region/registry boundary early.** For any image, registry, or
   external-endpoint symptom on a mainland-region cluster, check whether the target is
   *in-region* before anything else. Most ECI pull failures are this.
4. **Report the conclusion, not the dump.** End with: root cause → evidence (the one
   `aliyun`/`kubectl` line that proves it) → fix → blast radius → confidence.

## Triage order

```
0. Orient   → aliyun cs DescribeClusterDetail ; kube-context ; region/account match?
1. Workload → kubectl get pod -o wide ; on a real node or a virtual-node (ECI)?
2. Image    → for ContainerCreating/pull: is the registry in-region? mirror needed?
3. Nodes    → real node pool health, or ECI cold-start? kubectl get nodes
4. Scaling  → node-pool autoscaling: why no new ECS for Pending pods?
5. CNI      → Terway ENI/IP allocation; terway-* DaemonSet logs
6. Service  → CCM → SLB: Service events, EXTERNAL-IP, backend/listener health
7. RAM/region→ cross-region or RAM-permission failures on the managed components
```

Exact commands and per-symptom decision trees are in `references/ack-playbooks.md` —
open it once you know the symptom. The image-pull/mirror section and the CCM→SLB
section are the two deepest, and get the most detail there.

## ACK root causes that are easy to miss

The ones that waste the most time:

- **An ECI/Serverless pod stuck on image pull is almost always a cross-border /
  registry-reachability problem, not a broken image.** Serverless-ACK pods run on ECI
  virtual nodes that pull from the *public* registry endpoint by default; if the image
  lives on a registry that's slow or blocked from the mainland region (e.g. a foreign
  public registry), the pull times out and the pod sits `ContainerCreating`. The fix is
  to pull through an **in-region mirror / ACR instance** (rewrite the image to the
  regional registry, or configure a registry mirror), not to retry. See the playbook.

- **A long-running pod gives a false "image is fine" signal.** On a real node pool, an
  image that pulled successfully once is cached on that ECS node, so existing pods and
  re-deploys onto the *same* node look healthy — while a fresh node, a scale-up, or an
  ECI pod (no shared cache) fails the exact same pull. Always reproduce on a **fresh /
  Serverless** target before concluding the image is reachable. The cache hides the bug.

- **`type: LoadBalancer` with no traffic is usually CCM/SLB reconciliation, not the
  app.** ACK's Cloud Controller Manager provisions and wires the SLB from the Service.
  If the Service annotations are wrong, the SLB's vSwitch/subnet is in the wrong zone,
  the backend ECS isn't added, or the listener/health-check is misconfigured, you get an
  EXTERNAL-IP but zero healthy backends. Read the Service **events** (CCM logs its
  errors there) and the SLB backend health in the `aliyun slb` API — not the pod.

- **Terway gives pods real VPC ENIs/IPs; the vSwitch can run dry.** Like a cloud CNI
  elsewhere, Terway allocates from the pod vSwitch. A small vSwitch exhausts available
  IPs and new pods stall on ENI/IP allocation. Check the vSwitch free-IP count in VPC,
  not in Kubernetes.

- **ECI cold-start is latency, not failure.** Bursty Serverless workloads create ECI
  instances on demand; the first pods of a burst can take minutes (instance provision +
  image pull) before Ready. That's expected behavior, not a hang — distinguish "slow
  cold-start" from "stuck pull" by watching whether the pull progresses at all.

- **Cross-region access fails quietly.** A `aliyun` call or a cluster component pointed
  at the wrong region returns empty/timeout rather than an obvious error. Confirm the
  cluster's region and that every endpoint (registry, RAM, dependencies) is reached
  in-region before chasing exotic causes.

## Output template

```
Cluster/region: <name> / <region> / <account>
Root cause    : <one sentence, Alibaba-Cloud-layer, named>
Evidence      : <the single aliyun/kubectl line that proves it>
Fix           : <concrete, minimal, reversible — mirror/CCM/node-pool/Terway>
Blast radius  : <which nodes/workloads/zones; is it spreading?>
Confidence    : <high | medium — and what would raise it>
```
