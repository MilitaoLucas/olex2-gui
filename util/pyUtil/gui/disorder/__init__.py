"""
gui/disorder/__init__.py

Disorder modelling and display tools for the Olex2 GUI.

This module is the sole Olex2 interface for the disorder package.
Pure-Python helpers live in _core.py and are fully testable without Olex2.

Public API (registered with Olex2 as spy.gui.disorder.*)
---------------------------------------------------------
    get_existing_fvar_dropdown_items()
    set_part_colour([part])
    set_pC()
    set_pA_or_pB(part)
    set_mode_fit()
    has_disorder([num_return])
    show_unique_only()
    make_unique([add_to])
    sel_part(part [,sel_bonds])
    set_part_display(parts, part)
    make_disorder_quicktools([scope, show_options])
    get_clear_all_parts_cmds()
    clear_all_parts()

Back-compat registrations under spy.gui.*
-----------------------------------------
    get_html_colour_from_material(mat)
    clear_all_parts()
"""

from __future__ import annotations
from ._core import _parse_atom_table


# All GUI templating goes through the one shared mechanism in
# gui/tools/tmpl.py: make_template_getter() binds a get_template(name)
# to this package's own templates.htm and to the olex2.dev_mode flag
# (so template edits show up live in dev mode).  It is imported lazily
# because gui/__init__.py loads this package before gui.tools has
# finished importing.
_get_template = None

def get_template(name: str) -> str:
    """Fetch a named template from this package's templates.htm."""
    global _get_template
    if _get_template is None:
        from gui.tools.tmpl import make_template_getter
        _get_template = make_template_getter(__file__)
    return _get_template(name)


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_unique_selection: str = ''            # atoms forming the current 'unique' selection
_known_materials: dict[str, str] = {}  # cache: material string -> HTML colour


# ===========================================================================
# FVAR queries
# ===========================================================================

def get_existing_fvar_dropdown_items() -> str:
    """
    Return a semicolon-separated string of existing FVAR indices
    suitable for an Olex2 input-combo dropdown.

    FVARs are 1-indexed in SHELX; the dropdown shows indices starting
    from 2 (FVAR 1 is the overall scale factor, not a disorder FVAR).
    Returns e.g. '2;3;4' if three FVARs are defined.
    """
    try:
        from olexFunctions import OV
        fvar_num = 0
        while OV.GetFVar(fvar_num) is not None:
            fvar_num += 1
        return ';'.join(str(i + 1) for i in range(fvar_num))
    except Exception as e:
        print(f"[disorder] Could not get FVAR list: {e}")
        return ''


# ===========================================================================
# Atom info
# ===========================================================================

def get_selected_atom_info() -> dict[str, dict[str, str]]:
    """
    Return info for currently selected atoms by running the Olex2
    'info' command and parsing its output.

    Returns {atom_name: {header: value, ...}, ...}.
    Returns {} if nothing is selected or the command fails.
    """
    try:
        import gui.tools as gt
        lines = gt.scrub('info')[1:]
        return _parse_atom_table(lines)
    except Exception as e:
        print(f"[disorder] Could not get atom info: {e}")
        return {}


# ===========================================================================
# Part manipulation
# ===========================================================================

def _get_controls() -> tuple[str, str, str]:
    """Read the three disorder GUI control values."""
    from olexFunctions import OV
    val_parts      = OV.GetControlValue('SPLIT_PARTS',      None)
    val_fvars      = OV.GetControlValue('SPLIT_FVARS',      None)
    val_restraints = OV.GetControlValue('SPLIT_RESTRAINTS', None)
    return val_parts, val_fvars, val_restraints


