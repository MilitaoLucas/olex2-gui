"""What a protein needs before it can be refined, worked out from the model.

No Olex2 in here. The input is a list of residues and the output is a plain
description of restraints and constraints, so the same code can be emitted as
SHELX instructions for Olex2 or as cctbx proxies for a harness that refines
without it. Keeping the decisions in one place is what makes it possible to
check them at all: the GUI path and the headless path then cannot disagree.

A PDB entry carries statistics about the restraints its depositors used - the
_refine_ls_restr loop - but never the restraints themselves, so a structure
read from one arrives with none. Anisotropic ADPs on a few thousand atoms with
nothing holding them diverge in the first cycle.

What is generated, and why each one:

  RIGU once per residue. The rigid-bond condition says two bonded atoms have
    equal ADP components along the bond. That is a statement about a covalent
    unit, so it belongs within a residue and not across the chain.
  SIMU over the backbone N, CA, C, O of consecutive residues. Similarity
    across a residue boundary is defensible for the backbone, which is
    continuous, and not for side chains, which are not.
  DFIX and DANG from the standard amino acid geometry, plus the peptide bond
    that no single-residue table can hold.
  Occupancy constraints tying alternate conformers of a residue to sum to one,
    which the deposited file states as fixed numbers and therefore cannot
    refine.

Sigmas default to what SHELXL refinements of proteins actually achieve, which
the deposited statistics record: about 0.02 A on bonds and 0.04 A on 1,3
distances. A structure at 3 A wants tighter ones than a structure at 0.9 A.
"""

import aa_geometry

BACKBONE = ("N", "CA", "C", "O")

# The peptide bond and the 1,3 distances that cross it, which live between
# residues and so appear in no per-residue table. From the same idealised
# geometry, measured across a dipeptide.
PEPTIDE_BOND = 1.3290
PEPTIDE_13 = (
  (("CA", "N"), 2.4310),      # CA(i) - N(i+1)
  (("O", "N"), 2.2500),       # O(i)  - N(i+1)
  (("C", "CA"), 2.4350),      # C(i)  - CA(i+1)
)

# Residue classes that are not amino acids and must not be given amino acid
# geometry. Anything else without a table is reported rather than guessed at.
NON_RESIDUE = frozenset(("HOH", "WAT", "DOD"))


