""" Model-free twin statistics from intensities alone.

Run by FLINT before it solves and by the twin-law search before it builds its
model-based list. No mmtbx: the Olex2 cctbx bundle does not ship it, so
mmtbx.scaling.twin_analyses is out of reach and the few statistics needed are
computed here.

  <|E^2-1|>  acentric 0.736 untwinned, 0.541 perfect twin
  <|L|>      Padilla & Yeates (2003), local pairs h, h+2e: 0.500 / 0.375
  per law    correlation of E^2(h) and E^2(Th): for a hemihedral twin of
             fraction a, rho = 2a(1-a)/(1-2a+2a^2), inverted for a; and the
             H-test (Yeates 1988), <H> = 1/2 - a

Only reflections acentric under the rotation part of the group enter, so the
zones a 2-fold makes centric stay out. Baselines follow the group the data
carry: a perfectly twinned centrosymmetric crystal has *acentric* statistics,
so in a centric group 0.736 / 0.500 is the twinned end, not the normal one.

A law whose pairs agree to rho ~ 1 is indistinguishable from symmetry the
group lacks; the L-test, which needs no law, is what tells the two apart.
"""
import sys

from cctbx import crystal, miller, sgtbx
import cctbx.sgtbx.lattice_symmetry
import cctbx.sgtbx.cosets
from cctbx.array_family import flex

# (untwinned, perfect twin) for <|E^2-1|> and <|L|>
ACENTRIC = (0.736, 0.541), (0.500, 0.375)
CENTRIC = (0.968, 0.736), (0.637, 0.500)
# ponytail: fixed cuts. TWIN_SCORE 0.45 is <|L|> 0.444 for acentric data,
# about where xtriage starts to worry; tune on the farm's twinned ids
TWIN_SCORE = 0.45
# Real centrosymmetric data read low on <|L|> (noise, heavy atoms): 5 of 20
# untwinned COD controls passed 0.45, the highest at 0.84, the two clear
# twins at 0.94 and 1.14 (29 Oct 2026, 30 twinned + 20 controls)
TWIN_SCORE_CENTRIC = 0.9
ALPHA_MIN = 0.05
ALPHA_SYMMETRY = 0.45   # rho 0.98: the law acts like symmetry
MIN_PAIRS = 50


def twin_laws(cs, max_delta=3.0):
  """ Metric twin laws: the lattice group's cosets over the Laue group, in
  the input basis. iotbx reflection_statistics.possible_twin_laws without its
  printing and P1 expansion. """
  cb = cs.change_of_basis_op_to_minimum_cell()
  min_cs = cs.change_basis(cb)
  lattice = sgtbx.lattice_symmetry.group(min_cs.unit_cell(), max_delta=max_delta)
  lattice.expand_inv(sgtbx.tr_vec((0, 0, 0)))
  lattice.make_tidy()
  laue = min_cs.reflection_intensity_symmetry(anomalous_flag=False) \
    .space_group().build_derived_acentric_group().make_tidy()
  return sgtbx.cosets.left_decomposition_point_groups_only(g=lattice, h=laue) \
    .best_partition_representatives(cb_op=cb.inverse(),
      omit_first_partition=True, omit_negative_determinants=True)


def _intensities(f_obs):
  """ Merged, non-anomalous, absences out, cut where <I/sigma> per shell
  first drops below 3 (as xtriage does for its twin tests), negatives clamped
  to 0. Without the cut, noise pairs weak reflections into |L| ~ 1 and every
  real data set reads as anti-twinned. """
  a = f_obs
  if not a.is_xray_intensity_array():
    a = a.f_as_f_sq()
  if a.anomalous_flag():
    a = a.as_non_anomalous_array()
  a = a.map_to_asu()
  if not a.is_unique_set_under_symmetry():
    a = a.merge_equivalents().array()
  a = a.eliminate_sys_absent(integral_only=True)
  if a.sigmas() is not None and a.size() > 1000:
    a.setup_binner_counting_sorted(reflections_per_bin=200)
    s = a.sigmas().deep_copy()
    s.set_selected(s <= 0, 1e-6)
    ios = a.data() / s
    for b in a.binner().range_used():
      sel = a.binner().selection(b)
      if b > 3 and flex.mean(ios.select(sel)) < 3:   # keep >= 3 shells
        a = a.resolution_filter(d_min=a.binner().bin_d_range(b)[0])
        break
  d = a.data().deep_copy()
  d.set_selected(d < 0, 0.0)
  return a.customized_copy(data=d)


