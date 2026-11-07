---
Status: active
Owner: CT
Created: 2026-08-08
Last verified: 2026-11-06
Kind: issue
Level: I1
---

# Weekly dep-refresh cannot auto-land: required status checks predate the repo rename

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-11-06
- **Resolution:** Open. Needs an owner decision. The 2026-08-08 blocking state was not reconfirmed.
- **Severity:** High on 2026-08-08, when the recorded required checks could block every merge. Not reconfirmed as a live merge block on 2026-11-06.
- **Affected version:** master branch protection as observed 2026-08-08; `.github/workflows/ci.yml` at commit `972532a`, which was HEAD on that date. That file is absent after commit `736ebc6`.
- **Read when:** deciding whether this issue is closed after the GitHub workflows were removed, or before restoring branch protection or Actions.
- **Search terms:** branch protection, required status checks, pd-ocr-training CI, pdomain-ocr-training CI, dep-refresh, auto-merge stuck, rename drift, admin bypass.
- **Relates to:** `pdomain-ui` `docs/specs/2026-07-16-dep-refresh-auto-land-design.md`

## Summary

This issue stays open. On 2026-11-06 it needs an owner decision.

The required-check block is gone. Master is not branch-protected, and the workflow files are gone. Nothing here proves the old check names were corrected, because the workflows that posted them were removed.

Actions remains disabled. That still matches the August Actions defect.

On 2026-08-08, master branch protection required three status contexts named `pd-ocr-training CI (3.11)`, `pd-ocr-training CI (3.12)`, and `pd-ocr-training CI (3.13)`. Those names predated the rename from `pd-ocr-training` to `pdomain-ocr-training`. The `ci` workflow's job then reported itself as `pdomain-ocr-training CI`. Its matrix legs posted checks named `pdomain-ocr-training CI (3.11/3.12/3.13)`. Nothing produced the old three names. Those checks sat "Expected", so no pull request could merge, including the weekly `dep-refresh` PR.

On 2026-11-06, `gh api repos/pdomain/pdomain-ocr-training/branches/master/protection` returned HTTP 404, "Branch not protected". `.github/workflows` is not in the tree. Commit `736ebc6` deleted the CI, dep-refresh, nightly, release, and index-regen workflows. `gh api repos/pdomain/pdomain-ocr-training/actions/permissions` returned `enabled: false`. Actions being off was already true on 2026-08-08.

## Impact

- On 2026-08-08, no pull request could merge to master through the normal gate. That includes `dep-refresh` and any human PR. The gate held because three of the required checks never appeared under their expected names. On 2026-11-06 master had no branch protection, so that particular block was not present. Whether merges should again wait on GitHub checks is the open decision.
- On 2026-08-08, `dep-refresh` armed `gh pr merge --auto --rebase`. Auto-merge could not fire while the same three contexts blocked it. That workflow file was later deleted in `736ebc6`.
- As of 2026-08-08, nobody had hit this in a stuck pull request. `dep-refresh` had never run. Zero workflow runs were recorded. No PR had merged since the rename. The defect was therefore confirmed by configuration inspection, not by a stuck PR.

## Environment / versions

```text
repo:          pdomain/pdomain-ocr-training, branch master
observed:      2026-08-08
ci.yml:        commit 972532a (HEAD); workflow name "ci"; job name "pdomain-ocr-training CI"
rename commit: e0a6571 "rename: pd-ocr-training → pdomain-ocr-training (Phase 2)", 2026-05-26
```

## Evidence

Every subsection in this Evidence section records the 2026-08-08 inspection. A present-tense verb in that record means 2026-08-08. The 2026-11-06 recheck did not repeat:

- the five-repo Actions survey
- the peer weekly runs
- the claim that pull request #13 was still the latest merge

### 1. Required contexts used the pre-rename name on 2026-08-08

```text
$ gh api repos/pdomain/pdomain-ocr-training/branches/master/protection \
    --jq '.required_status_checks.contexts'
["pd-ocr-training CI (3.11)","pd-ocr-training CI (3.12)","pd-ocr-training CI (3.13)"]
```

### 2. `ci.yml` reports the post-rename name and corrects the assignment's premise

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

GitHub names a matrix job's checks from the job's `name:` field plus the matrix leg. It does not use the workflow name or the job id.

The checks this workflow actually posts are `pdomain-ocr-training CI (3.11)`, `pdomain-ocr-training CI (3.12)`, and `pdomain-ocr-training CI (3.13)`. They are **not** the `ci (3.11)` style the assignment's framing guessed. The mismatch is one word, "omain", not a change in shape.

### 3. The rename changed the job name but not branch protection

```text
$ git log -p --follow -- .github/workflows/ci.yml   # commit e0a6571, 2026-05-26
-    name: pd-ocr-training CI
+    name: pdomain-ocr-training CI
```

