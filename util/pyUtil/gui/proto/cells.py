"""
gui/proto/cells.py

Unit-cell comparison for the proto library, using cctbx.

Cells are compared as reduced (Niggli) cells of the primitive lattice, so
the same structure is recognised whatever setting or axis choice the data
were processed in. A match is then classified:

    'same'     same space group and the cells agree directly, i.e. the
               stored model can be used as it is
    'setting'  the lattices agree, but the space group or the setting
               differs -- the model would first have to be transformed
"""

from __future__ import annotations


def _symmetry(cell, space_group):
  from cctbx import crystal
  return crystal.symmetry(unit_cell=tuple(float(x) for x in cell),
                          space_group_symbol=str(space_group))


def reduced_cell(cell, space_group):
  """Niggli-reduced primitive cell as a 6-tuple."""
  cs = _symmetry(cell, space_group)
  return tuple(cs.primitive_setting().unit_cell().niggli_cell().parameters())


def primitive_volume(cell, space_group):
  cs = _symmetry(cell, space_group)
  return cs.unit_cell().volume() / cs.space_group().order_z() * \
      cs.space_group().order_p()


def same_space_group(sg1, sg2) -> bool:
  """True if both symbols describe the same group in the same setting."""
  if str(sg1).replace(' ', '') == str(sg2).replace(' ', ''):
    return True
  try:
    from cctbx import sgtbx
    g1 = sgtbx.space_group_info(str(sg1)).group()
    g2 = sgtbx.space_group_info(str(sg2)).group()
    return g1 == g2
  except (RuntimeError, ValueError):
    # Unknown symbol: the string comparison above is all we can do
    return False


def _cell_deviation(c1, c2):
  """(max relative length difference, max angle difference in degrees)."""
  dl = max(abs(a - b) / max(a, b) for a, b in zip(c1[:3], c2[:3]))
  da = max(abs(a - b) for a, b in zip(c1[3:], c2[3:]))
  return dl, da


def reduced_cells_match(red1, red2, rel_length_tol, angle_tol) -> bool:
  """
  Do two reduced cells describe the same lattice? Niggli cells near a
  boundary (angles close to 90 deg) can come out as different but
  equivalent choices, so cctbx's similarity search is used rather than
  a plain parameter comparison.
  """
  from cctbx import uctbx
  u1, u2 = uctbx.unit_cell(red1), uctbx.unit_cell(red2)
  try:
    return bool(u1.similarity_transformations(
        other=u2,
        relative_length_tolerance=rel_length_tol,
        absolute_angle_tolerance=angle_tol))
  except (AttributeError, TypeError):
    # Older cctbx without similarity_transformations
    return u1.is_similar_to(u2, rel_length_tol, angle_tol)


def setting_transform(cur_cell, cur_sg, old_cell, old_sg,
                      rel_length_tol=0.03, angle_tol=3.0):
  """
  Change-of-basis operator taking a model in (old_cell, old_sg) into the
  setting of (cur_cell, cur_sg), or None if there is none.

  Both settings are taken to their Niggli cells; every similarity
  transformation between those is tried (in both directions, so the
  convention of similarity_transformations doesn't matter), and the
  first operator is accepted that turns the old space group into exactly
  the current one and the old cell into one similar to the current.

  Returns the cctbx change_of_basis_op; its c() maps old fractional
  coordinates onto current ones.
  """
  from cctbx import sgtbx
  cs_cur = _symmetry(cur_cell, cur_sg)
  cs_old = _symmetry(old_cell, old_sg)
  cb_cur = cs_cur.change_of_basis_op_to_niggli_cell()
  cb_old = cs_old.change_of_basis_op_to_niggli_cell()
  n_cur = cs_cur.change_basis(cb_cur).unit_cell()
  n_old = cs_old.change_basis(cb_old).unit_cell()

  # Candidate operators between the two Niggli cells: identity first,
  # then the similarity transformations, built as cctbx itself does in
  # crystal/reindex.py
  candidates = [sgtbx.change_of_basis_op()]
  for m in n_old.similarity_transformations(
          other=n_cur,
          relative_length_tolerance=rel_length_tol,
          absolute_angle_tolerance=angle_tol):
    cb_m = sgtbx.change_of_basis_op(sgtbx.rt_mx(sgtbx.rot_mx(m)))
    candidates += [cb_m, cb_m.inverse()]

  target_group = cs_cur.space_group()
  for cand in candidates:
    total = cb_cur.inverse() * cand * cb_old
    moved = cs_old.change_basis(total)
    if moved.space_group() != target_group:
      continue
    if not moved.unit_cell().is_similar_to(
            cs_cur.unit_cell(), rel_length_tol, angle_tol):
      continue
    return total
  return None


def operator_parts(cb_op):
  """(R as a 9-tuple of floats, t as a 3-tuple) of cb_op.c()."""
  c = cb_op.c()
  return tuple(c.r().as_double()), tuple(c.t().as_double())


def compare(current: dict, entry: dict, rel_length_tol=0.03, angle_tol=3.0):
  """
  Compare the current structure with a library entry.

  current : {'cell': 6-tuple, 'space_group': str, 'reduced': 6-tuple}
  entry   : db row dict (cell_*, space_group, red_* possibly None)

  Returns None (no match) or a dict:
      kind      'same' or 'setting' (see module doc)
      dl, da    max relative length / angle deviation of the cells
                (direct cells for 'same', reduced cells otherwise)
      reduced   the entry's reduced cell (so callers can cache it)
  """
  ecell = tuple(entry[k] for k in ('cell_a', 'cell_b', 'cell_c',
                                   'cell_alpha', 'cell_beta', 'cell_gamma'))
  red = tuple(entry.get(k) for k in ('red_a', 'red_b', 'red_c',
                                     'red_alpha', 'red_beta', 'red_gamma'))
  if None in red:
    red = reduced_cell(ecell, entry['space_group'])

  if not reduced_cells_match(current['reduced'], red, rel_length_tol, angle_tol):
    return None

  dl, da = _cell_deviation(current['cell'], ecell)
  if (same_space_group(current['space_group'], entry['space_group'])
          and dl <= rel_length_tol and da <= angle_tol):
    return {'kind': 'same', 'dl': dl, 'da': da, 'reduced': red}
  dl, da = _cell_deviation(current['reduced'], red)
  return {'kind': 'setting', 'dl': dl, 'da': da, 'reduced': red}
