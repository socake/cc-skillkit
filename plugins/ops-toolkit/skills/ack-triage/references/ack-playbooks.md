# ACK playbooks

Open the section matching the symptom. Every command is read-only. Placeholders:
`<cluster-id>` ACK cluster id, `<region>` (e.g. a mainland or overseas region id),
`<ns>` namespace, `<pod>`, `<svc>`, `<slb-id>` load balancer id, `<vsw>` vSwitch id.
The `aliyun` CLI defaults to a configured region — pass `--region <region>` to be sure
(omitted below for brevity). `cs` = Container Service, `slb`/`nlb` = load balancer,
`vpc` = networking, `ecs` = compute.

First, orient — region/account/context mismatch is a real cause here:

```bash
aliyun cs DescribeClusterDetail --ClusterId <cluster-id> \
  --query '{name:name,region:region_id,state:state,version:current_version}'
kubectl config current-context
kubectl get nodes -o wide        # note virtual-kubelet / virtual-node entries (ECI)
```

---

## ECI / Serverless pod stuck ContainerCreating on image pull

The headline ACK trap. Confirm it's an image pull and whether the pod is on ECI:

```bash
kubectl describe pod <pod> -n <ns> | sed -n '/Events:/,$p'
#   look for: Pulling / Failed to pull image / context deadline exceeded / i/o timeout
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.nodeName}{"\n"}'
#   a virtual-node-* / virtual-kubelet node name = ECI, no local image cache
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[*].image}{"\n"}'
```

Decision:

- **Image registry is out-of-region (foreign public registry) on a mainland cluster**
  → cross-border pull, times out. This is the common case. Fixes (propose):
  - Rewrite the image reference to an **in-region ACR** (push/mirror the image into a
    Container Registry instance in `<region>`, reference that).
  - Or configure a **registry mirror** so the public registry resolves to a regional
    accelerator endpoint.
  - For ECI specifically, an **image cache** (ImageCache CRD / pre-pulled snapshot) in
    the region eliminates the pull-on-cold-start entirely.
  Verify the registry's reachability/zone rather than retrying blindly.
- **Pull works on existing nodes but fails on ECI / new nodes** → the working node has
  the image **cached locally**; ECI and fresh ECS have no cache and hit the real
  (slow/blocked) pull. Don't trust a running pod as proof the image is reachable —
  reproduce on a Serverless/fresh target.
