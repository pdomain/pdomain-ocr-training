---
Status: active
Owner: CT
Created: 2026-09-18
Last verified: 2026-09-18
Kind: decision
---

# ADR: The labeler's dataset export writes the glyph-feature sidecar

## Agent Index

- **Kind:** decision
- **Status:** active
- **Last verified:** 2026-09-18
- **Read when:** touching `_emit_glyph_slices`, `GlyphFeatureSet`,
  `RecognitionEvalConfig.glyph_annotations_path`, or asking where the
  glyph-feature sidecar comes from.
- **Search terms:** glyph sidecar writer, glyph feature ownership, crop id join,
  slice_glyph_features, GlyphFeatureSet producer.

**Date:** 2026-09-18
**Status:** Accepted

## The decision

`pdomain-ocr-labeler-spa`'s dataset export writes the glyph-feature JSON
sidecar. This repository keeps consuming it and never produces it.

## What was open

`docs/context/intent-map.md` carried this under "Needs owner decision": whether
dataset export or the trainer SPA writes the sidecar. `docs/context/current-state.md`
listed it as a current risk. Recognition eval could slice CER and WER by
ligature, long s and swash, and nothing anywhere wrote the file those slices
need, so the capability had never run on real data.

## Why the export

The export is the only place where both facts exist at the same moment: the
person's glyph annotations for a word, and the recognition crop filename that
word becomes. Any other producer has to rebuild that join from nothing, and a
join rebuilt from the wrong key produces a sidecar that silently matches no
crops.

The trainer SPA was the alternative. It sees crops and metrics, not the
labeling session where a person marked the glyphs, so it would be deriving the
annotation side second-hand.

## What the producer must honour

- The file is one JSON object, `dict[crop_id, GlyphFeatureSet]`, keyed by the
  DocTR recognition val-set label key. That is the per-crop filename or relative
  path, the same key `_run_recognition_inference` threads through. Keying by
  crop id rather than by iteration index is what makes the join survive any
  filtering or reordering of the val set.
- `ligatures` holds kind strings and is sliced per kind. They are never lumped
  into one bucket. They are the producer's own `LigatureKind` enum values,
  uppercase, emitted verbatim: `FI`, `LONG_ST` and so on. `_emit_glyph_slices`
  treats them as opaque and normalizes nothing, so a slice is named after the
  string exactly as given. Lowercasing on either side would split one ligature
  kind into two slices that never meet.
- **An absent crop means unknown, not feature-free.** `_emit_glyph_slices`
  excludes an absent crop from both the positive and the negative set of every
  feature. So only a word somebody actually reviewed gets an entry. Writing
  all-false for a word nobody looked at would assert the absence of something
  never checked, and would land that word in every feature's negative set.

## What this does not decide

Nothing here makes this repository import `pdomain-book-tools`. `GlyphFeatureSet`
stays the decoupled shape it is, carrying only the three facts recognition eval
needs, and the labeler matches that shape by hand rather than by sharing a type.

## Why now

The labeler settled a related question the same day: it will not build a glyph
predictor. The classifier this repository's predecessor `pd-ocr-trainer` was to
ship never existed, and that repository is retired. Glyph features therefore
come from people, not models, for the foreseeable future — which makes it worth
getting the marks people already make into eval. The labeler's reasoning is in
its `docs/context/decisions.md`, two entries dated 2026-09-18.
