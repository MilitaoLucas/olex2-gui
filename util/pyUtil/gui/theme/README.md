# Theme

How Olex2 looks: **skin** (GUI colours, `etc/skins/*.phil`), **icon set**
(classic or flat), **3D style** (`etc/styles/*.glds`) and **scene**
(`etc/styles/*.glsp`).  This package is the shipped part: the icon set, the
overlay and the redraw hooks.  The data stays in `etc/`, where Olex2 loads it
from and the installer ships it.

The **theme designer** is the **ThemeBuilder plugin** (`plugin-ThemeBuilder`, source in
`olex2_dev_bits/plugins/plugin-ThemeBuilder`, flat `themebuilder_*.py` modules, enabled
with `<ThemeBuilder>` in `plugins.xld`, released as a server module). Other developer
tools are in the **DevTools plugin** (`plugin-DevTools`, not shipped): `build/build_icons.py`
and `styles/olex2styles` (the generator of the modern/flexoki skins, styles and scenes,
a git checkout; ThemeBuilder carries its own copy of the generator). Settings shows the
Designer button only when ThemeBuilder is installed (`spy.gui.theme.has_designer()`).

## Files

| file | what |
|---|---|
| `__init__.py` | registers `spy.gui.theme.set_icon_set([classic\|flat])`, `spy.gui.theme.designer()` (opens the plugin's designer, or says it is not installed) and `has_designer()` |
| `overlay.py` | the designer's choices laid over the skin (`base()`: the saved theme last chosen, kept through later changes, for the designer's header), in `DataDir/theme_overlay.json`; `deal_with_gui_phil('load')` adds them after the skin, so they survive restarts and the reload each plugin does. Without the file it adds nothing |
| `background.py` | the 3D background as part of a theme: plain colour (`gl.lm.ClearColor`), gradient (`grad c1 c2 c3 c4`, corners in Olex2's dialog order: bottom left, bottom right, top right, top left) or picture (`grad -p=<file>`). Kept in the overlay (key `background`) because Olex2 stores gradient and picture in its own settings, not in the scene. F2 (`swapbg`) and F4 (`grad -i`) keep working on top. Colours are Olex2 integers with red in the low byte |
| `glcolours.py` | text colours of the 3D view: console (`gui.console_colours.*`: text, program output, errors, exceptions, help) and labels (`gui.label_colours.all`/`atoms`, laid over the 3D style's `Labels.Text`/`PLabels.Text`). `apply()` runs in `gui.skin.SetMaterials`; None keeps Olex2's or the style's own. Info and warning lines are fixed orange in the core (`core_patches/console_info_warning_materials.patch` in the DevTools plugin) |
| `live.py` | keeps skin values current: modules register a function that reads their skin colours (`on_skin_change`); `skin_loaded()` reruns them and redefines the image fonts after every skin load. `survives_vfs_clear` / `restore_vfs()`: start-up VFS work of plugins is done again after `change_skin` clears the VFS |
| `icons.py` | the icon set: switching (`user.icon_set`), painting the flat icons, the VFS images `action-*`, `player-*` |
| `flaticons.py` | the flat sprite format: `LAYOUT` (icon -> cell, role overrides), colour roles, `STATE_OVERRIDES`; PIL only |
| `snumtitle.py` | TRIAL (2026-11-11, may be reverted to the old per-type title colours): the striped file-type band under the sNum title: res/ins `gui.blue`, cif `gui.green`, oxm `gui.orange`, other `gui.grey`, ED alternates with `gui.ed_fg`; per skin `gui.timage.snumtitle.type_colour_*`, `type_band_height` (0 = off), `type_band_period`. The title itself always uses the skin colours |

## Hooks in existing code

- `PyToolLib/PilTools.py`
  - `open_icon_source`: `theme_icons.load()`
  - `icon_items(..., key=)`: `theme_icons.toolbar_cell(key)` replaces the classic cell, and `theme_icons.toolbar_border()` decides the frame
  - end of `make_icon_items`: `theme_icons.make_action_and_player_images()`
  - `make_timage('snumtitle')`: `theme_snumtitle.add_band()` before the final resize (the old per-file-type background colours and the yellow CIF title text are gone)
- `gui/skin/__init__.py` `SetMaterials`: `glcolours.apply()` after the console and label fonts
- `gui/skin/__init__.py` `Skin.change_skin`: `live.skin_loaded()` after the skin's params are loaded, before the images are drawn; `live.restore_vfs()` after they are drawn. `Skin.__init__`: `live.refresh_fonts()`
- `deal_with_gui_phil` in `gui/skin` and `gui/tools`: `overlay.phil_for(skin)` after the skin's phil
- `gui/tools/__init__.py`: `make_single_gui_image` and `add_tool_to_index` are `@survives_vfs_clear`
- `NoSpherA2/NSA2Folder/nsa2_folder.py`: `load_ressources` adds its block again after a clear
- modules that read skin colours at import now register them with `live.on_skin_change`: `gui/__init__.py` (status line), `gui/tools/__init__.py` (battery and more), `gui/restraints`, `gui/tools/GetMaskInfo.py`, `htmlMaker.py`, `PyToolLib/RunPrg.py`. Not done: `misc/Loader.py` (does not import gui, may load before it), `ACED7d` (own repository)
- `PyToolLib/FontInstances.py`: `font_file()` looks in `DataDir/fonts` before `etc/gui/fonts`; `add_font_files()` makes every font file there usable by its name
- `PyToolLib/Analysis.py`: legend and key text use `gui.graph.grey` / `light_grey` (same values as before); other literal colours have no matching param yet
- `initpy_funcs.import_gui`: `import gui.theme`
- `gui/images/__init__.py` and `etc/gui/h3-crystal_image.htm` use the VFS names `action-<which>_<state>.png` and `player-<which>.png`
- `etc/gui/settings.htm`: the Icons row
- Parameters: `user.icon_set` (`params.phil`, user scope, because a skin change resets the gui scope); `gui.icons.*` colours (`gui.params`, None = skin colour; skins may set them)

## Generated files

The skins and styles that `styles/olex2styles/build_modern.py` (DevTools plugin) writes, and `icons_flat.png`,
are generated: edit the generator and rerun it.  Never edit the output by hand,
because the next run overwrites it.  Drawing rules for the icons are in
`etc/gui/images/src/icons/README.md`.

## Not reachable from Python

Reported by the olex2styles author; these are in the C++ / wxWidgets code:
bitmap (3D overlay) text is lit, so dark skins need emission colours; Q-peak
colours are fixed in `xatom.cpp`; read-only combo boxes, checkbox squares and
slider thumbs are drawn by the operating system.  Not traced yet: `skin ...`
sometimes hides the results box until a restart.

## Next

- previews on the Skin, Style and Scene tabs
- the Style dropdown in Settings (`user.atoms.style`, `load style -c`) is a separate mechanism from `user.def_style`; unify them
