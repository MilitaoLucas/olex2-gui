"""A radial falloff shared by f' and f'', refined with the structure.

f' and f'' are stored per atom as constants and enter Fc unchanged at every
scattering angle, while f0 decays. The resonant scattering comes from core
electrons of finite extent, so it decays too, and with the same shape for both
parts since they come from the same oscillator strengths. This gives them one:

    f'_eff  = fp  R_g
    f''_eff = fdp R_g
    R_g     = 1 + c_{g,1} u + c_{g,2} u^2 + ...

where u is 1 - cos(2 theta) by default, or sin(theta)/lambda. The two are not
merely different units: cos(2 theta) = 1 - 2 lambda^2 s^2, so a polynomial in
the first is exactly a polynomial of the same degree in s^2 -- the even powers
of s and only those -- whereas powers of s span the odd ones too, and those are
not polynomials in cos(2 theta) at all. Choosing cos(2 theta) restricts the
model to what the physics asks for; it does not merely rewrite it.

The coefficients start at zero, where R is 1 and nothing has changed, and refine
as ordinary least-squares parameters alongside f' and f'' themselves. g is a
group: one per element, or one per atom.

There is no constant term. It would be exactly degenerate with f' and f'':
scaling f' by a constant is changing f'. Both choices of u vanish at theta = 0,
so R(0) = 1 and the tabulated values stand untouched at forward scattering,
which is where they are by definition right.

A caveat worth stating plainly, since the numbers this produces will end up in
a paper: f' and f'' are dominated by core electrons and are genuinely close to
constant in s. One empirical function shared by both is a phenomenological
correction, not a physical model of dispersion.

Macros, all under the disprad namespace:

    disprad.setup elements=Br,I n=2
    disprad.setup atoms=Pd1 n=3
    disprad.print_current
    disprad.remove

C.f. cctbx/xray/dispersion_radial.h for the refinement machinery.
"""
import json
import hashlib
import os

import olex
import olx
import gui

from cctbx import xray
from cctbx.array_family import flex

from olexFunctions import OV
from PluginTools import PluginTools as PT

if OV.HasGUI():
  get_template = gui.tools.TemplateProvider.get_template

try:
  p_path = os.path.dirname(os.path.abspath(__file__))
except Exception:
  p_path = os.path.dirname(os.path.abspath("__file__"))

p_name = "DispRadial"
p_htm = "DispRadial"
p_img = [("DispRadial", 'h1')]
p_scope = "DispRadial"

MAX_TERMS = 4


def _split(text):
  """Element symbols or atom labels, however the macro argument spelt them."""
  if not text:
    return []
  return [t for t in text.replace(',', ' ').split() if t]


def _has_anomalous_scattering(sc):
  """Whether this scatterer can contribute a gradient at all.

  An atom with f' = f'' = 0 leaves dR/dc multiplied by zero, so a group made
  only of those has an identically zero column and would make the normal matrix
  singular. use_fp_fdp is tested as well because the spherical and the tabulated
  structure factor paths honour it differently, and a group has to mean the same
  thing on both.
  """
  return sc.flags.use_fp_fdp() and (sc.fp != 0 or sc.fdp != 0)


def _assign_groups(xray_structure, mode, selection, log=True):
  """scatterer -> group index, -1 for the ones left alone.

  Returns (groups, n_groups, names), names labelling each group for reporting.
  """
  scatterers = xray_structure.scatterers()
  groups = flex.int(scatterers.size(), -1)
  wanted = set(s.upper() for s in selection)
  names = []
  by_key = {}
  skipped_no_anomalous = []
  skipped_not_selected = 0

  for i, sc in enumerate(scatterers):
    if mode == 'atom':
      key = sc.label
    else:
      key = sc.scattering_type
    if wanted and key.upper() not in wanted:
      skipped_not_selected += 1
      continue
    if not _has_anomalous_scattering(sc):
      skipped_no_anomalous.append(sc.label)
      continue
    if key not in by_key:
      by_key[key] = len(names)
      names.append(key)
    groups[i] = by_key[key]

  if log and skipped_no_anomalous:
    print("DispRadial: no f' or f'' on %s, left out -- a group of those alone"
          " would have no gradient at all"
          % ', '.join(skipped_no_anomalous[:12])
          + (' ...' if len(skipped_no_anomalous) > 12 else ''))
  if log and wanted:
    missing = wanted - set(n.upper() for n in names)
    if missing:
      print("DispRadial: nothing selected by %s" % ', '.join(sorted(missing)))
  return groups, len(names), names


