"""A downloaded mmCIF, written out as a SHELX .ins that keeps its PDB names.

Olex2 can read an mmCIF and export a .ins, but that export renames the atoms
of every alternate conformer - CB of part 2 becomes something like C3J - and
the PDB atom name is the join to every geometry table there is. Once it is
gone, no restraint can be generated for that conformer.

So the conversion is done here instead, keeping:

  the PDB atom name, with the conformer distinguished by PART as ShelXL
    intends rather than by renaming;
  the residue class, number and chain, as RESI class chain:number;
  the wavelength, which Olex2's export does not carry across and which
    otherwise silently defaults to Mo K-alpha.

Coordinates in this dictionary are orthogonal angstroem and have to be
fractionalised; B_iso_or_equiv is B, so U = B/8pi^2; and the anisotropic
displacements in _atom_site_anisotrop are U in angstroem squared, keyed by
atom id rather than by row order - unlike PDB ANISOU, they are not scaled.

usage: mmcif_to_ins.py <entry.cif> <out.ins> [hkl name]
"""
from __future__ import division, print_function
import math
import sys

EIGHT_PI_SQ = 8.0*math.pi*math.pi

# elements that appear in proteins, in the order SFAC will list them
COMMON = ("C", "N", "O", "S", "P", "SE", "CL", "NA", "MG", "K", "CA",
          "ZN", "FE", "MN", "CU", "NI", "CO", "BR", "I", "F")


# --------------------------------------------------------------------------
# Riding hydrogens
# --------------------------------------------------------------------------
# ShelXL's AFIX mn: m names the geometry, n the treatment, and the pivot is
# the atom *before* the constrained ones. n=3 rides, n=7 rides and lets the
# group rotate about its axis, which is what a methyl wants. The number of
# hydrogens following the instruction has to match the constraint exactly or
# the file will not parse at all.
#
# Restraining hydrogens instead of constraining them does not hold: DFIX and
# DANG on all 419 of crambin's cut the number escaping past one angstroem from
# 212 to 75, but a hydrogen has three parameters and one bond restraint, so it
# can still slide around the sphere. Riding removes the parameters.
#
# U is coded as -1.2 or -1.5, which ShelX reads as that multiple of the
# pivot's U_eq, so the hydrogens carry no displacement parameters either.
AFIX_METHYL = (137, -1.5)      # rotating, terminal tetrahedral XH3
AFIX_CH2 = (23, -1.2)          # secondary XH2
AFIX_NH2 = (93, -1.2)          # terminal planar XH2
AFIX_HYDROXYL = (83, -1.5)     # staggered terminal tetrahedral XH, also SH
AFIX_PLANAR_H = (43, -1.2)     # secondary planar XH: aromatic CH, amide NH
AFIX_TERTIARY = (13, -1.2)     # tertiary XH


def _element_of(name, fallback="C"):
  n = name.upper()
  if n.startswith("SE"):
    return "SE"
  for e in ("C", "N", "O", "S", "P"):
    if n.startswith(e):
      return e
  return fallback


# --------------------------------------------------------------------------
# Protonation
# --------------------------------------------------------------------------
# The hydrogens in a deposited entry already encode a protonation state, and
# it is not always the one wanted: the depositors chose it, often by whatever
# their refinement program did by default, and it corresponds to no stated pH.
# The groups it turns on are few and well known.
#
# What is honest to do here is report what the file actually contains and let
# the caller keep it or drop it. Generating hydrogens at a target pH is a
# different and larger job - it needs the local hydrogen-bonding environment,
# not just a pKa table, since a buried aspartate can stay protonated well
# above its solution pKa - and is deliberately not attempted.
IONISABLE = {
  # residue: (marker hydrogens, what their presence means)
  'ASP': (('HD2',), 'COOH, protonated carboxyl'),
  'GLU': (('HE2',), 'COOH, protonated carboxyl'),
  'LYS': (('HZ1', 'HZ2', 'HZ3'), 'NH3+, protonated amine'),
  'CYS': (('HG',), 'SH, neutral thiol'),
  'TYR': (('HH',), 'OH, neutral phenol'),
  'HIS': (('HD1', 'HE2'), 'imidazole NH'),
  'ARG': (('HH11', 'HH12', 'HH21', 'HH22'), 'guanidinium'),
}


