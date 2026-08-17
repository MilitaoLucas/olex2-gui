# Olex2 pipeline tests

End-to-end tests that run **inside Olex2**, with nothing stubbed. The suite in
the parent directory uses dummy `olx`/`olex` modules, so it can only reach code
that never touches a structure. Everything that matters - loading a model,
running a macro, solving, refining, generating form factors - needs the real
program behind it.

These run in `olex2c`, which is Olex2 without a window, so `olx`, `spy` and the
macro layer are genuine.

## Running

```
set PYTHONHOME=C:\Python38
set OLEX2_TEST_GROUPS=macros,refine,solve,nosphera2
olex2c.exe -b <rundir> pipeline.olx
```

where `pipeline.olx` is one line:

```
py.Run '<rundir>/util/pyUtil/regression/olex2_pipeline_tests/run_pipeline.py'
```

| variable | |
|---|---|
| `OLEX2_TEST_GROUPS` | `macros`, `refine`, `solve`, `nosphera2`; default is the first three |
| `OLEX2_TEST_FULL` | `1` to include the quantum backends, which are minutes to hours |
| `OLEX2_TEST_BACKENDS` | comma-separated NoSpherA2 backends to run, e.g. `ORCA`; default is all |
| `OLEX2_TEST_OUT` | where to write the result table |

`py.Run` takes a script path and no arguments of its own, which is why the
selection is by environment variable. It also runs the file without setting
`__file__`, so the entry point derives its own location from `olx.BaseDir()`.

## What is covered

**macros** - load, cell, space group, atom count and labels, `Ins`, `AddIns`
and `DelIns`, `HKLSrc`, a file write/read round trip, a phil get/set round
trip, the atom reference grammar, `kill $H` followed by `HAdd`, `CifCreate`,
and the solvent mask.

**refine** - `olex2.refine` on four samples against an R1 ceiling, CGLS-J
against Gauss-Newton on the same structure, a restrained model (THPP, which
carries a RIGU), and SHELXL.

**instructions** - `afix 0 $H` removes the 38 riding-group AFIX lines, `chiv`,
`split` (parts 0/1/2), `resi`, `fixunit` recounts UNIT, `himp`, and a model
carrying them still refines.

**validation** - a model broken in a way a user can produce by hand must fail
with a *diagnosis*, not with an index. See "Failing usefully" below.

**formats** - write and read back through `.res`, `.ins`, `.xyz`, `.mol`,
`.cif` and `.pdb`, requiring the atoms and the cell to survive; `.p4p` and
`.crs` are cell files and are checked for the cell; `.mas` refuses to be
written and must say so rather than report success and write nothing.

**geometry** - `Crd` and `CCrd` cross-checked against each other through the
cell metric (the same distance computed both ways has to agree), `htab` finds
hydrogen bonds and writes them, `addbond`/`delbond` write `BIND`/`FREE`, `VVol`
reports a volume inside the cell, and the reporting calls are accepted.

**symmetry** - the group is reported, `changesg P1` drops it, `standardise`
moves atoms without losing any, `addse` adds an element (P2(1) -> P2(1)/m), the
group can be changed and changed back with the refinement returning to the same
R1, and the symmetry queries are accepted.

**hkl** - `HKLF` reports the format, `hklmerge` reduces 13368 reflections to
2578 unique, `omit`/`shel` reach the written ins, `wilson` writes its csv,
`hklbrush` writes a brushed file, and the merged data still refines.

**cif** - `CifCreate` writes a structure that can be described, ACTA makes the
refinement write an fcf with reflections in it, `CifMerge` leaves the cif
readable, and the cif's `_refine_ls_R_factor_gt` matches the refinement that
produced it.

**solve** - `olex2.solve` charge flipping, SHELXT intrinsic phasing, SHELXS
direct methods, SHELXD dual space.

**nosphera2** - per backend: refine spherically, generate a tsc, refine again,
and require the aspherical R1 to have *changed* and not to be worse. DiscaMB
runs every time; the quantum backends are behind `OLEX2_TEST_FULL`.

The sample is sucrose, deliberately: it is neutral and closed shell, which is
what the charge 0 and multiplicity 1 the tests set actually describe. The
sample named `water` is a Mn complex, and its SCF diverged within five cycles
under those settings.