No corresponding change touched branch protection. `pd-ocr-training CI` and `pdomain-ocr-training CI` differ only by the missing "omain". That difference is enough for GitHub to treat them as unrelated contexts.

### 4. The last PR to merge cleanly predates the rename

```text
$ gh api repos/pdomain/pdomain-ocr-training/commits/f2ddbfa.../check-runs \
    --jq '.check_runs[] | {name, conclusion}'
{"name":"pd-ocr-training CI (3.13)","conclusion":"success"}
{"name":"pd-ocr-training CI (3.12)","conclusion":"success"}
{"name":"pd-ocr-training CI (3.11)","conclusion":"success"}
```

PR #13 merged on 2026-05-23, three days before the rename commit `e0a6571` on 2026-05-26. Its checks still carried the old name. They matched the still-old required contexts, so it merged cleanly. No PR had merged since that date, so #13 was the most recent merge known on 2026-08-08. This pass did not recheck later merges.

### 5. Dated dep-refresh branches were a secondary defect, already mitigated here

```yaml
BRANCH="dep-refresh/$(date +%Y-%m-%d)-$GITHUB_RUN_ID"
```

On 2026-08-08, `.github/workflows/dep-refresh.yml` created a fresh branch per run. Unlike the peer repos the design spec was written for, this repo already had delete-on-merge enabled. It then had no accumulation:

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

There were zero stray `dep-refresh` branches, zero open PRs, and zero `dep-refresh` runs so far.

### 6. GitHub Actions is disabled for the whole repository, and four other repos share the shutdown date

```text
$ gh api repos/pdomain/pdomain-ocr-training/actions/permissions --jq '.enabled'
false
$ gh run list --repo pdomain/pdomain-ocr-training --limit 1 --json createdAt,workflowName
[{"createdAt":"2026-07-12T10:09:09Z","workflowName":"Dependency Graph"}]
```

On 2026-08-08, Actions was disabled for the entire repository, not just for `dep-refresh.yml`. That is why `dep-refresh` had zero recorded runs. Evidence 5 shows that count. It is also why no workflow of any kind had executed since 2026-07-12.

The cron schedule in `dep-refresh.yml` was then unchanged. It was identical to the seven peer repos still running weekly through 2026-08-02. At the 2026-08-08 inspection, no workflow file needed editing to restore the schedule. Only the Actions setting was blocking it. That file was later deleted in `736ebc6`.

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

`pdomain-book-tools` ran `dep-refresh` successfully every week through 2026-08-02, including 2026-07-12. That is the same day this repo's last run of anything occurred. The book-tools run was hours earlier, before Actions went off here.

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

Five repos show their last recorded workflow run within the same few minutes on 2026-07-12. They are `pdomain-ocr-labeler-spa`, `pdomain-ocr-synth`, `pdomain-ocr-trainer-spa`, `pdomain-ocr-training`, and `pdomain-prep-for-pgdp`. `pdomain-ocr-training` is this repo. On 2026-08-08, Actions was disabled for all five. The other seven repos in the workspace have kept running weekly through 2026-08-02.

One date across five repos, minutes apart, is consistent with a single deliberate action rather than five unrelated coincidences. A workspace-level Actions policy change, or a batch repository-settings edit, is an example of that action. This is an inference from repository-scoped data, not a confirmed cause. This repo's data alone cannot show whether the disabling was intentional and temporary, or an unintended side effect of whatever else happened that day. If it was deliberate, the resolution should say so explicitly rather than leaving it to be inferred from silence.

Consequence: as of 2026-08-08, this repository has had no CI of any kind for nearly a month, from 2026-07-12 to 2026-08-08. Anything merged to any branch since 2026-07-12 merged without any check running. That is true regardless of the branch-protection defect described above. For that window, protection could not have been enforced by a check that never ran.

## Root-cause hypotheses

As of 2026-08-08, this repo carried two independent confirmed causes. Either alone would block auto-land. Restoring only one would leave the other still blocking. The 2026-11-06 check still found Actions disabled. It found master unprotected, so the rename mismatch was not a live branch-protection block on that date.

1. **(Confirmed on 2026-08-08) GitHub Actions was disabled for the whole repository. That is why `dep-refresh` had never run.** Evidence 6 records that date. The 2026-11-06 check still found Actions disabled for this repo. It does not say a restored run would stall on the old context names. Master was unprotected on that later date. The workflow files were already gone.
2. **(Confirmed on 2026-08-08) Branch protection had not been updated when the rename changed the job's display name.** Commit `e0a6571` on 2026-05-26 changed the job's `name:` from `pd-ocr-training CI` to `pdomain-ocr-training CI`. No commit through 2026-08-08 updated `required_status_checks.contexts` to match. That comparison used the API output in evidence 1, the workflow file in evidence 2, and the rename diff in evidence 3. On 2026-11-06 the protection endpoint returned unprotected, so this mismatch was not a live block then.
3. **Ruled out: a workflow/job-id naming mismatch (`ci (3.11)` style).** GitHub uses the job's `name:` field for matrix legs. That field already reads `pdomain-ocr-training CI`. Evidence 2 and the pre-rename check-run sample in evidence 4 confirm it.