def set_part_colour(part=None) -> None:
    """
    Set colours for disorder parts.

    If part is None, colours all parts currently in the model.
    Runs the 'set_part_colour_cmds' template via OV.runCommands.
    Does nothing if user.parts.colour is not set.
    """
    from olexFunctions import OV
    if not OV.GetParam('user.parts.colour'):
        return
    try:
        import olex
        if not part:
            olex.m('sp')
            parts = OV.ListParts()
            olex.m('freeze true')
            for p in parts:
                d = {'part': p, 'mat': OV.GetParam(f'gui.materials._p{p}')}
                OV.runCommands(cmds=(get_template('set_part_colour_cmds') % d).split('\n'))
            olex.m('freeze false')
        else:
            d = {'part': part, 'mat': OV.GetParam(f'gui.materials._p{part}')}
            OV.runCommands(cmds=(get_template('set_part_colour_cmds') % d).split('\n'))
    except Exception as e:
        print(f"[disorder] set_part_colour failed: {e}")


def set_pC() -> None:
    """
    Set part C (the common/shared part) for selected atoms.
    Runs the 'set_pC' template via OV.runCommands.
    """
    try:
        from olexFunctions import OV
        OV.runCommands(cmds=get_template('set_pC').split('\n'))
    except Exception as e:
        print(f"[disorder] set_pC failed: {e}")


def set_pA_or_pB(part: str) -> None:
    """
    Set selected atoms to disorder part A or B.

    part : 'A' or 'B'

    Reads GUI control values for parts, FVARs, and restraints, then
    runs the 'set_pA_or_pB' template. Q-peaks are renamed to C.
    """
    try:
        import olx
        from olexFunctions import OV

        val_parts, val_fvars, val_restraints = _get_controls()
        selected_atoms = get_selected_atom_info()
        d = {}

        if val_restraints != '--':
            d['restraints'] = val_restraints

        # Part assignment
        if val_parts != 'auto':
            idx = 0 if part == 'A' else 1
            p = val_parts.split('/')[idx].strip()
        else:
            p = '1' if part == 'A' else '2'
        d['part'] = p
        d['mat']  = OV.GetParam(f'gui.materials._p{p}')

        # FVAR assignment
        if val_fvars != 'auto':
            d['fvar'] = val_fvars if part == 'A' else f'-{val_fvars}'
        else:
            d['fvar'] = '2' if part == 'A' else '-2'

        for atom in selected_atoms:
            olx.Sel(atom)
        OV.runCommands(cmds=(get_template('set_pA_or_pB') % d).split('\n'))

        for atom in selected_atoms:
            olx.Sel(atom)
            if atom.startswith('Q'):
                olx.Name('C')

    except Exception as e:
        print(f"[disorder] set_pA_or_pB failed: {e}")


def set_mode_fit() -> None:
    """
    Enter Olex2 'mode fit' for the selected atoms, respecting
    the current GUI control values for parts, FVARs, and restraints.
    """
    try:
        import olex
        val_parts, val_fvars, val_restraints = _get_controls()

        cmd = 'mode fit -s'
        if val_restraints != '--':
            cmd += f' {val_restraints}'
        if val_parts != 'auto':
            cmd += f' -p={val_parts.split("/")[0].strip()}'
        if val_fvars != 'auto':
            cmd += f' -v={val_fvars}'

        olex.m(cmd)
    except Exception as e:
        print(f"[disorder] set_mode_fit failed: {e}")


# ===========================================================================
# Disorder detection
# ===========================================================================

def has_disorder(num_return: bool = False):
    """
    Return True (or 1) if the current model has real disorder parts.

    A model with only part 0 is not considered disordered.
    If num_return is True, returns 1 or 0 instead of True/False.
    """
    try:
        import olexex
        parts = olexex.OlexRefinementModel().disorder_parts()
        sp = set(parts) if parts else set()
        has = bool(sp and not (len(sp) == 1 and 0 in sp))
    except Exception:
        has = False
    return (1 if has else 0) if num_return else has


# ===========================================================================
# Unique selection
# ===========================================================================

def show_unique_only() -> None:
    """
    If user.parts.keep_unique is set, show only the unique (part 0) atoms
    using the stored unique selection.
    """
    global _unique_selection
    try:
        from olexFunctions import OV
        import olx
        if OV.GetParam('user.parts.keep_unique') is True:
            make_unique(add_to=True)
            if _unique_selection:
                olx.Sel('-u')
                olx.Uniq()
                olx.Sel(_unique_selection)
                olx.Uniq()
    except Exception as e:
        print(f"[disorder] show_unique_only failed: {e}")


