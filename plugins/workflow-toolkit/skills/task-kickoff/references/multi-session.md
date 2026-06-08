# task-kickoff — context switching & parallel sessions

Read when: the user asks how to handle a topic switch, whether to `/clear` vs
`/compact`, or how to run several sessions in parallel without crossing wires. Don't
load this in a normal kickoff — it wastes context.

---

## Part 1 — four context-switch strategies

Not a binary (keep going vs `/clear`). Pick one of four.

| Strategy | When | Cost | Benefit |
|---|---|---|---|
| **A. Continue** (same session) | strongly related topic, output reused immediately | context grows | continuity, cross-topic reuse |
| **B. Compact** (`/compact <instruction>`) | weakly related, some overlap | loses detail | keeps a summary, frees tokens |
| **C. Restart** (`/clear`) | unrelated / stuck in the same error loop / context polluted | loses everything | clean slate |
| **D. Split** (sub-agent / parallel session) | parallel work needing cross-reference | coordination overhead | main session keeps focus |

### Decision table

| Signal | Pick |
|---|---|
| strongly related + output reused | A |
| weakly related + want a summary kept | B |
| unrelated / same error ≥2 tries / polluted context | C |
| multiple topics need cross-reference / sub-task is independent | D (use a sub-agent) |

### Explicit redirect (pairs with A)

To keep the same session but switch topics, push the prior topic down to "background":

```
Topic switch: now doing <new-topic>, per task-kickoff.
The earlier <old-topic> is persisted (<file path>); no need to expand it.
From here, only <new-topic>.
```

### `/compact` instruction (B)

```
/compact keep: <specifics — file paths / key decisions / current task>
         drop: <specifics — raw research text / intermediate detail>
```

Don't run a bare `/compact` — with no instruction it drops things arbitrarily.

---

## Part 2 — isolating parallel sessions

Running several sessions at once (different topics / explore vs execute) is common.
They must not pollute each other.

### Shared-resource conflict points

| Resource | Risk | Isolation |
|---|---|---|
| A single "current session" pointer/lock | two sessions starting at once collide or overwrite | use a **per-session** lock (key by session id), not a singleton; the later starter checks for an existing lock first |
| Append-only journals | concurrent appends usually fine (atomic line writes), but can interleave | don't hand-write them; let the hook/tool append |
| Plan / report files | two sessions editing one file overwrite each other | name files by topic + date; one plan = one session |
| Git branches | two sessions on one branch → force-push clobber | one branch per session; use worktrees |
| Long-term notes / index | concurrent writes overwrite | one writer at a time; be especially careful with a shared index file |
| Status line / global UI state | global, overwritten by any session | each session sets its own on open, resets on switch back |
| CLI context / credentials (e.g. kube-context) | file-level shared, leaks between sessions | pass context explicitly per command; don't rely on a global "use-context" |
| A shared cache that a sync command writes | read-many, write-one | run the sync in only one session at a time |

### Keep the main session unpolluted

- **Prefer sub-agents over new chat windows** for sub-tasks: a sub-agent has its own
  context window and returns only a small summary, so the main session stays focused.
- **Sub-agents read / don't write** shared resources; concentrate writes in the main
  session.
- **Exchange cross-session state through files** (plan / report / notes), never
  through implicit memory or env vars.

### Red lines — never have two sessions simultaneously

- mutate the same infra resource,
- run the same pipeline,
- edit the same config entry,
- push to the same branch.

If unavoidable, coordinate explicitly ("A operates X now, B pauses") or serialize.

---

## Part 3 — sub-agent vs sub-session vs worktree

| Form | When | Isolation | Mechanism |
|---|---|---|---|
| **Sub-agent** | info gathering, independent sub-task, parallel queries | full context isolation | the agent/task tool |
| **Sub-session** (user opens a new window) | long independent work, writer/reviewer split | context + UI isolated | user opens it |
| **Worktree** | same repo, multiple branches in parallel | filesystem isolation | `git worktree add` + an isolated agent |

The main session **prefers sub-agents**: cheap, simple to coordinate, no user interruption.

---

## Part 4 — topic recognition (the easy place to trip)

A session's topic is implicit — nobody announces it. On each user message, judge:
continuation of the current topic, a switch to a new one, or just a passing mention.

| Message shape | Likely meaning | Action |
|---|---|---|
| "continue / keep going / yep" | current topic continues | proceed on the last plan |
| "also, how's X doing?" | a passing aside, **no switch** | answer briefly, return to topic |
| "now do X" / "switch to X" / "next: X" | explicit switch | use the Part 1 explicit-redirect |
| "**start X, then do Y**" compound | **most ambiguous**: could be two steps of the current task, or a different line pasted in | **ask to confirm**: "continue the current topic, or switch to the X–Y line?" |
| "that X project from before" | cross-session reference | read the relevant notes/docs first, then answer |
| an unrelated link/screenshot mid-task | could be a share, could be new work | ask intent, don't assume |

### The trap, concretely
Mid-task, the user says "start the archive session, then begin phase 0 of <other
thing>." Grabbing it as a real task and asking "which cluster?" is the mistake — the
other thing is a *different line*. Recognize it and ask:

```
The X you mentioned — I read it as possibly:
(a) the next step of the current topic (<summary of current work>)
(b) a different line that needs a topic switch (see Part 1)
(c) just flagged / hypothetical, not now

Which is it?
```

---

## Part 5 — anti-patterns

| Anti-pattern | Consequence | Action |
|---|---|---|
| Two sessions start an ops-session without checking the lock | the pointer is overwritten, archives tangle | check the lock before starting |
| Main + sub session edit the same plan.md | last write wins | one writer per file; different files per session |
| Cross-session "I remember A said X" | contexts don't share; guaranteed wrong | persist to a file, then reference it |
| Main session redoes a sub-agent's work | wasted tokens + polluted context | use the sub-agent's summary directly |
| Many topics stacked in one session, never redirected | attention rot, noise over signal | use the Part 1 explicit-redirect on switch |
