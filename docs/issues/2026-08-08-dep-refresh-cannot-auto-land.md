---
Status: active
Owner: CT
Created: 2026-08-08
Last verified: 2026-08-08
Kind: issue
Level: I1
---

# Weekly dep-refresh cannot auto-land: required status checks predate the repo rename

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-08-08
- **Resolution:** Open
- **Severity:** High — blocks every merge to master, automated or human, whether the run is green or not.
- **Affected version:** master branch protection as observed 2026-08-08; `.github/workflows/ci.yml` at commit `972532a` (current HEAD).
- **Read when:** a pull request or the weekly `dep-refresh` run stalls with required checks stuck "Expected"; before editing master branch protection or `.github/workflows/ci.yml`.
- **Search terms:** branch protection, required status checks, pd-ocr-training CI, pdomain-ocr-training CI, dep-refresh, auto-merge stuck, rename drift, admin bypass.
- **Relates to:** `pdomain-ui` `docs/specs/2026-07-16-dep-refresh-auto-land-design.md`

## Summary

Master branch protection requires three status contexts named `pd-ocr-training CI (3.11)`, `pd-ocr-training CI (3.12)`, and `pd-ocr-training CI (3.13)`. Those names predate this repo's rename from `pd-ocr-training` to `pdomain-ocr-training`. The `ci` workflow's job now reports itself as `pdomain-ocr-training CI`, so its matrix legs post checks named `pdomain-ocr-training CI (3.11/3.12/3.13)` — one word longer than what branch protection is waiting for. Nothing produces the old three-context names, so they sit "Expected" forever and no pull request can merge, including the weekly automated `dep-refresh` PR, regardless of whether the actual CI run is green.

## Impact

- No pull request can merge to master through the normal gate — not `dep-refresh`, not any human PR — because three of the required checks never appear under their expected names.
- `dep-refresh` arms `gh pr merge --auto --rebase`, but auto-merge itself can never fire: the same three contexts block it identically.
- Nobody has hit this in practice yet. `dep-refresh` has never run (zero workflow runs recorded), and no PR has merged since the rename landed, so the defect is confirmed by configuration inspection, not by a stuck PR.

## Environment / versions

```text
repo:          pdomain/pdomain-ocr-training, branch master
observed:      2026-08-08
ci.yml:        commit 972532a (HEAD); workflow name "ci"; job name "pdomain-ocr-training CI"
rename commit: e0a6571 "rename: pd-ocr-training → pdomain-ocr-training (Phase 2)", 2026-05-26
```

## Evidence

### 1. Required contexts still use the pre-rename name

```text
$ gh api repos/pdomain/pdomain-ocr-training/branches/master/protection \
    --jq '.required_status_checks.contexts'
["pd-ocr-training CI (3.11)","pd-ocr-training CI (3.12)","pd-ocr-training CI (3.13)"]
```

### 2. `ci.yml` reports the post-rename name — correcting the assignment's premise

`.github/workflows/ci.yml`:

```yaml
name: ci
jobs:
  ci:
    name: pdomain-ocr-training CI
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
```

GitHub names a matrix job's checks from the job's `name:` field plus the matrix leg, not the workflow name or the job id. The checks this workflow actually posts are `pdomain-ocr-training CI (3.11)`, `pdomain-ocr-training CI (3.12)`, and `pdomain-ocr-training CI (3.13)` — **not** `ci (3.11)` style as the assignment's framing guessed. The mismatch is one word ("omain"), not a change in shape.

### 3. The rename changed the job name but not branch protection

```text
$ git log -p --follow -- .github/workflows/ci.yml   # commit e0a6571, 2026-05-26
-    name: pd-ocr-training CI
+    name: pdomain-ocr-training CI
```

No corresponding change touched branch protection. `pd-ocr-training CI` and `pdomain-ocr-training CI` differ only by the missing "omain," which is enough for GitHub to treat them as unrelated contexts.

### 4. The last PR to merge cleanly predates the rename

```text
$ gh api repos/pdomain/pdomain-ocr-training/commits/f2ddbfa.../check-runs \
    --jq '.check_runs[] | {name, conclusion}'
{"name":"pd-ocr-training CI (3.13)","conclusion":"success"}
{"name":"pd-ocr-training CI (3.12)","conclusion":"success"}
{"name":"pd-ocr-training CI (3.11)","conclusion":"success"}
```

PR #13 merged 2026-05-23, three days before the rename (`e0a6571`, 2026-05-26). Its checks still carried the old name and matched the still-old required contexts, so it merged cleanly. No PR has merged since — #13 remains the most recent — so no one has yet been in a position to see a green run stall on this.