class Residue(object):
  """One residue, reduced to what the restraint decisions need.

  atoms maps an upper-case PDB atom name to the label the program knows it
  by, so the geometry table joins directly and the emitter can name atoms.
  """

  def __init__(self, number, chain, cls, atoms, parts=None,
               part_labels=None):
    self.number = int(number)
    self.chain = str(chain)
    self.cls = str(cls).upper()
    self.atoms = atoms
    # {atom name: disorder part}. Part 0 belongs to every conformer; a
    # positive part belongs to one alone. Absent means the residue is ordered.
    self.parts = parts or {}
    # {(name, part): label}. atoms keeps one label per name, which is all the
    # geometry table needs but loses the second conformer entirely - and the
    # second conformer is exactly what a SADI between parts has to name.
    self.part_labels = part_labels or {}

  def part_of(self, name):
    return self.parts.get(name, 0)

  def matched_parts(self):
    """(part_a, part_b, [names present in both]) when two conformers match.

    A minor conformer is usually modelled at low occupancy and is therefore
    poorly determined on its own, but it is the *same* chemical group as the
    major one and should keep its shape. Where both parts carry the same atom
    names, corresponding distances can be tied together - which restrains the
    weak conformer against the strong one rather than against a table.

    Returns None when the residue is ordered, or when the two parts do not
    describe the same set of atoms, since then there is no correspondence to
    exploit and pairing them up would invent one.
    """
    if not self.part_labels:
      return None
    parts = sorted(set(p for (_, p) in self.part_labels if p != 0))
    if len(parts) != 2:
      return None
    a, b = parts
    names_a = set(n for (n, p) in self.part_labels if p == a)
    names_b = set(n for (n, p) in self.part_labels if p == b)
    if not names_a or names_a != names_b:
      return None
    # And the two copies must be separately addressable. A restraint names an
    # atom by its label, and ShelX has no syntax for "the PART 2 one", so
    # where both conformers carry the same label - which is what keeping the
    # PDB atom name for both produces - every SADI written between them would
    # name the same pair twice and restrain nothing.
    if any(self.part_labels[(n, a)] == self.part_labels[(n, b)]
           for n in names_a):
      return None
    return (a, b, sorted(names_a))

  def part_groups(self):
    """[(part, [names])] - the sets an ADP restraint may be built over.

    An alternate conformer is the same atom in another state, so restraining
    one against the other is meaningless: they are never simultaneously
    present, and where a conformer barely moved they sit on top of each other
    and the rigid-bond gradient divides by zero. Atoms of part 0 are shared
    and so join every group.
    """
    present = sorted(set(self.parts.get(n, 0) for n in self.atoms))
    disordered = [p for p in present if p != 0]
    if not disordered:
      return [(0, sorted(self.atoms))]
    shared = [n for n in self.atoms if self.part_of(n) == 0]
    return [(p, sorted(shared + [n for n in self.atoms
                                 if self.part_of(n) == p]))
            for p in disordered]

  def _suffix(self):
    """How a restraint has to name a residue: chain:number, or number alone.

    A bare label is read in the context of whatever residue the instruction
    itself sits in, which for a block written before the atoms is residue 0 -
    so it resolves to nothing. Both SHELXL and the cctbx parser then skip the
    restraint without a word, which is the worst of both: the file looks
    restrained and the refinement is not.

    The chain is not optional once the file has one. Olex2 registers residues
    under their chain, and a bare number is looked up in the no-chain bucket
    only, so '_1' matches nothing at all on a structure written as
    'RESI LYS A:1' - which is every protein that came from a PDB entry.
    """
    if self.chain and self.chain not in (' ', '~'):
      return "_%s:%d" % (self.chain, self.number)
    return "_%d" % self.number

  def ref(self, name):
    """The restraint reference for an atom of this residue."""
    label = self.atoms[name]
    suffix = self._suffix()
    return label if label.endswith(suffix) else label + suffix

  def ref_part(self, name, part):
    """The restraint reference for one conformer's copy of an atom."""
    label = self.part_labels.get((name, part))
    if label is None:
      return self.ref(name)
    suffix = self._suffix()
    return label if label.endswith(suffix) else label + suffix

  def __repr__(self):
    return "Residue(%s:%d %s, %d atoms)" % (
      self.chain, self.number, self.cls, len(self.atoms))


class Plan(object):
  """The restraints and constraints decided for a structure.

  Each entry names atoms by label. Distances are in angstroem; nothing here
  carries a sigma, because the sigma is the caller's policy and not a
  property of the geometry.
  """

  def __init__(self):
    self.rigu = []          # [[label, ...]] - one per residue
    self.simu = []          # [[label, ...]] - one per consecutive pair
    self.dfix = []          # [(distance, label_a, label_b)]
    self.dang = []          # [(distance, label_a, label_b)]
    self.isor = []          # [label] - atoms with no rigid-bond partner
    self.sadi = []          # [(label_a1, label_b1, label_a2, label_b2)]
    self.part_simu = []     # [[label, ...]] - corresponding atoms of 2 parts
    self.free_occupancy = []  # [(part_a labels, part_b labels)] - to tie
    self.unknown_classes = set()
    self.chain_breaks = []  # [(chain, number)] where the next residue is gone

  def counts(self):
    return {
      'RIGU': len(self.rigu), 'SIMU': len(self.simu),
      'DFIX': len(self.dfix), 'DANG': len(self.dang),
      'SADI': len(self.sadi), 'part SIMU': len(self.part_simu),
      'ISOR atoms': len(self.isor),
      'occupancy groups': len(self.free_occupancy),
    }


