# Flat icon set

Toolbar, action-button and player icons for `user.icon_set = flat`
(switch: Settings > Icons, or `spy.gui.theme.set_icon_set(flat|classic)`;
colours: `spy.gui.theme.designer()`).  The code is in `util/pyUtil/gui/theme`
(see its README).

## Where to make changes

| To change ... | edit | then |
|---|---|---|
| the **drawing** of an icon | `etc/gui/images/src/icons/<name>.svg` | run `gui/theme/build/build_icons.py` |
| **add** an icon | new `<name>.svg` here + a cell in `LAYOUT` in `util/pyUtil/gui/theme/flaticons.py` + `iconIndex` in `PilTools.make_icon_items` | run `gui/theme/build/build_icons.py` |
| which **colour** a part of one icon gets (e.g. delete in red) | the role override in `LAYOUT` (`flaticons.py`), e.g. `'delete': (6, 0, {'acc': 'red'})` | restart / switch icons |
| the **colours** for everybody | `gui.icons` defaults in `gui.params` (None = skin colour) | |
| the colours of **one skin** | an `icons { ... }` block inside `gui { }` in `etc/skins/<skin>.phil` (the designer's *Show as phil* prints it) | change skin |
| hover / pressed look of the action buttons | `STATE_OVERRIDES` in `flaticons.py` | |
| frame round the toolbar icons | `toolbar_border` in `gui/theme/icons.py`; highlight colouring in `PilTools.icon_items` | |

After `build_icons.py`, switch icons in Olex2 (or restart) to see the result.

## Drawing rules

- 24 x 24 `viewBox`; keep about 2 units clear round the edge.  Icons are
  shown at `gui.skin.icon_size`, normally 25 px, so one unit is about a pixel.
- Lines: the default stroke is 1.2 units, round caps and joins (set on `<svg>`).
  Emphasis strokes about 1.8 at most, fine detail no thinner than 0.8.
- Colours only through the four role classes, `f-` for fill and `s-` for stroke:

  | class | role | default colour |
  |---|---|---|
  | `f-ink` / `s-ink` | lines and glyphs | `gui.html.font_colour` |
  | `f-acc` / `s-acc` | the one element that carries the meaning | `gui.html.highlight_colour` |
  | `f-sec` / `s-sec` | a second element: atoms, axes, arrows | `gui.action_colour` |
  | `f-mut` / `s-mut` | quiet fill behind outlines | ink at 25 % |

  No other colours, `opacity` or gradients: the build paints each role in a
  key colour and Olex2 takes them apart again (the build warns if a pixel is
  not a clean mix).  To cut a shape out of another, use a `<mask>` (see
  `info.svg`, `stop.svg`).
- The `<style>` block at the top of each file is only there so the file looks
  right in Inkscape or a browser; the build replaces it.
- Text: `font-family="Segoe UI" font-weight="700"`; it is rendered at build
  time, so the font is needed only on the machine that builds.

## Building

    pip install resvg-py
    python util/pyUtil/gui/theme/build/build_icons.py            # -> ../icons_flat.png
    python util/pyUtil/gui/theme/build/build_icons.py --preview  # also preview.png here, in four skins

`icons_flat.png` is the only file Olex2 reads.  It keeps the cells of the old
`icons.png` (10 x 10 cells of 64 px); `../icons_256_large.png` is the old set
at four times the size, the reference the flat icons were drawn from.
Icons not drawn yet fall back to the classic ones.

Still to draw: `platon`, `dimas`, `olex`, `cctbx` (logos) and `cap`.
