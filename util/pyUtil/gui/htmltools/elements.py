"""
gui/htmltools/elements.py

Reusable HTML primitives for Olex2 GUI tab generation.

Covers:
  - Olex2 colour scheme access
  - Layout blocks (tool-row wrappers)
  - Input controls (text, number, checkbox, file, dropdown)
  - Buttons (hover, action)
  - Tables (data tables, charge tables)
  - Help file wrapping
  - Writing to OlexFS

Design principles:
  - Every function returns a plain string — no side effects
  - Olex2 dependencies (olx, OV) are imported lazily and always
    inside try/except so modules load cleanly outside Olex2
  - Colours default to Olex2 dark theme if not available
  - All spy call strings are plain strings — callers compose them

Usage:
  from gui.htmltools import elements as he
  from gui.htmltools import page

  colors = he.get_colors()
  html = page.tool_row(he.dropdown('mysel', items, onchange='spy.foo(html.GetValue(~name~))>>html.update()'))
  page.write('myfile.htm', html)
"""

from __future__ import annotations
from textwrap import dedent


# ---------------------------------------------------------------------------
# Colour scheme
# ---------------------------------------------------------------------------

_DARK_DEFAULTS = {
    'bg':          '#222222',
    'font':        '#ffffff',
    'table_bg':    '#222222',
    'highlight':   '#ff8888',
    'link':        '#ababff',
    'font_name':   'Bahnschrift',
    'error':       '#ff6666',
    'secondary':   '#aaaaaa',
    'green':       '#88cc88',
    'amber':       '#ffcc66',
    'red':         '#ff6666',
}


def _hex(value) -> str:
    """Extract hex string from Olex2 colour object or plain string."""
    if hasattr(value, 'hexadecimal'):
        return value.hexadecimal
    return str(value)


def get_colors() -> dict:
    """
    Return Olex2 colour scheme as a plain dict.
    Keys: bg, font, table_bg, highlight, link, font_name,
          error, secondary, green, amber, red.
    Falls back to dark theme defaults outside Olex2.
    """
    try:
        import olx
        from olexFunctions import OV
        return {
            'bg':        olx.GetVar('HtmlBgColour',          _DARK_DEFAULTS['bg']),
            'font':      olx.GetVar('HtmlFontColour',        _DARK_DEFAULTS['font']),
            'table_bg':  olx.GetVar('HtmlTableBgColour',     _DARK_DEFAULTS['table_bg']),
            'highlight': olx.GetVar('HtmlHighlightColour',   _DARK_DEFAULTS['highlight']),
            'link':      olx.GetVar('HtmlLinkColour',        _DARK_DEFAULTS['link']),
            'font_name': olx.GetVar('HtmlFontName',          _DARK_DEFAULTS['font_name']),
            'error':     _hex(OV.GetParam('gui.red',         _DARK_DEFAULTS['error'])),
            'secondary': _hex(OV.GetParam('gui.grey',        _DARK_DEFAULTS['secondary'])),
            'green':     _hex(OV.GetParam('gui.green',       _DARK_DEFAULTS['green'])),
            'amber':     _hex(OV.GetParam('gui.orange',      _DARK_DEFAULTS['amber'])),
            'red':       _hex(OV.GetParam('gui.red',         _DARK_DEFAULTS['red'])),
        }
    except Exception:
        return dict(_DARK_DEFAULTS)


# ---------------------------------------------------------------------------
# Layout blocks
# ---------------------------------------------------------------------------

def tool_row(content: str, colspan: int = 3) -> str:
    """Wrap content in an Olex2 tool-row / row_table_off pair."""
    return (
        f"<!-- #include tool-row gui/blocks/tool-row.htm;1; -->\n"
        f"<td colspan={colspan}>\n"
        f"{content}\n"
        f"</td>\n"
        f"<!-- #include row_table_off gui/blocks/row_table_off.htm;1; -->\n"
    )


def tool_row_two_col(left: str, right: str,
                     left_width: str = '30%',
                     right_width: str = '70%') -> str:
    """Wrap content in a two-column tool-row."""
    return (
        f"<!-- #include tool-row gui/blocks/tool-row.htm;1; -->\n"
        f"<td width='{left_width}'>{left}</td>\n"
        f"<td width='{right_width}'>{right}</td>\n"
        f"<!-- #include row_table_off gui/blocks/row_table_off.htm;1; -->\n"
    )


