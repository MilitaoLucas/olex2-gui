"""Check a converted .ins for the faults that stop Olex2 loading or refining it.

Every one of these was found the expensive way - by a structure failing hours
into a batch, usually with a message naming neither the instruction nor the
atom. They are all properties of the file, so they can be checked before Olex2
ever sees it.

The AFIX checks use **connectivity from covalent radii**, via
smtbx.utils.connectivity_table, because that is the authority smtbx itself
consults when it decides whether a constraint is buildable. A classification
made from a flat distance cutoff can disagree with it, and then a group that
looks right is refused as "bad connectivity" - which is what made 3NIR drop
forty groups.

usage: validate_ins.py <file.ins> [more.ins ...]
"""
from __future__ import division, print_function

import io
import os
import re
import sys

# AFIX mn: m is the geometry, n the treatment. What each m implies about the
# pivot, taken from the same table mmcif_to_ins writes from.
#   m -> (hydrogens in the group, heavy neighbours the pivot should have)
AFIX_GEOMETRY = {
    1:  (1, 3),   # tertiary XH
    2:  (2, 2),   # secondary XH2
    4:  (1, 2),   # secondary planar XH: aromatic CH, amide NH
    8:  (1, 1),   # terminal tetrahedral XH: hydroxyl, SH
    9:  (2, 1),   # terminal planar XH2: amide NH2
    13: (3, 1),   # rotating terminal XH3: methyl, NH3
}

NOT_ATOMS = set("""TITL CELL ZERR LATT SYMM SFAC UNIT TEMP SIZE OMIT ESEL EGEN
LIST FMAP PLAN MORE BOND CONF HTAB EQIV L.S. CGLS SHEL FVAR WGHT MERG HKLF END
REM RESI PART AFIX ANIS ISOR DELU SIMU RIGU DFIX DANG FLAT CHIV SADI SAME EADP
EXYZ FREE BIND DAMP SWAT EXTI BASF TWIN SPEC MPLA RTAB ACTA BLOC BUMP HFIX
SUMP NEUT DISP LAUE STIR ABIN ANSC ANSR XNPD WPDB MOLE""".split())

ATOM = re.compile(r'^([A-Za-z][A-Za-z0-9_\']*)\s+(\d+)\s+'
                  r'(-?\d*\.\d+)\s+(-?\d*\.\d+)\s+(-?\d*\.\d+)\s+(-?\d*\.\d+)')


class Problem(object):
    def __init__(self, kind, line, text):
        self.kind, self.line, self.text = kind, line, text

    def __str__(self):
        return "  line %-6s %-18s %s" % (self.line, self.kind, self.text)


def scan(path):
    """Read the file once, returning its atoms in order and its structure."""
    atoms, cards = [], []
    resi, part, afix = (None, None), 0, None
    continued = False
    for n, raw in enumerate(io.open(path, encoding='utf-8',
                                    errors='replace'), 1):
        s = raw.rstrip('\n')
        if not s.strip():
            continued = False
            continue
        if continued:
            continued = s.rstrip().endswith('=')
            continue
        word = s.split()[0].upper()
        if word == 'RESI':
            w = s.split()
            num = None
            if len(w) > 2 and ':' in w[2]:
                try: num = int(w[2].split(':')[1])
                except ValueError: pass
            elif len(w) > 2:
                try: num = int(w[2])
                except ValueError: pass
            resi = (w[1] if len(w) > 1 else '?', num)
            cards.append(('RESI', n, resi))
        elif word == 'PART':
            w = s.split()
            part = int(float(w[1])) if len(w) > 1 else 0
            cards.append(('PART', n, part))
        elif word == 'AFIX':
            w = s.split()
            code = int(float(w[1])) if len(w) > 1 else 0
            afix = None if code == 0 else code
            cards.append(('AFIX', n, code))
        elif word == 'LATT':
            cards.append(('LATT', n, int(float(s.split()[1]))))
        elif word == 'SYMM':
            cards.append(('SYMM', n, s.split(None, 1)[1].strip()))
        elif word not in NOT_ATOMS:
            m = ATOM.match(s)
            if m:
                atoms.append({
                    'line': n, 'label': m.group(1), 'occ': float(m.group(6)),
                    'u': None, 'resi': resi, 'part': part, 'afix': afix,
                    'index': len(atoms),
                })
                tail = s[m.end():].split()
                if tail:
                    try: atoms[-1]['u'] = float(tail[0])
                    except ValueError: pass
        continued = s.rstrip().endswith('=')
    return atoms, cards


