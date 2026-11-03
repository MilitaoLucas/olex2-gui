"""
gui/htmltools/__init__.py

Reusable Olex2 HTML panel generation primitives.

Designed to be used by any Olex2 GUI tab generator, including:
  - gui/moiety  (moiety formula editor)
  - Niolon's plugin-olex2qcrbox (can replace gui_controller + html_templates)
  - Any future gui/ subpackage needing a dynamic HTML panel

Sub-modules
-----------
elements  : HTML primitives (colours, inputs, tables, buttons, layout)
page      : OlexFS write, page skeleton, PageBuilder

Quick start
-----------
    from gui.htmltools import elements as he, page

    colors = he.get_colors()

    pb = page.PageBuilder()
    pb.add(he.section_header('My Section', colors))
    pb.add(he.tool_row(
        he.dropdown('mysel',
                    items_expr='spy.mymod.get_items()',
                    value_expr='spy.mymod.get_current()',
                    onchange='spy.mymod.select(html.GetValue(~name~))>>html.update()')
    ))
    pb.add(he.tool_row(
        he.action_button('mybtn', 'Run', 'spy.mymod.run()>>html.update()', colors=colors)
    ))
    pb.write('mycontent.htm')

Replacing QCrBox's gui_controller + html_templates
---------------------------------------------------
    # Old:
    from qcrbox_plugin.gui_controller import get_olex2_colors, update_parameter_panel
    from qcrbox_plugin.html_templates import generate_string_parameter

    # New:
    from gui.htmltools import elements as he, page
    colors = he.get_colors()
    page.write('qcb-parameters.htm', he.parameter_row('param', he.text_input(...)))
"""

from . import elements
from . import page
from .elements import get_colors
from .page import PageBuilder, write, refresh

__all__ = [
    'elements',
    'page',
    'get_colors',
    'PageBuilder',
    'write',
    'refresh',
]
