# Audit playbook — AWS IAM + Aliyun RAM, read-only

Open the section for the cloud and step you're on. Every command is read-only
(`get`/`list`/`describe`/simulate/report). Placeholders: `<account-id>`, `<user>`,
`<role>`, `<policy-arn>`. Never `attach`/`detach`/`put`/`create`/`delete` here.

---

## A. AWS IAM

### A0. Orient + pull the credential report

The credential report is the single best starting artifact: one CSV row per user
with MFA, key age, last-used, password-last-used.

```bash
aws sts get-caller-identity
aws iam generate-credential-report          # then:
aws iam get-credential-report --query Content --output text | base64 -d
```
Columns to scan: `mfa_active`, `access_key_1_active`, `access_key_1_last_used_date`,
`access_key_1_last_rotated`, `password_last_used`, and the `<root_account>` row.

### A1. Identity surface — users, roles, keys

```bash
aws iam list-users   --query 'Users[].[UserName,CreateDate,PasswordLastUsed]' --output table
aws iam list-roles   --query 'Roles[].[RoleName,CreateDate]' --output table
# Access keys per user + last-used:
aws iam list-access-keys --user-name <user>
aws iam get-access-key-last-used --access-key-id <AKIA...>
# MFA devices:
aws iam list-mfa-devices --user-name <user>
aws iam list-virtual-mfa-devices --assignment-status Assigned
```
- **Root:** must have MFA, **no** access keys, near-zero use. The credential report's
  root row shows key presence + MFA — any active root key or `mfa_active=false` is a
  critical finding.

### A2. Stale credentials

- Users with `password_last_used` > 90 days and no recent key use → dormant.
- Keys with `last_used_date` empty (never used) or `last_rotated` > 90 days → flag.
- Roles never assumed:
  ```bash
  aws iam get-role --role-name <role> --query 'Role.RoleLastUsed'
  ```
- **Service last-accessed** (which services a principal actually touched — basis for
  trimming):
  ```bash
  JOB=$(aws iam generate-service-last-accessed-details --arn <principal-arn> --query JobId --output text)
  aws iam get-service-last-accessed-details --job-id "$JOB"
  ```
- Recommend disable→wait→delete; note break-glass/automation false positives.

### A3. Grants — expand and read every policy

```bash
# Managed policies attached to a principal:
aws iam list-attached-user-policies --user-name <user>
aws iam list-attached-role-policies --role-name <role>
aws iam list-attached-group-policies --group-name <group>
# Inline policies — these DON'T show in the above; list them explicitly:
aws iam list-user-policies --user-name <user>
aws iam get-user-policy --user-name <user> --policy-name <name>
aws iam list-role-policies --role-name <role>
aws iam get-role-policy --role-name <role> --policy-name <name>
# Expand a managed policy's actual JSON (default version):
V=$(aws iam get-policy --policy-arn <policy-arn> --query 'Policy.DefaultVersionId' --output text)
aws iam get-policy-version --policy-arn <policy-arn> --version-id "$V" \
  --query 'PolicyVersion.Document'
```
Flag in the JSON:
- `"Action":"*"` or `"<svc>:*"` with `"Resource":"*"` and `"Effect":"Allow"` →
  wildcard grant. AdministratorAccess (`arn:aws:iam::aws:policy/AdministratorAccess`)
  or any `*FullAccess` attached to a user/role used for narrow work → over-grant.
- Privileged statements with **no `Condition`** (no MFA, no SourceIp, no tag/ARN
  bound) → unscoped.
- Replace with action-scoped, resource-bound statements (least privilege).

### A4. Trust policies & external access

```bash
# Who can assume this role?
aws iam get-role --role-name <role> --query 'Role.AssumeRolePolicyDocument'
```
Flag: `Principal:"*"`, an external account id without `sts:ExternalId` /
`Condition`, or an over-broad federated/OIDC `aud`/`sub`.

**IAM Access Analyzer** — finds roles/resources granting access outside the account
(read-only once an analyzer exists):
```bash
aws accessanalyzer list-analyzers
aws accessanalyzer list-findings --analyzer-arn <arn> \
  --query 'findings[?status==`ACTIVE`]'
```

### A5. Privilege-escalation combos

Search expanded policies for these action sets on a single principal (each = a path
to admin even without AdministratorAccess attached):

