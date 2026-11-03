"""
gui/htmltools/page.py

Page-level operations for Olex2 GUI tabs:
  - Writing HTML to OlexFS (OV.write_to_olex)
  - Full page skeleton assembly (tool-top / tool-footer)
  - Dynamic section replacement pattern

Usage:
  from gui.htmltools import page

  page.write('moiety-content.htm', html_string)
  page.refresh()   # triggers html.update() equivalent from Python side
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# OlexFS write
# ---------------------------------------------------------------------------

def write(filename: str, content: str) -> bool:
  """
  Write an HTML string to the Olex2 virtual filesystem (OlexFS).
  The file can then be #included by a static .htm tab file.

  Returns True on success, False on failure (logs the error).

  Example:
      page.write('moiety-content.htm', html)
  """
  try:
    from olexFunctions import OV
    OV.write_to_olex(filename, content)
    print(f"[htmltools] Written {filename!r} to OlexFS ({len(content)} chars)")
    return True
  except Exception as e:
    print(f"[htmltools] Could not write {filename!r} to OlexFS: {e}")
    return False


def refresh():
  """
  Trigger an html.update() from the Python side.
  Call this after write() to make the GUI redraw.
  Note: usually the spy call in the GUI does >>html.update() itself;
  this is for cases where Python needs to force a refresh.
  """
  try:
    import olex
    olex.m('html.update()')
  except Exception as e:
    print(f"[htmltools] Could not trigger html.update(): {e}")


# ---------------------------------------------------------------------------
# Full page skeleton
# ---------------------------------------------------------------------------

def tool_page(name: str,
              image: str,
              onclick: str,
              content_file: str,
              scope: str = '',
              footer_colspan: int = 2) -> str:
  """
  Generate a complete Olex2 tool tab skeleton that #includes a
  dynamically-written content file.

  name         : tool name (for #include tag)
  image        : image token e.g. '#image'
  onclick      : onclick token e.g. '#onclick'
  content_file : path to the dynamic content file in OlexFS
  scope        : optional scope string

  The resulting .htm file is static and small -- Python rewrites
  content_file via page.write() to update the tab.

  Example output:
      <!-- #include tool-top gui/blocks/tool-top.htm;... -->
      <!-- #include moiety-content moiety-content.htm;1; -->
      <!-- #include tool-footer gui/blocks/tool-footer.htm;... -->
  """
  tag = content_file.replace('/', '-').replace('.htm', '').replace('.', '-')
  return '\n'.join([
      f"<!-- #include tool-top gui/blocks/tool-top.htm;"
      f"image={image};onclick={onclick};1; -->",
      f"",
      f"<!-- #include {tag} {content_file};1; -->",
      f"",
      f"<!-- #include tool-footer gui/blocks/tool-footer.htm;"
      f"colspan={footer_colspan};1; -->",
  ])


# ---------------------------------------------------------------------------
# Multi-section page builder
# ---------------------------------------------------------------------------

# tool_row() output: the row's content cell, closed right before row_table_off
_TOOL_ROW_CELL = re.compile(
    r"(<td colspan=\d+>\n)(.*?)(\n</td>\n<!-- #include row_table_off)",
    re.DOTALL)
_ABS_FONT_SIZE = re.compile(r"(<font\b[^>]*\bsize=')(\d)(')")


def scale_fonts(html: str, step: int) -> str:
  """
  Shift the text size of tool_row()-based HTML by `step` font sizes:
  each row's content is wrapped in a relative <font size='+n'>, and
  literal absolute sizes (size='2') are shifted too, clamped to 1..7.
  Sizes from Olex2 variables ($GetVar(...), used by input controls)
  are left alone.
  """
  if not step:
    return html
  html = _ABS_FONT_SIZE.sub(
      lambda m: f"{m.group(1)}{min(7, max(1, int(m.group(2)) + step))}{m.group(3)}",
      html)
  return _TOOL_ROW_CELL.sub(
      lambda m: f"{m.group(1)}<font size='{step:+d}'>\n{m.group(2)}\n</font>{m.group(3)}",
      html)


class PageBuilder:
  """
  Accumulates HTML sections and writes them to OlexFS as one file.

  Usage:
      pb = PageBuilder()
      pb.add(he.section_header('Charge Inference'))
      pb.add(he.tool_row(he.charge_table(rows)))
      pb.add(he.tool_row(he.dropdown(...)))
      pb.add(he.tool_row(he.action_button(...)))
      pb.write('moiety-content.htm')
  """

  def __init__(self, font_step: int = 0):
    """
    font_step : enlarge (+n) or shrink (-n) all text on the page by n
                HTML font-size steps. Input controls keep their size.
    """
    self._sections = []
    self._font_step = font_step

  def add(self, html: str) -> 'PageBuilder':
    """Append an HTML section. Returns self for chaining."""
    self._sections.append(html)
    return self

  def build(self) -> str:
    """Return the assembled HTML string."""
    return scale_fonts('\n'.join(self._sections), self._font_step)

  def write(self, filename: str) -> bool:
    """Write to OlexFS and return success bool."""
    return write(filename, self.build())

  def write_and_refresh(self, filename: str) -> bool:
    """Write to OlexFS and trigger html.update()."""
    ok = self.write(filename)
    if ok:
      refresh()
    return ok

  def clear(self) -> 'PageBuilder':
    self._sections = []
    return self