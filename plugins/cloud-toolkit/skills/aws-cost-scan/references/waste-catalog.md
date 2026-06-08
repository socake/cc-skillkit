# Waste catalog — per-category read-only checks

Open the section for the category you're scanning. Every command is read-only.
Placeholders: `<region>`, `<account-id>`, `<cluster>`, `<id>`. Loop `<region>` over
every active region (`aws ec2 describe-regions --query 'Regions[].RegionName' --output text`)
unless told otherwise. Price figures are *order-of-magnitude* US defaults — confirm
against the AWS pricing page / your CUR for the actual region and rate.

A useful orientation first:

```bash
aws sts get-caller-identity                       # which account am I in?
# Top services by unblended cost, last full month (Cost Explorer):
aws ce get-cost-and-usage \
  --time-period Start=<YYYY-MM-01>,End=<YYYY-MM-01> \
  --granularity MONTHLY --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[0].Groups|sort_by(@,&Metrics.UnblendedCost.Amount)[-10:]'
```

Cost Explorer must be enabled on the account; CUR (Cost & Usage Report) gives the
finest grain (per-resource, per-usage-type) once delivered to S3 and queried via
Athena. Use CE for fast grouping, CUR/Athena for resource-level and data-transfer
attribution.

---

## 1. Network

### Idle load balancers (NLB/ALB/CLB)

An LB bills an hourly + LCU/capacity charge whether or not it serves traffic.

```bash
# ALB/NLB inventory
aws elbv2 describe-load-balancers --region <region> \
  --query 'LoadBalancers[].[LoadBalancerArn,LoadBalancerName,Type,State.Code]' --output table
# For each LB, do its target groups have healthy targets?
aws elbv2 describe-target-groups --region <region> --load-balancer-arn <lb-arn> \
  --query 'TargetGroups[].TargetGroupArn' --output text
aws elbv2 describe-target-health --region <region> --target-group-arn <tg-arn> \
  --query 'TargetHealthDescriptions[].TargetHealth.State'
# Classic LBs:
aws elb describe-load-balancers --region <region> \
  --query 'LoadBalancerDescriptions[].[LoadBalancerName,Instances]'
```

**Confirm idle, both halves:**
1. No healthy targets / no instances registered, AND
2. ~0 traffic over a real window — CloudWatch metrics:
   ```bash
   # NLB: ActiveFlowCount / ProcessedBytes ; ALB: RequestCount
   aws cloudwatch get-metric-statistics --region <region> \
     --namespace AWS/ApplicationELB --metric-name RequestCount \
     --dimensions Name=LoadBalancer,Value=<lb-suffix> \
     --start-time <iso-14d-ago> --end-time <iso-now> \
     --period 86400 --statistics Sum
   ```
- Price basis: ~$16–22/mo hourly base per ALB/NLB + LCU. Disposal: delete LB + its
  empty target groups. **Caveat:** confirm no infrequent/batch backend and no
  Route53/DNS still pointing at it.

### Unattached Elastic IPs

An EIP not associated with a running instance/ENI bills hourly (~$3.6/mo each).

```bash
aws ec2 describe-addresses --region <region> \
  --query 'Addresses[?AssociationId==`null`].[PublicIp,AllocationId,Domain]' --output table
```
- Confirm: `AssociationId` is null AND not referenced in IaC. Disposal: release EIP.
  **Caveat:** a deliberately-held static IP for an allow-list — confirm with owner.

### Idle NAT Gateways

~$0.045/hr (~$32/mo) per gateway *plus* per-GB data processing, per AZ.

```bash
aws ec2 describe-nat-gateways --region <region> \
  --filter Name=state,Values=available \
  --query 'NatGateways[].[NatGatewayId,SubnetId,VpcId]' --output table
# Is anything actually behind it? Check route tables that point 0.0.0.0/0 at the NAT,
# then whether those private subnets hold running ENIs:
aws ec2 describe-route-tables --region <region> \
  --filter Name=route.nat-gateway-id,Values=<nat-id> \
  --query 'RouteTables[].Associations[].SubnetId' --output text
aws ec2 describe-network-interfaces --region <region> \
  --filters Name=subnet-id,Values=<subnet-id> \
  --query 'length(NetworkInterfaces)'
# Bytes processed (is it even used?):
aws cloudwatch get-metric-statistics --region <region> \
  --namespace AWS/NATGateway --metric-name BytesOutToDestination \
  --dimensions Name=NatGatewayId,Value=<nat-id> \
  --start-time <iso-14d-ago> --end-time <iso-now> --period 86400 --statistics Sum
```
- Disposal: delete unused NAT GW. Optimization even when used: route S3/DynamoDB via
  a **Gateway VPC endpoint** (no hourly, no data charge) and high-volume AWS APIs via
  interface endpoints to cut NAT data-processing.