def _stored_coefficients():
  """Whatever is in the phil, or an empty list if it is unusable."""
  try:
    values = json.loads(OV.GetParam('snum.DispRadial.coefficients', '') or '[]')
    return [float(c) for c in values]
  except (ValueError, TypeError):
    return []


def _wavelength():
  """The radiation, which the cos(2 theta) basis is a function of."""
  try:
    return float(olx.xf.exptl.Radiation())
  except Exception:
    return 0.


def _hash(xray_structure, mode, selection, n_terms, basis, wavelength):
  """What the stored coefficients were refined for.

  Reusing them after the model has changed underneath would warm-start the
  refinement from somewhere that no longer means anything. The basis and the
  wavelength are in here because a coefficient of s^k and a coefficient of
  (1 - cos 2theta)^k are different numbers for the same curve.
  """
  h = hashlib.md5()
  h.update(mode.encode())
  h.update(','.join(sorted(s.upper() for s in selection)).encode())
  h.update(str(n_terms).encode())
  h.update(basis.encode())
  h.update(('%.6f' % wavelength).encode())
  for sc in xray_structure.scatterers():
    h.update(("%s|%s|%.6f|%.6f;"
              % (sc.label, sc.scattering_type, sc.fp, sc.fdp)).encode())
  return h.hexdigest()


def build_correction(xray_structure, log=True):
  """The correction to hand to the reparametrisation, or None.

  None whenever there is nothing sensible to refine, which is the normal way of
  saying so: the caller carries on without it.
  """
  if not OV.GetParam('snum.DispRadial.enabled', False):
    return None
  mode = str(OV.GetParam('snum.DispRadial.mode', 'element'))
  selection = _split(OV.GetParam('snum.DispRadial.selection', ''))
  n_terms = int(OV.GetParam('snum.DispRadial.n_terms', 2))
  basis = str(OV.GetParam('snum.DispRadial.basis', 'cos_2theta'))
  if n_terms < 1 or n_terms > MAX_TERMS:
    print('DispRadial: n_terms must be between 1 and %i, got %i'
          % (MAX_TERMS, n_terms))
    return None

  in_cos_two_theta = (basis == 'cos_2theta')
  wavelength = _wavelength()
  if in_cos_two_theta and wavelength <= 0:
    print('DispRadial: the cos(2theta) basis is a function of theta and so'
          ' needs the wavelength, which could not be read. Set it, or use'
          ' basis=stol.')
    return None

  groups, n_groups, names = _assign_groups(xray_structure, mode, selection, log)
  if n_groups == 0:
    if log:
      print('DispRadial: no atom to correct, skipping')
    return None

  # the outermost sin(theta)/lambda of the data, which is what keeps R from
  # being pulled through zero at a resolution nothing was measured at
  s_max = 0.
  try:
    d_star_sq = xray_structure.unit_cell().d_star_sq
    s_max = max(d_star_sq(h) for h in olex_hkl_indices())**0.5/2
  except Exception as e:
    print('DispRadial: could not work out the resolution limit (%s), so R is'
          ' left unconstrained' % e)

  refine = bool(OV.GetParam('snum.DispRadial.refine', True))
  dc = xray.dispersion_radial_correction(groups, n_groups, n_terms, refine,
                                         s_max, 0.1, in_cos_two_theta,
                                         wavelength)
  dc.group_names = names

  """Where the starting values come from.

  Refining, the stored values are only a warm start and are worth having only
  if they were refined for this same model, hence the hash. Held fixed they are
  the user's assertion about the structure, so they stand whatever else has
  changed -- an atom moving does not make a belief about Pd's dispersion wrong.
  The length is checked either way, since n_terms may have changed underneath
  them and a short or long list would silently mean something else.
  """
  stored = _stored_coefficients()
  if refine and stored:
    if _hash(xray_structure, mode, selection, n_terms, basis,
             wavelength) != OV.GetParam('snum.DispRadial.coefficients_hash',
                                        ''):
      stored = []
  if stored:
    if len(stored) == dc.n_param:
      for i, c in enumerate(stored):
        dc.coefficients[i] = float(c)
    elif log:
      print('DispRadial: %i stored coefficient(s) but %i are wanted, so they'
            ' are ignored; set them again with disprad.set'
            % (len(stored), dc.n_param))

  if log:
    print('DispRadial: %i coefficient(s), %i term(s) in %s for %s%s'
          % (dc.n_param, n_terms,
             '1 - cos(2theta)' if in_cos_two_theta else 'sin(theta)/lambda',
             ', '.join(names),
             '' if refine else ' -- held fixed, not refined'))
    correlated = [xray_structure.scatterers()[i].label
                  for i in range(groups.size())
                  if groups[i] >= 0
                  and xray_structure.scatterers()[i].flags.grad_fp()]
    if correlated:
      print("DispRadial: f' and f'' are also being refined on %s; they and the"
            " coefficients both scale the anomalous part, so expect them to"
            " correlate" % ', '.join(correlated))
  return dc