def _by_chain(residues):
  out = {}
  for r in residues:
    out.setdefault(r.chain, {})[r.number] = r
  return out


def is_hydrogen(name):
  n = name.upper()
  return n.startswith("H") or n.startswith("D")


def plan_restraints(residues, adp=True, geometry=True, hydrogens=False,
                    isolated_adp=False):
  """Decide what this structure needs. Returns a Plan.

  hydrogens is off because a riding constraint already fixes them completely:
  restraining a constrained parameter adds nothing and fights the constraint.
  Turn it on only for a structure whose hydrogens are refined freely, where
  it is much better than nothing but still does not hold them - on crambin it
  cut the number escaping past an angstroem from 212 to 75, no further.
  """
  p = Plan()
  chains = _by_chain(residues)

  for r in residues:
    if adp:
      for (part, names) in r.part_groups():
        # a riding hydrogen has no ADP of its own - its U is a multiple of the
        # pivot's - so including it in a RIGU adds a row that is identically
        # zero, and where the H sits on the pivot it divides by zero
        heavy = [n for n in names if not is_hydrogen(n)]
        if len(heavy) >= 2:
          p.rigu.append([r.ref(n) for n in heavy])
        elif isolated_adp:
          # A lone atom - a water oxygen, an ion, a one-atom ligand - has no
          # rigid-bond partner, so nothing shapes its anisotropic tensor.
          # ISOR restrains it towards isotropic, which sounds right and was
          # measured to be wrong: on 3NIR it took the largest protein shift
          # from 0.31 to 18 A, and it improved nothing on the three other
          # structures. Off unless asked for, and not to be turned on again
          # without re-measuring.
          p.isor.extend(r.ref(n) for n in heavy)
    # Where two conformers describe the same atoms, tie them to each other.
    # The minor one sits at low occupancy and is barely determined on its own,
    # but it is the same chemical group and should keep the same shape: SADI
    # on corresponding distances says so without asserting what that shape is.
    # SIMU, not RIGU, for the ADPs across parts - RIGU divides by the distance
    # between the two atoms, and conformers that barely moved are coincident.
    matched = r.matched_parts()
    if adp and matched is not None:
      pa, pb, names = matched
      for n in names:
        p.part_simu.append([r.ref_part(n, pa), r.ref_part(n, pb)])
    if geometry and matched is not None:
      pa, pb, names = matched
      bonds = aa_geometry.BONDS.get(r.cls) or {}
      for (a, b) in sorted(bonds):
        if a in names and b in names:
          p.sadi.append((r.ref_part(a, pa), r.ref_part(b, pa),
                         r.ref_part(a, pb), r.ref_part(b, pb)))
    if not geometry:
      continue
    if r.cls in NON_RESIDUE:
      continue
    bonds = aa_geometry.BONDS.get(r.cls)
    angles = aa_geometry.ANGLES.get(r.cls)
    if bonds is None:
      # a ligand, a metal or something non-standard: no table, and inventing
      # one would be worse than leaving it free
      p.unknown_classes.add(r.cls)
      continue
    for (a, b), d in sorted(bonds.items()):
      if a in r.atoms and b in r.atoms:
        if not hydrogens and (is_hydrogen(a) or is_hydrogen(b)):
          continue
        p.dfix.append((d, r.ref(a), r.ref(b)))
    for (a, b), d in sorted(angles.items()):
      if a in r.atoms and b in r.atoms:
        if not hydrogens and (is_hydrogen(a) or is_hydrogen(b)):
          continue
        p.dang.append((d, r.ref(a), r.ref(b)))

  # Everything that crosses a residue boundary. A gap in the numbering is
  # treated as a chain break and gets nothing across it: a number that is not
  # a successor is already evidence enough not to tie the two together, and
  # it is recorded so the caller can see how fragmented the model is.
  for chain in sorted(chains):
    numbers = sorted(chains[chain])
    for n in numbers:
      here = chains[chain][n]
      nxt = chains[chain].get(n + 1)
      if nxt is None:
        if n != numbers[-1]:
          p.chain_breaks.append((chain, n))
        continue
      if here.cls in NON_RESIDUE or nxt.cls in NON_RESIDUE:
        continue
      if adp:
        # Backbone only, and only atoms shared by every conformer: tying two
        # residues together through one conformer of a disordered backbone
        # would restrain a state that is not always there.
        labels = [here.ref(a) for a in BACKBONE
                  if a in here.atoms and here.part_of(a) == 0]
        labels += [nxt.ref(a) for a in BACKBONE
                   if a in nxt.atoms and nxt.part_of(a) == 0]
        if len(labels) >= 4:
          p.simu.append(labels)
      if geometry:
        if 'C' in here.atoms and 'N' in nxt.atoms:
          p.dfix.append((PEPTIDE_BOND, here.ref('C'), nxt.ref('N')))
        for (a, b), d in PEPTIDE_13:
          if a in here.atoms and b in nxt.atoms:
            p.dang.append((d, here.ref(a), nxt.ref(b)))
  return p