- `iam:PassRole` (esp. `Resource:"*"`) **+** `ec2:RunInstances` / `lambda:CreateFunction`
  + `lambda:InvokeFunction` / `ecs:RunTask` / `cloudformation:CreateStack` /
  `glue:CreateDevEndpoint` → pass a privileged role to attacker-controlled code.
- `iam:AttachUserPolicy` / `iam:PutUserPolicy` / `iam:AttachRolePolicy` /
  `iam:CreatePolicyVersion` / `iam:SetDefaultPolicyVersion` on self → attach admin.
- `iam:CreateAccessKey` (on another user) / `iam:UpdateLoginProfile` /
  `iam:CreateLoginProfile` → take over another principal.
- `iam:UpdateAssumeRolePolicy` → make a privileged role assumable by self.

Validate suspicion with the **policy simulator** (read-only):
```bash
aws iam simulate-principal-policy --policy-source-arn <principal-arn> \
  --action-names iam:PassRole ec2:RunInstances --resource-arns '*'
```

---

## B. Alibaba Cloud RAM

Mirror of the AWS flow; the wildcard-named-policy trap is especially common here.

### B0. Orient

```bash
aliyun sts GetCallerIdentity
```

### B1. Identity surface — RAM users, roles, keys

```bash
aliyun ram ListUsers
aliyun ram ListRoles
# Access keys per user + status:
aliyun ram ListAccessKeys --UserName <user>
# MFA:
aliyun ram GetUserMFAInfo --UserName <user>
# Account-wide security posture (root/MFA/key summary):
aliyun ram GetAccountSecurityPracticeReport
```
- Flag long-lived AccessKeys on users that should use a **RAM role** (ECS instance
  RAM role, RRSA/OIDC for ACK, RamRoleArn assumption) instead.

### B2. Stale credentials

```bash
aliyun ram GetUser --UserName <user>            # LastLoginDate
aliyun ram ListAccessKeys --UserName <user>     # key status; cross-ref last-used
```
- Dormant logins, inactive/never-rotated keys → recommend disable then delete.

### B3. Grants — read the actual policy document

```bash
# Policies attached to a user/role:
aliyun ram ListPoliciesForUser --UserName <user>
aliyun ram ListPoliciesForRole --RoleName <role>
# Expand a custom policy's real document (THE name-vs-grant check):
aliyun ram GetPolicy --PolicyType Custom --PolicyName <name>
aliyun ram GetPolicyVersion --PolicyType Custom --PolicyName <name> --VersionId <v>
```
Flag:
- **The naming trap:** a custom policy named like read-only whose `Action` is
  `"<svc>:*"` (e.g. `"ecs:*"`, or `"*"`) with `"Resource":"*"`. The name is cosmetic;
  the grant is full control. This is the headline RAM finding — read every Action.
- `AdministratorAccess` system policy or any `*FullAccess` attached to narrow-use
  principals → over-grant. Note RAM system-policy names like `AliyunECSFullAccess`.
- Privileged statements with no `Condition` (no MFA `acs:MFAPresent`, no
  `acs:SourceIp`) → unscoped.

### B4. Trust / cross-account

```bash
aliyun ram GetRole --RoleName <role>            # AssumeRolePolicyDocument
```
Flag a trust document allowing an external account or RAM-user principal that's
broader than needed; prefer scoped `Service`/`RAM` principals with conditions.

### B5. Escalation combos

Same shape as AWS: `ram:PassRole` (broad `Resource`) **+** ability to create/run a
compute resource (ECS `ecs:RunInstances`, Function Compute, ACK) → inherit the passed
role. `ram:AttachPolicyToUser` / `ram:CreatePolicyVersion` /
`ram:SetDefaultPolicyVersion` / `ram:CreateAccessKey` on self/others → takeover.

---

## C. Reporting discipline

- **Quote the grant, not the name.** Every finding cites the offending `Action` /
  `Resource` / missing `Condition` line, or the credential-report field — not "looks
  too broad."
- **Severity = blast radius.** Wildcard admin on a live long-lived key > a no-MFA
  console user > a missing tag condition. Rank worst-first.
- **Confirm before recommending revoke.** Pair every "delete this stale credential"
  with the last-used evidence and a note on break-glass/automation false positives.
- **Tighten, don't just flag.** Each finding ends in a concrete minimal grant
  (action-scoped + resource-bound + condition) or "switch key→role" — reversible,
  applied by a human.