def _disulfides(atoms, cart):
  """The residues whose SG is bonded to another SG.

  A cystine has no HG because its sulfur is bonded to another sulfur, not
  because it lost a proton - and crambin, which is three disulfides holding
  forty-six residues together, would otherwise be reported as six
  deprotonated cysteines.
  """
  sgs = [(i, at) for i, at in enumerate(atoms)
         if at['name'].upper() == 'SG' and str(at['resi']).upper() == 'CYS']
  bonded = set()
  for a in range(len(sgs)):
    for b in range(a + 1, len(sgs)):
      i, j = sgs[a][0], sgs[b][0]
      d2 = sum((cart[i][k] - cart[j][k])**2 for k in range(3))
      if d2 < 2.4*2.4:
        bonded.add((sgs[a][1]['chain'], sgs[a][1]['seq']))
        bonded.add((sgs[b][1]['chain'], sgs[b][1]['seq']))
  return bonded


def protonation_report(atoms, cart=None):
  """What ionisable groups the file's own hydrogens imply.

  Counted per residue rather than assumed from the residue type, because that
  is the only thing the file actually says. HIS is reported by tautomer, since
  which nitrogen carries the hydrogen is the whole question there.
  """
  by_residue = {}
  for at in atoms:
    by_residue.setdefault((at['chain'], at['seq'], at['resi']), set()).add(
      at['name'].upper())
  ss = _disulfides(atoms, cart) if cart is not None else set()
  out = {}
  # A file with no hydrogens says nothing about protonation, and reporting
  # every ionisable group as deprotonated would be an assertion the data do
  # not make. Most deposited protein entries are in this state.
  if not any(at['element'] in ('H', 'D') for at in atoms):
    if ss:
      out['CYS in a disulfide'] = len(ss)
    out['no hydrogens in the file, so no protonation state'] = 1
    return out
  for (chain, seq, cls), names in by_residue.items():
    cls = str(cls).upper()
    if cls not in IONISABLE:
      continue
    markers, meaning = IONISABLE[cls]
    present = [m for m in markers if m in names]
    if cls == 'CYS' and (chain, seq) in ss:
      out['CYS in a disulfide'] = out.get('CYS in a disulfide', 0) + 1
      continue
    if cls == 'HIS':
      key = {0: 'HIS unprotonated', 1: 'HIS %s tautomer' % present[0]
             if present else '', 2: 'HIS doubly protonated (+)'}[len(present)]
    elif not present:
      key = '%s deprotonated' % cls
    else:
      key = '%s %s' % (cls, meaning)
    out[key] = out.get(key, 0) + 1
  return out