A disordered structure (THPP) gets its own case: every part's wavefunction goes
to **one** `cuqct_tsc` call, which becomes `-mtc`, and one table covers them
all. The case asserts that no `*_part_*.tsc` were left behind for a `-merge`
afterwards. It needs a wavefunction backend - `-mtc` takes wavefunctions, and
discamb emits finished tables instead, so discamb on a disordered structure has
nothing to hand `-mtc` and merges by construction.

## How these tests avoid passing when nothing happened

This is the part worth reading before adding a case. Three of the original
tests passed while testing nothing, and each failure mode is now closed:

- **A macro that does not exist.** `spy.solve.do_solve` is not a thing - the
  entry point is `spy.RunSolutionPrg()`. Calling it left the loaded model in
  place and all three solution tests reported it as a solution, in 0.0
  seconds. `olex.m` returns 0 for a missing macro, but *also* for `AddIns` and
  `sel`, which return 0 having worked - so the return value is not a usable
  signal. **Assert on the effect instead**: the solve tests now require the
  coordinates to have changed.
- **A stale value read back.** SHELXL "passed" in 0.1s with R1 0.0278, which
  was the number `olex2.refine` had produced a moment earlier. `clear_r1()` is
  called before every refinement so a run that does not happen has no R1 to
  find, and the same trick exposed CGLS: it had never run, and reported
  Gauss-Newton's R1 as its own.
- **A wrong invariant.** The round trip asserted on `GetAtomCount`, which
  includes Q peaks; writing a file correctly drops them, so 50 in and 45 out
  is right. It compares real atoms now.
- **A result that was produced but never used.** DiscaMB wrote a tsc, the
  refinement ran, and R1 came out at exactly the spherical value - because the
  label resync had read the wrong header line and the refinement carried on
  spherically. "Not worse than spherical" passes that happily. The tests now
  require the aspherical R1 to *differ*, which is the only thing that
  distinguishes a table that was applied from one that was written and
  ignored.
- **A test inheriting the previous test's structure.** `suite.sample()` copied
  once and reused, so the NoSpherA2 spherical baseline was the previous
  backend's aspherical result, tsc and refined res included. It re-copies per
  call now.
- **Counting atoms that are already gone.** `GetAtomCount` keeps counting a
  deleted atom, so sucrose reported 22 hydrogens before *and* after
  `kill $H`, then 44 after `HAdd` placed 22 fresh ones beside the dead ones.
  Use `deleted(i)`, which is `olx.xf.au.IsAtomDeleted`.
- **A call that failed without raising.** Most `olx.<Name>()` entries are
  macros behind a function name: they log and return a status, 1 done and 0
  refused. `FitCHN`, `TestHKLF`, `LS` and `SGS` were being called without their
  required argument, logging `is provided with 0 arguments`, and counted as
  answered - nothing raised, and nobody read the 0. `LastError()` does not help
  here; it stays empty. **Read the return value**: an `int` 0 is a refusal.
- **A "read-only" call that was not.** `SGE` sat in the api sweep's symmetry
  list. It is not an information call: it transformed sucrose from 45 atoms to
  26 and wrote a fresh ins, hkl and cif, so everything after it in that area
  ran against a structure the sweep had silently replaced. Before adding a name
  to the sweep, check that it only reports.
- **Expecting the wrong thing and blaming Olex2.** `changesg P1` does not
  expand the cell contents - the asymmetric unit stays at 45 atoms, so P1 holds
  half of what P2(1) held and R1 goes 0.028 -> 0.41. That is correct, and the
  first version of the case called it a failure. The invariant worth asserting
  is reversibility: change the group and change it back, and the refinement
  returns to the same R1.
- **Asserting against the wrong file.** The refinement writes a ~120 kB cif
  with the `_refine_ls_*` block; `CifCreate` writes an ~8 kB structure-only
  one. Calling `CifCreate` after refining overwrote the first with the second,
  and the test concluded Olex2 reports no R factor. Also, the item is
  `_space_group_name_H-M_alt` - the `_symmetry_`-prefixed name is superseded
  and Olex2 does not write it.

