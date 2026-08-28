"""
gui/tools/tmpl.py

Shared template-getter factory for Olex2 GUI subpackages.

Each package that has its own templates.htm calls make_template_getter
once at import time and gets back a get_template(name) function that is
already bound to that package's file and to the olex2.dev_mode flag.

Usage
-----
In any gui subpackage's __init__.py:

    from gui.tools.tmpl import make_template_getter
    get_template = make_template_getter(__file__)

    # then anywhere in the module:
    html = get_template('my_widget') % data
    cmds = get_template('my_cmds') % data

How it works
------------
make_template_getter(__file__) captures the directory of the calling
package and constructs the path to templates.htm sitting alongside it.
The returned function reads olex2.dev_mode on every call so that template
edits are picked up live during development without restarting Olex2.
"""

from __future__ import annotations
import os


def make_template_getter(package_file: str):
  """
    Return a get_template(name) -> str function bound to the templates.htm
    in the same directory as package_file.

    Parameters
    ----------
    package_file : str
        Pass __file__ from the calling package's __init__.py.
        The templates.htm is expected to sit in the same directory.

    Returns
    -------
    Callable[[str], str]
        get_template(name) -- fetches the named template, forcing a reload
        when olex2.dev_mode is True. Returns '' on any failure.
    """
  template_file = os.path.join(os.path.dirname(package_file), 'templates.htm')
  package_name  = os.path.basename(os.path.dirname(package_file))

  def get_template(name: str) -> str:
    try:
      from olexFunctions import OV
      import gui.tools
      dev_mode = bool(OV.GetParam('olex2.dev_mode', False))
      return gui.tools.TemplateProvider.get_template(
        name,
        template_file=template_file,
        force=dev_mode,
      )
    except Exception as e:
      print(f"[{package_name}] template '{name}' failed: {e}")
      return ''

  return get_template
