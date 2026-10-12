""" FLINT's last step (cand15, 12 Oct 2026): prune, then complete the final model, each change kept only when it passes
a significance test, so nothing is fitted to a score.

An atom is tested by the F test at 1 % on a local likelihood: the fixed-weight F^2 sum S with only that atom changed and
the scale re-fitted. The whole change is tested once more after a full refinement (Hamilton at 1 %) and undone when it
fails, or when it leaves an unreadable file or a newly blown ADP.
  prune  drop every atom whose removal does not raise S significantly (b = 4 iso / 9 aniso)
  add    Fo-Fc peaks >= 4 MAD-sigma at bond-to-contact distance from the model, element by best S, kept when
         significant (b = 4), at most the formula's room
Whole COD (82,776 ids) against cand14: fully clean 84.90 -> 85.98 % (+1.08, 95 % CI +1.01 to +1.16; 926 fixed,
28 broken), about 1 s a structure. If neither change holds, the model comes back exactly as FLINT left it.
"""
import os, re, shutil, math, traceback
import numpy as np
import olx, olex
from olexFunctions import OV
from cctbx import xray, maptbx
from cctbx.array_family import flex
from cctbx.eltbx import tiny_pse

K2 = 2*math.pi**2

def crit(b):
  # chi2(b) 99th percentile over b, Wilson-Hilferty; ponytail: the F(b, nu) tail for nu >~ 300, <= 6 % low below
  return 6.635 if b == 1 else (1 - 2/(9.*b) + 2.3263*math.sqrt(2/(9.*b)))**3

def gmin(f, a, b, n=20):
  g = 0.6180339887
  c, d = b - g*(b - a), a + g*(b - a)
  fc, fd = f(c), f(d)
  for _ in range(n):
    if fc < fd:
      b, d, fd = d, c, fc
      c = b - g*(b - a)
      fc = f(c)
    else:
      a, c, fc = c, d, fd
      d = a + g*(b - a)
      fd = f(d)
  return (c, fc) if fc < fd else (d, fd)

def zof(e):
  try:
    return tiny_pse.table(e.strip().capitalize()).atomic_number()
  except (RuntimeError, ValueError):
    return 0

def formula():
  F = {}
  for part in str(olx.xf.GetFormula('list')).split(','):
    if ':' in part:
      e, n = part.split(':')
      e = e.strip().capitalize()
      if e not in ('H', 'D'):
        F[e] = F.get(e, 0) + float(n)
  return F

class LL(object):
  """ S = sum w (Fo^2 - k|Fc|^2)^2 on the merged data, weights fixed from this model (WGHT 0.1), k re-fitted per call """
  def __init__(self):
    from cctbx_olex_adapter import OlexCctbxSolve
    s = OlexCctbxSolve()
    xs = s.xray_structure()
    self.xs = xs.select(flex.bool(xs.scatterers().size(), True))
    self.ms = s.reflections.f_sq_obs_merged.average_bijvoet_mates()
    self.fo2 = self.ms.data().as_numpy_array()
    sg = self.ms.sigmas().as_numpy_array()
    self.ds2 = self.ms.d_star_sq().data().as_numpy_array()
    self.fcm = self.ms.structure_factors_from_scatterers(self.xs, algorithm='direct').f_calc()
    self.fc = self.fcm.data().as_numpy_array()
    a = np.abs(self.fc)**2
    k = (self.fo2*a).sum()/(a*a).sum()
    self.w = 1/np.maximum(sg**2 + (0.1*(np.maximum(self.fo2, 0) + 2*k*a)/3)**2, 1e-12)
    self.S0 = self.S(self.fc)
    self.heavy = [x for x in self.xs.scatterers() if x.scattering_type not in ('H', 'D')]
    self.nu = max(len(self.fo2) - sum(9 if x.flags.use_u_aniso() else 4 for x in self.heavy) - 1, 1)
  def S(self, fc):
    a = np.abs(fc)**2
    wa = self.w*a
    k = (wa*self.fo2).sum()/max((wa*a).sum(), 1e-30)
    return float((self.w*(self.fo2 - k*a)**2).sum())
  def fj(self, i):
    sel = flex.bool(self.xs.scatterers().size(), False)
    sel[i] = True
    return self.ms.structure_factors_from_scatterers(self.xs.select(sel), algorithm='direct').f_calc().data().as_numpy_array()
  def atomf(self, site, e):
    s1 = xray.structure(crystal_symmetry=self.xs.crystal_symmetry())
    s1.add_scatterer(xray.scatterer(label='X', site=site, u=0.0, occupancy=1.0, scattering_type=e))
    s1.scattering_type_registry(table='wk1995')
    return self.ms.structure_factors_from_scatterers(s1, algorithm='direct').f_calc().data().as_numpy_array()

