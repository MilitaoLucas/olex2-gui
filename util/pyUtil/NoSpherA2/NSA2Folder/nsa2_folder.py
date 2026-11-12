"""
NSA2Folder: the NoSpherA2 runs of the loaded structure as chips; a click
makes that run's table the current one.

Self-contained: NoSpherA2 does not import this. Load it with
  py.run basedir()/util/pyUtil/NoSpherA2/NSA2Folder/start.py
It then adds itself to the GUI index (like a plugin) without changing any
file on disk. The reading of the history is in nsa2_runs.py.
"""
from olexFunctions import OlexFunctions
OV = OlexFunctions()

import os
import sys
import olx
import OlexVFS

import nsa2_runs

p_path = os.path.dirname(os.path.abspath(__file__))
p_name = "NSA2Folder"
p_scope = "nsa2folder"
p_htm = "nsa2folder"
p_img = [("NoSpherA2-Runs", 'h1')]

from PluginTools import PluginTools as PT

# the h3 block in NoSpherA2's refine interface: its header image and include
_H3_TEXT = "NoSpherA2-Runs"
# (path quoted as add_tool_to_index does it: an install path may have spaces)
_H3_INCLUDE = (r"""<!-- #include h3-NoSpherA2-Runs "'%s'";gui\blocks\tool-h3-off.htm;"""
               r"""image=h3-nosphera2-runs;onclick=;colspan=1;2; -->""")
# inserted before the interface's closing row
_H3_ANCHOR = r"<!-- #include row_table_off gui\blocks\row_table_off.htm;1; -->"
_IMAGE_NAME = "nsa2folder_grid.png"
_MAP_NAME = "nsa2folder_map"
# the second row: the runs of the series opened
_IMAGE_NAME_RUNS = "nsa2folder_runs.png"
_MAP_NAME_RUNS = "nsa2folder_runs_map"
_GREY = (0x9e, 0x9e, 0x9e)
# chip colour per program
_PROGRAM_COLOUR = {
  "ORCA": (0x2b, 0x5c, 0x9e),
  "pTB": (0x30, 0x71, 0x25),
  "xTB": (0x1f, 0x7a, 0x7a),
  "pySCF": (0xc0, 0x6a, 0x0c),
  "Psi4": (0x8a, 0x4b, 0x0f),
  "Tonto": (0x6d, 0x4c, 0x41),
  "DiSCaMB": (0x6a, 0x3d, 0x9a),
  "Thakkar": (0x60, 0x7d, 0x8b),
  "ELMOdb": (0xad, 0x14, 0x57),
  "SALTED": (0x00, 0x83, 0x8f),
  "Gaussian": (0x45, 0x5a, 0x64),
}