def section_header(title: str, colors: dict = None) -> str:
    """A bold section header row."""
    c = colors or get_colors()
    return tool_row(
        f"<font color='{c['highlight']}' size='3'><b>{title}</b></font>"
    )


def divider() -> str:
    """A horizontal rule row."""
    return tool_row("<hr width='100%'>")


# ---------------------------------------------------------------------------
# Text / font helpers
# ---------------------------------------------------------------------------

def colored(text: str, color: str) -> str:
    return f"<font color='{color}'>{text}</font>"


def bold(text: str) -> str:
    return f"<b>{text}</b>"


def small(text: str) -> str:
    return f"<font size='2'>{text}</font>"


# ---------------------------------------------------------------------------
# Input controls
# ---------------------------------------------------------------------------

def _font_wrap(content: str) -> str:
    return f"<font size=\"$GetVar('HtmlFontSizeControls')\">{content}</font>"


def text_input(name: str, value_expr: str, onchange: str,
               width: str = '100%', readonly: bool = False,
               on_commit: bool = False) -> str:
    """
    Single-line text input.

    value_expr : a spy call or literal, e.g. "spy.foo.get_val()" or "'hello'"
    onchange   : spy call string, e.g. "spy.foo.set_val(html.GetValue(~name~))"
    on_commit  : if True, run `onchange` only when the entry is confirmed
                 (Enter or leaving the box) instead of on every keystroke
    """
    ro = 'readonly' if readonly else ''
    if on_commit:
        events = f"onreturn='{onchange}'\n               onleave='{onchange}'"
    else:
        events = f"onchange='{onchange}'"
    return _font_wrap(dedent(f"""
        <input type='text' name='{name}' width='{width}'
               value='{value_expr}'
               {events}
               {ro}>
    """).strip())


def number_input(name: str, value_expr: str, onchange: str,
                 width: str = '100%') -> str:
    """Numeric text input — same as text_input but semantically distinct."""
    return text_input(name, value_expr, onchange, width)


def checkbox(name: str, checked_expr: str, onclick: str) -> str:
    """
    Checkbox input.

    checked_expr : spy call returning true/false, or 'true'/'false'
    onclick      : spy call string
    """
    return _font_wrap(dedent(f"""
        <input type='checkbox' name='{name}'
               checked='{checked_expr}'
               onclick='{onclick}'>
    """).strip())


def file_input(name: str, command_id, param_name: str,
               status_expr: str, browse_spy: str,
               width_status: str = '80%',
               width_browse: str = '20%') -> str:
    """
    File parameter: status label + Browse button.

    status_expr : spy call for current file status display
    browse_spy  : full spy call for the browse action (including FileOpen)
    """
    return _font_wrap(dedent(f"""
        <table width='100%' cellpadding='0' cellspacing='0' border='0'>
          <tr>
            <td width='{width_status}' name='{name}_status'>
              ${status_expr}
            </td>
            <td width='{width_browse}' align='right'>
              <a href='{browse_spy}>>html.Update()'>
                <button>Browse...</button>
              </a>
            </td>
          </tr>
        </table>
    """).strip())


def dropdown(name: str,
             items_expr: str,
             value_expr: str,
             onchange: str,
             width: str = '100%',
             readonly: bool = True) -> str:
    """
    Dropdown (input-combo snippet).

    items_expr : spy call returning semicolon-separated list, or literal
    value_expr : spy call or literal for current value
    onchange   : spy call, typically ends with >>html.update()

    Example:
        dropdown('mysel',
                 items_expr='spy.gui.moiety.candidate_list()',
                 value_expr='spy.gui.moiety.current_candidate()',
                 onchange='spy.gui.moiety.select(html.GetValue(~name~))>>html.update()')
    """
    ro = 'true' if readonly else 'false'
    return dedent(f"""
        $+
        html.Snippet("gui/snippets/input-combo",
          "name={name}",
          "width={width}",
          "items='{items_expr}'",
          "value={value_expr}",
          "onchange={onchange}",
          "readonly={ro}")
        $-
    """).strip()


def action_button(name: str, label: str, onclick: str,
                  width: str = '100%',
                  color: str = None,
                  enabled: bool = True,
                  colors: dict = None) -> str:
    """
    Full-width action button (input-button snippet).

    onclick : spy call string, e.g. 'spy.foo.run()>>html.update()'
    color   : hex background colour; defaults to highlight colour
    """
    c = colors or get_colors()
    bg = color or c['highlight']
    en = 'true' if enabled else 'false'
    return dedent(f"""
        $+
        html.Snippet("gui/snippets/input-button",
          "name={name}",
          "value={label}",
          "onclick={onclick}",
          "width={width}",
          "bgcolor={bg}",
          "enabled={en}")
        $-
    """).strip()


