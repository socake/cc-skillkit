---
name: pr-describe
description: Use when opening a pull request or writing/rewriting its description — turn a branch's git diff and commit log into a clear, reviewer-friendly PR writeup with what/why/how, breaking changes, risk, testing, rollback, and where reviewers should focus. Honest about gaps; no filler.
---

# pr-describe

Turn a branch of changes into a PR description a reviewer can actually act on.
The job is not to restate the diff — the reviewer can read the diff. The job is to
supply the **context the diff can't carry**: why this change exists, what could go
wrong, how it was verified, and where to look first. A good description is the
single highest-leverage thing you can do to get a fast, correct review.

## When to use

- Opening a PR / MR and you need a description
- An existing PR has a thin or stale description ("update stuff", "fix bug") and you
  want to rewrite it from the actual changes
- A reviewer asked "what is this even doing / why?"

**When *not* to use:** a one-line trivial change where the title says it all (typo,
version bump) — a heavy template there is noise. And don't use this to *generate* a
diff or write code; it describes work that already exists.

## Gather the evidence first

Read the actual change before writing a word. Don't narrate from memory.

```bash
git fetch origin                                  # know the real merge base
git merge-base HEAD origin/<base>                 # usually main / master
git diff --stat <base>...HEAD                     # scope: files, +/- size
git log --oneline --no-merges <base>..HEAD        # the story the commits tell
git diff <base>...HEAD                            # the substance — read it
```

Three-dot (`<base>...HEAD`) shows what *this branch* introduces relative to the
base, excluding changes that landed on the base meanwhile — that's what the
reviewer is being asked to approve. From this, answer for yourself:

- **What** changed, grouped by intent (not file by file)?
- **Why** — what problem/ticket/regression prompted it? The diff never says why.
- **How** — the approach, and any non-obvious decision or tradeoff.
- **What's risky** — data migrations, API/contract changes, auth, concurrency,
  anything irreversible or with wide blast radius.
- **How it was verified** — and, honestly, what *wasn't* covered.

## Writing rules

1. **Lead with the summary.** One or two sentences a busy reviewer reads first:
   what this does and why. Everything else is support.
2. **Group changes by intent, not by file.** "Adds retry with backoff to the client"
   beats "edited client.go, config.go, client_test.go". Reviewers think in
   behaviors.
3. **Be honest about gaps.** State what you did *not* test, known limitations,
   follow-ups deferred. A description that hides the soft spots wastes the
   reviewer's trust and time. Omitting risk doesn't remove it.
4. **No filler.** Delete "various improvements", "minor refactors", "as discussed".
   If a section is empty (no breaking changes, no migration), write "None" — don't
   pad it.
5. **Make review navigable.** Point to the file/function that's the heart of the
   change and say what to scrutinize. Call out generated/mechanical changes so the
   reviewer can skip them.
6. **Surface breaking changes loudly**, near the top — API shape, config keys,
   DB schema, wire format, default behavior. Say who must change what to adopt.

A side-by-side of weak vs strong descriptions, and how to phrase risk/rollback
honestly, is in `references/good-vs-bad.md`.

## Output template

Fill only the sections that apply; write "None" for the ones that don't rather than
deleting them, so reviewers see they were considered.

```markdown
## Summary
<1–2 sentences: what this changes and why. The reviewer's TL;DR.>

## Motivation
<The problem / ticket / regression this addresses. Why now. Link context.>

## Changes
<Grouped by intent, not by file:>
- <behavior 1 — what's now different>
- <behavior 2>
- <breaking change, if any — flag it explicitly>

## Testing
<How it was verified: tests added/updated, manual steps, environments.>
<Honest gaps: what is NOT covered and why.>

## Risk & rollback
<Blast radius; irreversible steps (migrations, data backfills, config).>
<How to roll back if it goes wrong — revert? flag off? migration down?>

## Reviewer notes
<Where to focus first; the load-bearing file/function. What to skip
(generated/mechanical). Open questions you want a second opinion on.>
```

Keep it as long as the change demands and no longer. A 3-line fix gets a 3-line
description; a schema migration earns every section.
