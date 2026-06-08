---
name: ram-iam-audit
description: Use when reviewing AWS IAM or Alibaba Cloud RAM for least-privilege — hunting wildcard Action/Resource (`*:*`, `*`), AdministratorAccess / *FullAccess over-grants, long-lived access keys instead of roles, unused or stale credentials, over-broad cross-account trust, inline policies, missing MFA, and privilege-escalation combos (iam:PassRole + compute, policy self-attach). Read-only audit that names each risk with evidence and a concrete tightening, applying no changes.
---

# ram-iam-audit

A read-only least-privilege review of AWS **IAM** and Alibaba Cloud **RAM** that
turns "are our permissions too loose?" into a *ranked list of named risks, each with
the evidence and the exact tightening*. The enemy is the policy that *reads* safe but
*grants* broad — a managed policy named like a read-only role that actually carries a
wildcard, a `PassRole` that quietly enables full privilege escalation. This skill
makes you read what a policy **grants**, not what it's **called**.

## When to use

Reach for this when someone asks to:

- review IAM/RAM for least privilege, or "are our permissions too broad?"
- onboard/offboard a user/role/RAM user and check the grant is minimal
- audit before exposing an account, automating with a key, or a security review
- investigate "who can do X" / blast-radius of a credential leak

Do **not** use it to *create or modify* policies, to manage SSO/identity federation
setup, or to design an org-wide SCP strategy from scratch — this is an audit that
*recommends*. Apply changes yourself after review.

## Operating rules

1. **Read-only.** `get`/`list`/`describe`/simulate and the credential/Access-Analyzer
   reports only. Never `put`/`attach`/`detach`/`create`/`delete` a policy or key as
   part of the audit. Output is findings + proposed tightenings a human applies.
2. **Confirm the scope first.** Which account/org? AWS or Aliyun (or both)? Which
   principals are in scope (all, or a subset)? State `aws sts get-caller-identity` /
   `aliyun sts GetCallerIdentity` before auditing.
3. **Read the grant, not the name.** A policy's *name* is not its *permission*.
   Expand every in-scope policy's JSON and judge the actual `Action`/`Resource`/
   `Effect`/`Condition`. Treat a reassuring name as zero evidence.
4. **Prefer evidence of *use* before recommending removal.** "Looks unused" → confirm
   with last-used data (credential report, access-key last-used, Access Analyzer
   last-accessed) before recommending a credential or grant be revoked. Note false-
   positive risk (break-glass roles, rarely-used automation).
5. **Rank by blast radius.** A wildcard admin on a long-lived key beats a missing tag
   condition. Order findings by what an attacker gains, worst first.

## Audit order

Identity surface first, then what each identity can do, then escalation paths. The
exact AWS and Aliyun commands, the privilege-escalation combos, and the RAM
naming-trap details live in `references/audit-playbook.md` — open it as you work each
step.

```
0. Orient   → account/org, cloud(s), principals in scope; pull the credential report
1. Identity → root usage/MFA; users vs roles; long-lived access keys; key age & MFA
2. Stale    → unused users/roles/keys (last-used), keys never rotated, dormant logins
3. Grants   → wildcard Action/Resource, Admin/*FullAccess attach, inline policies,
              missing Condition scoping (no MFA / no source-IP / no resource bound)
4. Trust    → cross-account/role trust breadth (Principal "*", external account,
              missing ExternalId/Condition), federation/OIDC audience
5. Escalate → privilege-escalation combos (iam:PassRole+run-compute, policy self-
              attach, CreateAccessKey on others, UpdateAssumeRolePolicy, lambda+role)
```

## Risks that are easy to miss

The findings people overlook because the surface reading is reassuring:

- **A policy named "…ReadOnly / …Query" can carry a wildcard.** The classic RAM trap:
  a custom policy presented as read-only whose statement is actually
  `{"Action":"<svc>:*","Resource":"*"}` — full control of that service. Never trust
  the name; expand and read every Action. (Same on AWS with custom managed policies.)