def hover_button(icon: str, onclick: str) -> str:
    """Small hover/icon button, e.g. for reload or info."""
    return f"$spy.MakeHoverButton('{icon}','{onclick}')"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def table(rows: list[list[str]],
          headers: list[str] = None,
          col_widths: list[str] = None,
          colors: dict = None,
          border: int = 0) -> str:
    """
    Generate an HTML table.

    rows       : list of lists of cell content strings
    headers    : optional list of header strings
    col_widths : optional list of width strings e.g. ['10%','60%','15%','15%']
    """
    c = colors or get_colors()
    parts = [f"<table width='100%' border='{border}' cellpadding='2' cellspacing='1' "
             f"bgcolor='{c['table_bg']}'>"]

    if headers:
        parts.append("<tr>")
        for i, h in enumerate(headers):
            w = f" width='{col_widths[i]}'" if col_widths and i < len(col_widths) else ''
            parts.append(
                f"<td{w}><font color='{c['secondary']}'>"
                f"<b><small>{h}</small></b></font></td>"
            )
        parts.append("</tr>")

    for row in rows:
        parts.append("<tr>")
        for i, cell in enumerate(row):
            w = f" width='{col_widths[i]}'" if col_widths and i < len(col_widths) else ''
            parts.append(f"<td{w}>{cell}</td>")
        parts.append("</tr>")

    parts.append("</table>")
    return '\n'.join(parts)


def charge_text(charge) -> str:
    """Chemist's notation: 2+, 1-, 0; '?' for unknown (None)."""
    if charge is None:
        return '?'
    if charge == 0:
        return '0'
    return f"{abs(charge)}{'+' if charge > 0 else '-'}"


def signed(n) -> str:
    """+2, -1, -0.5, 0 -- no sign on zero."""
    return f"{n:+g}" if n else '0'


def charge_table(rows: list[dict], colors: dict = None,
                 edit_spy: str = None) -> str:
    """
    Specialised table for charge inference display.

    Each row dict:
        mult        : int multiplicity (1 = blank)
        formula     : str formula string
        charge      : int or None
        confidence  : str confidence key
        warn        : str optional warning suffix

    Columns: n, Formula, Total (n x charge), Charge, Confidence.

    edit_spy : optional spy function name, e.g. 'spy.gui.moiety.set_charge'.
               When given, each charge cell is a (narrow) text input that
               calls <edit_spy>(row_index, value)>>html.update() on Enter
               or when the box is left.

    Confidence -> colour mapping:
        lookup           -> green
        balance          -> font (normal)
        assumed_neutral  -> secondary (grey)
        element_ambiguous -> amber
        element_guess    -> font
        balance_suspect  -> red
        unknown          -> red
        parsed           -> font
        user             -> font
        user_lookup      -> green
    """
    c = colors or get_colors()

    _conf_color = {
        'lookup':           c['green'],
        'balance':          c['font'],
        'assumed_neutral':  c['secondary'],
        'element_ambiguous': c['amber'],
        'element_guess':    c['font'],
        'balance_suspect':  c['red'],
        'unknown':          c['red'],
        'parsed':           c['font'],
        'user':             c['font'],
        'user_lookup':      c['green'],
    }

    _conf_label = {
        'lookup':           'lookup',
        'balance':          'balance',
        'assumed_neutral':  'assumed neutral',
        'element_ambiguous': 'ambiguous!',
        'element_guess':    'element',
        'balance_suspect':  'SUSPECT',
        'unknown':          '???',
        'parsed':           'from string',
        'user':             'user',
        'user_lookup':      'user lookup',
    }

    table_rows = []
    for i, r in enumerate(rows):
        mult = str(r['mult']) if r['mult'] > 1 else ''
        formula = r['formula']
        charge = r.get('charge')
        conf = r.get('confidence', 'unknown')
        warn = r.get('warn', '')
        occ = r.get('occupancy', 1.0)

        if charge is None:
            charge_str = total_str = colored('?', c['red'])
        else:
            q_color = c['font'] if charge == 0 else _conf_color.get(conf, c['font'])
            charge_str = colored(charge_text(charge), q_color)
            total_str = colored(charge_text(r['mult'] * charge), q_color)

        if edit_spy:
            name = f'moiety_charge_{i}'
            charge_str = text_input(
                name, charge_text(charge),
                f'{edit_spy}({i},html.GetValue({name}))>>html.update()',
                width='30', on_commit=True)

        conf_color = _conf_color.get(conf, c['font'])
        conf_label = _conf_label.get(conf, conf)
        conf_cell = colored(small(conf_label), conf_color)

        if occ < 1.0:
            formula_cell = f"{formula} <font color='{c['amber']}'><small>({occ:.3f})</small></font>"
        else:
            formula_cell = formula

        warn_cell = colored(small(f' ← {warn}'), c['amber']) if warn else ''

        table_rows.append([
            colored(mult, c['secondary']),
            formula_cell,
            total_str,
            charge_str,
            conf_cell + warn_cell,
        ])

    return table(
        table_rows,
        headers=['n', 'Formula', 'Total', 'Charge', 'Confidence'],
        col_widths=['5%', '40%', '12%', '13%', '30%'],
        colors=c,
    )


