# proto -- solve from a library of finished structures

Deliberately kept at a low level: spy functions only, no GUI.

## Where we left off (2026-09-30)

Done:
- 2026-09-29: library always present in `DataDir()/gui/proto`, add / find /
  apply / solve / library / remove, reduced-cell matching, AC7 API kept.
  **Confirmed working in Olex2.**
- 2026-09-30: matches in *another setting of the same space group* are
  transformed into the current setting and applied (`transform.py`,
  `cells.setting_transform`).
- 2026-09-30: after an apply, the other usable hits are listed as
  `spy.proto.apply(N)` -- e.g. to switch to a disordered model of the same
  compound; each becomes its own solution node in the history, and
  switching between proto hits doesn't ask again before replacing atoms.
- 2026-09-30: test data generator `make_setting_test.py` and three test
  data sets (see Testing).

Not yet confirmed in Olex2 (offline tests and a mock pass):
- the cctbx operator search for other settings (`cells.setting_transform`)
  -- the step most likely to need a fix. If a copy shows as `other`
  instead of `setting`, note the two space groups and cells.
- the hit switching after an apply.
- `ZP2_bca` also tests a non-standard space-group symbol (P21cn) going
  from Olex2 into cctbx.

Next step: run the test procedure in the Testing section in Olex2.

## Idea

When a structure is finished, add it to a library. A later data set of
the same compound (same lattice) can then be "solved" straight from the
library instead of running a solution program.

## Files

| File | What |
|---|---|
| `proto.py` | Olex2 side: spy functions, applying a model, AC7 compatibility |
| `db.py` | SQLite storage, plain Python (no Olex2 imports) |
| `cells.py` | Cell comparison and setting operator with cctbx (reduced/Niggli cells) |
| `transform.py` | Rewrites a model into another setting (xyz, Uij, EQIV), plain Python |
| `proto.phil` | Parameters (`proto.*`) |
| `test_db.py` | Tests for `db.py` |
| `test_transform.py` | Tests for `transform.py` (distance / U / symmetry invariance) |
| `make_setting_test.py` | Makes test data: an ins/hkl pair in another setting (see Testing) |
| `__init__.py` | Imports `proto.py` only inside Olex2, so the tests run outside it |

Loaded at startup by `import gui.proto` in `util/pyUtil/initpy_funcs.py`
(`import_gui()`, outside the HasGUI block, so it works headless too).

## Spy functions

| Call | What |
|---|---|
| `spy.proto.add([comment], [class], [name])` | Add the loaded, refined structure (its res/ins) |
| `spy.proto.find()` | Print matches for the loaded data, best first |
| `spy.proto.apply([N])` | Use match N (default 1) of the last find/solve as the solution; after an apply the other hits are listed, and switching between them doesn't ask again before replacing atoms |
| `spy.proto.solve()` | find + apply the best match |
| `spy.proto.library()` | List everything in the library |
| `spy.proto.remove(ID)` | Remove library entry ID |
| `spy.proto.check()` | Number of applicable (`same` + `setting`) matches (for a future GUI) |

Console commands, if wanted, belong in `macro.xld` as thin macros calling
these spy functions -- no Python macros (`OV.registerMacro`).

## Library and parameters

- `proto.library` = `DataDir()/gui/proto/proto.sqlite` -- always exists;
  created empty when the module loads. `add` writes here.
- `proto.extra_dbs` -- `;`-separated further databases, searched but never
  written to (e.g. `BaseDir()/util/pyUtil/AC7/sponge/sponge.sqlite`).
- `proto.length_tolerance` (%, default 3), `proto.angle_tolerance`
  (degrees, default 3) -- cell match tolerances.
- `db_location`, `db_name`, `tolerance`, `class`, `sg` -- AC7 only, see below.

Paths in params may start with `DataDir()` or `BaseDir()`.

## How it works

- **Schema**: one table `proto`. The first columns are those of the
  original AC7 sponge database, so old databases are readable as they are.
  Newer columns (comment, reduced cell `red_*`, r1, added, hash, path) are
  added in place only when a database is opened for writing
  (`db.ensure_schema`). Read-only sources are never altered.
- **Duplicates**: `hash` = SHA1 of the model text (line endings and
  trailing blanks ignored); `add` refuses only a byte-identical model.
  Other models of the same compound (disordered, re-refined, ...) are
  added as their own entries on purpose -- several hits per compound are
  wanted, and the user picks one with `spy.proto.apply(N)`.