def _e_sq(i_obs):
  """ E^2 = I/(eps <I/eps>) by resolution shell. """
  i_obs.setup_binner_counting_sorted(reflections_per_bin=200)
  q = i_obs.data() / i_obs.epsilons().data().as_double()
  e2 = flex.double(i_obs.size(), 0.0)
  for b in i_obs.binner().range_used():
    sel = i_obs.binner().selection(b)
    if sel.count(True):
      m = flex.mean(q.select(sel))
      if m > 0:
        e2.set_selected(sel, q.select(sel) / m)
  return e2


def l_test(i_ac):
  """ (<|L|>, its standard error, unique pairs) over h, h+2e in P1, in the
  primitive cell: in a centred one h+2e is often absent. """
  p1 = i_ac.change_basis(i_ac.change_of_basis_op_to_primitive_setting()) \
    .expand_to_p1().generate_bijvoet_mates()
  idx, d = p1.indices(), p1.data()
  h, k, l = [c.iround() for c in idx.as_vec3_double().parts()]
  absl = flex.double()
  for dh, dk, dl in ((2, 0, 0), (0, 2, 0), (0, 0, 2)):
    shifted = flex.miller_index(h + dh, k + dk, l + dl)
    p = miller.match_indices(idx, shifted).pairs()
    a, b = d.select(p.column(0)), d.select(p.column(1))
    s = a + b
    ok = s > 0
    absl.extend(flex.abs((a - b).select(ok) / s.select(ok)))
  n = absl.size() // 2   # every pair also comes as its Friedel image
  if n < MIN_PAIRS:
    return None, None, n
  return flex.mean(absl), absl.standard_deviation_of_the_sample() / n**0.5, n


def _cb(law):
  """ The law as a change of basis, with the denominators twin_data uses:
  the coset representatives carry t_den 12, which change_of_basis_op
  rejects. """
  return sgtbx.change_of_basis_op(
    sgtbx.rt_mx(law.as_xyz(), r_den=24, t_den=288))


def law_fraction(e2_ac, law):
  """ (rho, alpha from rho, alpha from the H-test, pairs) for one law.
  `e2_ac` is a miller array of E^2. The image is put back into the original
  symmetry before map_to_asu, so a law that does not normalise the group still
  pairs h with the asu copy of Th. Reflections the law maps onto themselves
  are dropped: they would correlate perfectly with no twinning at all. """
  t = e2_ac.change_basis(_cb(law)) \
    .customized_copy(crystal_symmetry=e2_ac.crystal_symmetry()).map_to_asu()
  p = miller.match_indices(e2_ac.indices(), t.indices()).pairs()
  i0, i1 = p.column(0), p.column(1)
  keep = i0 != i1
  x = e2_ac.data().select(i0.select(keep))
  y = e2_ac.data().select(i1.select(keep))
  n = x.size() // 2   # (h, Th) and (Th, h) both appear
  if n < MIN_PAIRS:
    return None, None, None, n
  rho = flex.linear_correlation(x, y).coefficient()
  a_rho = 0.0
  if rho > 0:
    a_rho = (1 - ((1 - rho) / (1 + rho))**0.5) / 2
  s = x + y
  ok = s > 0
  a_h = 0.5 - flex.mean(flex.abs((x - y).select(ok) / s.select(ok)))
  return rho, a_rho, min(max(a_h, 0.0), 0.5), n


