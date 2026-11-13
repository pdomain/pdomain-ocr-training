---
Status: active
Owner: CT
Created: 2026-05-21
Last verified: 2026-11-13
---

# docs/

Start with [Architecture: pdomain-ocr-training](architecture/00-overview.md), then [Where training work lives](architecture/suite-boundaries.md) and the [roadmap](ROADMAP.md).

- Durable rationale is in [decisions](context/decisions.md).
- The [current state](context/current-state.md) and [intent map](context/intent-map.md) hold deferred work and open decisions.
- Open issue files are indexed in [docs/issues/README.md](issues/README.md).
- Process references include the [writing style](process/writing-style.md) and [lint suppression catalogue](process/lint-deviations.md).

How documentation is organized in this repo.

| Folder | Purpose | Use when |
| --- | --- | --- |
| `architecture/` | Durable reference — how the system works today. | Capturing current shape (modules, data flow, contracts, current-state diagrams). |
| `decisions/` | ADRs — dated, append-only "we chose X because Y." | Recording a specific design choice with context, alternatives, consequences. |
| `plans/` | Active execution — what order to make a spec real. | Sequencing work for an approved spec. |
| `process/` | Cross-cutting workflow conventions (verification rules, merge strategy, release process). | Capturing how the team works, not what the system does. |
| `research/` | Investigation in progress. Messy by design. | Exploring before committing to a design. |
| `runbooks/` | Operational reference — something is broken or being operated. | An on-call or ops task needs a recipe. |
| `specs/` | Aspirational, pre-implementation design. | Describing what to build, before code. |
| `templates/` | Issue, spec, plan, ADR boilerplate. | Adding a starter template for a new doc type. |
| `usage/` | Downstream reference — how to consume this app/tool/library. | A user or integrator needs to know how to use it. |

Empty folders are intentional and tracked via `.gitkeep`.

Retired documents live in Git history, with durable behavior in architecture
and retirement receipts in the decision log. The empty archive folders were
removed by commit `e50bb66`. A superseded plan may remain on disk when current
work still refers to its unfinished requirements.

Active issues live in `docs/issues/` as governed, evidence-bearing reports. The GitHub issue
tracker is no longer used for status.
This layout is workspace-standard; see
`/workspaces/ocr-container/docs/README.md` for the master.