A backend that is not installed is a **SKIP with the reason named**, never a
silent omission - "no ORCA here" and "ORCA works" have to look different.

## Failing usefully

A wrong model failing is fine. A wrong model failing with `Index out of range`
is not, and that was the state.

`resi TOL 1 C23` puts one carbon into a residue while the hydrogens riding on
it stay outside. The riding-ADP constraint then refers to a scatterer index
that no longer exists, and `iotbx/builders_depending_on_smtbx.py` indexed the
array directly:

```
olexFunctions.SilentException: Index out of range.
```

naming neither RESI, nor an atom, nor a constraint. `add_u_iso_proportional_to_pivot_u_eq`
and `add_occupancy_pair_affine_constraint` now check the index first and say:

```
A riding-ADP constraint's pivot refers to scatterer 44, but the structure has
23 (O10, O1, O20, O23, H23, O21, ...). A constraint or a restraint is left over
from a different atom ordering - check any AFIX group split across a RESI, or
an instruction naming an atom that has been renamed or deleted.
```

The `validation` group asserts this: it breaks the model on purpose and
requires the failure to name something actionable. Its control case refines the
same untouched sample, so "everything fails" cannot pass.

**Adding a case here is the way to handle any similar trap.** Break the model
the way a user would, and assert on the *message*, not on the failure.

## Backend names are not constants

None of the NoSpherA2 source names can be hardcoded, and both obvious guesses
were wrong:

- discamb is compared against the *value* of `user.NoSpherA2.discamb_exe`
  (`discambMATTS2tsc` here), not against any label.
- ORCA carries its version, from what `orca -v` reported at startup:
  `ORCA 6.1` here, `ORCA 5.0` or bare `ORCA` elsewhere.

Both fell past every branch into `Wfn_Job`, which refused them as wavefunction
programs. So the tests resolve the name from `spy.NoSpherA2.getwfn_softwares()`
- the list the settings dropdown is built from. No entry means the backend is
not offered here, which is a skip with the offered list printed.

`charge` and `multiplicity` have no usable defaults either: multiplicity ships
as `0`, which is even, and `launch` refuses an even multiplicity with an even
electron count. Only the settings page ever fills them in, so a headless caller
must.

## Running olex2c from a script

Do not pipe olex2c's stdout through a shell that might be killed. A QM job
prints continuously through the parent, and if whatever is reading the pipe
goes away, olex2c blocks on the write and hangs indefinitely - which looks
exactly like a crash in the backend. Redirect straight to a file
(`Start-Process -RedirectStandardOutput`), and give the run its own process so
a harness timeout does not take the reader with it.

## The one case that is red on a clean checkout

**pTB fails**, and it is meant to:

```
FAIL  nsa2  tsc and refine: pTB  - pTB finished, but its wavefunction is empty
```

pTB runs to completion and hands back a wavefunction with zero MO occupations,
so no table can be made from it. NoSpherA2 detects this correctly; the defect
is in the backend, not in Olex2. It is left failing rather than skipped because
it is a real, reportable problem with an installed program - a skip would say
"not installed", which is untrue and would hide it.

Everything else is green: **93 passed, 1 failed, 10 skipped**.

## Known gaps, as of 17 Aug 2026

- **SALTED is not offered outside debug mode** (`getwfn_softwares` adds it only
  when `OV.IsDebugging()`), and no trained model is installed here. Skipped
  with both reasons named.
- **Tonto** is offered and has no branch in `Wfn_Job`; untested here.
- `CifMerge` after a refinement fails headlessly with
  `module 'gui' has no attribute 'report'`. Caught and reported by the
  refinement, and it does not affect R1, but it is a GUI-only path.

## Adding a case

```python
def register(suite):
  suite.run("group", "what it checks", t_my_case, suite)

def t_my_case(suite):
  folder = suite.sample("sucrose")   # a private copy, see below
  ...
  return "what it found"             # shown in the table
```

Raise `SkipTest` for "cannot run here", any other exception for a failure, and
return a short string saying what was actually measured. `suite.sample()`
copies the structure to scratch first: **a refinement overwrites its own
res**, so running against the samples in place compares each run with the
previous run's output rather than with the structure as committed.
