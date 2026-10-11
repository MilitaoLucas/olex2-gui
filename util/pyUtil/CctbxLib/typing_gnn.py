""" Graph re-typer: the last word on FLINT's element types (cand11, 6 Oct 2026).

Three message-passing networks (typgnn.py, mode fam, trained on whole-COD
pass 4 against the deposited types) read the last re-typing round -- density
read, U, geometry posteriors, neighbours, the pipeline's own call -- plus the
input formula, and pass messages along every contact under 3 A of the final
model. Their averaged posterior re-types an atom when its argmax beats the
pipeline's call by more than the margin (0.3, tuned on fold 7). Held out
(folds 7-9): 1016 of 1628 mistyped-only structures fixed, 31 of 11787 clean
ones broken. Plain numpy so it runs in Olex2's python; the features are
typset.py / typset2.py and the edges graphs.py, line for line.

cand14 (10 Oct 2026): after the network, coord() renames Na, K, Al and Se,
which it cannot assign, from their coordination while the model holds fewer
of the element than the formula's share (lev3.py: 20 structures fixed, none
broken on the whole COD).
"""
import math, itertools
import numpy as np

EL = ['H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si','P','S','Cl','Ar','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni',
      'Cu','Zn','Ga','Ge','As','Se','Br','Kr','Rb','Sr','Y','Zr','Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd','In','Sn','Sb','Te','I','Xe',
      'Cs','Ba','La','Ce','Pr','Nd','Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu','Hf','Ta','W','Re','Os','Ir','Pt','Au',
      'Hg','Tl','Pb','Bi','Po','At','Rn','Fr','Ra','Ac','Th','Pa','U','Np','Pu']
Zof = dict((e, i + 1) for i, e in enumerate(EL))
GEO = ['C','N','O','F','B','P','Cl','I','Si','S','Br']
NBT = ['C','N','O','H','S','P','F','Cl','Br','I','B','Si']
METAL = set(e for e in EL if e not in set(NBT) | set(['He','Ne','Ar','Kr','Xe','Rn','Se','Te','As','Ge','At']))
GRPS = [(1,), (3, 11, 19, 37, 55, 87), (4, 12, 20, 38, 56, 88), tuple(range(21, 31)), tuple(range(39, 49)), tuple(range(72, 81)),
        tuple(range(57, 72)), tuple(range(89, 95)), (5, 13, 31, 49, 81), (6, 14, 32, 50, 82), (7, 15, 33, 51, 83), (8, 16, 34, 52, 84),
        (9, 17, 35, 53, 85), (2, 10, 18, 36, 54, 86)]

def feats(a, T, zc):
  z, u, um = a['z'], a['u'], max(a.get('u_med') or 0, 1e-4)
  fz = Zof.get(a['final'], 0)
  nb = sorted(a.get('nbs') or [])
  d = [x[0] for x in nb]
  cnt = [sum(1 for x in nb if x[1] == t) for t in NBT] + [sum(1 for x in nb if x[1] in METAL)]
  top = a.get('top') or {}
  al = set(T['allowed'])
  dd = (d + [9, 9, 9, 9])[:4]
  return [z, u, um, u / um, fz, z - fz, z / zc if zc else 0, len(nb), np.mean(d) if d else 9] + dd + cnt + \
         [top.get(g, 0) for g in GEO] + [float(g in al) for g in GEO] + [len(al), float(bool(al & METAL)),
         max([Zof.get(e, 0) for e in al] or [0]), T.get('consistency') or 0, len(T['atoms'])]

def ffeats(F, T):
  def frac(c):
    n = sum(v for k, v in c.items() if k not in ('H', 'D')) or 1
    return [c.get(g, 0) / n for g in GEO] + [sum(v for k, v in c.items() if k in METAL) / n]
  got = {}
  for a in T['atoms']:
    got[a['final']] = got.get(a['final'], 0) + 1
  e, g = frac(F), frac(got)
  return e + g + [b - a for a, b in zip(e, g)]

def family(z):
  f = np.zeros((len(z), len(GRPS) + 8))
  for k, g in enumerate(GRPS):
    f[np.isin(z, g), k] = 1
  f[np.arange(len(z)), len(GRPS) + np.searchsorted([0, 2, 10, 18, 36, 54, 86, 118], z, 'left')] = 1
  return f

def edges(S, M, R, Tt, cut=3.0):
  """ every image (all operators, nearest lattice image and its 26
  neighbours) of atom j within 0.3-3 A of atom i, as j -> i """
  img = (np.einsum('oab,nb->ona', R, S) + Tt[:, None, :]).reshape(-1, 3)
  jj = np.tile(np.arange(len(S)), len(R))
  src, dst, dist = [], [], []
  for i in range(len(S)):
    dv = img - S[i]
    dv -= np.round(dv)
    for sh in itertools.product((-1, 0, 1), repeat=3):
      dd = np.sqrt((((dv + sh) @ M) ** 2).sum(1))
      k = np.where((dd < cut) & (dd > .3))[0]
      src += list(jj[k]); dst += [i] * len(k); dist += list(np.round(dd[k], 3))
  return np.array(src, int), np.array(dst, int), np.array(dist, float)

def _erf(x):
  try:
    from scipy.special import erf
    return erf(x)
  except ImportError:
    return np.vectorize(math.erf)(x)

def _gelu(x):
  return 0.5 * x * (1 + _erf(x / math.sqrt(2)))