def make_unique(add_to: bool = False) -> None:
    """
    Build and apply the unique selection from currently selected atoms.
    If add_to is True, merges with any existing unique selection.
    """
    global _unique_selection
    try:
        import olx
        import gui.tools as gt

        if not _unique_selection:
            add_to = True
        if add_to:
            olx.Sel('-a')

        raw = ' '.join(gt.scrub('Sel'))
        raw = raw.replace('Sel', ' ')
        while '  ' in raw:
            raw = raw.replace('  ', ' ').strip()

        atoms = raw.split()
        if atoms:
            if add_to and _unique_selection:
                atoms = list(set(atoms + _unique_selection.split()))
            _unique_selection = ' '.join(atoms)

        olx.Sel(_unique_selection)
        olx.Uniq()
    except Exception as e:
        print(f"[disorder] make_unique failed: {e}")


# ===========================================================================
# Part selection and display
# ===========================================================================

def sel_part(part, sel_bonds: bool = True) -> None:
    """
    Select atoms in the given disorder part.
    Does nothing if user.parts.select is not set.
    If sel_bonds is True, also selects bonds connected to selected atoms.
    """
    try:
        from olexFunctions import OV
        import olex
        if not OV.GetParam('user.parts.select'):
            return
        olex.m(f'sel part {part}')
        if sel_bonds:
            olex.m('sel bonds where xbond.a.selected==true||xbond.b.selected==true')
    except Exception as e:
        print(f"[disorder] sel_part failed: {e}")


def set_part_display(parts, part) -> None:
    """
    Show the specified disorder parts and optionally colour and select them.

    parts : 'all' to show everything, or a space-separated part string
    part  : the specific part for colour/selection highlighting
    """
    try:
        from olexFunctions import OV
        import olex
        show_unique_only()

        if parts in ('all', 'main'):
            olex.m("ShowP -v=spy.GetParam(user.parts.keep_unique)")
            part = ''
        else:
            olex.m(f"ShowP 0 {parts} -v=spy.GetParam(user.parts.keep_unique)")

        if OV.GetParam('user.parts.colour'):
            set_part_colour(part)

        if OV.GetParam('user.parts.select'):
            olex.m(f'sel part {parts}')
            olex.m('sel atom bonds -a')
    except Exception as e:
        print(f"[disorder] set_part_display failed: {e}")


# ===========================================================================
# Colour helpers
# ===========================================================================

def get_html_colour_from_material(mat) -> str | None:
    """
    Convert an Olex2 material parameter to an HTML hex colour string.

    If mat contains no ';', it is treated as a named colour scheme entry
    and looked up via drawplus.colour_schemes. Otherwise it is unpacked
    from a packed integer RGBA value.

    Results are cached in _known_materials.
    Returns None if conversion fails.
    """
    global _known_materials
    try:
        from olexFunctions import OV
        from ImageTools import IT
        import struct

        mat = str(mat)

        if ';' not in mat:
            scheme = OV.GetParam('drawplus.group_colour_scheme')
            mat = OV.GetParam(f'drawplus.colour_schemes.{scheme}.{mat}')
            if mat in _known_materials:
                return _known_materials[mat]
            return None

        if mat in _known_materials:
            return _known_materials[mat]

        packed = int(mat.split(';')[1])
        rgba   = struct.unpack('4B', struct.pack('>I', packed))
        rgb    = (rgba[3], rgba[2], rgba[1])
        html   = IT.RGBToHTMLColor(rgb)
        _known_materials[mat] = html
        return html

    except Exception as e:
        print(f"[disorder] get_html_colour_from_material failed: {e}")
        return None


# ===========================================================================
# Clear all parts
# ===========================================================================

