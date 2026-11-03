# Olex2 help (the 'i' buttons)

Set up 2026-10-01; replaces the startup walk over all `.md` files, the
`DataDir()/all_help_d.pickle` cache and `help.zip` / `HELP_EN.htm`.

## Writing help

- Help lives in files named **`*.help.md`** — next to the code they
  describe (e.g. `gui/moiety/moiety.help.md`) or in the central tree
  `gui/help/gui/EN/<tab>/`. Plain `.md` files (READMEs, notes) are never help.
- Each top-level heading is one entry. Its **ID** is the heading in upper
  case with spaces as underscores: `# Moiety Formula` → `MOIETY_FORMULA`.
  Sub-headings (`##`) belong to the entry.
- The 'i' button of tool `h3-xyz` shows entry `XYZ`; any other button:
  `$spy.MakeHoverButton('btn-info@Name',"spy.make_help_box -name='Name' -popout='False'")`
  shows `NAME` (`-` → `_`).
- **IDs must be unique** across all help files — the build reports
  duplicates (the later file wins). `# Moiety` already exists (Sorting),
  hence `# Moiety Formula`.
- **Images** sit next to the help file (e.g. an `images/` folder beside it)
  and are referenced relatively: `![0.5 caption](images/x.png)` — the
  optional leading number is the width as a fraction of the help box.
  Fallback: `gui/help/images/`.
- **Inline code is a command**: `` `refine 4` `` becomes a button that runs
  it (sized to its text). Don't use inline code for anything else — CIF
  items, values, paths: use bold or italics.
- **Plugins**: tool names are often generic (Settings, Collections). Pass
  the plugin's scope to the 'i' button (`scope=reportplus` in the
  `tool-h3` / `tool-row-help` include) and the help is looked up as
  `REPORTPLUS_<NAME>` first, then `<NAME>`. Write the headings with the
  prefix: `# ReportPlus Settings 1`.
- Hyphens in a button's name become `_` in the lookup, but a heading keeps
  them: write `# ReportPlus Image` for `help_ext=ReportPlus-Image`.
- Text before the first heading (YAML front matter, `[comment]: < ... >`) is
  ignored. A heading ending in `-target` (e.g. `# start-target`) is raw
  text, not markdown (old format, still used).

- **Generated, numbered rows** (e.g. ReportPlus additional items,
  `help_ext=...Images_%(n)s`): one entry without the number covers them —
  `…_IMAGES_3` falls back to `…_IMAGES`.
- **Legacy help files**: help written before this convention in plain
  `.md` files (AC7, ACED, FragmentDB, NoSpherA2, DrawPlus, SISYPHOS, …) is
  listed in `LEGACY_HELP_FILES` in `help_index.py` and compiled like
  `*.help.md`. Rename a file to `*.help.md` and drop it from the list.
- **Which buttons have no help?**
  `python util/pyUtil/gui/help/help_index.py <BaseDir> --check` lists every
  'i' button in `etc/gui` and `util/pyUtil` (incl. plugin snippets) whose
  help ID has no entry, by GUI file.

## How it is built and loaded

| | |
|---|---|
| `help_index.py` | compiler: `*.help.md` → `help_index.json` (plain Python) |
| `help_index.json` | the compiled help, shipped with Olex2 |
| `__init__.py` | `GetHelp`: lookup, help box |
| `test_help_index.py` | tests: `python -m unittest test_help_index` (here) |

- **Release:** `util/scripts/unleash_olex2.py` runs
  `python help_index.py <working copy>` before gathering files and ships
  `help_index.json` (svn property `olex-update`). `help.zip` is no longer
  built or shipped.
- **Startup:** nothing is read. The index is loaded on the **first** 'i'
  click (a few ms).
- **Plugins / modules** (`util/pyUtil/PluginLib`, `DataDir()/modules`):
  their `*.help.md` are compiled on that first click if not in the shipped
  index, and cached in `DataDir()/help_extra_index.json` until the files
  change. Core help wins over plugin help with the same ID.
- **Development** (debug or developer mode): an entry whose help file
  changed since it was indexed is recompiled when shown; the box shows
  *Edit* / *Recompile* links. New help files: `spy.help.rebuild()` (also
  rewrites `help_index.json` when writable). Without a shipped index the
  help is compiled in memory on the first click.
- Compatibility: `gui.help.gh.git_help(quick, specific)` (ACED, the
  *Recompile* link) — a help file is recompiled; a folder has *all* its
  `.md` files added as help (explicit request).

## Shipping a new help file

A file only ships if it is in svn with the release property, like the
code next to it:

    svn add path/to/thing.help.md
    svn propset olex-update "" path/to/thing.help.md
    svn propset olex-install "" path/to/thing.help.md

Images next to it need the same.