def hydrogen_groups_from_geometry(atoms, cart):
  """{index of pivot: (afix code, u code, [indices of its hydrogens])}.

  Worked out from the coordinates rather than from a residue table, because
  the constraint's validity is a property of the structure: smtbx checks the
  pivot's real neighbours, and a backbone N is bonded to the previous
  residue's carbon, which no per-residue table knows about. Classifying from
  the table gave a CH2 constraint to a carbon smtbx could see only one
  neighbour for, and the refinement refused to start.

  Bonds are taken by distance, with disorder respected: an atom of part 1
  bonds to part 1 and to part 0, never to part 2.
  """
  n = len(atoms)
  heavy_nb = [0]*n
  hs_of, nearest = {}, {}
  for i in range(n):
    ai = atoms[i]
    hi = ai['element'] in ('H', 'D')
    for j in range(i + 1, n):
      aj = atoms[j]
      hj = aj['element'] in ('H', 'D')
      if hi and hj:
        continue                      # two hydrogens are never bonded
      pi, pj = ai['part'], aj['part']
      if pi and pj and pi != pj:
        continue                      # different conformers do not bond
      dx = cart[i][0] - cart[j][0]
      if dx > 2.1 or dx < -2.1:
        continue                      # cheap reject before the square root
      d2 = dx*dx + (cart[i][1] - cart[j][1])**2 + (cart[i][2] - cart[j][2])**2
      if hi or hj:
        # X-H, up to 1.5 for S-H and Se-H
        limit = 1.5 if (ai['element'] in ('S', 'SE') or
                        aj['element'] in ('S', 'SE')) else 1.35
        if d2 < limit*limit:
          # Nearest pivot only. A hydrogen can fall inside the bonding radius
          # of two heavy atoms at once, and letting both claim it wrote the
          # same atom into the file twice - which the parser then rejects as a
          # duplicate label, taking the whole structure down with it.
          h, pivot = (i, j) if hi else (j, i)
          # and in the same residue. A riding hydrogen always belongs to a
          # heavy atom of its own residue, and without that the search takes
          # whatever is nearest: 2VB1 has a water oxygen 0.55 A from an
          # asparagine HD22 of part 2 - the two overlap in the deposited
          # model - so the water became a hydroxyl pivot for a hydrogen of
          # another residue, and the constraint surfaced far later as
          # "pivot refers to scatterer 1984, but the structure has 280".
          if (atoms[h]['chain'], atoms[h]['seq']) !=              (atoms[pivot]['chain'], atoms[pivot]['seq']):
            continue
          if h not in nearest or d2 < nearest[h][1]:
            nearest[h] = (pivot, d2)
      elif d2 < 2.1*2.1:
        heavy_nb[i] += 1
        heavy_nb[j] += 1

  for h, (pivot, _) in nearest.items():
    hs_of.setdefault(pivot, []).append(h)

  out = {}
  for pivot, hs in hs_of.items():
    el = atoms[pivot]['element']
    n_h, n_heavy = len(hs), heavy_nb[pivot]
    code = None
    if (n_h, n_heavy) == (3, 1):
      code = AFIX_METHYL
    elif (n_h, n_heavy) == (2, 2):
      code = AFIX_CH2
    elif (n_h, n_heavy) == (2, 1):
      code = AFIX_NH2               # planar XH2: an amide NH2 or a =CH2
    elif n_h == 1 and n_heavy == 1 and el in ('O', 'S', 'SE'):
      code = AFIX_HYDROXYL
    elif (n_h, n_heavy) == (1, 2):
      code = AFIX_PLANAR_H
    elif (n_h, n_heavy) == (1, 3):
      code = AFIX_TERTIARY
    if code is not None:
      out[pivot] = (code[0], code[1], sorted(hs))
  return out


def hydrogen_groups(residue_class, present):
  """{pivot name: (afix_code, u_code, [hydrogen names])} for one residue.

  Worked out from the same idealised geometry the restraints come from, so a
  hydrogen is attached to the heavy atom it is bonded to there, and the class
  follows from how many hydrogens that atom carries and how many heavy
  neighbours it has. A residue with no table, or a hydrogen whose name is not
  in it, yields nothing for that atom - which leaves it an ordinary free atom
  and is reported rather than guessed at.
  """
  import aa_geometry
  bonds = aa_geometry.BONDS.get(str(residue_class).upper())
  if not bonds:
    return {}
  neighbours = {}
  for (a, b) in bonds:
    if a not in present or b not in present:
      continue
    neighbours.setdefault(a, set()).add(b)
    neighbours.setdefault(b, set()).add(a)

  out = {}
  for pivot, nbrs in neighbours.items():
    if _is_h(pivot):
      continue
    hs = sorted(n for n in nbrs if _is_h(n))
    if not hs:
      continue
    n_heavy = len(nbrs) - len(hs)
    el = _element_of(pivot)
    code = None
    if len(hs) == 3:
      code = AFIX_METHYL              # CH3, and a terminal NH3 rotates too
    elif len(hs) == 2:
      code = AFIX_CH2 if el == "C" else AFIX_NH2
    elif len(hs) == 1:
      if el in ("O", "S", "SE"):
        code = AFIX_HYDROXYL
      elif el == "N":
        code = AFIX_PLANAR_H
      elif el == "C":
        code = AFIX_TERTIARY if n_heavy >= 3 else AFIX_PLANAR_H
    if code is not None:
      out[pivot] = (code[0], code[1], hs)
  return out


def _is_h(name):
  n = name.upper()
  return n.startswith("H") or n.startswith("D")


def _first_block(model, needed):
  for name in model:
    if needed in model[name]:
      return model[name]
  return None


def _f(block, key, default=None):
  v = block.get(key)
  if v is None:
    return default
  try:
    return float(str(v).split('(')[0])
  except (TypeError, ValueError):
    return default


