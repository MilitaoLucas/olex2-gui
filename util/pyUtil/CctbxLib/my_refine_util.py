from cctbx import xray
from cctbx import crystal
from cctbx.array_family import flex
from cctbx import adptbx
from iotbx import reflection_file_reader
from iotbx import reflection_file_utils
import itertools
from cctbx import sgtbx
from cctbx import maptbx
from smtbx.refinement.constraints import InvalidConstraint
from scitbx.matrix import col
from olexFunctions import OV

def shelx_adp_converter(crystal_symmetry):
  def u_star(u11, u22, u33, u23, u13, u12):
    # non-diagonal ADP in reverse order compared to ShelX
    return adptbx.u_cart_as_u_star(
      crystal_symmetry.unit_cell(),
      (u11, u22, u33, u12, u13, u23)
#            (u11, u22, u33, u23, u13, u12)
    )
  return u_star

def print_thermal_axes(s0, s):
  cs = s0.special_position_settings()
  for a0, a in zip(s0.scatterers(), s.scatterers()):
    if not a.anisotropic_flag: continue
    print('*** %s ***' % a0.label)
    for u in (a0.u_star, a.u_star):
      u_cart = adptbx.u_star_as_u_cart(cs.unit_cell(), u)
      eigensys = adptbx.eigensystem(u_cart)
      for i in range(3):
        print('v=(%.5f, %.5f, %.5f)' % eigensys.vectors(i), end=' ')
        print('lambda=%.6f' % list(eigensys.values())[i])
      print('---')


def compare_structures(s0, s):
  for a0, a in zip(s0.scatterers(), s.scatterers()):
    diff_sites = tuple(
      (flex.double(a.site)-flex.double(a0.site))/flex.double(a0.site)
      *100
    )
    if a.anisotropic_flag:
      diff_adp = tuple(
        (flex.double(a.u_star)-flex.double(a0.u_star))
        / flex.double(a0.u_star)
      )
      n = 6
    else:
      diff_adp = ( ( a.u_iso - a0.u_iso )/a0.u_iso, )
      n = 1
    print(
      '%s: site moved by ' + '%.0f%%, '*3
      + 'and adp moved by ' + '%.0f%%, '*n
      ) % (
        (a.label,) + diff_sites
        + diff_adp
      )

def shake_structure(s, thermal_shift, site_shift):
  for a in s.scatterers():
    if(a.flags.grad_site()):
      a.site = [ x + site_shift for x in a.site ]
    elif(a.flags.use_u_iso() and a.flags.grad_u_iso()):
      a.u_iso += (thermal_shift * random.random())
    elif(a.flags.use_u_aniso() and a.flags.grad_u_aniso()):
      a.u_star = [ u + thermal_shift * random.random()
                   for u in a.u_star ]

def create_xray_stucture_model(cell, spacegroup, atom_iter, reflections):
  """ cell is a 6-uple, spacegroup a string and atom_iter yields tuples (label, xyz, u) """
  cs = crystal.symmetry(cell, spacegroup)
  xs = xray.structure(cs.special_position_settings())
  reflections = reflections
  u_star = shelx_adp_converter(cs)
  for label, xyz, u, elt in atom_iter:
    if len(u) != 1:
      a = xray.scatterer(label, xyz, u_star(*u))
    else:
      a = xray.scatterer(label, xyz,u[0])

    a.flags.set_grad_site(True)
    if a.flags.use_u_iso() == True:
      a.flags.set_grad_u_iso(True)
      a.flags.set_grad_u_aniso(False)
    if a.flags.use_u_aniso()== True:
      a.flags.set_grad_u_aniso(True)
      a.flags.set_grad_u_iso(False)
    xs.add_scatterer(a)

  from cctbx.eltbx import wavelengths, sasaki
  lambda_ = wavelengths.characteristic('Mo').as_angstrom()
  for sc in xs.scatterers():
    if sc.scattering_type in ('H','D'):continue
    fp_fdp = sasaki.table(sc.scattering_type).at_angstrom(lambda_)
    sc.fp = fp_fdp.fp()
    sc.fdp = fp_fdp.fdp()
  return xs

