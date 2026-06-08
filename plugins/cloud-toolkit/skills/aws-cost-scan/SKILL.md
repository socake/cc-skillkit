---
name: aws-cost-scan
description: Use when asked to find AWS waste, cut cloud spend, do a cost review/FinOps pass, explain a bill spike, or hunt idle/orphaned resources (unused load balancers, unattached EIPs, orphan EBS volumes & old snapshots, over-provisioned node pools, NAT/cross-AZ traffic, never-expiring logs, RI/Savings Plans gaps, EKS extended-support fees, stale AMIs). Read-only investigation that produces a prioritized, evidence-backed savings checklist — it never deletes anything.
---

# aws-cost-scan

A read-only sweep that turns "the AWS bill is too high" into a *prioritized,
evidence-backed savings checklist* — each line naming the resource, the monthly
waste, why it's safe (or not) to act, and the exact disposal action for a human to
run. The enemy is the confident-but-wrong cut: a load balancer with "no traffic"
that fronts a once-a-day batch job, a snapshot that's the only copy of a deleted
volume. This skill forces you to prove a resource is idle *and* unreferenced before
recommending its removal.

## When to use

Reach for this when someone asks to:

- find waste / "where is the money going" / cut the AWS bill
- do a cost-optimization or FinOps review of an account or region
- explain a month-over-month cost spike (pair with Cost Explorer grouping)
- audit for idle/orphaned resources after a migration, teardown, or cluster removal

Do **not** use it to *delete* resources, to right-size application code, or to design
a budget/tagging policy from scratch — this is investigation and recommendation.

## Operating rules

1. **Read-only. Always.** `describe`/`list`/`get`, Cost Explorer queries, and CUR
   reads only. Never `delete`, `release`, `deregister`, `terminate`, or `modify` as
   part of the scan. Every finding ends in a *proposed* action the human runs.
2. **Confirm the target first.** Which account (`aws sts get-caller-identity`) and
   which region(s)? Most "idle" hunts must loop every active region — waste hides in
   regions nobody looks at. State account + region set out loud before scanning.
3. **Prove idle AND unreferenced before recommending removal.** "Looks unused" is a
   lead, not a verdict. An EIP with no association, a volume with no attachment, an
   LB with zero healthy targets *and* zero request/flow-log bytes over a real window
   (≥14 days) — confirm both halves. Check for IaC ownership (Terraform/CDK/CFN tags)
   so you don't recommend deleting something that'll just be recreated.
4. **Quantify every finding.** No "this is wasteful" without a dollar/month estimate
   and the price basis. Rank the checklist by monthly savings, biggest first.
5. **Report a checklist, not a dump.** Each row: resource id → monthly waste →
   evidence it's idle → disposal action → confidence/caveat.

## Scan order

Cheapest-to-confirm and highest-yield first. The per-category commands, price bases,
and "is it really idle" checks live in `references/waste-catalog.md` — open it for
the category you're working.

```
0. Orient   → account id, active regions, top services by spend (Cost Explorer)
1. Network  → idle NLB/ALB (no targets / 0 bytes), unattached EIPs, idle NAT GW,
              cross-AZ & inter-region data transfer
2. Storage  → unattached EBS volumes, orphan snapshots (source volume gone),
              gp2→gp3 upgrades, stale/unused AMIs, old multipart uploads in S3
3. Compute  → stopped-but-billing resources, oversized/idle EKS node pools,
              low-utilization instances, idle RDS/ElastiCache
4. Commit   → RI / Savings Plans coverage & utilization gaps (Cost Explorer)
5. Platform → EKS extended-support surcharge, CloudWatch Logs never-expiring,
              NAT vs VPC-endpoint, unused provisioned IOPS/throughput
```

## Waste that's easy to misjudge

The traps that produce a wrong cut or a missed saving:

- **"Stopped" rarely means "free."** A stopped EC2 instance still bills for its EBS
  volumes and any attached EIP; a stopped RDS instance bills storage and *auto-starts
  after 7 days*; provisioned-IOPS volumes bill while detached. The compute meter
  stopping is not the bill stopping — look at what the resource still holds.

- **An idle NAT Gateway is a silent ~$32+/mo floor per AZ, plus per-GB.** One per AZ
  is common; teardown often leaves them. If the subnets they serve have no running
  workloads, that's pure waste. And NAT data-processing charges for traffic that
  could go through a (free-ish) S3/DynamoDB Gateway VPC endpoint or interface
  endpoint is a classic recurring leak — check what's actually flowing through it.

- **Cross-AZ traffic is invisible until you group the CUR by it.** Chatty services
  spread across AZs pay per-GB both directions. It never shows as a line item called
  "waste" — you find it by grouping Cost Explorer / CUR on usage type `*-DataTransfer-Regional-Bytes`.

- **A snapshot can be the *only* copy left.** Before flagging an old snapshot for
  deletion, check whether its source volume still exists and whether an AMI
  references it. An orphan snapshot of a deleted volume is a judgment call, not an
  auto-delete — surface it, don't recommend blind removal.

- **Memory/over-provisioned node pools look "healthy" while burning money.** A node
  pool sized for a long-gone peak, or one a memory-Utilization autoscaler pinned high
  (steady-baseline workloads read as "needs more nodes"), runs many near-idle nodes.
  Check requests-vs-allocatable and actual utilization, not just "nodes are Ready."

- **Never-expiring CloudWatch Logs compound forever.** Log groups default to infinite
  retention; ingestion is the big cost but stored GB-months accrete silently. A group
  with no retention policy and steady ingest is a guaranteed slow leak — setting
  retention is reversible and safe.

- **EKS extended support is a per-cluster surcharge that turns on automatically.** A
  cluster left on an EOL'd Kubernetes minor moves into extended support and the
  hourly control-plane price jumps (often several-fold). Multiplied across clusters
  this is real money for *zero* feature gain — list cluster versions and flag any in
  (or near) extended support; the fix is upgrading, not deleting.

- **RI/SP "savings" can be negative.** Unused reservation/commitment hours are waste
  you already paid for. Check *utilization* (are you using what you committed?) and
  *coverage* (is on-demand spend that could be covered going uncovered?) — both gaps
  cost money, in opposite directions.

## Output template

Lead with the ranked checklist; total it.

```
Account/Region : <account-id> / <regions scanned>
Window         : <lookback used for "idle", e.g. last 14–30 days>

# Findings (highest monthly saving first)
| Resource                | Category | Est. $/mo | Evidence (idle + unreferenced)        | Action (human runs)            | Confidence |
|-------------------------|----------|-----------|---------------------------------------|--------------------------------|------------|
| nat-<id> (<az>)         | network  | $XX       | 0 running ENIs in subnets; <X> GB/mo  | delete NAT GW; add S3 VPC endpt| high       |
| eipalloc-<id>           | network  | $X        | no association; not in any TF state   | release EIP                    | high       |
| vol-<id>                | storage  | $X        | available 30d; no AMI references it   | snapshot then delete           | medium     |
| ...                     | ...      | ...       | ...                                   | ...                            | ...        |

Estimated total: $<sum>/mo  (~$<*12>/yr)

Notes: <anything needing owner confirmation before action; IaC-managed items>
```

Always: confirm-before-delete. The skill investigates and recommends; a human
executes destructive actions after verifying the resource is truly unused.