def connectivity(path, parts=None):
    """{scatterer index: [neighbour indices]} from covalent radii, or None.

    The same table smtbx consults, so a group this accepts is a group the
    refinement will accept.

    PART is passed through as conformer_indices, or an atom of one alternate
    bonds to atoms of the other and every disordered side chain reads as
    over-coordinated. On 2VB1 that alone was 185 false neighbours.
    """
    try:
        from cctbx import xray
        from cctbx.array_family import flex
        import smtbx.utils
        xs = xray.structure.from_shelx(filename=path)
        kwds = {}
        if parts is not None and len(parts) == xs.scatterers().size():
            kwds['conformer_indices'] = flex.size_t([abs(p) for p in parts])
        ct = smtbx.utils.connectivity_table(xs, **kwds)
        nb = {}
        for i_seq, d in enumerate(ct.pair_asu_table.extract_pair_sym_table()):
            nb.setdefault(i_seq, [])
            for j_seq in d.keys():
                nb.setdefault(j_seq, [])
                nb[i_seq].append(j_seq)
                nb[j_seq].append(i_seq)
        return xs, nb
    except Exception as e:
        return None, str(e)


def check(path):
    problems = []
    atoms, cards = scan(path)

    # --- the file-level ones, which need no chemistry -------------------
    latt = next((v for k, n, v in cards if k == 'LATT'), None)
    symms = [(n, v) for k, n, v in cards if k == 'SYMM']
    if latt is not None and abs(latt) != 1:
        # a SYMM that is a pure translation is the centring, which LATT has
        # already declared - Olex2 rejects the repeat as an invalid matrix list
        for n, v in symms:
            body = v.replace(' ', '').lower()
            if re.match(r'^[+.\d/]*\+?x,[+.\d/]*\+?y,[+.\d/]*\+?z$', body) \
               and body not in ('x,y,z',):
                problems.append(Problem(
                    'symmetry', n,
                    "SYMM %s is a centring translation, which LATT %d already "
                    "declares" % (v, latt)))

    for k, n, v in cards:
        if k == 'RESI' and v[1] is not None and v[1] < 1:
            problems.append(Problem(
                'residue', n,
                "residue number %d - Olex2 keeps 0 for MainResidue and refuses "
                "to rename it" % v[1]))

    for at in atoms:
        if abs(at['occ']) < 10 and at['occ'] != 0:
            problems.append(Problem(
                'occupancy', at['line'],
                "%s has a bare occupancy %.5f, which is free to refine; the "
                "fixed form is 10 + occ" % (at['label'], at['occ'])))
            break   # one is enough, it is always the whole file

    # --- AFIX groups ----------------------------------------------------
    groups = []          # (pivot atom or None, code, [member atoms], line)
    open_group = None
    prev_atom = None
    for k, n, v in sorted([(k, n, v) for k, n, v in cards if k == 'AFIX'] +
                          [('ATOM', a['line'], a) for a in atoms],
                          key=lambda t: t[1]):
        if k == 'AFIX':
            if v == 0:
                if open_group is not None:
                    groups.append(open_group)
                    open_group = None
            else:
                if open_group is not None:      # a group left open
                    groups.append(open_group)
                open_group = [prev_atom, v, [], n]
        else:
            if open_group is not None:
                open_group[2].append(v)
            prev_atom = v
    if open_group is not None:
        groups.append(open_group)

    for pivot, code, members, line in groups:
        m = code // 10 if code >= 10 else code
        want = AFIX_GEOMETRY.get(m)
        if not members:
            problems.append(Problem(
                'afix', line,
                "AFIX %d has no atoms in it - an empty group still binds the "
                "next constraint to a stale index" % code))
            continue
        if pivot is None:
            problems.append(Problem('afix', line,
                                    "AFIX %d has no pivot before it" % code))
            continue
        if any(a['resi'] != pivot['resi'] for a in members):
            problems.append(Problem(
                'afix', line,
                "AFIX %d on %s spans a RESI change - its hydrogens land in "
                "another residue" % (code, pivot['label'])))
        if any(a['part'] != pivot['part'] for a in members):
            problems.append(Problem(
                'afix', line,
                "AFIX %d on %s spans a PART change" % (code, pivot['label'])))
        if want and len(members) != want[0]:
            problems.append(Problem(
                'afix', line,
                "AFIX %d on %s has %d atoms, the geometry implies %d"
                % (code, pivot['label'], len(members), want[0])))

    # a negative U means "this multiple of the pivot's U_eq", so the atom has
    # to be inside a group or there is no pivot to be a multiple of
    in_group = set()
    for pivot, code, members, line in groups:
        for a in members:
            in_group.add(a['index'])
    for at in atoms:
        if at['u'] is not None and at['u'] < 0 and at['index'] not in in_group:
            problems.append(Problem(
                'riding', at['line'],
                "%s has a riding U (%.2f) but is in no AFIX group, so its "
                "pivot is whatever precedes it" % (at['label'], at['u'])))

    # --- what only the connectivity can say -----------------------------
    xs, nb = connectivity(path, [a['part'] for a in atoms])
    if xs is None:
        problems.append(Problem('load', 0,
                                "cctbx will not read this file: %s" % nb))
        return problems, len(atoms), len(groups)

    elements = [s.scattering_type for s in xs.scatterers()]
    n_sc = len(elements)
    for pivot, code, members, line in groups:
        if pivot is None or pivot['index'] >= n_sc:
            continue
        m = code // 10 if code >= 10 else code
        want = AFIX_GEOMETRY.get(m)
        if not want:
            continue
        heavy = [j for j in nb.get(pivot['index'], [])
                 if j < n_sc and elements[j] not in ('H', 'D')]
        if len(heavy) != want[1]:
            problems.append(Problem(
                'connectivity', line,
                "AFIX %d on %s implies %d heavy neighbour(s), the bonding "
                "gives %d - smtbx decides from covalent radii and will refuse "
                "this" % (code, pivot['label'], want[1], len(heavy))))
        for a in members:
            if a['index'] < n_sc and pivot['index'] not in nb.get(a['index'], []):
                problems.append(Problem(
                    'connectivity', a['line'],
                    "%s rides on %s but is not bonded to it"
                    % (a['label'], pivot['label'])))
    return problems, len(atoms), len(groups)


def main():
    worst = 0
    for path in sys.argv[1:]:
        problems, n_atoms, n_groups = check(path)
        by_kind = {}
        for p in problems:
            by_kind[p.kind] = by_kind.get(p.kind, 0) + 1
        head = "%s: %d atoms, %d AFIX groups" % (
            os.path.basename(path), n_atoms, n_groups)
        if not problems:
            print("%s - clean" % head)
            continue
        worst = 1
        print("%s - %d problem(s): %s" % (
            head, len(problems),
            ", ".join("%s x%d" % (k, v) for k, v in sorted(by_kind.items()))))
        shown = {}
        for p in problems:
            shown[p.kind] = shown.get(p.kind, 0) + 1
            if shown[p.kind] <= 3:
                print(str(p))
    return worst


if __name__ == '__main__':
    sys.exit(main())