### 5. Secondary defect — dated dep-refresh branches — already mitigated here

```yaml
BRANCH="dep-refresh/$(date +%Y-%m-%d)-$GITHUB_RUN_ID"
```

`.github/workflows/dep-refresh.yml` still creates a fresh branch per run. Unlike the peer repos the design spec was written for, this repo already has delete-on-merge enabled and currently has no accumulation:

```text
$ gh api repos/pdomain/pdomain-ocr-training --jq '.delete_branch_on_merge'
true
$ gh api repos/pdomain/pdomain-ocr-training/branches --jq '.[].name'
master
$ gh pr list --repo pdomain/pdomain-ocr-training --state open --json number
[]
$ gh run list --repo pdomain/pdomain-ocr-training --workflow=dep-refresh.yml --limit 10
[]
```

Zero stray `dep-refresh` branches, zero open PRs, and zero `dep-refresh` runs so far.

### 6. GitHub Actions is disabled repository-wide, and this repo is one of five that went dark on the same date

```text
$ gh api repos/pdomain/pdomain-ocr-training/actions/permissions --jq '.enabled'
false
$ gh run list --repo pdomain/pdomain-ocr-training --limit 1 --json createdAt,workflowName
[{"createdAt":"2026-07-12T10:09:09Z","workflowName":"Dependency Graph"}]
```

Actions is disabled for the entire repository, not just for `dep-refresh.yml`. That is why `dep-refresh` has zero recorded runs (evidence 5) and why no workflow of any kind has executed since 2026-07-12. The cron schedule in `dep-refresh.yml` is unchanged and identical to the seven peer repos still running weekly — no workflow file needs editing to restore the schedule; only the Actions setting is blocking it.

Contrast with an enabled peer:

```text
$ gh api repos/pdomain/pdomain-book-tools/actions/permissions --jq '.enabled'
true
$ gh run list --repo pdomain/pdomain-book-tools --workflow=dep-refresh.yml --limit 5 --json createdAt,status,conclusion
[{"conclusion":"success","createdAt":"2026-08-02T05:11:59Z","status":"completed"},
 {"conclusion":"success","createdAt":"2026-07-26T05:16:13Z","status":"completed"},
 {"conclusion":"success","createdAt":"2026-07-19T04:56:46Z","status":"completed"},
 {"conclusion":"success","createdAt":"2026-07-12T05:01:07Z","status":"completed"},
 {"conclusion":"success","createdAt":"2026-07-05T05:50:24Z","status":"completed"}]
```

`pdomain-book-tools` ran `dep-refresh` successfully every week through 2026-08-02, including 2026-07-12 itself — same day this repo's last run of anything occurred, hours earlier, before Actions went off here.

Four other repos share this repo's exact shutdown date, within minutes:

```text
$ for repo in pdomain-ocr-labeler-spa pdomain-ocr-synth pdomain-ocr-trainer-spa pdomain-prep-for-pgdp; do
    gh api repos/pdomain/$repo/actions/permissions --jq '.enabled'
    gh run list --repo pdomain/$repo --limit 1 --json createdAt,workflowName
  done
pdomain-ocr-labeler-spa:  false, last run 2026-07-12T10:08:58Z "Dependency Graph"
pdomain-ocr-synth:        false, last run 2026-07-12T10:09:02Z "Dependency Graph"
pdomain-ocr-trainer-spa:  false, last run 2026-07-12T10:09:06Z "Dependency Graph"
pdomain-prep-for-pgdp:    false, last run 2026-07-12T10:09:14Z "Dependency Graph"
```

Five repos — `pdomain-ocr-labeler-spa`, `pdomain-ocr-synth`, `pdomain-ocr-trainer-spa`, `pdomain-ocr-training` (this repo), and `pdomain-prep-for-pgdp` — all show their last recorded workflow run within the same few minutes on 2026-07-12, and Actions disabled now for all five. The other seven repos in the workspace have kept running weekly through 2026-08-02. One date across five repos, minutes apart, is consistent with a single deliberate action (for example, a workspace-level Actions policy change or a batch repository-settings edit) rather than five unrelated coincidences — but this is an inference from repository-scoped data, not a confirmed cause. Whether the disabling was intentional and temporary, or an unintended side effect of whatever else happened that day, cannot be determined from what this repo's data alone shows. If it was deliberate, the resolution should say so explicitly rather than leaving it to be inferred from silence.

Consequence: this repository has had no CI of any kind for nearly a month (2026-07-12 to 2026-08-08). Anything merged to any branch since 2026-07-12 merged without any check running, regardless of the branch-protection defect described above — for that window, protection could not have been enforced by a check that never ran.

