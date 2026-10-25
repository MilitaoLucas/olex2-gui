# NSA2Folder: development notes

Chips for the NoSpherA2 runs of the loaded structure; a click makes that run's
table the current one. Self-contained: nothing in NoSpherA2 (Florian's code)
imports or knows about this folder. Delete the folder and it is gone.

## Loading

Automatic: `NoSpherA2/__init__.py` imports `nsa2_folder` at startup when this
folder exists (a guarded hook at its end; a failure only prints a message).
That is the only line outside this folder. Delete the folder and the tool is
gone. (In fast-startup mode, OLEX2_FAST_STARTUP, NoSpherA2 and so this tool
load on first use.)

To reload after editing:

    py.run basedir()/util/pyUtil/NoSpherA2/NSA2Folder/start.py

It appears as an h3 block,
"NoSpherA2-Runs", at the bottom of NoSpherA2's own refine panel (only shown
when NoSpherA2 is switched on). To get there, `_inject_h3()` reads
`NoSpherA2_refine_interface.htm` from disk, inserts one `#include` line before
its closing `row_table_off`, and writes the result into Olex2's virtual file
system only. The file on disk is not changed.

Not yet confirmed inside Olex2: under which VFS key the include of
`..\util\pyUtil\NoSpherA2\NoSpherA2_refine_interface.htm` is looked up.
`_inject_h3` writes the text under several spellings of the path. If the
block does not appear, that is the place to look.

(The first version was an h2 tool in the Tools tab via `add_tool_to_index`;
`_remove_old_h2()` takes it out of the index for the running session.)

## Files

- `nsa2_runs.py`: reading the history, grouping, switching. No Olex2 imports.
- `nsa2_folder.py`: the Olex2 part (chips, image map, `spy.nsa2folder.*`).
- `nsa2folder.htm` (the h3 block), `nsa2folder.phil` (columns, chip height).
- `tests/test_nsa2_runs.py`: unittest on a synthetic history in a temp dir.

## How the data hangs together

- `olex2/NoSpherA2_history/<name>_<table mtime>/` holds one wavefunction run:
  `.tscb`, `.wfnlog`, and `.gbw`/`.xtb`/... NoSpherA2 moves the files of the
  previous run there at the start of the next one, so the latest run sits in
  the structure folder until then (the chip marked `*`).
- Disorder: one log and wavefunction per part, `<name>_part<N>.wfnlog/.xtb`,
  and one merged `<name>.tscb`. `belongs()` decides which files are a run's.
- `olex2/Wfn_job/backup_N` is the job folder of run N (input geometry,
  ORCA .inp / pTB .log). Not used here yet.
- One history entry per wavefunction calculation: a refinement with 5
  iterations makes 5 entries. Refinements are told apart by a pause of more
  than 60 s or a change of settings; chips flow across the columns and carry
  `R<refinement>.<cycle>`.
- Settings come from the table's `NSA2_*` header lines, and from the .wfnlog
  when the table has none (older tables) or when the log knows better.
  Method and basis are hidden for programs that do not use them (pTB etc.);
  the header records the GUI's choice regardless.

## Switching (`use_run`)

1. What is in the structure folder is cleared into the history
   (`archive_top`). A run switched to earlier is recognised by its logs and
   wavefunctions (`copy_of`, by name, size and time); its copies are removed.
   Anything else is moved as NoSpherA2 would (folder named by the table's
   mtime).
2. The chosen run's files are copied in with their times kept.
3. `nsa2_adopt_tsc_file(<name>.tscb, normalise=False)` selects the table, and
   `Calculate` ("Update Table") is switched off so the next refinement uses it.

## Pitfalls

- Olex2 ships Pillow 7.1.2: no `ImageDraw.rounded_rectangle`, no `textbbox`.
  `nsa2_folder.py` falls back to drawing by hand / `font.getsize`. A system
  Python has a newer Pillow, so test renders there can hide this.
- Olex2 rewrites a table soon after taking it up (labels to the current
  model; sucrose: 17 s after the switch, size changed). So a copied table is
  not byte-identical to its history original. Runs are matched by their
  logs/wavefunctions instead, and a run NoSpherA2 later re-archives under
  a new name is shown once (`scan` drops repeats of the same logs).
- 2026-10-25: the first switch code ignored `_part<N>` files and left a
  disordered structure (Mo, HECRA workshop) with run 1's table next to the
  latest run's wavefunctions. Put right by hand; `belongs()` fixes the cause.

## Open

- No quality figures yet (R1, wR2, residual density): nothing per run stores
  them. Look at what `.hist6` holds per refinement node.
- Charge is unknown for pTB runs whose table has no header (log has none).
- Wfn_job/backup_N could be linked to its chip (same N, same times).