def convert(cif_path, ins_path, hkl_name=None, model_num="1",
            keep_hydrogens=True, protonation="as_deposited",
            drop_solvent_u=0.9):
  """Write ins_path from cif_path. Returns a short summary dict."""
  import iotbx.cif
  from cctbx import crystal, sgtbx, uctbx

  model = iotbx.cif.reader(file_path=cif_path).model()
  block = _first_block(model, "_atom_site.label_atom_id")
  if block is None:
    raise RuntimeError("%s has no _atom_site loop" % cif_path)

  a = _f(block, "_cell.length_a")
  b = _f(block, "_cell.length_b")
  c = _f(block, "_cell.length_c")
  al = _f(block, "_cell.angle_alpha", 90.0)
  be = _f(block, "_cell.angle_beta", 90.0)
  ga = _f(block, "_cell.angle_gamma", 90.0)
  if None in (a, b, c):
    raise RuntimeError("%s has no cell" % cif_path)
  uc = uctbx.unit_cell((a, b, c, al, be, ga))

  hm = block.get("_symmetry.space_group_name_H-M") or \
       block.get("_space_group.name_H-M_alt")
  sg = None
  if hm:
    try:
      sg = sgtbx.space_group_info(symbol=str(hm).strip())
    except Exception:
      sg = None
  if sg is None:
    n = block.get("_symmetry.Int_Tables_number")
    if n:
      sg = sgtbx.space_group_info(number=int(str(n).strip()))
  if sg is None:
    raise RuntimeError("%s has no usable space group" % cif_path)
  symmetry = crystal.symmetry(unit_cell=uc, space_group_info=sg)

  # the wavelength, which otherwise defaults to Mo and quietly changes f' f''
  wavelength = (_f(block, "_diffrn_source.pdbx_wavelength") or
                _f(block, "_diffrn_radiation_wavelength.wavelength") or
                0.71073)

  def col(*names):
    for n in names:
      if n in block:
        return block[n]
    return None

  name_c = col("_atom_site.label_atom_id")
  elem_c = col("_atom_site.type_symbol")
  comp_c = col("_atom_site.auth_comp_id", "_atom_site.label_comp_id")
  seq_c = col("_atom_site.auth_seq_id", "_atom_site.label_seq_id")
  asym_c = col("_atom_site.auth_asym_id", "_atom_site.label_asym_id")
  alt_c = col("_atom_site.label_alt_id")
  x_c = col("_atom_site.Cartn_x")
  y_c = col("_atom_site.Cartn_y")
  z_c = col("_atom_site.Cartn_z")
  occ_c = col("_atom_site.occupancy")
  b_c = col("_atom_site.B_iso_or_equiv")
  id_c = col("_atom_site.id")
  mdl_c = col("_atom_site.pdbx_PDB_model_num")

  # The anisotropic loop, keyed by atom id. The values are U_cart in angstroem
  # squared, while a ShelX .ins carries U_cif - referred to the reciprocal
  # cell axes - so they have to be converted. Written straight through, the
  # anisotropic model is no better than making every atom isotropic with the
  # same U_eq, which at 0.54 A is proof enough that the basis is wrong.
  from cctbx import adptbx
  aniso = {}
  ab = _first_block(model, "_atom_site_anisotrop.U[1][1]")
  if ab is not None:
    aid = ab["_atom_site_anisotrop.id"]
    u11 = ab["_atom_site_anisotrop.U[1][1]"]
    u22 = ab["_atom_site_anisotrop.U[2][2]"]
    u33 = ab["_atom_site_anisotrop.U[3][3]"]
    u12 = ab["_atom_site_anisotrop.U[1][2]"]
    u13 = ab["_atom_site_anisotrop.U[1][3]"]
    u23 = ab["_atom_site_anisotrop.U[2][3]"]
    for i in range(len(aid)):
      try:
        # the file lists U11 U22 U33 U12 U13 U23; cctbx wants that same order
        cart = (float(u11[i]), float(u22[i]), float(u33[i]),
                float(u12[i]), float(u13[i]), float(u23[i]))
      except ValueError:
        continue
      cif = adptbx.u_star_as_u_cif(uc, adptbx.u_cart_as_u_star(uc, cart))
      # and ShelXL writes them U11 U22 U33 U23 U13 U12
      aniso[str(aid[i]).strip()] = (cif[0], cif[1], cif[2],
                                    cif[5], cif[4], cif[3])

  dropped_waters = 0
  # alternate locations become PART numbers, in the order they first appear
  alt_seen = {}

  atoms, elements = [], []
  for i in range(len(name_c)):
    if mdl_c is not None and str(mdl_c[i]).strip() not in ("1", ".", "?", ""):
      continue          # first model only; an NMR ensemble is not a structure
    el = str(elem_c[i]).strip().upper() if elem_c is not None else "C"
    if el in ("H", "D") and (not keep_hydrogens or protonation == "none"):
      # Deposited hydrogens are real refined positions, not idealised ones,
      # and at high resolution they carry real scattering: dropping them from
      # crambin at 0.54 A costs about ten points of R1. Kept by default and
      # discarded only on request.
      continue
    if el not in elements:
      elements.append(el)
    frac = uc.fractionalize((float(x_c[i]), float(y_c[i]), float(z_c[i])))
    alt = str(alt_c[i]).strip() if alt_c is not None else "."
    if alt in ("", ".", "?"):
      part = 0
    else:
      part = alt_seen.setdefault(alt, len(alt_seen) + 1)
    try:
      seq = int(str(seq_c[i]).strip())
    except (TypeError, ValueError):
      seq = None
    b_iso = _f({"b": b_c[i]}, "b", 15.0) if b_c is not None else 15.0
    if (drop_solvent_u
        and str(comp_c[i] if comp_c is not None else "").upper()
            in ('HOH', 'WAT', 'DOD')
        and b_iso/EIGHT_PI_SQ >= drop_solvent_u):
      # A water this diffuse is not supported by the data - U 0.9 is B 71 -
      # and it has six ADP parameters with almost no density to determine
      # them, so they grow: on 3NIR one went from U 0.94 to 1.66 and pushed
      # the Debye-Waller exponent past the point where a structure factor can
      # be computed at all, ending the refinement while the protein itself
      # had moved 0.3 A. Deleting such waters is what a crystallographer does
      # with them; freezing them isotropic was tried instead and was worse,
      # because an isotropic U of 1.15 at 0.48 A overflows where the
      # anisotropic tensor did not.
      dropped_waters += 1
      continue
    atoms.append({
      'name': str(name_c[i]).strip(),
      'element': el,
      'resi': str(comp_c[i]).strip() if comp_c is not None else "",
      'seq': seq,
      'chain': str(asym_c[i]).strip() if asym_c is not None else "",
      'frac': frac,
      'occ': float(occ_c[i]) if occ_c is not None else 1.0,
      'u_iso': b_iso/EIGHT_PI_SQ,
      'aniso': aniso.get(str(id_c[i]).strip()) if id_c is not None else None,
      'part': part,
    })

  # SFAC in a stable order, common elements first so the file reads normally
  elements.sort(key=lambda e: (COMMON.index(e) if e in COMMON else 99, e))
  sfac = {e: i + 1 for i, e in enumerate(elements)}

  sg_ops = symmetry.space_group()
  latt = _latt_number(sg_ops)
  lines = []
  lines.append("TITL from %s" % cif_path.replace("\\", "/").split("/")[-1])
  lines.append("CELL %.5f %.4f %.4f %.4f %.4f %.4f %.4f"
               % (wavelength, a, b, c, al, be, ga))
  lines.append("ZERR %d 0 0 0 0 0 0" % sg_ops.order_z())
  lines.append("LATT %d" % latt)
  for op in _symm_lines(sg_ops):
    lines.append("SYMM %s" % op)
  lines.append("SFAC %s" % " ".join(e.capitalize() for e in elements))
  lines.append("UNIT %s" % " ".join(
    str(max(1, int(round(sg_ops.order_z()*_count(atoms, e)))))
    for e in elements))
  lines.append("")
  lines.append("L.S. 5")
  lines.append("WGHT 0.1")
  lines.append("FVAR 1")
  if hkl_name:
    lines.append('REM <olex2.extras>')
    lines.append('REM <HklSrc "%%.\\\\%s">' % hkl_name)
    lines.append('REM </olex2.extras>')
  lines.append("")

  # Order the atoms so each pivot is immediately followed by its hydrogens,
  # wrapped in AFIX. ShelXL takes the pivot to be the atom before the
  # instruction and counts the constrained ones exactly, so the grouping is
  # the whole of it: a hydrogen written anywhere else stays a free atom.
  for at in atoms:
    at['_afix'] = None
  groups = {}
  if keep_hydrogens:
    cart = [uc.orthogonalize(at['frac']) for at in atoms]
    groups = hydrogen_groups_from_geometry(atoms, cart)

  claimed = set()
  for pivot, (code, u_code, hs) in groups.items():
    atoms[pivot]['_afix'] = (code, u_code)
    for h in hs:
      atoms[h]['_riding'] = u_code
    claimed.update(hs)

  # Emit each pivot immediately before its hydrogens, keeping everything else
  # in file order. A hydrogen written anywhere else stays a free atom.
  ordered, placed, dropped_h = [], set(), 0
  for i, at in enumerate(atoms):
    if i in claimed:
      continue
    if at['element'] in ('H', 'D') and not at.get('_riding'):
      # no constraint claimed it; see the note below
      dropped_h += 1
      placed.add(i)
      continue
    ordered.append(at)
    placed.add(i)
    if at['_afix'] is not None:
      emitted = 0
      for h in groups[i][2]:
        ordered.append(atoms[h])
        placed.add(h)
        emitted += 1
      # an AFIX card with no hydrogens after it still opens a group, and the
      # next atoms - from another residue - fall into it. Only claim the
      # pivot if it really got its hydrogens.
      at['_afix_emitted'] = emitted > 0
  # A hydrogen no constraint claimed has three free parameters and almost no
  # scattering to determine them, so it wanders: 26 such atoms in crambin took
  # the largest shift to 87 angstroem while every constrained one stayed put.
  # Dropping them is the honest option - the whole hydrogen contribution is
  # worth 0.0008 in R1 at this resolution, so a few unmodelled ones cost
  # nothing measurable, and an atom refined into the next unit cell is not a
  # model of anything.
  for i, at in enumerate(atoms):
    if i not in placed:
      if at['element'] in ('H', 'D') and at.get('_riding'):
        # marked riding, but no group ever claimed it, so it reaches here with
        # a negative U and no pivot for that to be a multiple of. ShelXL then
        # takes the preceding atom, which after this reordering is whatever
        # happens to be next to it - in 2VB1 an asparagine HD22 landed between
        # two waters and rode on one of them, and the constraint surfaced much
        # later as "pivot refers to scatterer 1984, but the structure has 280".
        # Same case as the unclaimed hydrogens above, so the same remedy.
        dropped_h += 1
        continue
      ordered.append(at)
  n_riding = len(claimed)
  # hydrogens no constraint claimed: they stay free, which is worth reporting
  # because they are the ones that will wander
  unclassified = dropped_h
  atoms = ordered

  # Olex2 keeps residue 0 for MainResidue, so an entry numbering from zero or
  # below cannot be written as it stands: TAsymmUnit refuses it with "Cannot
  # rename main residue" and the whole file fails to load - 1US0 starts at
  # RESI MET A:0 and produced no atoms at all. Shift the structure so the
  # lowest residue is 1, which keeps the order and the spacing between them.
  # The deposited numbering is lost, but restraints are generated from this
  # file, so nothing downstream depends on matching the entry.
  seqs = [a['seq'] for a in atoms if a['seq'] is not None]
  resi_offset = 1 - min(seqs) if seqs and min(seqs) < 1 else 0
  if resi_offset:
    for a in atoms:
      if a['seq'] is not None:
        a['seq'] += resi_offset

  cur_key, cur_part, open_afix = None, 0, False
  n_aniso = 0
  for at in atoms:
    if open_afix and not at.get('_riding'):
      lines.append("AFIX 0")
      open_afix = False
    key = (at['chain'], at['seq'])
    if key != cur_key:
      if cur_part != 0:
        lines.append("PART 0")
        cur_part = 0
      if at['seq'] is None:
        lines.append("RESI 0")
      else:
        lines.append("RESI %s %s"
                     % (at['resi'],
                        ("%s:%d" % (at['chain'], at['seq'])) if at['chain']
                        else str(at['seq'])))
      cur_key = key
    if at['part'] != cur_part:
      lines.append("PART %d" % at['part'])
      cur_part = at['part']
    f = at['frac']
    # ShelX codes a parameter's behaviour into its value: a bare 1.00000 means
    # an occupancy free to refine starting at one, and 10 has to be added to
    # fix it. Written bare, every atom's occupancy refines - four hundred
    # parameters the data do not determine - and any atom driven towards zero
    # stops scattering and then drifts away with nothing to hold it. That is
    # what threw a proline CB fifty angstroem out of crambin at occupancy
    # 0.009, and a tyrosine CE2 to an occupancy of 1.264.
    head = "%-4s %2d %11.6f %11.6f %11.6f %9.5f" % (
      at['name'], sfac[at['element']], f[0], f[1], f[2], 10.0 + at['occ'])
    if at.get('_riding'):
      # a negative U is read as that multiple of the pivot's U_eq, so a
      # riding hydrogen carries no displacement parameter of its own either
      lines.append("%s %9.5f" % (head, at['_riding']))
    elif at['aniso']:
      u = at['aniso']
      n_aniso += 1
      lines.append("%s %9.5f %9.5f =" % (head, u[0], u[1]))
      lines.append("  %9.5f %9.5f %9.5f %9.5f" % (u[2], u[3], u[4], u[5]))
    else:
      lines.append("%s %9.5f" % (head, at['u_iso']))
    if at.get('_afix') and at.get('_afix_emitted'):
      lines.append("AFIX %d" % at['_afix'][0])
      open_afix = True
  if open_afix:
    lines.append("AFIX 0")
  if cur_part != 0:
    lines.append("PART 0")
  lines.append("HKLF 4")
  lines.append("END")

  with open(ins_path, "w") as out:
    out.write("\n".join(lines) + "\n")
  return {
    'resi_offset': resi_offset,
    'atoms': len(atoms),
    'hydrogens': sum(1 for a in atoms if a['element'] in ('H', 'D')),
    'riding': n_riding,
    'unconstrained H dropped': unclassified,
    'diffuse waters dropped': dropped_waters,
    'anisotropic': n_aniso,
    'residues': len(set((at['chain'], at['seq']) for at in atoms)),
    'parts': len(alt_seen),
    'space_group': str(sg),
    'wavelength': wavelength,
    'protonation': (protonation_report(atoms, [uc.orthogonalize(a['frac'])
                                                for a in atoms])
                    if keep_hydrogens else {}),
  }


