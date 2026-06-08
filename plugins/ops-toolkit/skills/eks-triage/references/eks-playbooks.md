# EKS playbooks

Open the section matching the symptom. Every command is read-only. Placeholders:
`<cluster>` cluster name, `<region>`, `<account>`, `<ng>` nodegroup, `<ns>`
namespace, `<pod>`, `<sa>` serviceaccount, `<role>` IAM role, `<subnet>`. Assume
`--region <region>` on every `aws` call (omitted below for brevity).

First, always orient — the wrong-cluster/region/account mistake is common:

```bash
aws sts get-caller-identity                       # which account/principal am I?
kubectl config current-context                    # which cluster context?
aws eks describe-cluster --name <cluster> \
  --query 'cluster.{status:status,version:version,health:health}'
```

---

## Nodes never join / NotReady

The node's real reason lives in the **nodegroup health**, not in `kubectl`:

```bash
kubectl get nodes -o wide                         # do the instances even appear?
aws eks describe-nodegroup --cluster-name <cluster> --nodegroup-name <ng> \
  --query 'nodegroup.{status:status,health:health,scaling:scalingConfig}'
```

Read `health.issues[]`. Common codes and what they mean:

- `Ec2LaunchTemplateNotFound` / `Ec2LaunchTemplateVersionMismatch` → the launch
  template was changed/deleted out from under the nodegroup.
- `NodeCreationFailure` → instances launched but never registered with the API. Top
  causes, in order to check:
  1. **Node role not authorized.** The node IAM role must be mapped. Check the
     `aws-auth` ConfigMap **or** EKS access entries:
     ```bash
     kubectl -n kube-system get configmap aws-auth -o yaml         # legacy path
     aws eks list-access-entries --cluster-name <cluster>          # access-entry path
     ```
     The role needs `AmazonEKSWorkerNodePolicy`, `AmazonEC2ContainerRegistryReadOnly`,
     and (for the CNI fallback) `AmazonEKS_CNI_Policy`.
  2. **Can't reach the API endpoint.** Private-only endpoint + node subnet lacking a
     route / DNS, or a security group that blocks 443 to the control plane:
     ```bash
     aws eks describe-cluster --name <cluster> \
       --query 'cluster.resourcesVpcConfig.{endpointPrivate:endpointPrivateAccess,endpointPublic:endpointPublicAccess,sgs:securityGroupIds,subnets:subnetIds}'
     ```
  3. **Bootstrap failure** (custom AMI / userdata). The kubelet/bootstrap log on the
     instance (`/var/log/cloud-init-output.log`, journald `kubelet`) names it — read
     via SSM Session Manager, not SSH, if available.
- `AccessDenied` → the nodegroup/cluster role can't perform a required action.

A node that is `Ready` but workloads won't schedule on it is a *scheduling* problem
(taints/affinity) → use `k8s-triage`, not this.

---

## aws-node (VPC CNI) CrashLoop / pods stuck ContainerCreating

Symptom from the pod side: `failed to assign an IP address to container` /
`NetworkPlugin cni failed to set up pod`. Two very different root causes:

```bash
kubectl -n kube-system get ds aws-node
kubectl -n kube-system logs ds/aws-node -c aws-node --tail=80
kubectl describe pod <pod> -n <ns> | sed -n '/Events:/,$p'
```

### Cause A — IRSA not effective, fell back to node role lacking CNI policy

If the logs show `AccessDenied` / `UnauthorizedOperation` on
`ec2:DescribeNetworkInterfaces`, `ec2:CreateNetworkInterface`,
`ec2:AssignPrivateIpAddresses`, the CNI is using a role without
`AmazonEKS_CNI_Policy`. Check whether IRSA is even wired on the `aws-node` SA:

```bash
kubectl -n kube-system get sa aws-node \
  -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}{"\n"}'
# empty / wrong  → aws-node is silently using the NODE INSTANCE role
```

If the annotation is missing or wrong, the pod assumes the **node instance role**. Verify
that role actually carries the CNI policy:

```bash
aws iam list-attached-role-policies --role-name <node-role>     # want AmazonEKS_CNI_Policy
```

Fix: attach `AmazonEKS_CNI_Policy` to the role that aws-node actually assumes (either
fix the IRSA annotation + its role, or attach the policy to the node role).

### Cause B — subnet IP exhaustion

The VPC CNI assigns each pod a real VPC IP. A small worker subnet runs dry; new pods
sit `ContainerCreating` with `InsufficientFreeAddressesInSubnet`. Look at EC2, not K8s:

```bash
aws ec2 describe-subnets --subnet-ids <subnet> \
  --query 'Subnets[].{az:AvailabilityZone,cidr:CidrBlock,free:AvailableIpAddressCount}'
```