def balance_equation(frags: list[dict], colors: dict = None) -> str:
    """
    Render a balance equation like:
      (Co 3+)  +  C8H14N4O4 ?  +  C5H5N 0  +  C3H7 ?
         +3    +       ?        +      0     +    ?    = +3 + ? from 2 unknowns

    Each frag dict: mult, formula, charge (int or None). mult may be
    fractional (e.g. 1.5(H3 O) when Z' > 1).
    """
    c = colors or get_colors()
    parts_top = []
    parts_bot = []

    for f in frags:
        sym = f['formula']
        mult = f['mult']
        if mult != 1:
            sym = f"{mult:g}({sym})"

        charge = f.get('charge')
        if charge is None:
            charge_str = colored('?', c['red'])
            total_str  = colored('?', c['red'])
        else:
            charge_str = colored(signed(charge), c['green'] if charge == 0 else c['font'])
            total = round(mult * charge, 3)
            total_str = colored(signed(total), c['green'] if total == 0 else c['font'])

        parts_top.append(f"{sym} {charge_str}")
        parts_bot.append(total_str)

    sep = f"&nbsp;<font color='{c['secondary']}'>+</font>&nbsp;"
    top_line = sep.join(parts_top)
    bot_line = sep.join(parts_bot)

    known = round(sum(f['mult'] * f['charge'] for f in frags
                      if f.get('charge') is not None), 3)
    n_unk = sum(1 for f in frags if f.get('charge') is None)

    if n_unk == 0 and known == 0:
        result = colored('= 0 ✓', c['green'])
    elif n_unk > 0:
        sign = '+' if known > 0 else ''
        result = colored(f"= {sign}{known:g} + ? from {n_unk} unknown(s)", c['amber'])
    else:
        sign = '+' if known > 0 else ''
        result = colored(f"= {sign}{known:g} ✗", c['red'])

    return (
        f"<table width='100%' border='0' cellpadding='2'>"
        f"<tr><td>{top_line}&nbsp;&nbsp;{result}</td></tr>"
        f"<tr><td><font color='{c['secondary']}'><small>{bot_line}</small></font></td></tr>"
        f"</table>"
    )


# ---------------------------------------------------------------------------
# Page / help structure
# ---------------------------------------------------------------------------

def help_page(content: str, colors: dict = None) -> str:
    """
    Wrap content in the standard Olex2 help file HTML structure.
    Equivalent to QCrBox's generate_help_file_html().
    """
    c = colors or get_colors()
    return dedent(f"""
        <body link="{c['link']}" bgcolor='{c['bg']}'>
        <font size='3' color='{c['font']}' face="{c['font_name']}">
        <table bgcolor='{c['table_bg']}' width='100%' border='0' cellspacing='5' cellpadding='5'>
        <tr bgcolor='{c['table_bg']}'>
        <td bgcolor='{c['table_bg']}'>
        {content}
        </td>
        </tr>
        </table>
        </font>
        </body>
    """).strip()


def parameter_row(label: str, control: str,
                  label_width: str = '30%',
                  control_width: str = '70%',
                  required: bool = False) -> str:
    """
    A labelled parameter row for forms.
    Equivalent to QCrBox's BOOL/STRING/NUMBER_PARAMETER_TEMPLATE rows.
    """
    req = ' <b>*</b>' if required else ''
    return tool_row_two_col(
        left=f"<b>{label}</b>{req}",
        right=control,
        left_width=label_width,
        right_width=control_width,
    )