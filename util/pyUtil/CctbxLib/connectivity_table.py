from __future__ import absolute_import, division, print_function
from cctbx import crystal, sgtbx
import libtbx

class connectivity_table(object):
  """ Bond connectivity tabulated """
  conformer_indices = None
  sym_excl_indices = None

  def rt_mx_from_olx(self, olx_input):
    from libtbx.utils import flat_list
    return sgtbx.rt_mx(flat_list(olx_input[:-1]), olx_input[-1])

  def __init__(self,
               structure,
               olx_rm):
    from cctbx.eltbx import covalent_radii
    olx_conn = olx_rm.model['conn']
    self.radii = {}
    max_r = 0
    for l, v in olx_conn['type'].items():
      r = v['radius']
      if r > max_r:
        max_r = r
      self.radii[str(l)] = r
    self.delta = olx_conn['delta']
    tries = 0;
    while tries < 3:
      tries += 1
      try:
        self.create(structure, olx_rm.atoms(), max_r+self.delta)
      except RuntimeError:
        self.delta += 0.5

  def create(self, structure, olx_atoms, buffer_thickness):
    asu_mappings = structure.asu_mappings(buffer_thickness=buffer_thickness)
    self._pair_asu_table = crystal.pair_asu_table(asu_mappings)
    for a in olx_atoms:
      for b in a['neighbours']:
        if isinstance(b, tuple):
          self._pair_asu_table.add_pair(a['aunit_id'], b[0], self.rt_mx_from_olx(b[2]))
          pass
        else:
          self._pair_asu_table.add_pair(a['aunit_id'], b, sgtbx.rt_mx())
    self.pair_sym_table = self.pair_asu_table.extract_pair_sym_table()

  @property
  def pair_asu_table(self):
    return self._pair_asu_table