### Cross-AZ & inter-region data transfer

Not a deletable resource — a usage pattern. Surface it by grouping the CUR/CE on
usage type:

```bash
aws ce get-cost-and-usage --time-period Start=<m>,End=<m> --granularity MONTHLY \
  --metrics UnblendedCost --group-by Type=DIMENSION,Key=USAGE_TYPE \
  --filter '{"Dimensions":{"Key":"USAGE_TYPE_GROUP","Values":["EC2: Data Transfer - Inter AZ"]}}'
```
- Look for `*-DataTransfer-Regional-Bytes` (cross-AZ, ~$0.01–0.02/GB each way) and
  `*-DataTransfer-Out-Bytes`. Fix is architectural (AZ affinity, endpoints), flagged
  for the team — not a delete.

---

## 2. Storage

### Unattached EBS volumes

A detached `available` volume bills full GB-month (gp3 ~$0.08/GB-mo; io2 far more).

```bash
aws ec2 describe-volumes --region <region> \
  --filters Name=status,Values=available \
  --query 'Volumes[].[VolumeId,Size,VolumeType,CreateTime]' --output table
```
- Confirm: status `available` (not in-use) and not referenced by any AMI. Disposal:
  snapshot (cheap insurance) then delete. **Caveat:** detached deliberately for a
  pending reattach — check age and tags.

### Orphan snapshots

Old snapshots whose source volume no longer exists.

```bash
aws ec2 describe-snapshots --region <region> --owner-ids <account-id> \
  --query 'Snapshots[].[SnapshotId,VolumeId,StartTime,VolumeSize]' --output table
# Does the source volume still exist? Is the snapshot used by an AMI?
aws ec2 describe-images --region <region> --owners <account-id> \
  --query 'Images[].BlockDeviceMappings[].Ebs.SnapshotId' --output text | tr '\t' '\n' | sort -u
```
- ~$0.05/GB-mo (incremental). **Judgment call:** an orphan snapshot may be the only
  remaining copy of deleted data, or an AMI's backing store. Surface with context;
  recommend a retention policy / lifecycle rule rather than blind deletion. Don't flag
  snapshots that back an in-use AMI.

### gp2 → gp3 migration

gp3 is ~20% cheaper than gp2 at the same size with better baseline performance.

```bash
aws ec2 describe-volumes --region <region> \
  --filters Name=volume-type,Values=gp2 \
  --query 'Volumes[].[VolumeId,Size]' --output table
```
- Action: modify gp2→gp3 (online, reversible). Estimate: ~20% of those volumes' spend.

### Stale / unused AMIs (and their snapshots)

Old self-owned AMIs nobody launches still hold snapshot storage.

```bash
aws ec2 describe-images --region <region> --owners self \
  --query 'Images[].[ImageId,Name,CreationDate]' --output table
# Cross-check against AMIs actually in use by running instances / launch templates / ASGs.
```
- Action: deregister unused AMI + delete its snapshots (after confirming no launch
  template / ASG / Auto Scaling references it).

### S3 hygiene

```bash
# Incomplete multipart uploads silently accrue storage:
aws s3api list-multipart-uploads --bucket <bucket> --query 'length(Uploads)'
```
- Recommend lifecycle rules: abort incomplete multipart uploads after N days,
  transition cold data to IA/Glacier, expire old versions. All reversible config.

---

## 3. Compute

### Stopped-but-billing

```bash
aws ec2 describe-instances --region <region> \
  --filters Name=instance-state-name,Values=stopped \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,LaunchTime]' --output table
```
- A stopped instance still bills its **EBS volumes** and any **EIP**. Stopped **RDS**
  bills storage and auto-starts after 7 days. Flag the *attached* storage cost, not
  the (zero) compute. Action: terminate if truly abandoned; otherwise snapshot+delete
  the volumes.

### Oversized / idle EKS node pools

