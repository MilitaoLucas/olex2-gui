# Experimental Labels: vector labels, TrueType printing, geometric trim

Developer notes, 2026-11-14. User help: `labelmode.help.md` (the 'i' buttons).
GUI: Images > **Experimental Labels** (`etc/gui/h3-Experimental-Labels.htm`, included
from `etc/gui/tools/images-body.htm` below Image Series).

## The two modes

`user.image.labels.mode` = `normal` | `vector` (`spy.gui.images.label_mode(...)`).

- **normal**: exactly as Olex2 always did it. Ctrl+P / Bitmap Images: `pict`; Trim =
  render an intermediate `temp.bmp`, trim by the background colour (`ImageTools.trim_image`),
  render again at the scaled size, trim. Does not work on gradient/picture backgrounds.
- **vector**: label fonts `@<size>` (Olex2's vector font: zooms with the structure, keeps
  dragged places). In images Olex2's labels get the font `@1` for the moment of the
  `pict` (fonts put back after; drags survive a font change) and are drawn again in a
  TrueType font (`labelmode.render` / `draw`). `vector_both` (panel: Compare, default
  off) leaves Olex2's labels in, for comparing. Not used, and why: transparent
  `PLabels.Text` does not hide vector text; `kill labels` hides but `label` re-shows
  with SetOffset (bond labels lose their drag); `@0` is accepted by the core
  (MetaFont::SetIdString) but zero size may divide by zero. Trim
  = from the geometry (`_make_trimmed`): one rendering at the size that makes the
  picture's box the target width, then a crop; works on any background.

Switching saves the user parameters (before 2026-11-14 it did not: after a restart the
fonts to come back to were gone). `normal` restores `normal_atom_font` /
`normal_bond_font`, else the scene's font (`<AtomLabels id=...>` of `user.def_scene`),
else `#olex2.fnt:frb_18`; it only touches fonts that are vector fonts.
The Bitmap Images header runs `setfont AtomLabels ...` when opened; its onclick now ends
with `spy.gui.images.label_reapply()` which puts the vector fonts back in vector mode.

## How Olex2 draws vector labels (source, `gxlib/gllabel.cpp`)

- Position: `GetVectorPosition` = `Project(offset + M * center * Scale)` -- the drag
  (`center`) is added **in 3D before projection**, so perspective scales it.
- Size: `DrawVectorText(T, text, zoom / CalcZoom())`; `CalcZoom = 1/|max - min|` of the
  scene (`glib/glrender.cpp`). So in view Angstrom a label is `k * pt / CalcZoom` high:
  it grows relative to the atoms when the structure is grown. Perspective does not
  change the size.
- `CalcZoom` is computed from the saved model's `<Renderer max= min=>`
  (`screenbox.calc_zoom`).

Drag: `center * GetScale()` with `GetScale() = 1/Height` (`glib/glrender.h`), so a drag
is `drag / window height` in view Angstrom -- used as is, NOT calibrated any more
(2026-11-14: a fitted drag scale from a calibration with few or small drags threw the
labels far out of the image). `calib_drag_scale` is no longer read.

Calibration (`spy.gui.images.label_calibrate`) renders once with labels in magenta,
finds them (`find_boxes`) and fits the size constant and the offset (`fit`; the offset
as the median of what is left once anchor and drag are taken off). Since
2026-11-14 it stores `calib_size_k` (per pt per 1/CalcZoom); older calibrations
(`calib_size_per_pt`, a fixed size in Angstrom) are used unchanged until the next one.
`ttf_scale` (default 1.18) scales the printed TrueType labels (user: they came out ~0.9 of
Olex2's printed vector labels; Olex2 prints vector labels a little bigger than on
screen; 2026-11-16 at 1.1, atoms @10/@12, no perspective: positions perfect, size
~0.93 -> 1.18). Default atom size @20 -> @12; panel sizes 6-20 (atoms), 3-12 (bonds).

## Projection (`screenbox.py`)

- `gl.Basis()`: matrix applied by columns, `v_i = sum_j M[j][i] (p_j + c_j)`; pixels =
  `v * zoom * window height` from the window centre, y up (confirmed 2026-11-12).
- Perspective (`glib/glrender.cpp` SetView/Project): eye at 2 view units (NearPlane 1),
  frustum half height `tan(angle/2) * 0.5` at the near plane, so
  `px = h * zoom * v / (tan(angle/2) * (2 - zoom * v_z))` (`depth_factor`, `flat`).
- Olex2 cannot be asked whether perspective is on (`IsPerspectiveEnabled` is not
  exposed): `spy.gui.images.perspective(angle|off)` runs `gl.Perspective` and keeps
  `user.image.perspective` (not saved over a restart, as in Olex2).

## The trim box (vector mode)

From one temporary `save model` (`labels.current_model`):
- atoms: `screenbox.drawn_atoms` -- every lattice atom (grown copies), without deleted
  ones (`flags & 1`), hidden ones (Visibility bits) and H / Q when switched off as a
  group; each with its drawn reach (`1.5382 * sqrt(Uiso)`, H 0.15 A);
- legend: `screenbox.legend_box` -- `AtomLegend Left/Top` of the structure style in the
  model, size from the legend measurement of the theme designer (`user.legend.width`,
  `row_height`) times the number of elements;
- labels: `labelmode.label_boxes_px` -- where vector mode prints them.

The union is printed as one console line per image (`Trim: n atoms -> ...`). Any failure
falls back to the colour trim and says why. Padding/border from the Bitmap panel; the
border colour from `user.image.trim_border_colour` (what the panel sets).

## Parameters (`params.phil`, `user.image`)

`labels.mode`, `vector_atom_size`, `vector_bond_size`, `normal_atom_font`,
`normal_bond_font`, `calib_size_per_pt` (old), `calib_size_k`, `calib_drag_scale`,
`calib_offset_x/y`, `ttf_scale`; `image.perspective`; `bitmap.trim*`.

## Open

- Why a grown structure came out untrimmed (2026-11-14): unknown; the console line now
  tells. Suspect: a legend far away, or the Trim box being off.
- Labels under perspective: offsets fixed from the source, not yet confirmed on screen.
- For Oleg: a getter for perspective; vector label rendering itself.

## Tests

The designer suite (`plugin-DevTools/theme_designer/tests/test_themes.py`, class
`ScreenBoxTest`) covers projection with perspective, `calc_zoom`, drawn atoms and legend
of the user's grown sample, union/rect conversion.