## Root-cause hypotheses

This repo carries two independent confirmed causes. Either alone would block auto-land; together, restoring only one leaves the other still blocking.

1. **(Confirmed) GitHub Actions is disabled for the whole repository, which is why `dep-refresh` has never run at all.** Evidence 6 below. This is the more fundamental of the two: even a correctly-configured `dep-refresh.yml` cannot fire while Actions is off. Restoring Actions alone does not fix defect 2 — a run would then execute but still stall behind the pre-rename required-context names.
2. **(Confirmed) Branch protection was never updated when the rename changed the job's display name.** Commit `e0a6571` (2026-05-26) changed the job's `name:` from `pd-ocr-training CI` to `pdomain-ocr-training CI`. No commit updated `required_status_checks.contexts` to match. Confirmed directly by comparing the API output (evidence 1) against the workflow file (evidence 2) and the rename diff (evidence 3). This is independent of defect 1 — it would block merges even if Actions were enabled and every run were green.
3. **Ruled out: a workflow/job-id naming mismatch (`ci (3.11)` style).** GitHub uses the job's `name:` field for matrix legs, and that field already reads `pdomain-ocr-training CI`, confirmed by evidence 2 and the pre-rename check-run sample in evidence 4.

## Defects to fix

1. **(Primary) Master branch protection requires `pd-ocr-training CI (3.11/3.12/3.13)`, a name the workflow has not produced since the 2026-05-26 rename.** Nothing satisfies these three contexts, so no pull request — `dep-refresh`'s or anyone else's — can merge, green or not.
2. **(Secondary, low urgency) `dep-refresh.yml` still creates a dated branch per run** (`dep-refresh/$(date +%Y-%m-%d)-$GITHUB_RUN_ID`) instead of the reusable single branch the workspace design spec recommends. This is not currently causing accumulation here, because delete-on-merge is already on and no PR has ever stayed open long enough to test it — but it is inconsistent with the rest of the workspace, and would resume accumulating red weeks once `dep-refresh` starts running.

## Next steps

Design authority for the fix shape: `pdomain-ui` `docs/specs/2026-07-16-dep-refresh-auto-land-design.md` (read-only reference; that repo's own defects differ in detail — its Bug 1 is a missing check, this repo's is a misnamed one).

0. Decide whether to re-enable GitHub Actions. This is not a per-repo decision — the same shutdown hit five repos on the same date (evidence 6), so it should be made once, at the workspace level, for all five together, not repo by repo here. If the disabling was deliberate and is meant to stay in place, the resolution should say so explicitly; if it was unintended or was only meant to be temporary, re-enable `repos/{owner}/{repo}/actions/permissions` for the five. Either way, this decision comes first: nothing below fires without it, and the branch-protection fix (step 2) is necessary but not sufficient on its own.
1. Update master's `required_status_checks.contexts` to `pdomain-ocr-training CI (3.11)`, `pdomain-ocr-training CI (3.12)`, `pdomain-ocr-training CI (3.13)` — the names `ci.yml` already produces. This is a repository-settings change, not a code change. It is required regardless of step 0's outcome, and by itself is still not sufficient — with Actions off, no run exists to satisfy even correctly-named contexts.
2. Optionally, once step 1 is live, adopt the spec's reusable single-branch pattern in `dep-refresh.yml` for workspace consistency (design section B). Treat this as cleanup, not urgent: this repo's delete-on-merge is already correct, and it has zero accumulated branches or PRs today.
3. Rollout note from the spec, applied here: a change to required checks cannot satisfy its own new gate. That bootstrap problem is sharpest for pdomain-ui's fix, which adds a new check via a `ci.yml` PR that must itself pass the gate it creates. Step 1 above sidesteps it — correcting branch-protection contexts is an admin/API settings change, not a PR through `ci.yml`, so it does not need to pass its own gate. Step 2, however, is an ordinary `ci.yml`/`dep-refresh.yml` PR: it cannot merge until step 0 and step 1 have already landed, and if attempted first it would need the same admin bypass the spec describes.

## What is NOT broken

- Delete-on-merge is already correct (`delete_branch_on_merge: true`), unlike the peer repos the design spec was written for.
- No stray `dep-refresh` branches or open PRs have accumulated — verified at zero for both.
- `dep-refresh.yml`'s actual dependency-refresh steps (Actions SHA-pin refresh, `make upgrade-deps`, PR creation) are not implicated by this defect; the workflow has simply never run yet.
- The CI matrix and `make ci` invocation in `ci.yml` are unaffected — the defect is entirely in the required-context names, not in what CI runs or checks.

## Resolution

*Open.*