class hydrogen_atom_constraints_customisation(object):
  def __init__(self, src, olx_atoms, max_pivot_neigbours):
    self.src = src
    self._add_to = src.add_to
    self.olx_atoms = olx_atoms
    self.max_pivot_neigbours = max_pivot_neigbours

  def j_rt_mx_from_olx(self, inp):
    if isinstance(inp, tuple):
      from libtbx.utils import flat_list
      return inp[0], sgtbx.rt_mx(flat_list(inp[2][:-1]), inp[2][-1])
    else:
      return inp, sgtbx.rt_mx()

  def add_to(self, reparametrisation):
    i_pivot = self.src.pivot
    self.reparametrisation = reparametrisation
    scatterers = reparametrisation.structure.scatterers()
    self.pivot_site = scatterers[i_pivot].site
    if not scatterers[i_pivot].flags.grad_site():
      if OV.IsDebugging():
        print("Skipping conflicting AFIX for %s" %scatterers[i_pivot].label)
      return
    # check for fixed coordinates
    for i_sc in self.src.constrained_site_indices:
      sc = scatterers[i_sc]
      if not sc.flags.grad_site():
        if OV.IsDebugging():
          print("Skipping conflicting AFIX for %s" %scatterers[i_pivot].label)
        return

    self.pivot_site_param = reparametrisation.add_new_site_parameter(i_pivot)
    self.pivot_neighbour_sites = ()
    self.pivot_neighbour_site_params = ()
    self.pivot_neighbour_substituent_site_params = ()
    part = self.olx_atoms[self.src.constrained_site_indices[0]]['part']
    special_sites = []
    excluded_sites = []
    neighbours = []

    for b in self.olx_atoms[i_pivot]['neighbours']:
      j, op = self.j_rt_mx_from_olx(b)
      if j in self.src.constrained_site_indices: continue
      b_part = self.olx_atoms[j]['part']
      if part != 0 and b_part != 0 and b_part != part:
        excluded_sites.append(b)
        continue
      if not op.is_unit_mx() and op*scatterers[i_pivot].site == scatterers[i_pivot].site:
        special_sites.append((j, op))
        continue
      s = reparametrisation.add_new_site_parameter(j, op)
      self.pivot_neighbour_site_params += (s,)
      self.pivot_neighbour_sites += (op*scatterers[j].site,)
      neighbours.append(b)
      # complete with need_pivot_neighbour_substituents after possibly shrinking
      #  the list of the pivot neighbours

    length_value = self.src.bond_length
    if length_value is None:
      length_value = self.src.ideal_bond_length(scatterers[i_pivot],
                                            reparametrisation.temperature)
    import smtbx.refinement.constraints as _
    if self.src.stretching:
      uc = reparametrisation.structure.unit_cell()
      _length_value = uc.distance(
        col(scatterers[i_pivot].site),
        col(scatterers[self.src.constrained_site_indices[0]].site))
      if _length_value > 0.5: #check for dummy values
        length_value = _length_value

    self.bond_length = reparametrisation.add(
      _.independent_scalar_parameter,
      value=length_value,
      variable=self.src.stretching)

    if not self.src.stretching:
      for i in self.src.constrained_site_indices:
        reparametrisation.fixed_distances.setdefault(
          (i_pivot, i), self.bond_length.value)

    #shrink the list of neigbours if needed
    if len(self.pivot_neighbour_sites) > self.max_pivot_neigbours:
      uc = reparametrisation.structure.unit_cell()
      x_s = col(self.pivot_site)
      d_s = sorted(
          (uc.distance(s, x_s), i)
          for i, s in enumerate(self.pivot_neighbour_sites)
      )
      new_sites = []
      new_site_params = []
      new_neighbours = []
      for ni in range(self.max_pivot_neigbours):
        new_sites.append(self.pivot_neighbour_sites[d_s[ni][1]])
        new_site_params.append(self.pivot_neighbour_site_params[d_s[ni][1]])
        new_neighbours.append(neighbours[d_s[ni][1]])
      self.pivot_neighbour_sites = new_sites
      self.pivot_neighbour_site_params = new_site_params
      neighbours = new_neighbours
    else:
      while len(self.pivot_neighbour_sites) < self.max_pivot_neigbours and excluded_sites:
        b = excluded_sites[0]
        j, op = self.j_rt_mx_from_olx(b)
        s = reparametrisation.add_new_site_parameter(j, op)
        self.pivot_neighbour_site_params += (s,)
        self.pivot_neighbour_sites += (op*scatterers[j].site,)
        neighbours.append(b)
        excluded_sites.pop(0)

    # complete
    if (self.src.need_pivot_neighbour_substituents):
      for b in neighbours:
        j, op = self.j_rt_mx_from_olx(b)
        for c in self.olx_atoms[j]['neighbours']:
          k, op_k = self.j_rt_mx_from_olx(c)
          if k != i_pivot and scatterers[k].scattering_type != 'H':
            k_part = self.olx_atoms[k]['part']
            if part != 0 and k_part != 0 and k_part != part:
              continue
            s = reparametrisation.add_new_site_parameter(k, op.multiply(op_k))
            self.pivot_neighbour_substituent_site_params += (s,)

    self.hydrogens = tuple(
      [ scatterers[i_sc] for i_sc in self.src.constrained_site_indices ])
    if not self.try_add(True):
      if special_sites:
        for j, op in special_sites:
          s = reparametrisation.add_new_site_parameter(j, op)
          self.pivot_neighbour_site_params += (s,)
          self.pivot_neighbour_sites += (op*scatterers[j].site,)
      # propagate the exception if thrown in either case
      self.try_add(False)

  def try_add(self, quiet):
    try:
      param = self.src.add_hydrogen_to(
        reparametrisation=self.reparametrisation,
        bond_length=self.bond_length,
        pivot_site=self.pivot_site,
        pivot_neighbour_sites=self.pivot_neighbour_sites,
        pivot_site_param=self.pivot_site_param,
        pivot_neighbour_site_params=self.pivot_neighbour_site_params,
        pivot_neighbour_substituent_site_params=
          self.pivot_neighbour_substituent_site_params,
        hydrogens=self.hydrogens)
      for i_sc in self.src.constrained_site_indices:
        self.reparametrisation.asu_scatterer_parameters[i_sc].site = param
      return True
    except InvalidConstraint as exc:
      if not quiet:
        raise exc
      return False