def labels_used():
  used = {}
  for i in range(int(olx.xf.au.GetAtomCount())):
    m = re.match(r'([A-Za-z]+?)(\d+)', str(olx.xf.au.GetAtomName(i)))
    if m:
      used[m.group(1).capitalize()] = max(used.get(m.group(1).capitalize(), 0), int(m.group(2)))
  return used

def nextlabel(used, e):
  used[e] = used.get(e, 0) + 1
  return '%s%d' % (e, used[e])

def prune():
  L, out = LL(), []
  s2 = L.S0/L.nu
  for i, x in enumerate(L.xs.scatterers()):
    if x.scattering_type in ('H', 'D'):
      continue
    b = 9 if x.flags.use_u_aniso() else 4
    if (L.S(L.fc - L.fj(i)) - L.S0)/b/s2 < crit(b):
      out.append(x.label)
  if out:
    olex.m('kill %s' % ' '.join(out))
    olex.m('compaq -q')
  return -len(out)

def add():
  L = LL()
  xs, F = L.xs, formula()
  els = sorted(F) or ['C', 'N', 'O']
  ops = list(xs.space_group().all_ops())
  cap, room = 10**6, None
  zc = float(olx.xf.au.GetZ())
  # the adapter's expectedZs rule: counts that are all one are qualitative, no cap from them
  if F and (len(F) == 1 or max(F.values()) > 1):
    have = {}
    for x in L.heavy:
      have[x.scattering_type] = have.get(x.scattering_type, 0) + x.occupancy*x.multiplicity()
    room = dict((e, F[e]*zc - have.get(e, 0)) for e in F)
    cap = int((sum(F.values())*zc - sum(have.values()))/len(ops) + 0.75)
  if cap <= 0 or not L.heavy:
    return 0
  sel = L.ms.data() > 0
  fo, fc = L.ms.select(sel).f_sq_as_f(), L.fcm.select(sel)
  afc = flex.abs(fc.data())
  k = flex.sum(fo.data()*afc)/flex.sum(afc*afc)
  fft = fo.customized_copy(data=fo.data()/k - afc).phase_transfer(fc).fft_map(
    symmetry_flags=maptbx.use_space_group_symmetry, resolution_factor=1/3.)
  fft.apply_volume_scaling()
  a = fft.real_map_unpadded().as_1d().as_numpy_array()
  sig = 1.4826*float(np.median(np.abs(a - np.median(a))))
  if sig <= 0:
    return 0
  M = np.array(xs.unit_cell().orthogonalization_matrix()).reshape(3, 3).T
  X = np.array([op*x.site for x in L.heavy for op in ops], dtype=float)
  Z = np.array([zof(x.scattering_type) for x in L.heavy for op in ops])
  def near(p, Y):
    d = Y - p
    d -= np.round(d)
    d = np.sqrt(((d @ M)**2).sum(axis=1))
    j = int(d.argmin())
    return float(d[j]), j
  pk = fft.peak_search(parameters=maptbx.peak_search_parameters(peak_search_level=1, interpolate=True,
    min_distance_sym_equiv=0.7), verify_symmetry=False).all(max_clusters=max(40, len(L.heavy)))
  new = []
  for p, h in zip(pk.sites(), pk.heights()):
    if h < 4*sig or len(new) >= cap:
      break
    p = np.array([float(v) for v in p])
    d, j = near(p, X)
    # bond to contact: an H peak sits under 1.15 A, a heavy atom's ripple under its shortest bond
    if not (1.15 if Z[j] <= 10 else 1.4 if Z[j] <= 18 else 1.55) <= d <= 3.3:
      continue
    if new and near(p, np.array([op*q[0] for q in new for op in ops], dtype=float))[0] < 1.15:
      continue
    best = None
    for e in els:
      if room is not None and room.get(e, 0) < 0.5*len(ops):
        continue
      F0 = L.atomf(tuple(p), e)
      u, S = gmin(lambda u: L.S(L.fc + F0*np.exp(-K2*u*L.ds2)), 0.005, 0.25)
      if best is None or S < best[1]:
        best = (e, S, u, F0)
    if best is None or (L.S0 - best[1])/4/(best[1]/max(L.nu - 4, 1)) < crit(4):
      continue
    e, S, u, F0 = best
    L.fc, L.S0, L.nu = L.fc + F0*np.exp(-K2*u*L.ds2), S, max(L.nu - 4, 1)
    new.append((tuple(float(v) for v in p), e, u))
    if room is not None:
      room[e] -= len(ops)
  used = labels_used()
  for site, e, u in new:
    i = olx.xf.au.NewAtom(nextlabel(used, e), *site)
    if i != '-1':
      olx.xf.au.SetAtomU(i, '%.4f' % u)
  return len(new)

