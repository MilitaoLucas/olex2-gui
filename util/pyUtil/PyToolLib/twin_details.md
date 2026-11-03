# twin_details — `_twin_special_details` from the twin law

Status (2026-10-01): **working in Olex2**, confirmed by the user for a TWIN
structure and an HKLF 5 structure (GUI field, metacif and CIF).

## What it does

For a twinned structure, Olex2 writes a description of the twin law into
the CIF item `_twin_special_details`, e.g.

    Twin law (TWIN 0 0 1 0 -1 0 1 0 0 2): component 2 rotated by 180\%
    around [0.71 0.00 0.71] (reciprocal) or [0.71 0.00 0.71] (direct).

    Twin law (HKLF 5, derived from 2979 overlapping reflections): component 2
    rotated by 179.9\% around [0.10 0.00 -0.99] (reciprocal) or
    [0.00 0.00 -1.00] (direct).

(`\%` is the CIF code for the degree sign — the metacif takes ASCII only.)
This is the same form data-reduction software (CrysAlisPro, CELL_NOW)
uses. Previously the item only reached reports when a user or another
program had put it into the CIF; ReportPlus prints it among the special
details whenever it is present.

## Files

| File | What |
|---|---|
| `twin_details.py` | Everything: maths (plain Python), HKLF 5 fit, Olex2 hooks |
| `test_twin_details.py` | 17 tests, run outside Olex2 |
| `CifInfo.py` | `MergeCif` calls `twin_details.update_metacif()` before writing the metacif |
| `../htmlMaker.py` | `diffractionMetadataHtmlMaker` appends `twin_details.gui_fields()` |
| ReportPlus `ReportPlus.py` | its own `diffractionMetadataHtmlMaker` appends `gui_fields()` too (guarded import) |

**ReportPlus replaces htmlMaker's Diffraction generator** when it is
installed (it re-registers `diffractionMetadataHtmlMaker`; the section is
`etc/gui/metadata-h3.htm` → `$spy.#nameMetadataHtmlMaker()`). So the field
has to be added in both. `util/pyUtil/RPAC7d/RPAC.py` is a synced copy of
ReportPlus and gets the change at its next sync — not edited directly.

## Where it appears

- **Work > Report > Diffraction**: a "Twin Special Details" field, shown
  only for twinned structures (TWIN or HKLF 5) or when the item already
  has text; pre-filled each time the section is built. Edited text is the
  user's and is never regenerated.
- **Metacif / CIF**: `MergeCif` (runs after every refinement by default,
  `snum.refinement.cifmerge_after_refinement`) fills the metacif item; the
  Olex2 core's CifMerge writes it into the CIF — *after the
  `_twin_individual_*` loop, near the end of the file*, not among the other
  special details at the top.

Rule (`update_metacif`): the item is written only if it is empty (`?`) or
still holds generated text (recognised by the opening `PREFIX = "Twin law ("`).
Generated text is updated when the law changes and reset to `?` when the
structure is no longer twinned. User-written text is never touched.

## How it works

**Input.** TWIN and HKLF are read from Olex2's refinement model
(`OV.GetRefinementModel(False)['twin' / 'hklf']`, `twinning_from_model`) —
*not* `olx.Ins('TWIN')`, which does not return them (the first version used
it, and nothing appeared). Cell from `olx.xf.au.GetCell()`.

**TWIN** (`describe`). The matrix M acts on hkl as a column vector
(h' = M h), the same convention as Olex2's cctbx adapter
(`twin_laws_from_model`). With A the direct orthogonalisation matrix and
B = A^-T, R = B M B^-1 is the law in Cartesian space; for a
pseudo-merohedral twin it isn't exactly orthogonal, so the nearest rotation
(polar decomposition) is used. Angle from the trace; axis from the
antisymmetric part (or the largest column of R + I near 180°), given in
reciprocal (A^T x) and direct (A^-1 x) coordinates, normalised, first
non-zero component positive. Also handled: improper laws ("…, combined
with inversion" — meaningful for TWIN, e.g. with anomalous data), N > 2
components (M^(k-1)), TWIN −N ("also present as its inversion partner").
Pure inversion twins are skipped — olex2.refine already writes "Refined as
an inversion twin".

**HKLF 5** (`overlap_groups`, `fit_laws`, `describe_hklf5`). Overlapping
reflections form groups (component = |batch|, negative batch for all but the
last line, up to the 0 0 0 terminator); each group with components 1 and k
gives a pair (h1, hk). Programs list the other component's indices as
*arbitrary Laue equivalents*, varying per reflection, so:
1. on three independent pairs every combination of Laue operators is tried,
   M solved exactly, and the M explaining a sample of all pairs best kept
   (stops early for an exact, merohedral law);
2. each pair gets its best equivalent for that M, then a least-squares refit.

The HKLF matrix (`HKLF 5 s r11..r33`) is applied to all indices first.
Laue operators come from cctbx (`laue_ops_for`, Laue group of the current
space group) and are always closed under −1 (`with_friedel`): cctbx's
`group.smx()` omits the inversion unless `with_inversion=True` — without
it a real law came out "…, combined with inversion" (fixed 2026-10-01).

Description (`canonical_law`): among the equivalent laws g M, a twofold
(within 0.5°) if there is one — the usual way to state a (pseudo-)merohedral
law — otherwise the proper rotation with the smallest angle. The fitted
law is approximate (indices are rounded in the file), so e.g. 179.9°
is real, not a formatting issue. ~1–2 s per file, cached until the file
changes.

Not reported (message printed, item left alone):
- rms index residual > `MAX_RMS` (0.5): no single law fits;
- a law equivalent to a symmetry operator of the crystal (< `MIN_ANGLE`,
  0.5°) — this is what a **small-angle non-merohedral twin** (e.g. "rotated
  by 2.24°" from CrysAlisPro) looks like: only reflections whose indices
  coincide overlap, so the indices carry no angle. That angle comes from
  the orientation matrices of data reduction and cannot be derived here.

## Testing

From `util/pyUtil/PyToolLib`: `python -m unittest test_twin_details` (17).
Covers the str1878Pbca TWIN case, a 2.2444° rotation recovered from its
matrix, twofolds, inversion / improper / N = 3 / TWIN −N, the refinement-
model reader, HKLF 5 parsing, an exact merohedral law given as random
equivalents (must match the TWIN text), a non-merohedral twofold from
rounded indices, the HKLF matrix, unrelated data and small-angle twins
(must give nothing), the twofold preference, and Laue operators without −1.

Real data was used during development (not in the repository).
(`str1878Pbca_pl.res`, TWIN; `*.olex2_hklf5.hkl`, HKLF 5).

cctbx can't be imported outside Olex2 here (Olex2's `pyl.exe` fails on
numpy), so `laue_ops_for` is only exercised in Olex2; its cctbx calls follow
the bundled sources (`cctbx/cctbx_sources`: `r().num()`/`r().den()`,
`smx(with_inversion=...)`, `build_derived_laue_group()`).

## Possible next steps

- Small-angle non-merohedral twins: read the law from data-reduction output
  (orientation matrices) instead of the indices.
- Optionally also include the refined fractions (`_twin_individual_*`) in
  the sentence.
- The GUI label `%Twin Special Details%` has no entry in the (unmaintained)
  language dictionary — fine in English.