def _report_problems(ins_path):
  """Check the finished file and say what is wrong with it.

  Called once the groups smtbx refuses have been pruned, which is the point at
  which the model is actually finished. Every fault validate_ins looks for used
  to surface hours later inside a refinement, naming neither the instruction
  nor the atom - a riding hydrogen whose pivot was a water in another residue
  took a day to find that way. Reported, never raised: a caller may still want
  the file, and this is not the place to decide that.
  """
  try:
    import validate_ins
    for problem in validate_ins.check(ins_path)[0][:5]:
      print("  ** %s" % str(problem).strip())
  except Exception as e:
    print("  ** the model check did not run: %s" % e)


def drop_invalid_afix(ins_path, hkl_path, max_rounds=40):
  """Remove any AFIX group smtbx refuses, until the model builds.

  The classification here works from interatomic distances with a flat
  cutoff, while smtbx decides bonding from covalent radii - so the two can
  disagree about how many neighbours an atom has, and a constraint that looks
  right is then rejected as "bad connectivity". One such atom stops the whole
  refinement before it starts.

  Rather than try to reproduce smtbx's criterion exactly, which would be a
  copy that drifts, its verdict is taken as the authority: build the model,
  and where a constraint is refused drop that one group and try again. The
  affected hydrogens fall back to being ordinary free atoms, which is worse
  than riding but does not prevent the structure from refining, and the count
  is returned so it can be reported rather than hidden.
  """
  import re
  import smtbx.refinement
  dropped = []
  for _round in range(max_rounds):
    try:
      # far enough to build the reparametrisation: from_shelx alone parses the
      # AFIX happily and the constraint is only constructed here, so checking
      # the load was checking nothing
      smtbx.refinement.model.from_shelx(
        ins_or_res=ins_path, hkl=hkl_path).least_squares()
      _report_problems(ins_path)
      return dropped
    except Exception as e:
      m = re.search(r"constraint involving (\S+?):", str(e))
      if m is None:
        raise
      label = m.group(1)
      if not _remove_afix_for(ins_path, label):
        raise
      dropped.append(label)
  _report_problems(ins_path)
  return dropped