- **`iam:PassRole` is the master key to escalation.** A principal who can `PassRole`
  *and* launch a compute resource (EC2/Lambda/ECS/CloudFormation/Glue) can pass a
  high-privilege role to code it controls and inherit that role's permissions. Audit
  `PassRole` targets: a broad `Resource:"*"` on `PassRole` is effectively "become any
  role." On Aliyun the equivalent is `ram:PassRole` + ECS/FC/etc.

- **Self-service admin: policy-attach on yourself.** `iam:AttachUserPolicy` /
  `PutUserPolicy` / `CreatePolicyVersion` / `AttachRolePolicy` on one's own principal
  = attach AdministratorAccess to self. Likewise `CreateAccessKey` on *another* user,
  or `UpdateAssumeRolePolicy` / `UpdateLoginProfile`, are quiet full-takeover paths.
  These rarely look dangerous in isolation — they're escalation *combos*.

- **Long-lived access keys where a role would do.** A static access key on a user (or
  worse, embedded in CI/an instance) is a permanent, exfiltratable credential. EC2
  workloads should use **instance roles**, CI should use **OIDC role assumption**,
  cross-service should use **assumed roles** — not keys. Flag every long-lived key and
  ask "why isn't this a role?"

- **Unused/stale credentials are standing attack surface.** A user who hasn't logged
  in in 90+ days, an access key never rotated or never used, a role last-assumed
  "never" — each is risk with no benefit. The **credential report** (AWS) and
  last-used fields give the evidence; recommend disable-then-delete, mindful of
  break-glass exceptions.

- **Cross-account trust with `Principal:"*"` or no ExternalId.** A role any account can
  assume, or one trusting an external account without an `ExternalId`/Condition, is an
  open door (confused-deputy). Read every `AssumeRole` trust policy's `Principal` and
  `Condition`. **IAM Access Analyzer** finds resource/role policies that grant access
  outside the account — run it.

- **Inline policies hide from inventory.** Inline (embedded) policies don't show up
  when you list managed-policy attachments, so over-grants in them get missed. List
  inline policies explicitly per user/role/group and read them too.

- **Missing Conditions = unscoped grant.** Even a "reasonable" action set is loose
  without scoping: no `aws:MultiFactorAuthPresent` on sensitive actions, no
  `aws:SourceIp`, no `aws:ResourceTag`/ARN bound on `Resource`. Absence of Condition
  is itself a finding for privileged statements.

- **Root account: any use, or missing MFA, is critical.** Root should have MFA, no
  access keys, and effectively zero day-to-day use. The credential report shows root
  key presence and MFA — flag immediately.

## Output template

Lead with the ranked findings; one tightening each.

```
Scope    : <account/org id> · <AWS | Aliyun | both> · <principals audited>
Source   : <credential report date; Access Analyzer run; policies expanded>

# Findings (worst blast radius first)
| Principal / Policy        | Risk                              | Evidence (the grant/usage)              | Tightening (human applies)             | Severity |
|---------------------------|-----------------------------------|-----------------------------------------|----------------------------------------|----------|
| user/<x>                  | long-lived key + AdministratorAccess | key age 400d; AdministratorAccess attached | rotate→role; scope to needed actions | critical |
| policy/<y> "…ReadOnly"    | name says RO, grants <svc>:* on *  | Statement Action="<svc>:*" Resource="*" | replace with action-scoped read set    | critical |
| role/<z>                  | PassRole Resource:* + ec2:RunInstances | escalation combo                     | bound PassRole to specific role ARNs   | high     |
| user/<w>                  | no MFA, console login              | cred report mfa_active=false            | enforce MFA; deny w/o MFA condition    | high     |
| ...                       | ...                               | ...                                     | ...                                    | ...      |

Stale (revoke after confirming non-break-glass): <users/keys/roles + last-used>

Notes: <Access Analyzer external-access findings; items needing owner sign-off>
```

Always least-privilege-oriented and reversible: recommend the *minimal* grant,
prefer roles over keys, and let a human apply changes after reviewing blast radius.