## Defects to fix

The list below is the 2026-08-08 defect list. Commit `736ebc6` later removed the workflow files. The 2026-11-06 check found master unprotected. It also found Actions still disabled. Do not read this list as a confirmed live defect list.

1. **(Primary, as observed 2026-08-08) Master branch protection required `pd-ocr-training CI (3.11/3.12/3.13)`, a name the workflow had not produced since the 2026-05-26 rename.** Nothing satisfied those three contexts. No pull request could merge, including `dep-refresh`, green or not.
2. **(Secondary, low urgency, as observed 2026-08-08) `dep-refresh.yml` created a dated branch per run** (`dep-refresh/$(date +%Y-%m-%d)-$GITHUB_RUN_ID`) instead of the reusable single branch the workspace design spec recommends. It was not causing accumulation then, because delete-on-merge was already on and no PR had stayed open long enough to test it. The file was later deleted in `736ebc6`.

## Next steps

These steps are the 2026-08-08 proposal. They assume `ci.yml` and `dep-refresh.yml` still exist. The open decision is whether to follow them or treat commit `736ebc6` as closing the issue.

Design authority for the fix shape is `pdomain-ui` `docs/specs/2026-07-16-dep-refresh-auto-land-design.md`. That file is a read-only reference. That repo's own defects differ in detail. Its Bug 1 is a missing check. This repo's is a misnamed one.

0. Decide whether to re-enable GitHub Actions. This is not a per-repo decision. The same shutdown hit five repos on the same date. Evidence 6 records that shutdown. The decision should be made once, at the workspace level, for all five together, not repo by repo here. If the disabling was deliberate and is meant to stay in place, the resolution should say so explicitly. If it was unintended, or was only meant to be temporary, re-enable `repos/{owner}/{repo}/actions/permissions` for the five. Either way, this decision comes first. Nothing below fires without it. The branch-protection fix (step 2) is necessary but not sufficient on its own.
1. Update master's `required_status_checks.contexts` to `pdomain-ocr-training CI (3.11)`, `pdomain-ocr-training CI (3.12)`, and `pdomain-ocr-training CI (3.13)`. Those are the names `ci.yml` already produces. This is a repository-settings change, not a code change. It is required regardless of step 0's outcome. By itself it is still not sufficient. With Actions off, no run exists to satisfy even correctly-named contexts.
2. Optionally, once step 1 is live, adopt the spec's reusable single-branch pattern in `dep-refresh.yml` for workspace consistency. That pattern is design section B. Treat this as cleanup, not urgent. This repo's delete-on-merge is already correct. It has zero accumulated branches or PRs today.
3. Rollout note from the spec, applied here. A change to required checks cannot satisfy its own new gate. That bootstrap problem is sharpest for pdomain-ui's fix. That fix adds a new check via a `ci.yml` PR. The PR must itself pass the gate it creates. Step 1 above sidesteps the problem. Correcting branch-protection contexts is an admin/API settings change, not a PR through `ci.yml`. It does not need to pass its own gate. Step 2 is an ordinary `ci.yml`/`dep-refresh.yml` PR. It cannot merge until step 0 and step 1 have already landed. If it is attempted first, it would need the same admin bypass the spec describes.

## What is NOT broken

This section records the 2026-08-08 tree. `ci.yml` and `dep-refresh.yml` were deleted in commit `736ebc6`.

- Delete-on-merge was already correct, with `delete_branch_on_merge: true`. That differs from the peer repos the design spec was written for.
- No stray `dep-refresh` branches or open PRs have accumulated. Both were verified at zero.
- `dep-refresh.yml`'s actual dependency-refresh steps are not implicated by this defect. Those steps are the Actions SHA-pin refresh, `make upgrade-deps`, and PR creation. The workflow has simply never run yet.
- The CI matrix and `make ci` invocation in `ci.yml` are unaffected. The defect is entirely in the required-context names, not in what CI runs or checks.

## Resolution

*Open. Needs an owner decision.*

Checked again on 2026-11-06 from this repository and the GitHub API:

- Branch protection on master returned HTTP 404, "Branch not protected".
- `.github/workflows` is absent. Commit `736ebc6` deleted the workflows. Its message, `ci: remove the GitHub workflows, release from here instead`, states that branch protection is off.
- Actions permissions returned `enabled: false`.

That recheck does not by itself say whether this issue is closed.
