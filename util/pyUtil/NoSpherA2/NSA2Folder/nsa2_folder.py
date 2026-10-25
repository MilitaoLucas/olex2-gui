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
    for f in (self.get_grid_html, self.summary_html, self.use_run, self.refresh,
              self.set_columns, self.open_history_folder):
      OV.registerFunction(f, False, self.p_scope)

  # -- the GUI ---------------------------------------------------------------
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

  def use_run(self, idx):
    """Make run `idx` (as shown) the current one and point NoSpherA2 at its
    table, with 'Update Table' off so that the next refinement uses it."""
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
    try:
      from utilities import nsa2_adopt_tsc_file
      from variableFunctions import nsa2_set_param
      nsa2_adopt_tsc_file(os.path.basename(table),
                          origin="%s (history %s)" % (run["program"], run["label"]),
                          normalise=False)
      nsa2_set_param('Calculate', False)
    except Exception as err:
      _report(err, "select %s in NoSpherA2" % os.path.basename(table))
    self._cache_key = None
    print("NSA2Folder: now using %s from %s; 'Update Table' is off, refine to use it."
          % (os.path.basename(table), run["label"]))
    OV.UpdateHtml()

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
    return "<b>%d runs</b> in %d refinements" % (len(runs), len(groups))

  @staticmethod
  def _chip_lines(r, gi, ii):
    prog = r["program"] + ((" " + r["version"]) if r["program"] == "ORCA" and r["version"] else "")
    if r["parts"] > 1:
      prog += ", %d parts" % r["parts"]
    if r["method"] or r["basis_name"]:
      second = "/".join(x for x in (r["method"], r["basis_name"]) if x)
    else:
      second = "QM/MM" if r["qmmm"] else "-"
    third = "R%d.%d  M%s q%s" % (gi, ii, r["multiplicity"] or "?", r["charge"] or "?")
    return [prog, second, third]

  @staticmethod
  def _tip(r, gi, ii, n):
    bits = [r["label"], r["program"] + (" " + r["version"] if r["version"] else "")]
    if r["parts"] > 1:
      bits.append("%d disorder parts" % r["parts"])
    if r["method"] or r["basis_name"]:
      bits.append("%s/%s" % (r["method"] or "?", r["basis_name"] or "?"))
    bits.append("charge %s, mult %s" % (r["charge"] or "?", r["multiplicity"] or "?"))
    if r["qmmm"]:
      bits.append("QM/MM")
    if r["relativistic"]:
      bits.append("relativistic")
    if r["energy"]:
      bits.append("E = %s Eh" % r["energy"])
    bits.append("refinement %d, cycle %d of %d" % (gi, ii, n))
    if not r["header"]:
      bits.append("no settings in table, from log")
    return " - ".join(bits)

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

  def _render(self, groups, active, avail_w):
    """The chips in reading order, `nsa2folder.columns` per row; a chip's
    'R2.3' is refinement 2, cycle 3. Returns (w, h, areas)."""
    from PIL import Image, ImageDraw
    cols = max(1, self._int_param('nsa2folder.columns', 4))
    ch = self._int_param('nsa2folder.chip_height', 46)
    gap, margin = 5, 2
    cw = max(36, (avail_w - 2 * margin - (cols - 1) * gap) // cols)
    n = sum(len(g) for g in groups)
    rows = max(1, (n + cols - 1) // cols)
    img_h = 2 * margin + rows * ch + (rows - 1) * gap
    try:
      bg = tuple(OV.GetParam('gui.html.table_bg_colour').rgb) + (255,)
    except Exception:
      bg = (255, 255, 255, 255)
    try:
      hl = tuple(OV.GetParam('gui.html.highlight_colour').rgb) + (255,)
    except Exception:
      hl = (0xff, 0xa5, 0x00, 255)
    im = Image.new('RGBA', (avail_w, max(img_h, ch)), bg)
    draw = ImageDraw.Draw(im)
    font = self._font(10 if cols <= 4 else 8)
    try:
      asc, desc = font.getmetrics()
      lh = asc + desc
    except Exception:
      lh = 12
    areas = []
    idx = 0
    for gi, g in enumerate(groups):
      for ii, r in enumerate(g):
        row, c = divmod(idx, cols)
        y = margin + row * (ch + gap)
        x0 = margin + c * (cw + gap)
        x1, y1 = x0 + cw, y + ch
        colour = _PROGRAM_COLOUR.get(r["program"], _GREY)
        if idx == active:
          # the outline: the highlight colour, the chip drawn 3 px inside it
          self._rounded(draw, [x0, y, x1, y1], 6, hl)
          self._rounded(draw, [x0 + 3, y + 3, x1 - 3, y1 - 3], 4, colour + (255,))
        else:
          self._rounded(draw, [x0, y, x1, y1], 6, colour + (255,))
        if r.get("live"):
          draw.text((x1 - 10, y + 1), "*", font=font, fill=(255, 255, 255, 255))
        lines = self._chip_lines(r, gi + 1, ii + 1)
        ty = y + (ch - lh * len(lines)) / 2
        for ln in lines:
          ln = self._fit(draw, ln, font, cw - 8)
          draw.text((x0 + (cw - self._tw(draw, ln, font)) / 2, ty), ln,
                    font=font, fill=(255, 255, 255, 255))
          ty += lh
        areas.append((x0, y, x1, y1, idx, self._tip(r, gi + 1, ii + 1, len(g))))
        idx += 1
    OlexVFS.save_image_to_olex(im, _IMAGE_NAME, 1)
    return avail_w, max(img_h, ch), areas

  def get_grid_html(self):
    d, n, runs = self._scan()
    if not runs:
      return ""
    groups = nsa2_runs.group(runs)
    active = self._active(d, n, runs)
    w, h, areas = self._render(groups, active, self._available_width())
    out = ["<zimg border='0' src='%s' usemap='%s' width='%d' height='%d'>"
           % (_IMAGE_NAME, _MAP_NAME, w, h), '<map name="%s">' % _MAP_NAME]
    for x0, y0, x1, y1, idx, tip in areas:
      out.append('<area shape="rect" coords="%d,%d,%d,%d" href="spy.nsa2folder.use_run(%d)" target="%s">'
                 % (x0, y0, x1, y1, idx, tip.replace('"', "'")))
    out.append('</map>')
    out.append("<br><font color='grey' size='1'>R2.3: refinement 2, cycle 3 &#183; "
               "outlined: the table in use &#183; *: latest, not yet archived</font>")
    return "\n".join(out)


NSA2Folder_instance = NSA2Folder()