def save_coefficients(xray_structure, dc, esds=None):
  """Keep the refined coefficients for the next run."""
  mode = str(OV.GetParam('snum.DispRadial.mode', 'element'))
  selection = _split(OV.GetParam('snum.DispRadial.selection', ''))
  n_terms = int(OV.GetParam('snum.DispRadial.n_terms', 2))
  basis = str(OV.GetParam('snum.DispRadial.basis', 'cos_2theta'))
  OV.SetParam('snum.DispRadial.coefficients',
              json.dumps([float(c) for c in dc.coefficients]))
  OV.SetParam('snum.DispRadial.coefficients_hash',
              _hash(xray_structure, mode, selection, n_terms, basis,
                    _wavelength()))
  if esds is not None:
    OV.SetParam('snum.DispRadial.esds',
                json.dumps([float(e) for e in esds]))


def report(xray_structure, dc, esds=None, out=None):
  """The coefficients, and what they do to R over the data's own range.

  R going negative somewhere in range means f' and f'' change sign there, which
  is not a refinement one should report without noticing.
  """
  import sys
  if out is None:
    out = sys.stdout
  names = getattr(dc, 'group_names', None) or \
    ['group %i' % g for g in range(dc.n_groups)]
  d_star_sq = [xray_structure.unit_cell().d_star_sq(h)
               for h in _indices(xray_structure)]
  if d_star_sq:
    lo, hi = min(d_star_sq), max(d_star_sq)
  else:
    lo, hi = 0., 4.
  if dc.in_cos_two_theta:
    variable = 'u = 1 - cos(2theta)'
  else:
    variable = 'u = sin(theta)/lambda'
  print("Radial correction of f' and f'' -- R = 1 + c1 u + c2 u^2 + ...,"
        " %s%s" % (variable, '' if dc.grad else '   [FIXED, not refined]'),
        file=out)
  n = dc.n_terms
  for g, name in enumerate(names):
    terms = []
    for k in range(n):
      c = dc.coefficients[g*n + k]
      if esds is not None and len(esds) == dc.n_param:
        terms.append('c%i = %9.5f(%.5f)' % (k + 1, c, esds[g*n + k]))
      else:
        terms.append('c%i = %9.5f' % (k + 1, c))
    print('  %-6s %s' % (name, '  '.join(terms)), file=out)
    r_lo, r_hi = dc.R_at(lo, g), dc.R_at(hi, g)
    print('  %-6s R(%.3f) = %.4f   R(%.3f) = %.4f'
          % ('', lo**0.5/2, r_lo, hi**0.5/2, r_hi), file=out)
    worst = _smallest_R(dc, g, lo, hi)
    if worst <= 0:
      print("  %-6s WARNING: R falls to %.4f inside the data range, so f' and"
            " f'' change sign there" % ('', worst), file=out)


def _indices(xray_structure):
  try:
    return list(olex_hkl_indices())
  except Exception:
    return []


def olex_hkl_indices():
  """The reflections actually being refined against, for the range of s."""
  from cctbx_olex_adapter import OlexCctbxAdapter
  return OlexCctbxAdapter().reflections.f_sq_obs_filtered.indices()


