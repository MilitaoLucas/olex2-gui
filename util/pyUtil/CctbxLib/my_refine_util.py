from cctbx import xray
from cctbx import crystal
from cctbx.array_family import flex
from cctbx import adptbx
from iotbx import reflection_file_reader
from iotbx import reflection_file_utils
import itertools
from cctbx import sgtbx
from cctbx import maptbx

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
  for a0, a in itertools.izip(s0.scatterers(), s.scatterers()):
    if not a.anisotropic_flag: continue
    print '*** %s ***' % a0.label
    for u in (a0.u_star, a.u_star):
      u_cart = adptbx.u_star_as_u_cart(cs.unit_cell(), u)
      eigensys = adptbx.eigensystem(u_cart)
      for i in xrange(3):
        print 'v=(%.5f, %.5f, %.5f)' % eigensys.vectors(i), 
        print 'lambda=%.6f' % eigensys.values()[i]
      print '---'


def compare_structures(s0, s):
  for a0, a in itertools.izip(s0.scatterers(), s.scatterers()):
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
    print (
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
  def __init__(self, src, olx_atoms):
    self.src = src
    self._add_to = src.add_to
    self.olx_atoms = olx_atoms

  def j_rt_mx_from_olx(self, inp):
    if isinstance(inp, tuple):
      from libtbx.utils import flat_list
      return inp[0], sgtbx.rt_mx(flat_list(inp[2][:-1]), inp[2][-1])
    else:
      return inp, sgtbx.rt_mx()

  def add_to(self, reparametrisation):
    i_pivot = self.src.pivot
    scatterers = reparametrisation.structure.scatterers()
    pivot_site = scatterers[i_pivot].site
    pivot_site_param = reparametrisation.add_new_site_parameter(i_pivot)
    pivot_neighbour_sites = ()
    pivot_neighbour_site_params = ()
    pivot_neighbour_substituent_site_params = ()
    part = self.olx_atoms[self.src.constrained_site_indices[0]]['part']
    for b in self.olx_atoms[i_pivot]['neighbours']:
      j, op = self.j_rt_mx_from_olx(b)
      if j in self.src.constrained_site_indices: continue
      b_part = self.olx_atoms[j]['part']
      if part != 0 and (b_part != 0 and b_part != part):
        continue 
      if not op.is_unit_mx() and op*scatterers[i_pivot].site == scatterers[i_pivot].site:
        continue
      s = reparametrisation.add_new_site_parameter(j, op)
      pivot_neighbour_site_params += (s,)
      pivot_neighbour_sites += (op*scatterers[j].site,)
      if (self.src.need_pivot_neighbour_substituents):
        for c in reparametrisation.pair_sym_table[j].items():
          k, op_k = self.j_rt_mx_from_olx(c)
          if k != i_pivot and scatterers[k].scattering_type != 'H':
            k_part = self.olx_atoms[k]['part']
            if part != 0 and (k_part != 0 or k_part != part):
              continue 
            s = reparametrisation.add_new_site_parameter(k, op*op_k)
            pivot_neighbour_substituent_site_params += (s,)

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

    bond_length = reparametrisation.add(
      _.independent_scalar_parameter,
      value=length_value,
      variable=self.src.stretching)

    if not self.src.stretching:
      for i in self.src.constrained_site_indices:
        reparametrisation.fixed_distances.setdefault(
          (i_pivot, i), bond_length.value)

    hydrogens = tuple(
      [ scatterers[i_sc] for i_sc in self.src.constrained_site_indices ])

    param = self.src.add_hydrogen_to(
      reparametrisation=reparametrisation,
      bond_length=bond_length,
      pivot_site=pivot_site,
      pivot_neighbour_sites=pivot_neighbour_sites,
      pivot_site_param=pivot_site_param,
      pivot_neighbour_site_params=pivot_neighbour_site_params,
      pivot_neighbour_substituent_site_params=
        pivot_neighbour_substituent_site_params,
      hydrogens=hydrogens)
    for i_sc in self.src.constrained_site_indices:
      reparametrisation.asu_scatterer_parameters[i_sc].site = param