def _report(err, what):
  """Print what failed; re-raise while debugging in Wing."""
  print("NSA2Folder: could not %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise


class NSA2Folder(PT):

  def __init__(self):
    super(NSA2Folder, self).__init__()
    self.p_name = p_name
    self.p_path = p_path
    self.p_scope = p_scope
    self.p_htm = p_htm
    self.p_img = p_img
    self.deal_with_phil(operation='read')
    self.print_version_date()
    self._inject_h3()
    self._cache_key = None
    self._runs = []
    # the series whose runs are shown: the label of its first run
    self._open_series = None
    for f in (self.get_grid_html, self.summary_html, self.use_run, self.refresh, self.toggle_series,
              self.set_columns, self.open_history_folder):
      OV.registerFunction(f, False, self.p_scope)

  # -- the GUI ---------------------------------------------------------------
  def load_ressources(self):
    """A skin change or redraw clears the virtual file system: add the block again."""
    self._inject_h3()

  def _inject_h3(self):
    """Add our h3 block to NoSpherA2's refine interface -- in Olex2's virtual
    file system only: the file on disk is not changed, and without this
    folder (nothing loads this module) the block is not there."""
    if not OV.HasGUI():
      return
    from gui.tools import make_single_gui_image
    make_single_gui_image(_H3_TEXT, img_type='h3')
    olx.FlushFS()
    line = _H3_INCLUDE % os.path.join(self.p_path, self.p_htm + ".htm")
    rel = os.path.join("util", "pyUtil", "NoSpherA2", "NoSpherA2_refine_interface.htm")
    base = OV.BaseDir()
    disk = os.path.join(base, rel)
    try:
      with open(disk, 'r', encoding='utf-8') as f:
        txt = f.read()
    except (IOError, OSError) as err:
      _report(err, "read %s" % disk)
      return
    if _H3_ANCHOR not in txt:
      print("NSA2Folder: NoSpherA2_refine_interface.htm has changed; not added to the GUI")
      return
    txt = txt.replace(_H3_ANCHOR, line + "\n" + _H3_ANCHOR, 1)
    # the interface is included as ..\util\pyUtil\NoSpherA2\... from etc;
    # cover the ways that path may be spelled as a VFS key
    keys = {disk, disk.replace("\\", "/"),
            os.path.join(base, "etc", "..", rel), (base + "/etc/../" + rel).replace("\\", "/")}
    for k in keys:
      OlexVFS.write_to_olex(k, txt, 0)
    self._remove_old_h2()

  @staticmethod
  def _remove_old_h2():
    """The first version added an h2 tool to the Tools index; drop it this session."""
    index = r'%s/etc/gui/blocks/index-tools.htm' % OV.BaseDir()
    t = OlexVFS.read_from_olex(index)
    if not t:
      return
    t = t.decode() if isinstance(t, bytes) else t
    if 'NSA2Folder' in t:
      t = "\n".join(l for l in t.splitlines() if 'NSA2Folder' not in l)
      OlexVFS.write_to_olex(index, t, 0)

  # -- the structure -------------------------------------------------------
  @staticmethod
  def _structure():
    """(folder, name) of the loaded structure, or (None, None)."""
    try:
      d, n = OV.FilePath(), OV.FileName()
    except Exception as err:
      _report(err, "read the structure name")
      return None, None
    if not d or not n or not os.path.isdir(d):
      return None, None
    return d, n

  def _scan(self):
    d, n = self._structure()
    if not d:
      self._runs = []
      return d, n, []
    root = nsa2_runs.history_root(d)
    top = [os.path.join(d, n + e) for e in nsa2_runs.TABLE_ENDINGS]
    key = (d, n,
           os.path.getmtime(root) if os.path.isdir(root) else None,
           tuple((os.path.getmtime(t), os.path.getsize(t)) if os.path.exists(t) else None
                 for t in top))
    if key != self._cache_key:
      self._runs = nsa2_runs.scan(d, n)
      self._cache_key = key
    return d, n, self._runs

  @staticmethod
  def _active(d, n, runs):
    return nsa2_runs.active_index(runs, d, n)

  # -- actions -------------------------------------------------------------
  def refresh(self):
    self._cache_key = None
    OV.UpdateHtml()

  def set_columns(self, value):
    try:
      OV.SetParam('nsa2folder.columns', max(1, min(12, int(value))))
      self.deal_with_phil(operation='save')
    except ValueError:
      print("NSA2Folder: columns must be a number")
    OV.UpdateHtml()

  def open_history_folder(self):
    d, n = self._structure()
    if d:
      root = nsa2_runs.history_root(d)
      olx.Shell(root if os.path.isdir(root) else d)

  def use_run(self, idx, update=True):
    """Make run `idx` (as shown) the current one: its table becomes the
    'Source of tsc' (so the next refinement uses it, without recalculating)
    and NoSpherA2 Options opens on it."""
    d, n, runs = self._scan()
    try:
      run = runs[int(idx)]
    except (ValueError, IndexError):
      print("NSA2Folder: no run %s" % idx)
      return
    try:
      table = nsa2_runs.switch_to(d, n, run)
    except (IOError, OSError) as err:
      _report(err, "switch to %s" % run["label"])
      return
    if not table:
      print("NSA2Folder: %s has no table" % run["label"])
      return
    name = os.path.basename(table)
    try:
      # as choosing the file under 'Source of tsc' does (change_tsc_generator),
      # but keeping where the table came from as its origin
      from utilities import nsa2_adopt_tsc_file, reset_unused_generator_flags
      from variableFunctions import nsa2_set_param
      nsa2_set_param('source', "  " + name)
      reset_unused_generator_flags(name)
      nsa2_adopt_tsc_file(name, origin="%s (history %s)" % (run["program"], run["label"]),
                          normalise=False)
      nsa2_set_param('Calculate', False)
    except Exception as err:
      _report(err, "select %s in NoSpherA2" % name)
    self._cache_key = None
    print("NSA2Folder: now using %s from %s as the source of tsc; refine to use it."
          % (name, run["label"]))
    try:
      # open NoSpherA2 Options on it (closing first rebuilds the block)
      OV.SetItemState("h3-NoSpherA2-extras 2")
      OV.SetItemState("h3-NoSpherA2-extras 1")
    except Exception as err:
      _report(err, "open NoSpherA2 Options")
    self._check_h_model(table)
    if update:
      OV.UpdateHtml()

  @staticmethod
  def _check_h_model(table):
    """Warn when the table was computed for other H positions than the model
    now has (riding vs free H); the refinement would still run against it."""
    try:
      from utilities import nsa2_read_settings_header, nsa2_hydrogen_model,         nsa2_hydrogen_model_difference
      then = (nsa2_read_settings_header(table) or {}).get('H_MODEL')
      if not then:
        return
      diff = nsa2_hydrogen_model_difference(then, nsa2_hydrogen_model())
      if diff:
        print("NSA2Folder: WARNING - this table was made for another hydrogen model: %s. "
              "Recalculate (Update Table on) to match the current model, or refine "
              "against it knowingly." % diff)
    except Exception as err:
      _report(err, "compare the hydrogen model with %s" % os.path.basename(table))

  # -- html ----------------------------------------------------------------
  @staticmethod
  def _int_param(name, default):
    try:
      v = OV.GetParam(name)
      return int(v) if v not in (None, '') else default
    except Exception:
      return default

  def _available_width(self):
    pw = self._int_param('gui.htmlpanelwidth', 400)
    pw -= self._int_param('gui.htmlpanelwidth_margin_adjust', 22)
    pw -= self._int_param('gui.html.table_firstcol_width', 8)
    pw -= 12
    return max(pw, 80)

  def summary_html(self):
    d, n, runs = self._scan()
    if not d:
      return "<font color='grey'>No structure loaded</font>"
    if not runs:
      return "<font color='grey'>No NoSpherA2 runs for %s</font>" % n
    groups = nsa2_runs.group(runs)
    return "<b>%d runs</b> in %d series" % (len(runs), len(groups))

  def toggle_series(self, gi):
    """Switch to the latest run of series `gi` (unless a run of it is in use
    already) and open its runs in the row below; a second click closes them."""
    d, n, runs = self._scan()
    groups = nsa2_runs.group(runs)
    try:
      gi = int(gi)
      key = groups[gi][0]["label"]
    except (ValueError, IndexError):
      print("NSA2Folder: no series %s" % gi)
      return
    first = sum(len(g) for g in groups[:gi])
    active = self._active(d, n, runs)
    if active is None or not first <= active < first + len(groups[gi]):
      self._open_series = key
      self.use_run(first + len(groups[gi]) - 1, update=False)
    else:
      self._open_series = None if self._open_series == key else key
    OV.UpdateHtml()

  @staticmethod
  def _program(r):
    prog = r["program"] + ((" " + r["version"]) if r["program"] == "ORCA" and r["version"] else "")
    if r["parts"] > 1:
      prog += ", %d parts" % r["parts"]
    return prog

  @staticmethod
  def _energy_line(s):
    if s["lowest"]:
      return "lowest E"
    if s["delta_kj"] is not None:
      return "+%.1f kJ/mol" % s["delta_kj"]
    if s["energy"] is not None:
      return "E %.4f" % s["energy"]
    if s["gap"] is not None:
      return "gap %.2f eV" % s["gap"]
    return "no energy"

  def _series_chip(self, s, gi, active_series):
    r = s["run"]
    n = len(s["runs"])
    lines = [self._program(r) + (" x%d" % n if n > 1 else ""),
             " ".join(s["changes"]),
             self._energy_line(s)]
    tip = ["series %d: %s, %d run%s" % (gi + 1, self._program(r), n, "s" if n > 1 else "")]
    first, last = s["runs"][0]["time"], r["time"]
    tip.append(first.strftime("%Y-%m-%d %H:%M") + ("" if first == last else last.strftime(" to %H:%M")))
    if r["method"] or r["basis_name"]:
      tip.append("%s/%s" % (r["method"] or "?", r["basis_name"] or "?"))
    tip.append("charge %s, mult %s" % (r["charge"] or "?", r["multiplicity"] or "?"))
    if r["qmmm"]:
      tip.append("QM/MM")
    if r["relativistic"]:
      tip.append("relativistic")
    if r["solvation"]:
      tip.append("solvent %s" % r["solvation"])
    if s["energy"] is not None:
      tip.append("E = %.6f Eh" % s["energy"])
      if s["delta_kj"] is not None:
        tip.append("lowest of its level of theory" if s["lowest"]
                   else "%.1f kJ/mol above the lowest" % s["delta_kj"])
    elif s["gap"] is not None:
      tip.append("HOMO-LUMO gap %.3f eV (pTB gives no total energy)" % s["gap"])
    tip.append("click: use its latest run and show its runs")
    return dict(colour=_PROGRAM_COLOUR.get(r["program"], _GREY), lines=lines,
                outline=gi == active_series, live=any(x.get("live") for x in s["runs"]),
                opened=s["runs"][0]["label"] == self._open_series,
                mark=s["lowest"], tip=" - ".join(tip),
                href="spy.nsa2folder.toggle_series(%d)" % gi)

  def _run_chip(self, r, k, n, idx, active):
    if r["energy"]:
      third = "E %.4f" % float(r["energy"])
    elif r["gap"]:
      third = "gap %.2f eV" % float(r["gap"])
    else:
      third = "-"
    tip = [r["label"], self._program(r), "run %d of %d" % (k, n)]
    if r["energy"]:
      tip.append("E = %s Eh" % r["energy"])
    if not r["header"]:
      tip.append("no settings in table, from log")
    tip.append("click: make this run's table the source of tsc")
    return dict(colour=_PROGRAM_COLOUR.get(r["program"], _GREY),
                lines=["run %d/%d" % (k, n), r["time"].strftime("%H:%M:%S"), third],
                outline=idx == active, live=bool(r.get("live")), mark=False,
                tip=" - ".join(tip), href="spy.nsa2folder.use_run(%d)" % idx)

  def _font(self, size):
    from PIL import ImageFont
    fonts = os.path.join(OV.BaseDir(), 'etc', 'gui', 'fonts')
    for c in (os.path.join(fonts, 'VeraBd.ttf'), os.path.join(fonts, 'Vera.ttf'),
              'arialbd.ttf', 'arial.ttf'):
      try:
        return ImageFont.truetype(c, size)
      except (IOError, OSError):
        continue
    return ImageFont.load_default()

  @staticmethod
  def _tw(draw, t, font):
    # Olex2 ships Pillow 7: no textbbox there
    if hasattr(draw, 'textbbox'):
      b = draw.textbbox((0, 0), t, font=font)
      return b[2] - b[0]
    return font.getsize(t)[0]

  @staticmethod
  def _rounded(draw, box, r, fill):
    """A filled rounded rectangle; drawn by hand on Pillow 7 (no rounded_rectangle)."""
    x0, y0, x1, y1 = box
    if hasattr(draw, 'rounded_rectangle'):
      draw.rounded_rectangle(box, radius=r, fill=fill)
      return
    d = 2 * r
    draw.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    draw.rectangle([x0, y0 + r, x1, y1 - r], fill=fill)
    draw.pieslice([x0, y0, x0 + d, y0 + d], 180, 270, fill=fill)
    draw.pieslice([x1 - d, y0, x1, y0 + d], 270, 360, fill=fill)
    draw.pieslice([x0, y1 - d, x0 + d, y1], 90, 180, fill=fill)
    draw.pieslice([x1 - d, y1 - d, x1, y1], 0, 90, fill=fill)

  def _fit(self, draw, text, font, w):
    if self._tw(draw, text, font) <= w:
      return text
    while text and self._tw(draw, text + '...', font) > w:
      text = text[:-1]
    return text + '...'

  def _render(self, chips, avail_w, image_name):
    """The chips in reading order, `nsa2folder.columns` per row, saved as
    `image_name`. Returns (w, h, areas)."""
    from PIL import Image, ImageDraw
    cols = max(1, self._int_param('nsa2folder.columns', 4))
    ch = self._int_param('nsa2folder.chip_height', 46)
    gap, margin = 5, 2
    cw = max(36, (avail_w - 2 * margin - (cols - 1) * gap) // cols)
    rows = max(1, (len(chips) + cols - 1) // cols)
    img_h = 2 * margin + rows * ch + (rows - 1) * gap
    try:
      bg = tuple(OV.GetParam('gui.html.table_bg_colour').rgb) + (255,)
    except Exception:
      bg = (255, 255, 255, 255)
    try:
      hl = tuple(OV.GetParam('gui.html.highlight_colour').rgb) + (255,)
    except Exception:
      hl = (0xff, 0xa5, 0x00, 255)
    white = (255, 255, 255, 255)
    im = Image.new('RGBA', (avail_w, max(img_h, ch)), bg)
    draw = ImageDraw.Draw(im)
    font = self._font(10 if cols <= 4 else 8)
    try:
      asc, desc = font.getmetrics()
      lh = asc + desc
    except Exception:
      lh = 12
    areas = []
    for idx, c in enumerate(chips):
      row, col = divmod(idx, cols)
      y = margin + row * (ch + gap)
      x0 = margin + col * (cw + gap)
      x1, y1 = x0 + cw, y + ch
      colour = c["colour"] + (255,)
      if c["outline"]:
        # the outline: the highlight colour, the chip drawn 3 px inside it
        self._rounded(draw, [x0, y, x1, y1], 6, hl)
        self._rounded(draw, [x0 + 3, y + 3, x1 - 3, y1 - 3], 4, colour)
      else:
        self._rounded(draw, [x0, y, x1, y1], 6, colour)
      if c["live"]:
        draw.text((x1 - 10, y + 1), "*", font=font, fill=white)
      if c["mark"]:
        # the lowest energy: a dot in the corner, besides its text
        draw.ellipse([x0 + 5, y + 5, x0 + 11, y + 11], fill=hl)
      if c.get("opened"):
        # its runs are the row below: a notch pointing down at them
        xm = (x0 + x1) // 2
        draw.polygon([(xm - 5, y1 - 6), (xm + 5, y1 - 6), (xm, y1 - 1)], fill=white)
      ty = y + (ch - lh * len(c["lines"])) / 2
      for ln in c["lines"]:
        ln = self._fit(draw, ln, font, cw - 8)
        draw.text((x0 + (cw - self._tw(draw, ln, font)) / 2, ty), ln, font=font, fill=white)
        ty += lh
      areas.append((x0, y, x1, y1, c["href"], c["tip"]))
    OlexVFS.save_image_to_olex(im, image_name, 1)
    return avail_w, max(img_h, ch), areas

  def _image_html(self, chips, avail_w, image_name, map_name):
    w, h, areas = self._render(chips, avail_w, image_name)
    out = ["<zimg border='0' src='%s' usemap='%s' width='%d' height='%d'>"
           % (image_name, map_name, w, h), '<map name="%s">' % map_name]
    for x0, y0, x1, y1, href, tip in areas:
      out.append('<area shape="rect" coords="%d,%d,%d,%d" href="%s" target="%s">'
                 % (x0, y0, x1, y1, href, tip.replace('"', "'")))
    out.append('</map>')
    return out

  def get_grid_html(self):
    d, n, runs = self._scan()
    if not runs:
      return ""
    groups = nsa2_runs.group(runs)
    series = nsa2_runs.describe(groups)
    active = self._active(d, n, runs)
    # the index of each series' first run, as use_run() counts runs
    first, active_series = [], None
    k = 0
    for gi, g in enumerate(groups):
      first.append(k)
      if active is not None and k <= active < k + len(g):
        active_series = gi
      k += len(g)
    avail = self._available_width()
    out = self._image_html([self._series_chip(s, gi, active_series) for gi, s in enumerate(series)],
                           avail, _IMAGE_NAME, _MAP_NAME)
    open_gi = next((gi for gi, g in enumerate(groups) if g[0]["label"] == self._open_series), None)
    if open_gi is not None:
      g = groups[open_gi]
      out.append("<br><b>Series %d</b> <font color='grey'>(click a run to use its table)</font><br>"
                 % (open_gi + 1))
      out += self._image_html([self._run_chip(r, k + 1, len(g), first[open_gi] + k, active)
                               for k, r in enumerate(g)], avail, _IMAGE_NAME_RUNS, _MAP_NAME_RUNS)
    out.append("<br><font color='grey' size='1'>a chip per series of runs with the same settings, "
               "with what changed &#183; dot: lowest energy of its level of theory, the others in kJ/mol "
               "above it &#183; click: use its latest run, show its runs &#183; outlined: in use &#183; *: latest, not yet archived</font>")
    return "\n".join(out)


NSA2Folder_instance = NSA2Folder()