def _smallest_R(dc, group, d_star_sq_lo, d_star_sq_hi, n=100):
  values = []
  for i in range(n + 1):
    x = d_star_sq_lo + (d_star_sq_hi - d_star_sq_lo)*i/n
    values.append(dc.R_at(x, group))
  return min(values)


class DispRadial(PT):
  def __init__(self):
    self.p_name = p_name
    # No GUI entry unless debugging: this is macro-only for now, and a tool
    # button for something with no controls behind it is a promise the plugin
    # does not keep. p_htm is what puts it in the tool index; the macros are
    # registered either way.
    self.p_htm = p_htm if OV.IsDebugging() else None
    self.p_img = p_img
    self.p_scope = p_scope
    self.p_path = p_path
    self._load_phil()
    self.register_methods()

  def _load_phil(self):
    phil_path = os.path.join(p_path, 'DispRadial.phil')
    with open(phil_path, 'r', encoding='utf-8') as f:
      phil = f.read()
    olx.phil_handler.adopt_phil(phil_string=phil)
    olx.phil_handler.rebuild_index()

  def register_methods(self):
    # OV.registerMacro has no namespace argument, so these go through olex
    # directly, the way leverage.py does
    olex.registerMacro(self.setup,
      "elements-element symbols to give a shared radial function, e.g. Br,I"
      "&;atoms-atom labels to give one each, e.g. Pd1"
      "&;n-how many powers of the variable (1..%i, default 2)" % MAX_TERMS
      + "&;basis-cos_2theta (default) or stol",
      False, "disprad")
    olex.registerMacro(self.set,
      "group-which group to set, by element symbol or atom label; omit to give"
      " every coefficient at once"
      "&;c-the coefficients, comma separated, in order c1,c2,..."
      "&;fix-also stop refining them (default False)",
      False, "disprad")
    olex.registerMacro(self.fix, "", False, "disprad")
    olex.registerMacro(self.refine, "", False, "disprad")
    olex.registerMacro(self.print_current, "", False, "disprad")
    olex.registerMacro(self.plot, "", False, "disprad")
    olex.registerMacro(self.remove, "", False, "disprad")

  def setup(self, elements=None, atoms=None, n=None, basis=None):
    """Turn the correction on for a set of elements or of atoms."""
    if elements and atoms:
      print('DispRadial: give elements or atoms, not both')
      return
    if basis is not None:
      basis = str(basis)
      if basis not in ('cos_2theta', 'stol'):
        print("DispRadial: basis must be cos_2theta or stol, got '%s'" % basis)
        return
      OV.SetParam('snum.DispRadial.basis', basis)
    if atoms:
      OV.SetParam('snum.DispRadial.mode', 'atom')
      OV.SetParam('snum.DispRadial.selection', str(atoms))
    elif elements:
      OV.SetParam('snum.DispRadial.mode', 'element')
      OV.SetParam('snum.DispRadial.selection', str(elements))
    else:
      OV.SetParam('snum.DispRadial.mode', 'element')
      OV.SetParam('snum.DispRadial.selection', '')
    if n is not None:
      n = int(n)
      if n < 1 or n > MAX_TERMS:
        print('DispRadial: n must be between 1 and %i' % MAX_TERMS)
        return
      if n > 2:
        print('DispRadial: %i terms of an unnormalised s span three decades by'
              ' the highest power; expect the coefficients to be poorly'
              ' determined' % n)
      OV.SetParam('snum.DispRadial.n_terms', n)
    # a different selection makes any stored coefficients meaningless, and the
    # hash would catch it anyway; clearing them says so plainly. Refining is
    # reset with them: setting up again and silently inheriting a fix from
    # whatever was there before is not what anyone means by it.
    OV.SetParam('snum.DispRadial.coefficients', '')
    OV.SetParam('snum.DispRadial.coefficients_hash', '')
    OV.SetParam('snum.DispRadial.esds', '')
    OV.SetParam('snum.DispRadial.refine', True)
    OV.SetParam('snum.DispRadial.enabled', True)
    self.print_current()

  def print_current(self):
    """What is set up, and what the last refinement made of it."""
    if not OV.GetParam('snum.DispRadial.enabled', False):
      print('DispRadial: not enabled')
      return
    from cctbx_olex_adapter import OlexCctbxAdapter
    xs = OlexCctbxAdapter().xray_structure()
    dc = build_correction(xs, log=False)
    if dc is None:
      print('DispRadial: enabled but nothing to refine')
      return
    try:
      esds = json.loads(OV.GetParam('snum.DispRadial.esds', '') or '[]')
    except ValueError:
      esds = []
    report(xs, dc, esds if len(esds) == dc.n_param else None)

  def set(self, group=None, c=None, fix=None):
    """Put values of your own into one group, or into all of them.

    disprad.set group=Pd c=-1.8,2.0     one group, by element or atom label
    disprad.set c=-1.8,2.0,-0.3,0.1     every coefficient, group-major
    disprad.set group=Pd c=-1.8,2.0 fix=True

    Setting values does not by itself stop them being refined -- they may be a
    starting point rather than an answer. Add fix=True, or say disprad.fix.
    """
    if c is None:
      print('DispRadial: give the coefficients, e.g. disprad.set group=Pd'
            ' c=-1.8,2.0')
      return
    try:
      values = [float(v) for v in _split(str(c))]
    except ValueError:
      print("DispRadial: could not read '%s' as a list of numbers" % c)
      return
    if not OV.GetParam('snum.DispRadial.enabled', False):
      print('DispRadial: not enabled; run disprad.setup first so there are'
            ' groups to set')
      return

    from cctbx_olex_adapter import OlexCctbxAdapter
    xs = OlexCctbxAdapter().xray_structure()
    dc = build_correction(xs, log=False)
    if dc is None:
      print('DispRadial: nothing set up to put values into')
      return
    names = getattr(dc, 'group_names', [])
    n = dc.n_terms

    if group is None:
      if len(values) != dc.n_param:
        print('DispRadial: %i coefficient(s) wanted, %i given. The order is'
              ' %s, %i term(s) each.'
              % (dc.n_param, len(values), ', '.join(names), n))
        return
      coefficients = values
    else:
      group = str(group)
      matching = [i for i, name in enumerate(names)
                  if name.upper() == group.upper()]
      if not matching:
        print("DispRadial: no group called '%s'; there is %s"
              % (group, ', '.join(names) or 'none'))
        return
      if len(values) != n:
        print('DispRadial: %i term(s) per group, %i given' % (n, len(values)))
        return
      # the ones already in place stay put, so groups can be set one at a time
      coefficients = [dc.coefficients[i] for i in range(dc.n_param)]
      g = matching[0]
      coefficients[g*n:(g + 1)*n] = values

    OV.SetParam('snum.DispRadial.coefficients', json.dumps(coefficients))
    # by hand, so no longer the output of any refinement
    OV.SetParam('snum.DispRadial.coefficients_hash', '')
    OV.SetParam('snum.DispRadial.esds', '')
    if fix is not None and str(fix).lower() in ('true', '1', 'yes'):
      OV.SetParam('snum.DispRadial.refine', False)
    self.print_current()

  def fix(self):
    """Hold the coefficients where they are; the correction still applies."""
    OV.SetParam('snum.DispRadial.refine', False)
    # they are no longer what any refinement produced, and no s.u. describes
    # a number that is not being refined
    OV.SetParam('snum.DispRadial.esds', '')
    self.print_current()

  def refine(self):
    """Let the coefficients refine again, starting from where they are."""
    OV.SetParam('snum.DispRadial.refine', True)
    self.print_current()

  def plot(self):
    """f' and f'' against sin(theta)/lambda: flat before, curved after."""
    # imported here rather than at the top: it pulls in the whole Analysis
    # module, which is not worth doing on every Olex2 start
    from disp_radial_plot import make_plot
    make_plot()

  def remove(self):
    """Switch it off and forget the coefficients."""
    OV.SetParam('snum.DispRadial.enabled', False)
    OV.SetParam('snum.DispRadial.coefficients', '')
    OV.SetParam('snum.DispRadial.coefficients_hash', '')
    OV.SetParam('snum.DispRadial.esds', '')
    OV.SetParam('snum.DispRadial.refine', True)
    print('DispRadial: off')


disp_radial_instance = DispRadial()
