---
Status: active
Owner: CT
Created: 2026-11-12
Last verified: 2026-11-13
Kind: architecture
---

# Where training work lives

## Agent Index

- **Kind:** architecture
- **Status:** active
- **Last verified:** 2026-11-13
- **Read when:** deciding which repository owns a training, typography, measurement, or synthesis change.
- **Search terms:** suite boundaries, formatting model, separate repository, pgdp-measure, book-contracts.

The formatting model is not built. When it is built, it belongs in this package, not in a new one.

This package trains DocTR detection and recognition. It trains a caller-supplied layout model, and it evaluates detection and recognition. Layout training does not download DocTR or PP-DocLayout weights.

Typography contracts, corpus preparation, scan measurement, and synthetic rendering already live in other repositories.

Shipped runner behavior is in [Architecture: pdomain-ocr-training](00-overview.md). The ordered work is the [roadmap](../ROADMAP.md).

## What this package owns today

`pdomain_ocr_training` exposes torch-free configuration and runner protocols. Importing the package does not load torch. Resolving `LocalTrainingRunner` does, because that loads `detect.py` and `recog.py`.

The modules on disk are detection training, recognition training, caller-supplied layout training, dataset export helpers, and synchronous detection and recognition evaluation.

The evaluation backend can read a glyph-feature sidecar and emit per-feature
slices. The public runner currently drops the enabling configuration; the
[architecture overview](00-overview.md#ievalrunner) records that limitation.
This package does not write the sidecar. The labeler does. The contract is the
[glyph-sidecar ADR](../decisions/2026-09-18-glyph-sidecar-writer.md).

There is no `formatting` package and no `train_formatting` method. A search of the Python tree on 2026-11-12 found neither.

## What the sibling repositories own today

This pass read the checkouts under `/mnt/work/projects/pdomain` on 2026-11-12.

`pdomain-book-contracts` 0.3.0 owns the canonical typography types and the PGDP F2 reader.

- Labels, spans, records, review, and exchange live under `pdomain_book_contracts/typography/`.
- The F2 tokenizer, parser, and project rules live under `pdomain_book_contracts/sources/pgdp/f2/`.
- Token alignment lives in `pdomain_book_contracts/matching/alignment.py`.

`pdomain-book-tools` keeps the old import paths. Its `typography` and `pgdp/f2` modules re-export the contracts package.

The package itself is not torch-free. It requires torch, torchvision, torchaudio, transformers, and python-doctr. This training package depends on it. A base install still pulls that stack, even though the public import does not load torch.

`pdomain-source-data` on master (`4601095`) owns corpus tasks. `tasks/typography/crops.py` defines `align_page`. That function projects F2 style spans onto OCR words the caller already supplied. It returns styled tokens plus alignment evidence. It does not open an image, and it does not write a pixel crop.

That same tree also materializes page ground truth and prepares labeler books.

`pdomain-pgdp-measure` already owns font-free measurement of PGDP scans: geometry, alignment, typography, and glyphs. Its README says it was extracted from `pdomain-ocr-synth`. The same README says its runtime is pydantic, Pillow, and numpy.

`pdomain-source-data` does not depend on that package. Its intent map already forbids a second measurement library.

Crop records stay in source-data. Scan measurement should call `pdomain-pgdp-measure` instead of a second measurer.

`pdomain-ocr-synth` already shapes text with HarfBuzz and rasterizes with FreeType for detection and recognition recipes. It has no `typography/` package and no mixed-span formatting renderer.

That renderer is still future work in the synthesizer, not a new repository.

`pdomain-ocr-labeler-spa` writes the glyph sidecar from `core/jobs/handlers/glyph_sidecar.py`. This pass confirmed the sidecar file.

The 2026-11-09 decision record says the labeler also implements typography review. This pass did not re-test the review UI.

`pdomain-ocr-trainer-spa` is the worker that calls these runners. It is not a second training implementation.

`pdomain-pgdp-api-client` is the existing acquisition repository. This pass confirmed the checkout. It did not re-read the client.

## Where the unbuilt formatting model belongs

Build the formatting model in this package, behind a new `FormattingConfig` and a formatting runner method. Do not add those fields to `RecognitionConfig` or `train_recognition()`. Detection and recognition behavior stay as they are.

Do not start a formatting-only repository. The model shares this package's runner protocol and its training extra. A split is worth revisiting only if that model stops sharing the runner.

The design for the model remains the [typography spec](../specs/2026-08-21-fine-grained-typography-model-design.md). Read the [2026-08-31 re-verification](../research/2026-08-31-typography-corpus-reverification.md) before the August research counts. The execution checklist is the [phase-two plan](../plans/2026-08-31-fine-grained-typography-phase-two.md). The August 21 plan is a historical checklist.

## Work that should stay in the repository that already has it

- Span types, F2 parsing, and alignment contracts stay in `pdomain-book-contracts`. Do not copy a torch-free mirror back into this package or into the synthesizer.
- Corpus inventory, edition matching, split manifests, and training-crop records stay in `pdomain-source-data`.
- Scan measurement stays in `pdomain-pgdp-measure`.
- Mixed-span synthetic pages stay in `pdomain-ocr-synth`, and they should depend on `pdomain-book-contracts` for span types. They should not depend on `pdomain-book-tools` for those types. That dependency pulls the training stack.
- The glyph sidecar stays in the labeler. An absent crop means unknown, not feature-free.
- Interactive review stays in the labeler. If unreviewed batch geometry is produced for a silver-tier baseline, it stays out of the gold set.

## Consider a new repository for these, and not before

**An OCR and HTR comparison harness.** Compare PP-OCRv5 through ONNX, HTR engines, and licensed historical datasets with the DocTR baseline. Require reproducible accuracy, runtime, model size, and license evidence before any of them joins a training stack. Put that comparison in its own repository. Do not add a second training stack to this package in order to run the comparison.

**A typeface or glyph classifier, after the scope is chosen.** The labeler will not build a glyph predictor. The classifier once planned for `pd-ocr-trainer` was never shipped. That repository is retired. If a classifier is built later, give it a separate model package. Add a runner contract here only after the owner confirms the scope. Do not extend `detect.py` or `recog.py` for it.

**Inference deployment, after the owner names the home.** The spec leaves two choices open: who packages inference, and which hardware it targets. A provider protocol may later enter `pdomain-book-tools`. The heavy torch implementation stays in a deployment package or an optional adapter. Neither choice belongs in this training repository.

## Where these claims come from

- Code:
  - `pdomain_ocr_training/` has no `formatting` module.
  - `align_page` is `pdomain-source-data` `pdomain_source_data/tasks/typography/crops.py`.
  - Contracts version `0.3.0` is `pdomain_book_contracts/_version.py`.
  - Book-tools typography modules re-export `pdomain_book_contracts`.
  - The labeler writer is `src/pdomain_ocr_labeler_spa/core/jobs/handlers/glyph_sidecar.py`.
  - Synth rendering is `src/pdomain_ocr_synth/render/word_crop.py`.
  - Measure scope is the `pdomain-pgdp-measure` README.
- Tests: this pass did not re-run the suite. The last recorded full local run remains 139 tests on 2026-11-07, noted in [current state](../context/current-state.md).
- Verified: 2026-11-12 by reading the checkouts above. `pdomain-source-data` master was `4601095`.
