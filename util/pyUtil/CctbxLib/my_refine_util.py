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