def refine():
  """ 4 cycles of the engine as the tidy-up calls it; (S, n, p) or None """
  try:
    from refinement import FullMatrixRefine
    fmr = FullMatrixRefine(max_cycles=4, max_peaks=0)
    fmr.write_oxl = lambda cif_block=None: None
    fmr.run()
    fmr.log.close()
    if fmr.failure:
      return None
    ne = fmr.normal_eqns
    n, p = ne.observations.fo_sq.size(), fmr.reparametrisation.n_independents
    return ne.goof()**2*(n - p), n, p
  except Exception as err:
    print('refine failed: %s' % err)
    return None

def accept(ref, r):
  """ Hamilton at 1 % between two refinements (S, n, p) """
  dp = r[2] - ref[2]
  if dp > 0:
    return (ref[0] - r[0])/dp/(r[0]/(r[1] - r[2])) > crit(dp)
  if dp < 0:
    return (r[0] - ref[0])/(-dp)/(ref[0]/(ref[1] - ref[2])) < crit(-dp)
  return r[0] < ref[0]

def blown(res):
  """ atoms of a written .res with a diagonal U or Uiso in (1, 5) A^2, or 'FV' when a field reads as a free variable the
  FVAR line lacks (|x| > 15 as 10m+p, m > FVAR count): iotbx and SHELXL refuse that file (4 of 82,776 models) """
  out, nfv = set(), 0
  for l in open(res, errors='replace').read().replace('=\n', ' ').splitlines():
    p = l.split()
    if not p:
      continue
    if p[0].upper() == 'FVAR':
      nfv += len(p) - 1
      continue
    if p[0].upper() in ('HKLF', 'END'):
      break
    if nfv and len(p) >= 7 and p[1].isdigit():
      try:
        u = [float(x) for x in p[2:]]
      except ValueError:
        continue
      if any(abs(x) > 15 and int(abs(x)/10 + 0.5) > nfv for x in u):
        out.add('FV')
      if any(1 < x < 5 for x in (u[4:5] if len(u) < 9 else u[4:7])):
        out.add(p[0])
  return out

def final_levers():
  """ prune, then add, on the model in <name>.res; never raises, and leaves that file as it was unless a change held """
  # absolute: after a relative reap OV.FilePath() is 'none', and a refinement with MORE -n fails writing <path>/<name>.npy
  res = os.path.abspath('%s.res' % OV.FileName())
  if not os.path.exists(res) or re.search(r'^\s*(TWIN|HKLF\s+5)', open(res).read(), re.M | re.I):
    return
  orig, cur = res[:-4] + '.flint.res', res[:-4] + '.lever.res'
  def load(f):
    shutil.copyfile(f, res)
    olex.m('reap "%s"' % res)
  kept = []
  try:
    shutil.copyfile(res, orig)
    olex.m('reap "%s"' % res)
    ref = refine()
    ref = ref and refine()
    if ref:
      OV.File(res)
      shutil.copyfile(res, cur)
      load(cur)
    for name, fn in (('pruned', prune), ('added', add)):
      if not ref:
        break
      try:
        ch = fn()
      except Exception:
        print(traceback.format_exc())
        load(cur)
        continue
      if not ch:
        load(cur)
        continue
      r = refine()
      if r and accept(ref, r):
        OV.File(res)
        # a lever must not leave an unreadable file or a newly blown ADP (U > 1 A^2)
        if 'FV' in blown(res) or blown(res) - blown(cur):
          load(cur)
          continue
        shutil.copyfile(res, cur)
        ref = r
        kept.append('%s %d' % (name, abs(ch)))
      else:
        load(cur)
  except Exception as err:
    print('Final levers failed: %s' % err)
    kept = []
  if kept:
    print('Final levers kept (Hamilton at 1 %%): %s atom(s)' % ', '.join(kept))
  else:
    load(orig)
  for f in (orig, cur):
    if os.path.exists(f):
      os.remove(f)
