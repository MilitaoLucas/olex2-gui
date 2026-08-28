"""
gui/disorder/_core.py

Pure-Python core for the disorder package — no Olex2 dependencies.
Everything here is fully testable without a running Olex2 instance.
"""

from __future__ import annotations


def _parse_atom_table(lines: list[str]) -> dict[str, dict[str, str]]:
  """
    Parse the tabular output of the Olex2 'info' command into a dict.

    Input  : list of strings (lines from the info command output).
    Output : {atom_name: {header: value, ...}, ...}

    The table starts with a line beginning 'Atom Type' and ends at
    'Mean Uiso'. Each data row must have the same number of columns as
    the header row; mismatched rows are silently skipped.

    Example
    -------
    >>> _parse_atom_table([
    ...     'Atom Type    x         y         z         Ueq',
    ...     'C1   C    0.123   0.234   0.345   0.032',
    ...     'Mean Uiso  0.033',
    ... ])
    {'C1': {'Type': 'C', 'x': '0.123', 'y': '0.234', 'z': '0.345', 'Ueq': '0.032'}}
    """
  atoms: dict[str, dict[str, str]] = {}
  headers: list[str] = []
  in_table = False

  for line in lines:
    line = line.strip()
    if not line:
      continue
    if line.startswith('Atom Type'):
      headers = line.split()
      in_table = True
      continue
    if line.startswith('Mean Uiso'):
      break
    if in_table and headers:
      parts = line.split()
      if len(parts) == len(headers):
        atom_name = parts[0]
        atoms[atom_name] = dict(zip(headers[1:], parts[1:]))

  return atoms
