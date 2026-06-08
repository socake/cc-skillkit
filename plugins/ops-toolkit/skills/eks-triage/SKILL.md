---
name: eks-triage
description: Use when an AWS EKS cluster has problems that are specific to EKS rather than generic Kubernetes — managed nodegroup nodes won't join / stay NotReady, the aws-node (VPC CNI) DaemonSet CrashLoops, pods stuck ContainerCreating with CNI/ENI errors, IRSA/IAM permission denials, Karpenter/cluster-autoscaler refusing to scale, subnet IP exhaustion, addon rollouts self-locking, or AZ/EBS volume-affinity conflicts. Read-only `kubectl` + `aws eks/ec2` triage that names the AWS-layer root cause.
---

# eks-triage

EKS hands you a managed control plane, but the failures that actually page you live
in the seam between Kubernetes and AWS: IAM, the VPC CNI, ENIs, subnets, nodegroups,
addons, and autoscalers. Those don't show up in a plain `kubectl describe` story —
you have to cross into the AWS API to see them. This skill drives that crossing in a
fixed, read-only order and reports the **AWS-layer root cause**, not a log dump.

Use `k8s-triage` for symptoms that are pure Kubernetes (CrashLoop from an app bug,
bad readiness probe, OOM). Use **this** when the problem smells like AWS underneath:
nodes that never register, CNI that can't hand out IPs, IRSA that silently isn't
working. The tell is usually "the workload config looks fine but it still won't run."

## When to use

Reach for this when someone reports, on an EKS cluster:

- a managed (or self-managed) **nodegroup whose nodes never become `Ready`**, or go
  `NotReady` / never `kubectl get nodes` at all
- **`aws-node` (VPC CNI) DaemonSet CrashLoopBackOff**, or pods stuck
  `ContainerCreating` with `failed to assign an IP` / `NetworkPlugin cni failed`
- **IRSA / IAM** errors: `AccessDenied`, `is not authorized to perform`,
  `UnauthorizedOperation`, `WebIdentityErr`, `ec2:DescribeNetworkInterfaces` denied
- **Karpenter / cluster-autoscaler not scaling**: pods Pending with
  `no matching nodepool`, NodeAffinity unmatched, `did not tolerate`, limits/quota hit
- pods Pending/ContainerCreating from **subnet IP exhaustion** (`InsufficientFreeAddressesInSubnet`)
- an **EKS addon stuck `Degraded` / `Updating`** (CNI, CoreDNS, kube-proxy, EBS CSI)
- **AZ / EBS volume node-affinity conflict** (`volume node affinity conflict`)
- after a **control-plane minor-version upgrade**, an addon or DaemonSet misbehaving

**When *not* to use:** app-level crashes, probe misconfig, OOM, Helm authoring, or
anything where the cause is inside the container, not in AWS — that's `k8s-triage`.

## Operating rules

1. **Read-only by default.** `kubectl get/describe/logs` and `aws eks describe-* /
   aws ec2 describe-*` only. Never `delete`/`patch`/`scale`/`rollout restart` or any
   `aws ... create/modify/delete` as a *diagnostic*. Propose the fix; let a human apply it.
2. **Confirm the target first.** Which cluster, region, and account? `aws sts
   get-caller-identity` + `kubectl config current-context`. A shocking share of "EKS
   outages" are credentials/context pointed at the wrong cluster or region. State it.
3. **Cross into AWS early.** If the symptom is nodes, CNI, IAM, or scaling, the
   Kubernetes view alone will not contain the answer — you must read the EKS/EC2 API.
4. **Report the conclusion, not the dump.** End with: root cause → evidence (the one
   AWS/kubectl line that proves it) → fix → blast radius → confidence.

## Triage order

Work top-down; stop when the evidence names a cause.

```
0. Orient   → aws sts get-caller-identity ; kubectl config current-context ; --region
1. Cluster  → aws eks describe-cluster: status, version, endpoint access, health
2. Nodes    → kubectl get nodes -o wide ; do nodegroup instances even register?
3. Nodegroup→ aws eks describe-nodegroup: health issues block node join (the gold mine)
4. CNI      → aws-node DaemonSet logs ; ENI/IP allocation ; IRSA on aws-node SA
5. IAM/IRSA → does the SA's role exist, trust the OIDC provider, hold the right policy?
6. Scaling  → Karpenter / cluster-autoscaler logs: why no node for Pending pods?
7. Addons   → aws eks describe-addon: Degraded/conflict; version vs control plane
8. Storage/AZ→ EBS CSI ; PV zone vs pod's node AZ
```

