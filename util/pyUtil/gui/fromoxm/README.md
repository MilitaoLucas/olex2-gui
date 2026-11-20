# gui/fromoxm -- the picture of a saved model on another model (experimental)

Developer notes, 2026-11-14. User help: `fromoxm.help.md` (the 'i' buttons).

## What it does

`spy.from_oxm(name[, part ...][, option ...])` reads a saved model (`.oxm`) and
repeats its picture on the structure that is open: the same grown atoms with the same
symmetry operators, the same hidden atoms, the view, and optionally the drawing style,
the planes and the lines. Atoms are matched by **position**, so the labels may differ;
atoms with other names can be given the sample's names.

| call | effect |
|---|---|
| `spy.from_oxm(Frag1b)` | everything (`all`) |
| `spy.from_oxm(Frag1b,grow,view)` | parts: `grow view styles planes lines all` (`,` or `\|`) |
| `spy.from_oxm(Frag1b,names)` | only rename atoms as in the oxm |
| options | `names` (rename, no question), `keepnames`, `bylabel`, `margin=0.3` |

GUI: View > Symmetry Generation > **Experimental Growing**
(`etc/gui/h3-Experimental-Growing.htm`, included from `etc/gui/symmetry-generation.htm`),
settings `user.fromoxm.{file, parts, names, margin}` in `params.phil`; spy functions
`spy.gui.fromoxm.choose()`, `run([names])`, `file_label()`.

## Files

| file | |
|---|---|
| `_core.py` | pure Python, no Olex2: reads the oxm, matches atoms, builds the commands |
| `__init__.py` | Olex2 side: reads the model now, asks, runs the commands; panel functions |
| `test_fromoxm.py` | `python test_fromoxm.py` (10 tests; one uses the user's real sample if present, `FROMOXM_OXM` to point elsewhere) |
| `fromoxm.help.md` | help entries EXPERIMENTAL_GROWING, _SAMPLE, _WHAT, _NAMES |

Imported at startup from `initpy_funcs.py` (`import gui.fromoxm`). `gui/images/screenbox.py`
also uses `_core` helpers (`_section`, `_attrs`, `_visibility`) to read drawn atoms.

## The .oxm format (what is used)

An oxm is `b'oxm'` followed by a zip with entries `model` (Olex2 XL text) and `grid`.
In `model` (source: `gxlib/gxapp.cpp` SaveModel/LoadModel, github.com/pcxod/olex2):

- `XFiles/0/Lattice/AUnit`: `cell` (a..gamma with esds), `symm latt="n"` with
  `symmop "..."` children (SHELX LATT/SYMM), `residues/*/atom label= type= x= y= z=`.
  The order of the atoms is the `atom_id` of the lattice; checked against coordinates.
- `Lattice/Matrices`: `symop "1/2-X,..." id=...` -- `matrix_id` is the **index** in this
  list; planes refer to the `id` attribute (`m_id`).
- `Lattice/Atoms`: one `Atom atom_id= matrix_id= crd="x,y,z" flags=` per drawn atom,
  Cartesian (Olex2: a along x, b in the xy plane). `flags & 1` = deleted.
- `Lattice/Planes`: `Plane def_id=` once per grown copy, `atom a_id= m_id=` children.
- top level: `Style` (a complete .glds, with `LinkFile`), `Scene`, `NameRegistry`
  (plane names keyed by an MD5 of the plane definition), `Basis zoom=` with `matrix`
  and `center`, `Visibility` (`atoms=` base64 bit array + one digit = count % 8, one bit
  per non-deleted atom; `h_atoms`, `q_atoms`, `legend` flags), `AtomLabels` /
  `BondLabels` (`Label offset= center= visible= text=`), `Lines` (`object "name"
  base= edge= r=`), `Renderer max= min=` (scene extents).

## Matching by position (`match_atoms`)

- The space group from the sample: identity + SYMM, their inverses when LATT > 0,
  each with the centring vectors of |LATT| (`group`).
- A pair (sample atom, model atom) counts when an operator plus a lattice translation
  puts the model atom within `margin` (default 0.5 A) of the sample atom, same element.
  Candidates are sorted by distance and taken greedily one-to-one.
- A model atom paired through a non-identity operator is **moved** first
  (`sgen -m <op> <labels>` after `fuse`), so the sample's growing operators apply as
  they are. `format_symop` writes the operator the way Olex2 does (`1/2-X,-1+Y,+Z`).
- `renamed()` lists pairs whose names differ; `rename_commands()` renames through
  temporary labels (`<El>Z<base36>`, never in use), hydrogen atoms last (naming a
  parent may rename its H atoms). `name A B` steals B from another atom by default
  (`gxlib/gxmacro.cpp` macName, `-ns` would prevent it).
- Q-peaks are never matched or grown.

## The commands, in order (`commands`)

1. Styles are **never loaded** (history, 2026-11-14): `load style` of the oxm's Style
   section (only the *structure* style, `TGXApp::SaveStructureStyle`) replaced the whole
   style -> built-in atom look; merging it into the live style and loading that still
   lost the atoms' draw styles: `ads`/`telp` keep them as a runtime `DS` parameter of
   each atom's style (`TXAtom::DrawStyle`), which a style reload does not carry ->
   ellipsoids became spheres. Also: inside an oxm material references read
   `olex_model.Style.Materials.PropN`, not `style.Materials.PropN`.
   Now `styles` = `__init__._apply_materials`, run last: `save style` to a temp file
   only to see which entries/primitives exist (after planes and lines are made), then
   `SetMaterial "name.primitive" material` for each sample colour that has a home here
   (`style_materials`, structure entries only -- `NOT_STRUCTURE` skips console,
   background, legend, cell, grid ...). Shapes (PMask) are not set this way.
2. `fuse` (grow/planes), then the moves `sgen -m`.
3. `mpln [-n=name] <labels>` per plane definition, before growing: the lattice repeats a
   plane for every grown copy whose atoms are all there (as seen in the sample: one
   def_id per copy). *Not yet verified in Olex2.*
4. `sgen <op> <labels>` per operator, 40 labels per line; `hide -b <labels>` for atoms
   hidden in the sample, only where the label has one copy (a label hides all copies).
5. `line [-n=name] x1 y1 z1 x2 y2 z2`: an end within 0.1 A of a drawn sample atom is put
   on the same atom and operator in this model (`line_end`), others stay.
6. View: `matr` with the nine numbers **transposed** (macMatr transposes),
   `center -cx -cy -cz` (macCenter sets -v), `gl.Zoom -a z`.

All inside `freeze true` / `freeze false`.

## Known limits / open

- Labels: no command places a label at its dragged offset (Oleg).
- Plane names come back only when every plane has one (MD5 key, see above).
- `sgen -m` changes the asymmetric unit of the model (unsaved); reported in the console.
- The cell is compared (2 %, 1 degree) and only warned about.
- Not yet run inside Olex2: everything here is tested on the user's sample file and
  synthetic models only.

## Before committing

`svn add` this folder (`__init__.py`, `_core.py`, `test_fromoxm.py`, `fromoxm.help.md`,
`README.md`), `etc/gui/h3-Experimental-Growing.htm`; set `olex-update`/`olex-install` on
the help file (see `gui/help/README.md`). In a dev tree the new help shows after
`spy.help.rebuild()` (which also rewrites `help_index.json` -- do not commit that).