- **Private registry `unauthorized` / `pull access denied`** → missing/expired
  imagePullSecret (or the ECI's instance RAM role lacks ACR pull). Check:
  ```bash
  kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.imagePullSecrets}{"\n"}'
  ```
- **Pull is progressing but slow** → likely ECI cold-start + a large image, not a
  failure. See the cold-start section.

---

## ECI cold-start latency (slow, not stuck)

Bursty Serverless pods provision an ECI instance on demand: instance create + image
pull happen before Ready, so the first pods of a burst can take minutes.

```bash
kubectl get pod -n <ns> -o wide --sort-by=.metadata.creationTimestamp
kubectl describe pod <pod> -n <ns> | sed -n '/Events:/,$p'   # watch Pulling progress
```

- If events show steady pull progress / "Started container" eventually → cold-start
  latency, expected. To reduce it (propose): regional **image cache** so the pull is
  near-instant, smaller images, or keep a warm replica so bursts don't all cold-start.
- If the pull never progresses → it's the stuck-pull case above, not cold-start.

---

## Node pool not scaling

Pending pods on a real (non-ECI) node pool, no new ECS appearing:

```bash
kubectl get pod <pod> -n <ns> -o wide        # Pending, no node
kubectl describe pod <pod> -n <ns> | sed -n '/Events:/,$p'   # FailedScheduling reasons
kubectl -n kube-system logs deploy/cluster-autoscaler --tail=120 \
  | grep -i -E 'scale|node ?group|max|failed'
aliyun cs DescribeClusterNodePools --ClusterId <cluster-id> \
  --query 'nodepools[].{name:nodepool_info.name,size:status.total_nodes,scaling:scaling_group}'
```

- `FailedScheduling` from nodeSelector / taints / affinity → constraint mismatch, will
  never schedule regardless of capacity (cross-check the pod's `nodeSelector` /
  `tolerations`). Not a scaling problem → see `k8s-triage`.
- autoscaler not firing → node pool autoscaling disabled, scaling group at **max size**,
  or the chosen ECS instance type is out of stock in the zone. The node-pool detail and
  autoscaler logs name which.
- ECS provisioned but pods still Pending → the node joined but Terway can't give IPs
  (next section) or a taint blocks scheduling.

---

## Terway CNI — ENI / IP allocation

Terway assigns pods ENIs/IPs from the pod vSwitch. Exhaustion or ENI quota stalls pods:

```bash
kubectl describe pod <pod> -n <ns> | grep -i -E 'eni|ip|terway|alloc'
kubectl -n kube-system get ds -l app=terway-eniip -o wide
kubectl -n kube-system logs ds/terway-eniip -c terway --tail=80 | grep -i -E 'eni|ip|error'
aliyun vpc DescribeVSwitchAttributes --VSwitchId <vsw> \
  --query '{az:ZoneId,cidr:CidrBlock,free:AvailableIpAddressCount}'
```

- `free` near 0 on the pod vSwitch → **IP exhaustion**. Fix: add a larger pod vSwitch /
  more vSwitches to the node pool, not retry.
- `failed to alloc eni` with IPs available → likely the **ENI-per-instance quota** for
  that ECS type is hit (small instances allow few ENIs/IPs). Check the instance type's
  ENI limit; use a larger type or Terway IP-sharing (Trunk ENI) mode.

---

## Service type LoadBalancer — CCM / SLB has no/unhealthy targets

ACK's Cloud Controller Manager turns a `type: LoadBalancer` Service into an SLB/NLB.
When traffic doesn't flow, the failure is usually in that reconciliation, logged on the
Service's events:

```bash
kubectl get svc <svc> -n <ns> -o wide          # EXTERNAL-IP present?
kubectl describe svc <svc> -n <ns> | sed -n '/Events:/,$p'   # CCM errors land here
kubectl get svc <svc> -n <ns> -o jsonpath='{.metadata.annotations}{"\n"}'  # CCM annotations
kubectl get endpoints <svc> -n <ns>            # do Pods even back the Service?
```

Then inspect the SLB itself:

```bash
aliyun slb DescribeLoadBalancerAttribute --LoadBalancerId <slb-id> \
  --query '{status:LoadBalancerStatus,addr:Address,listeners:ListenerPortsAndProtocol}'
aliyun slb DescribeHealthStatus --LoadBalancerId <slb-id>   # backend server health
```

- **EXTERNAL-IP `<pending>`** → CCM can't create the SLB. Events name it: vSwitch in the
  wrong zone, RAM role lacks SLB permissions, or an invalid annotation. Fix the
  annotation/RAM, not the app.
- **EXTERNAL-IP present, endpoints empty** → no ready Pods back the Service (readiness
  failing) → that's `k8s-triage`, not CCM.
- **Endpoints present, SLB backends unhealthy** → health-check misconfig (wrong port/
  path/protocol annotation) or the backend ECS not added. `DescribeHealthStatus` shows
  which backends are down; align the health-check annotation.
- **Reused / manually-edited SLB** → if the SLB is shared or was hand-edited, CCM may
  refuse to manage it or fight your changes. Check for the
  `service.beta.kubernetes.io/alibaba-cloud-loadbalancer-id` (existing-SLB) annotation
  and whether `override-listeners` is set.

---

## Cross-region / RAM permission

A managed component (CCM, autoscaler, Terway, CSI) failing with empty results or
timeouts can be a region mismatch or a RAM authorization gap on the cluster's worker /
component RAM role:

```bash
aliyun cs DescribeClusterDetail --ClusterId <cluster-id> --query 'region_id'
# confirm every dependency (registry, SLB, VPC, RAM) is reached in THIS region
kubectl -n kube-system logs deploy/cloud-controller-manager --tail=80 | grep -i -E 'forbidden|denied|region'
```

- `Forbidden` / `NoPermission` in a component's logs → the worker RAM role / RRSA role
  lacks the action. Identify the missing action from the error and propose adding it to
  the role policy (don't apply).
- Empty/timeout to an endpoint that should exist → wrong region on the call or the
  resource genuinely lives in another region (cross-region is slow/blocked). Re-issue
  the query against the cluster's actual region.

---

## Wrap-up

Close with the `SKILL.md` output template: cluster/region/account, the named
Alibaba-Cloud-layer root cause, the single `aliyun`/`kubectl` line that proves it, a
minimal reversible fix, and the blast radius. For any image/registry/endpoint symptom
on a mainland-region cluster, rule out the cross-border boundary *first* — and never
let a long-running, locally-cached pod convince you the image is reachable.