def twin_matrix(law):
  """ SHELX TWIN matrix (rows act on hkl) for a law, via its effect on hkl. """
  cb = _cb(law)
  cols = [cb.apply(flex.miller_index([e]))[0]
          for e in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
  return [cols[c][r] for r in range(3) for c in range(3)]


def intensity_twin_check(f_obs, max_delta=3.0, log=sys.stdout):
  """ Print and return the model-free twin verdict for `f_obs` (amplitudes
  or intensities, merged or not) in the group the array carries. """
  i_obs = _intensities(f_obs)
  e2 = _e_sq(i_obs)
  rot = i_obs.space_group().build_derived_acentric_group()
  ac = ~miller.set(crystal.symmetry(i_obs.unit_cell(), space_group=rot),
                   i_obs.indices(), False).centric_flags().data()
  i_ac = i_obs.select(ac)
  e2_ac = i_ac.customized_copy(data=e2.select(ac), sigmas=None)
  centric_group = i_obs.space_group().is_centric()
  (e_un, e_tw), (l_un, l_tw) = CENTRIC if centric_group else ACENTRIC
  r = {"space_group": str(i_obs.space_group_info()),
       "centric_group": centric_group, "n_acentric": i_ac.size(),
       "e2m1": None, "l": None, "l_se": None, "l_pairs": 0,
       "twin_score": None, "laws": [], "verdict": []}
  if i_ac.size() < MIN_PAIRS:
    r["verdict"].append("too few acentric reflections for a twin check")
  else:
    r["e2m1"] = flex.mean(flex.abs(e2_ac.data() - 1.0))
    r["l"], r["l_se"], r["l_pairs"] = l_test(i_ac)
    if r["l"] is not None:
      r["twin_score"] = (l_un - r["l"]) / (l_un - l_tw)
  l_twinned = r["twin_score"] is not None and r["twin_score"] > (
    TWIN_SCORE_CENTRIC if centric_group else TWIN_SCORE)
  if l_twinned:
    r["verdict"].append(
      "L-test: twinned%s" % (" or the group is wrongly centrosymmetric"
                             if centric_group else ""))
  for law in twin_laws(i_obs.crystal_symmetry(), max_delta):
    try:
      rho, a_rho, a_h, n = law_fraction(e2_ac, law)
      m = twin_matrix(law)
    except Exception as e:   # a non-integral law in a centred setting
      print("Twin check: law %s skipped (%s)" % (law.as_xyz(), e), file=log)
      continue
    hkl = _cb(law).as_hkl()
    r["laws"].append({"law": hkl, "twin": m, "rho": rho, "alpha": a_rho,
                      "alpha_h": a_h, "pairs": n})
    if rho is None or rho < 4.0 / n**0.5 or a_rho < ALPHA_MIN:
      continue
    if a_rho >= ALPHA_SYMMETRY and not l_twinned:
      r["verdict"].append("%s acts as symmetry: the Laue group is too low, "
                          "or a perfect twin the L-test misses" % hkl)
    elif a_rho >= ALPHA_SYMMETRY:
      r["verdict"].append("%s: perfect twin, or symmetry missing from the "
                          "group" % hkl)
    else:
      r["verdict"].append("%s: twin fraction ~%.2f%s" % (
        hkl, a_rho, "" if l_twinned else " (or pseudo-symmetry; the L-test "
        "is clean)"))
  if not r["verdict"]:
    r["verdict"].append("no sign of twinning")

  print("Twin check (intensities only), %s, %d acentric:" % (
    r["space_group"], r["n_acentric"]), file=log)
  if r["e2m1"] is not None:
    print("Twin check:   <|E^2-1|> %.3f (untwinned %.3f, perfect twin %.3f)" % (
      r["e2m1"], e_un, e_tw), file=log)
  if r["l"] is not None:
    print("Twin check:   <|L|> %.3f +- %.3f, %d pairs (untwinned %.3f, "
          "perfect twin %.3f)" % (r["l"], r["l_se"], r["l_pairs"], l_un, l_tw),
          file=log)
  for x in r["laws"]:
    if x["rho"] is None:
      print("Twin check:   law %-12s %d pairs, too few" % (x["law"], x["pairs"]),
            file=log)
    else:
      print("Twin check:   law %-12s TWIN %s  rho %.3f alpha %.3f (H %.3f), "
            "%d pairs" % (x["law"], " ".join("%d" % v for v in x["twin"]),
            x["rho"], x["alpha"], x["alpha_h"], x["pairs"]), file=log)
  for v in r["verdict"]:
    print("Twin check: => %s" % v, file=log)
  return r


if __name__ == "__main__":
  # Synthetic P4 data on a tetragonal lattice: the one metric law (k,h,-l)
  # applied at 0, 0.3 and 0.5 must come back as no twin, ~0.3 and a perfect
  # twin.
  import random
  from cctbx.development import random_structure
  random.seed(1)
  flex.set_random_seed(1)
  xs = random_structure.xray_structure(
    space_group_info=sgtbx.space_group_info("P 4"),
    unit_cell=(11, 11, 17, 90, 90, 90), elements=["C"] * 30 + ["O"] * 6)
  i_calc = xs.structure_factors(d_min=0.8, algorithm="direct").f_calc() \
    .as_intensity_array()
  laws = twin_laws(i_calc.crystal_symmetry())
  assert len(laws) == 1, [l.as_xyz() for l in laws]
  for alpha in (0.0, 0.3, 0.5):
    data = i_calc if alpha == 0 else i_calc.twin_data(laws[0].as_xyz(), alpha)
    r = intensity_twin_check(data)
    law = r["laws"][0]
    assert abs(law["alpha"] - alpha) < 0.06, (alpha, law)
    l_expect = {0.0: 0.5, 0.3: None, 0.5: 0.375}[alpha]
    if l_expect is not None:
      assert abs(r["l"] - l_expect) < 0.03, (alpha, r["l"])
    print()
  print("OK")