def _remove_afix_for(ins_path, label):
  """Delete the AFIX wrapping the group whose pivot is `label`.

  The pivot is the atom before the AFIX, so the block is found by walking to
  the named atom and removing the instruction that follows it and its
  matching AFIX 0. The hydrogens stay, as free atoms.
  """
  """Note: every group with this pivot label, not just the first.

  smtbx names only the label in its complaint, and a protein has one CG2 per
  threonine, valine and isoleucine - so removing the first leaves the real
  offender in place, the next round reports the same label again, and the
  loop grinds through one innocent group per cycle without ever reaching the
  guilty one. On 3NIR that exhausted forty rounds and still failed. Removing
  all of them terminates, at the cost of some constraints that were fine;
  the count is reported rather than hidden.
  """
  lines = open(ins_path).read().splitlines()
  out, i, hit = [], 0, False
  while i < len(lines):
    line = lines[i]
    out.append(line)
    bits = line.split()
    # An anisotropic atom spans two lines, the first ending in '=', so the
    # AFIX that follows its pivot is not always the next line.
    j = i
    while j < len(lines) and lines[j].rstrip().endswith("="):
      j += 1
      out.append(lines[j])
    nxt = lines[j + 1].split() if j + 1 < len(lines) else []
    if (bits and bits[0].upper() == label.upper()
        and nxt[:1] == ["AFIX"] and nxt[1] != "0"):
      hit = True
      i = j + 1                               # skip the opening AFIX
      while i + 1 < len(lines):
        i += 1
        b = lines[i].split()
        if b[:1] == ["AFIX"] and b[1] == "0":
          break                               # and skip the closing AFIX 0
        # The hydrogens go with it. Leaving them behind as free atoms is the
        # worst of both: the constraint that held them is gone and nothing
        # replaces it, which on 3NIR sent one of them 19 angstroem. The
        # policy elsewhere is that a hydrogen we cannot constrain is not
        # modelled, and it applies here too.
      i += 1
      continue
    i = j + 1
  if not hit:
    return False
  with open(ins_path, "w") as f:
    f.write("\n".join(out) + "\n")
  return True