```bash
aws eks list-nodegroups --cluster-name <cluster> --region <region>
aws eks describe-nodegroup --cluster-name <cluster> --nodegroup-name <ng> --region <region> \
  --query 'nodegroup.scalingConfig'
# Actual utilization (needs kubectl/metrics-server or CloudWatch Container Insights):
kubectl top nodes
```
- A pool sized for a vanished peak, or pinned high by a **memory-Utilization
  autoscaler** on steady-baseline workloads, runs many near-idle nodes. Compare
  requests-vs-allocatable and real CPU/mem use. Action: lower min/desired, right-size
  instance family, or switch to a consolidating autoscaler — flagged for the team.

### Low-utilization instances / RDS / ElastiCache

```bash
# CPU over 14 days; <~5% avg with low max ⇒ right-size candidate:
aws cloudwatch get-metric-statistics --region <region> \
  --namespace AWS/EC2 --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=<id> \
  --start-time <iso-14d-ago> --end-time <iso-now> --period 86400 --statistics Average Maximum
```
- AWS Compute Optimizer (read-only) aggregates this:
  ```bash
  aws compute-optimizer get-ec2-instance-recommendations --region <region>
  aws compute-optimizer get-ebs-volume-recommendations --region <region>
  ```
- Action: right-size down a family/size, or schedule off-hours stop for non-prod.

---

## 4. Commitments (RI / Savings Plans)

Both *under*-coverage (paying on-demand for steady usage) and *under*-utilization
(paying for committed hours you don't use) are waste.

```bash
# Are existing commitments being used?
aws ce get-savings-plans-utilization --time-period Start=<m>,End=<m> --granularity MONTHLY
aws ce get-reservation-utilization   --time-period Start=<m>,End=<m> --granularity MONTHLY
# Where is on-demand spend that *could* be covered?
aws ce get-savings-plans-coverage    --time-period Start=<m>,End=<m> --granularity MONTHLY
aws ce get-reservation-coverage      --time-period Start=<m>,End=<m> --granularity MONTHLY
# AWS's own purchase recommendations (read-only):
aws ce get-savings-plans-purchase-recommendation \
  --savings-plans-type COMPUTE_SP --term-in-years ONE_YEAR --payment-option NO_UPFRONT
```
- Low utilization ⇒ commitment too big / workload changed (waste already paid). Low
  coverage on stable usage ⇒ buy a Compute Savings Plan to cut ~ up to 60% vs
  on-demand. Recommend, with the numbers; purchasing is a human decision.

---

## 5. Platform-level leaks

### EKS extended-support surcharge

A cluster on an EOL'd Kubernetes minor moves to extended support; control-plane price
jumps (commonly from ~$0.10/hr to ~$0.60/hr — several-fold) for no feature gain.

```bash
aws eks list-clusters --region <region> --query 'clusters' --output text
aws eks describe-cluster --name <cluster> --region <region> \
  --query 'cluster.{version:version,status:status}'
```
- Flag any cluster in (or within a release of) extended support. Fix is to **upgrade**
  the minor version, not delete — but quantify the surcharge × cluster-count × hours.

### CloudWatch Logs never-expiring

```bash
aws logs describe-log-groups --region <region> \
  --query 'logGroups[?!retentionInDays].[logGroupName,storedBytes]' --output table
```
- Groups with no `retentionInDays` keep data forever. Action: set retention (e.g. 30/
  90 days) — reversible, immediately caps stored-GB growth. Also flag high-ingest
  groups; ingestion (~$0.50/GB) usually dwarfs storage.

### Provisioned IOPS / throughput you don't use

io2/gp3 provisioned IOPS and throughput bill whether consumed or not. Cross-check
provisioned values against actual `VolumeReadOps`/`VolumeWriteOps` and bytes; surface
over-provisioned volumes for right-down.

### VPC endpoints vs NAT

Already covered under NAT — interface/gateway endpoints often pay for themselves by
removing NAT data-processing for AWS-API and S3/DynamoDB traffic.

---

## Estimating savings honestly

- Use the **observed** size/hours × the **region's** rate, not list US-East-1.
- For "idle" claims, state the **lookback window** you used (≥14 days for traffic; 30
  for utilization) — a 1-day window catches weekly batch jobs as "idle" wrongly.
- Separate **certain** savings (release unattached EIP) from **conditional** ones
  (right-size, needs owner sign-off). Rank by $/mo; total at the bottom.