def get_clear_all_parts_cmds() -> str:
    """
    Build the command string for resetting all disorder parts.
    Uses the 'reset_all_parts_cmds' template, passing even-numbered parts
    (the B/C parts that get removed when clearing disorder).
    """
    try:
        import olexex
        parts = set(olexex.OlexRefinementModel().disorder_parts())
        even_parts = ' '.join(
            str(p) for p in sorted(parts)
            if p != 0 and p % 2 == 0
        )
        return get_template('reset_all_parts_cmds') % even_parts
    except Exception as e:
        print(f"[disorder] get_clear_all_parts_cmds failed: {e}")
        return ''


def clear_all_parts() -> None:
    """
    Prompt the user then remove all disorder parts, resetting the structure.
    """
    try:
        import olx
        from olexFunctions import OV
        if olx.Alert('Run',
                     'PARTS will be removed and your structure will be reset. Continue?',
                     'NY') == 'N':
            return
        OV.runCommands(cmds=get_clear_all_parts_cmds().split('\n'))
    except Exception as e:
        print(f"[disorder] clear_all_parts failed: {e}")


# ===========================================================================
# Disorder quicktools HTML panel
# ===========================================================================

def make_disorder_quicktools(scope: str = 'main',
                             show_options: bool = True) -> str:
    """
    Generate and return the HTML for the disorder quicktools panel.

    scope        : panel scope string (default 'main')
    show_options : whether to show the options section (checkboxes, label combo)
    """
    try:
        import olexex
        from olexFunctions import OV

        if 'scope' in str(scope):
            scope = str(scope).split('scope=')[1]

        parts = set(olexex.OlexRefinementModel().disorder_parts())
        parts_display = ''

        for item in sorted(parts):
            if item == 0:
                continue
            bg_colour = None
            if OV.GetParam('user.parts.colour'):
                try:
                    mat = OV.GetParam(f'gui.materials._p{item}')
                    bg_colour = get_html_colour_from_material(mat)
                except Exception:
                    pass
            if not bg_colour:
                bg_colour = OV.GetVar('linkButton.bgcolor')

            d = {
                'part':         item,
                'parts':        item,
                'scope':        scope,
                'show_options': show_options,
                'bg_colour':    bg_colour,
            }
            parts_display += get_template('part_0_and_n') % d

        clear_parts = get_template('reset_all_parts') % 'spy.gui.disorder.clear_all_parts()'

        dd = {
            'parts_display': parts_display,
            'scope':         scope,
            'show_options':  show_options,
            'clear_parts':   clear_parts,
        }

        template = 'disorder_quicktool' if show_options else 'disorder_quicktool_no_options'
        return get_template(template) % dd

    except Exception as e:
        print(f"[disorder] make_disorder_quicktools failed: {e}")
        return ''


# ===========================================================================
# Olex2 registration
# ===========================================================================

try:
    from olexFunctions import OV
    # Modelling
    OV.registerFunction(get_existing_fvar_dropdown_items, False, 'gui.disorder')
    OV.registerFunction(set_part_colour,                  False, 'gui.disorder')
    OV.registerFunction(set_pC,                           False, 'gui.disorder')
    OV.registerFunction(set_pA_or_pB,                     False, 'gui.disorder')
    OV.registerFunction(set_mode_fit,                     False, 'gui.disorder')
    # Display
    OV.registerFunction(has_disorder,                     False, 'gui.disorder')
    OV.registerFunction(show_unique_only,                 False, 'gui.disorder')
    OV.registerFunction(make_unique,                      False, 'gui.disorder')
    OV.registerFunction(sel_part,                         False, 'gui.disorder')
    OV.registerFunction(set_part_display,                 False, 'gui.disorder')
    OV.registerFunction(make_disorder_quicktools,         False, 'gui.disorder')
    OV.registerFunction(get_clear_all_parts_cmds,         False, 'gui.disorder')
    OV.registerFunction(clear_all_parts,                  False, 'gui.disorder')
    # Back-compat: these were originally registered under 'gui' scope
    OV.registerFunction(get_html_colour_from_material,    True,  'gui')
    OV.registerFunction(clear_all_parts,                  True,  'gui')
except ImportError:
    pass