def _count(atoms, element):
  return sum(1 for a in atoms if a['element'] == element)


def _latt_number(sg):
  """The ShelXL LATT code: sign for the inversion, magnitude for centring."""
  letters = {'P': 1, 'I': 2, 'R': 3, 'F': 4, 'A': 5, 'B': 6, 'C': 7}
  t = sg.conventional_centring_type_symbol()
  n = letters.get(t, 1)
  return n if sg.is_centric() else -n


def _symm_lines(sg):
  """The symmetry operations ShelXL wants: primitive, identity omitted.

  LATT carries the centring and the inversion, so only what is left after
  removing both is written. cctbx already holds the group in that form -
  smx() is the list with the lattice translations and the inversion factored
  out - so it is taken from there rather than filtered out of all_ops().

  Doing it by filtering all_ops() emitted the centring operator as a SYMM line
  of its own on every centred group, which LATT had already declared. Olex2
  rejects the repeat with "invalid matrix list" out of SymmSpace::GetInfo, and
  2ERL and 1BYI would not load at all.
  """
  out = []
  for op in sg.smx():
    if op.t().is_zero() and op.r().is_unit_mx():
      continue
    out.append(op.as_xyz(decimal=True, t_first=True))
  return out


def main():
  if len(sys.argv) < 3:
    print(__doc__)
    return 1
  info = convert(sys.argv[1], sys.argv[2],
                 sys.argv[3] if len(sys.argv) > 3 else None,
                 keep_hydrogens="--no-h" not in sys.argv,
                 protonation="none" if "--no-h" in sys.argv
                 else "as_deposited")
  print("%s -> %s" % (sys.argv[1], sys.argv[2]))
  for k in sorted(info):
    if k == 'protonation':
      if info[k]:
        print("  protonation, as the file's own hydrogens have it:")
        for state, n in sorted(info[k].items()):
          print("      %-34s %d" % (state, n))
      continue
    print("  %-14s %s" % (k, info[k]))
  return 0


if __name__ == "__main__":
  sys.exit(main())