The exact commands and per-symptom decision trees are in
`references/eks-playbooks.md` — open it once you know the symptom. AWS IAM/IRSA and
VPC-CNI specifics (the two deepest rabbit holes) get their own sections there.

## EKS root causes that are easy to miss

The ones that burn the most time because the Kubernetes-only reading is wrong:

- **A `NotReady` / never-joining node is usually an IAM, CNI, or networking problem,
  not a bad kubelet.** The node's own diagnosis lives in
  `aws eks describe-nodegroup ... .health.issues` (e.g. `Ec2LaunchTemplateNotFound`,
  `NodeCreationFailure`, `AccessDenied`) and in the kubelet/bootstrap logs on the
  instance. A node that can't reach the API endpoint (security group / subnet route /
  private-endpoint DNS) or whose role isn't in `aws-auth` / an access entry will never
  register. Check `aws-auth` ConfigMap or EKS **access entries** for the node role.

- **`aws-node` CrashLoop or `failed to assign an IP` is usually IAM or IP exhaustion,
  not a CNI bug.** Two distinct causes that look identical from the pod:
  - **IRSA not effective → fell back to the node instance role, which lacks
    `AmazonEKS_CNI_Policy`.** If the `aws-node` ServiceAccount's IRSA annotation is
    missing/wrong, the pod silently uses the **node role**; if that role doesn't carry
    the CNI policy, `ec2:DescribeNetworkInterfaces` / `CreateNetworkInterface` get
    `AccessDenied` and IP allocation fails. Verify the SA annotation *and* that the
    assumed role actually has the policy.
  - **Subnet IP exhaustion.** The VPC CNI hands each pod a real VPC IP; a small /24
    worker subnet runs out and new pods sit `ContainerCreating` with
    `InsufficientFreeAddressesInSubnet`. Check free IPs per subnet in EC2, not in K8s.

- **IRSA silently does nothing if the OIDC provider isn't associated.** The SA can be
  annotated perfectly, but if the cluster's **IAM OIDC provider isn't created**, or
  the role's **trust policy** doesn't reference that provider + the exact
  `namespace:serviceaccount`, the token exchange fails and the pod falls back to the
  node role. `WebIdentityErr` / "not authorized to perform sts:AssumeRoleWithWebIdentity"
  is the fingerprint. The fix is in the trust policy, not the pod.

- **Karpenter/autoscaler "won't scale" is usually a constraint mismatch, not a quota.**
  `no matching nodepool` / `incompatible requirements` means the Pending pod's
  nodeSelector / affinity / taints / arch don't match any NodePool's allowed values —
  it will wait forever on a cluster with spare quota. Before raising limits, diff the
  pod's requirements against the NodePool's. Also check the NodePool/provisioner
  `limits` (cpu/memory) — once hit, it stops provisioning by design.

- **An addon update can self-lock.** An EKS addon set to a version with a
  `CONFLICT`/overwrite issue, or stuck mid-`UPDATING`, will report `DEGRADED` while the
  underlying DaemonSet won't fully roll. `aws eks describe-addon` + `describe-update`
  name the conflict; resolving it (resolve-conflicts / fix the override) is the fix,
  not deleting pods.

- **EBS volume node-affinity conflict pins a pod to one AZ.** A `gp3`/EBS PV exists in
  one AZ; if the pod is rescheduled to a node in another AZ it goes Pending with
  `volume node affinity conflict`. Single-AZ nodegroups + multi-AZ PVs are the trap.

- **Post-upgrade incompatibility.** After a control-plane minor bump, a pinned
  kube-proxy/CoreDNS/CNI addon version that's outside the skew window misbehaves.
  Compare addon versions to the new control-plane version before blaming the workload.

## Output template

```
Cluster/region: <name> / <region> / <account>
Root cause    : <one sentence, AWS-layer, named>
Evidence      : <the single aws/kubectl line that proves it>
Fix           : <concrete, minimal, reversible — IAM/CNI/addon/nodepool>
Blast radius  : <which nodes/workloads/AZs; is it spreading?>
Confidence    : <high | medium — and what would raise it>
```