def _net(W, p, X, src, dst, rb):
  lin = lambda n, x: x @ W[p + n + '.weight'].T + W[p + n + '.bias']
  h = lin('enc.2', _gelu(lin('enc.0', X)))
  for k in range(int(W[p + 'L'])):
    g = 1 / (1 + np.exp(-lin('gate.%d.0' % k, rb)))
    m = lin('msg.%d.2' % k, _gelu(lin('msg.%d.0' % k, np.hstack([h[src], rb])))) * g
    ag = np.zeros_like(h)
    np.add.at(ag, dst, m)
    x = h + lin('upd.%d.3' % k, _gelu(lin('upd.%d.0' % k, np.hstack([h, ag]))))
    h = (x - x.mean(1, keepdims=True)) / np.sqrt(x.var(1, keepdims=True) + 1e-5) * W[p + 'norm.%d.weight' % k] + W[p + 'norm.%d.bias' % k]
  return lin('out.2', _gelu(lin('out.0', h)))

def probs(W, X, fin, src, dst, dist):
  """ averaged masked posteriors over classes [noise] + GEO + [keep] """
  CZ = [int(z) for z in W['CZ']]
  K = len(CZ) + 1
  ci = dict((z, k) for k, z in enumerate(CZ))
  fc = np.array([ci.get(z, K - 1) for z in fin])
  names = [str(n) for n in W['names']]
  Xn = np.hstack([(np.clip(X, W['lo'], W['hi']) - W['mu']) / W['sd'], np.eye(K)[fc], family(fin)])
  M = np.zeros((len(fin), K), bool)
  M[:, 1:K - 1] = np.stack([X[:, names.index('allowed_' + g)] for g in GEO], 1) > 0
  M[np.arange(len(fin)), fc] = True
  M[:, 0] = True
  rb = np.exp(-((dist[:, None] - np.linspace(0.8, 3.0, 24)) / 0.15) ** 2)
  P = 0
  for m in range(int(W['n'])):
    lg = np.where(M, _net(W, 'm%d/' % m, Xn, src, dst, rb), -1e9)
    e = np.exp(lg - lg.max(1, keepdims=True))
    P = P + e / e.sum(1, keepdims=True)
  return P / int(W['n']), fc, CZ, K

def coord(t, F, nb):
  """ t = {label: element} after the network, F the formula, nb = {label:
  [(neighbour, d)]}; returns {label: new element} """
  tot = sum(v for k, v in F.items() if k != 'H') or 1
  n, out = len(t), {}
  short = lambda e: sum(1 for v in t.values() if v == e) < 0.75 * F.get(e, 0) / tot * n
  for a, el in t.items():
    ns = nb.get(a, [])
    on = lambda lo, hi: sum(1 for b, x in ns if lo <= x <= hi and t.get(b) in ('O', 'N'))
    dmin = min([x for _, x in ns] or [9])
    if 'Na' in F and el in ('O', 'N', 'C') and dmin >= 2.0 and on(2.25, 2.65) >= 4 and short('Na'): out[a] = 'Na'
    elif 'K' in F and el in ('O', 'N', 'C', 'P') and dmin >= 2.4 and on(2.6, 3.0) >= 5 and short('K'): out[a] = 'K'
    elif 'Al' in F and el == 'Si':
      o = sorted(x for b, x in ns if t.get(b) == 'O')[:4]
      if len(o) == 4 and sum(o) / 4 > 1.69 and short('Al'): out[a] = 'Al'
    elif 'Se' in F and el == 'S':
      c = [x for b, x in ns if t.get(b) == 'C' and 1.6 <= x <= 2.1]
      if c and sum(c) / len(c) > 1.86 and short('Se'): out[a] = 'Se'
  return out

def retype(path, T, F, labels, S, M, R, Tt, th=None):
  """ T = the last re-typing round {allowed, atoms (rows with label, final,
  z, u, ...), consistency}, F = the input formula {element: count};
  labels / S the model's non-H atoms and fractional sites, M the
  orthogonalisation matrix (row vector convention), R / Tt the space group's
  rotations and translations. Returns {label: (old, new)}. """
  W = np.load(path)
  th = float(W['th']) if th is None else th
  L = dict((a['label'], a) for a in T['atoms'])
  zs = [a['z'] for a in T['atoms'] if a['final'] == 'C']
  zc = float(np.median(zs)) if zs else 0
  ff = ffeats(F, T)
  idx = [k for k, l in enumerate(labels) if l in L and L[l].get('z') is not None and L[l].get('u') is not None]
  if not idx:
    return {}
  rows = [L[labels[k]] for k in idx]
  X = np.array([feats(a, T, zc) + ff for a in rows], np.float32).astype(float)
  fin = np.array([Zof.get(a['final'], 0) for a in rows])
  src, dst, dist = edges(np.asarray(S, float)[idx], M, R, Tt)
  P, fc, CZ, K = probs(W, X, fin, src, dst, dist)
  arg = P.argmax(1)
  marg = P.max(1) - P[np.arange(len(fin)), fc]
  out = {}
  for j in np.where((arg != fc) & (arg != 0) & (arg != K - 1) & (marg > th))[0]:
    out[labels[idx[j]]] = (rows[j]['final'], GEO[arg[j] - 1])
  t = dict((labels[k], out[labels[k]][1] if labels[k] in out else r['final']) for k, r in zip(idx, rows))
  nb = {}
  for a, b, x in zip(src, dst, dist):
    nb.setdefault(labels[idx[b]], []).append((labels[idx[a]], x))
  for l, w in coord(t, F, nb).items():
    out[l] = (L[l]['final'], w)
  return out