- **Matching** (`proto._find`, `cells.compare`):
  1. cheap volume pre-filter in SQL-land (`db.entries`), allowing for
     centring multiplicities 1-4;
  2. reduced primitive cells compared with cctbx
     `similarity_transformations` (handles Niggli ambiguity near 90 deg);
  3. classified `same` (same space group and the direct cells agree),
     `setting` (same space group in another setting/axis choice -- a
     change-of-basis operator was found) or `other` (same lattice,
     different space group -- listed, never applied);
  4. ranked: `same`, `setting`, `other`, then element overlap of the
     formulae, then cell deviation.
  Reduced cells missing on legacy rows are computed on the fly and cached
  (writable databases only).
- **Applying** (`proto.apply` -> `_model_for_current` -> `_load_solution`):
  the stored model gets the loaded file's TITL, CELL, ZERR and HKLF lines,
  is written as `<name>.res`, reloaded (`OV.reloadStructureAtreap`), the
  HKL source is kept, and a *solution* history node is created -- the same
  outcome as a normal solution program. The loaded file is never
  overwritten. With the GUI, you're asked before existing atoms are
  replaced.
- **Other settings** (`cells.setting_transform`, `transform.transform_model`):
  both settings are taken to their Niggli cells; the identity and every
  cctbx `similarity_transformations` matrix between them (and inverses)
  are tried, and the first operator is accepted that turns the stored
  space group into *exactly* the current one and the stored cell into one
  similar to the current. The model is then rewritten: x' = R x + t,
  U*' = R U* R^T (SHELX Uij via U*_ij = U_ij a*_i a*_j), EQIV operators
  S' = C S C^-1 (exact fractions); coordinate fix codes (10+x) are dropped;
  CELL, ZERR, LATT/SYMM, TITL, HKLF come from the loaded res/ins (required
  for this path). Restraints and everything else are kept as they are.
  Limitation: only linear operators -- settings that differ by an origin
  shift (e.g. origin choice 1 vs 2) end up as `other`.

## AC7 compatibility

`find_in_proto`, `solve_with_proto`, `add_to_proto`,
`cleanup_proto_disorder` and `cp` keep their original API for AC7's sponge
module (`AC7/sponge` and `AC7d/sponge`, identical copies -- not edited).
They use the database at `proto.db_location`/`proto.db_name`, which
`SPONGE.phil` sets. Fixed on the way: the crash in `solve_with_proto` for
space groups other than C2/c, and the crash when the database is missing.

## Not done yet / ideas

- Origin shifts between settings (see limitation above).
- Proto as a solution method next to ShelXT / olex2.solve, or a
  "this structure is in proto -- load it?" button on the Solution tab
  (`spy.proto.check()` is there for that).
- RODFolder integration (add solved structures / bulk import) -- deferred.
- `macro.xld` wrappers (`proto_add` etc.) -- not added.

## Testing

- From `util/pyUtil/gui`: `python -m unittest proto.test_db proto.test_transform`.
- Test data for other settings:
  `python -m proto.make_setting_test <ins> <hkl> <out_dir> <basis> [tag]`
  (basis e.g. `a,b,c-a` or `b,c,a`). Made from sample_data into
  a local folder (2026-09-30): `thpp_P21c`
  (thpp is P21/n), `water_P21n` (water is P21/c), `ZP2_bca` (Pna21 as
  P21cn). hkl d-spacings checked unchanged. Solve + refine the original,
  `spy.proto.add()`, load the copy, `spy.proto.find()` -> 'setting'.
- Everything else needs Olex2 (olex/olx and cctbx). Olex2's `pyl.exe`
  could not import numpy/cctbx standalone, so the Olex2 side was checked
  with a mock of olex/olx/OV and a cctbx stand-in, calling the functions
  through their registered `spy.proto.*` names. The 2026-09-29 state was
  then confirmed in Olex2; the 2026-09-30 additions not yet.
- Check with `compile()`, not just `ast.parse()`: a misplaced `global`
  passed `ast.parse` but broke the module on import.
- The cctbx calls in `cells.setting_transform` follow cctbx's own usage
  (`crystal/reindex.py`: `sgtbx.rt_mx(sgtbx.rot_mx(m))`); the bundled
  sources are under `Olex2-1.5-dev/cctbx/cctbx_sources` (Python only).
