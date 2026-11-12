# Restraints

The tables in the Disorder tools panel (`etc/gui/h3-disorder-tools.htm`): free
variables and restraints, and the **Sanitise** button that tidies free variables
and PART numbers.

## Files

| file | what |
|---|---|
| `__init__.py` | the Olex2 side: `spy.gui.restraints.make_fvar_table`, `make_restraints_table`, `spy.gui.sanitise_FVARs()` and its dialogs |
| `fvar_sanitise.py` | free variables, on the text of a .res/.ins; imports nothing from Olex2. Also the .res helpers (`_cards`, `_tokens`, `_is_atom`, `_read`) |
| `part_sanitise.py` | PART numbers, on the same text; imports nothing from Olex2 |
| `tests/test_fvar_sanitise.py` | tests of both, without Olex2. The folder has no `__init__.py` on purpose: inside the package, the loader would import the real `gui`, which needs Olex2 |

## Sanitise

The button appears next to the free variables when some values match, or when a
disorder pair is not at PART 1/2.  `sanitise_FVARs`:

1. writes the current model to the loaded file (.res or .ins only);
2. asks which free variables to merge (Cancel stops here);
3. asks which PARTs to renumber (Leave PARTs keeps the merges from step 2);
4. copies the file to `olex2/<name>_before_sanitise_<n>.<ext>`, writes the new
   text once and reloads it.  The user then refines.

Free variables come first, because merging a complement changes which part of a
pair is the positive one.  The work is done on the text rather than with macros
so that it can be checked exactly, against SHELXL.

### Free variables

- Variables between 0 and 1 are grouped by `min(v, 1 - v)`; a group spans at most
  `TOL` (0.03).  0.8 and 0.2 are the same variable with the parts swapped.
- There is a tick per variable, not per group.  The ticked ones in a group become
  one, and the lowest ticked number stays.  To merge a group as two separate
  pairs, tick one pair and press Sanitise again for the other.
- A complement swaps the sign of its references: `81` becomes `-21`, `-81` becomes
  `21`.  The merged value is the mean.  The remaining variables are renumbered.
- Variables not used by any atom are removed.
- A variable used outside occupancies (x, y, z, U, DFIX, DANG, CHIV, SUMP, AFIX or
  HFIX sof and U) is never merged and keeps its number.

Similar values do not prove that two disorders are linked: merging says they
move together.  R1 cannot tell, so this is the user's decision.

### PARTs

Atoms bond only within one PART or to PART 0, so disorder pairs can share numbers
as long as no new bonds appear.

- A pair is the two parts linked by one free variable.  The part with the positive
  reference (`21`) gets the odd number, the negative one the even number.
- Each pair takes the lowest set (1/2, then 3/4, ...) where its atoms would bond to
  nothing: non-hydrogen atoms of the same sign must stay further apart than
  r1 + r2 + 0.5 A (SHELXL's CONN default), symmetry equivalents included.
- Left alone, with their numbers reserved: parts with fixed occupancies or several
  variables, parts named in BIND, variables used outside occupancies (three-way
  disorder with SUMP).
- Negative PARTs are left alone and reserve nothing: -1 and 1 are different PARTs.

For speed the button does not measure distances, so it can appear when a clash
blocks every change.  Pressing it then reports that nothing changed.

## Testing

From Wing, `test_run` with
`util/pyUtil/gui/restraints/tests/test_fvar_sanitise.py::<Class>`.

To check a change on a real structure, copy `name.res` to `name.ins` with its
`.hkl` in a scratch folder and run SHELXL on the model before and after.  R1, the
restraint count and the connectivity table in the `.lst` should agree, the
parameters should drop by the number of variables merged.  The `^a` letters in
the connectivity table encode the PART: strip them before comparing.

The dialogs and the reload need Olex2 itself.

## Next

- use esds rather than a fixed tolerance; `olx.xf.rm.FVar` gives only the value
- restore a backup from the GUI