def as_shelx(plan, bond_sigma=0.02, angle_sigma=0.04,
             rigu_sigma=0.004, simu_sigma=0.04, simu_distance=1.7,
             sadi_sigma=0.02, isor_sigma=0.1, damp=None, npd=True):
  """The plan as SHELX instructions, in the order they should be added.

  damp is (shift, U damping) for a DAMP instruction, or None for none. A
  protein is worth damping whatever else is done to it: the first step of an
  undamped refinement over ten thousand parameters is long enough to take the
  ADPs negative, and a model that starts at its deposited geometry has
  nowhere useful to go in one jump anyway.
  """
  out = []
  if damp is not None:
    out.append("DAMP %g %g" % damp)
  if npd:
    # ShelXL's XNPD, which Olex2 turns into an npd_adp restraint on every
    # anisotropic atom being refined: keep the ADPs positive definite. A
    # protein at atomic resolution has atoms with U as small as 0.007, and a
    # refinement pushes a few of those below zero - a negative ADP is not a
    # small error but a density that cannot exist, and the structure factors
    # cannot be computed once it happens.
    out.append("XNPD")
  for labels in plan.rigu:
    out.append("RIGU %.4f %.4f %s"
               % (rigu_sigma, rigu_sigma, " ".join(labels)))
  for labels in plan.simu:
    out.append("SIMU %.4f %.4f %.2f %s"
               % (simu_sigma, simu_sigma*2, simu_distance, " ".join(labels)))
  # ShelXL takes at most a line's worth of atoms comfortably, so these go out
  # in batches rather than one enormous instruction
  for i in range(0, len(plan.isor), 12):
    batch = plan.isor[i:i + 12]
    out.append("ISOR %.3f %.3f %s"
               % (isor_sigma, isor_sigma*2, " ".join(batch)))
  for (d, a, b) in plan.dfix:
    out.append("DFIX %.4f %.3f %s %s" % (d, bond_sigma, a, b))
  for (d, a, b) in plan.dang:
    out.append("DANG %.4f %.3f %s %s" % (d, angle_sigma, a, b))
  # SADI carries no target: it says two distances are equal, which is the
  # whole point where one conformer is well determined and the other is not.
  for (a1, b1, a2, b2) in plan.sadi:
    out.append("SADI %.3f %s %s %s %s" % (sadi_sigma, a1, b1, a2, b2))
  for labels in plan.part_simu:
    out.append("SIMU %.4f %.4f %.2f %s"
               % (simu_sigma, simu_sigma*2, simu_distance, " ".join(labels)))
  return out