`free` near 0 = exhaustion. Fixes (propose, don't apply): enable prefix delegation
(`ENABLE_PREFIX_DELEGATION=true` on aws-node) to pack more pods per ENI, add a larger
secondary CIDR / bigger subnets, or use custom networking to move pod IPs to a roomy
subnet. Tune `WARM_IP_TARGET` / `MINIMUM_IP_TARGET` to stop over-reserving.

Note: a long-running node can mask both causes — its ENIs/IPs are already allocated, so
existing pods look fine while *new* pods/nodes fail. Test on a fresh node.

---

## IRSA / IAM permission denials

Fingerprints: `WebIdentityErr`, `not authorized to perform
sts:AssumeRoleWithWebIdentity`, or an app getting `AccessDenied` despite "having a role."
IRSA fails silently and falls back to the node role, so the app sees the *node's*
permissions, not the ones you intended. Verify the whole chain:

```bash
# 1. SA is annotated with the role
kubectl -n <ns> get sa <sa> \
  -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}{"\n"}'

# 2. cluster has an IAM OIDC provider associated
aws eks describe-cluster --name <cluster> --query 'cluster.identity.oidc.issuer'
aws iam list-open-id-connect-providers      # the issuer host must appear here

# 3. the role TRUSTS that OIDC provider for the exact ns:sa
aws iam get-role --role-name <role> --query 'Role.AssumeRolePolicyDocument'
#   Condition StringEquals must contain  "<oidc>:sub": "system:serviceaccount:<ns>:<sa>"
#   (a ":aud": "sts.amazonaws.com" condition is also required)

# 4. the role actually has the needed permission policy
aws iam list-attached-role-policies --role-name <role>
aws iam list-role-policies --role-name <role>
```

The two classic breaks: **(2)** the OIDC provider was never created (token exchange
can't happen at all), and **(3)** the trust policy's `sub` doesn't match the real
`namespace:serviceaccount` (typo, wrong ns, hardcoded). Confirm what identity the pod
*actually* has by checking the projected token env:

```bash
kubectl -n <ns> exec <pod> -- env | grep AWS_   # want AWS_ROLE_ARN + AWS_WEB_IDENTITY_TOKEN_FILE
```

If `AWS_ROLE_ARN` is absent, the pod is on the node role — webhook didn't inject (SA
annotation missing, or pod predates the annotation). Fix the SA + restart the workload.

---

## Karpenter / cluster-autoscaler won't scale

Pending pods + no new nodes. Read the autoscaler's own reasoning:

```bash
# Karpenter
kubectl -n kube-system logs deploy/karpenter --tail=120 | grep -i -E 'nodepool|requirement|incompatible|limit'
kubectl get nodepool -o yaml        # (or provisioner, older versions)

# cluster-autoscaler
kubectl -n kube-system logs deploy/cluster-autoscaler --tail=120 | grep -i -E 'scale|nodegroup|nogroup|max'
```

- `no matching nodepool` / `incompatible requirements` / `did not tolerate` → the
  Pending pod's nodeSelector / affinity / taints / arch / capacity-type match no
  NodePool's allowed values. Diff them:
  ```bash
  kubectl get pod <pod> -n <ns> \
    -o jsonpath='{.spec.nodeSelector}{"\n"}{.spec.tolerations}{"\n"}{.spec.affinity}{"\n"}'
  ```
  Fix: widen the NodePool requirements or correct the pod's constraints. It will
  **never** schedule on its own — this is not a quota issue.
- `limits exceeded` / NodePool `limits` (cpu/memory) hit → autoscaler stops by design.
  Raise the limit (deliberately) or free capacity.
- cluster-autoscaler: ASG `maxSize` reached, or the node group lacks the
  `k8s.io/cluster-autoscaler/enabled` tag so it's ignored. Check ASG tags + max.
- Subnet IP exhaustion (above) also presents as "scaled the node but pods still
  Pending" — the node joins but the CNI can't give pods IPs.

---

## Addon stuck Degraded / Updating

```bash
aws eks list-addons --cluster-name <cluster>
aws eks describe-addon --cluster-name <cluster> --addon-name <addon> \
  --query 'addon.{status:status,version:addonVersion,health:health}'
aws eks describe-addon-versions --addon-name <addon> \
  --kubernetes-version <cluster-k8s-version> \
  --query 'addons[0].addonVersions[0].addonVersion'   # latest compatible
```

- `DEGRADED` with `health.issues[]` of type `ConfigurationConflict` /
  `AccessDenied` → the addon's managed manifest conflicts with a field you edited, or
  its service-account role lacks a permission. The issue text names the resource/field.
- stuck `UPDATING` → inspect the update:
  ```bash
  aws eks list-updates --name <cluster> --addon-name <addon>
  aws eks describe-update --name <cluster> --addon-name <addon> --update-id <id>
  ```
- Version skew after a control-plane upgrade: if the addon version predates the new
  Kubernetes version's support window, it can misbehave. Compare against the
  `describe-addon-versions` output above.

Fix is to resolve the conflict (align the field, grant the permission, or update to a
compatible version with the right conflict-resolution choice) — not to delete pods.

---

## EBS / AZ volume node-affinity conflict

```bash
kubectl describe pod <pod> -n <ns> | grep -i 'volume node affinity conflict'
kubectl get pv <pv> -o jsonpath='{.spec.nodeAffinity}{"\n"}'   # which AZ is the PV pinned to?
kubectl get nodes -L topology.kubernetes.io/zone               # which AZs have nodes?
```

An EBS-backed PV lives in exactly one AZ; the pod can only run on a node in that AZ.
If the only nodes are in other AZs (single-AZ nodegroup, or the pod's AZ scaled to 0),
it stays Pending. Fixes: ensure a node exists in the PV's AZ (NodePool/ASG spanning
that AZ), or use a topology-aware StorageClass (`volumeBindingMode: WaitForFirstConsumer`)
for new volumes so the volume is created in a schedulable AZ.

---

## Wrap-up

Close with the `SKILL.md` output template: cluster/region/account, the named
AWS-layer root cause, the single `aws`/`kubectl` line that proves it, a minimal
reversible fix, and the blast radius. Resist proposing the fix until the evidence —
from the AWS API, not just Kubernetes — names the cause.
