"""References the CIF carries for the NoSpherA2 methods a refinement used.

CifInfo asks nsa2_cif_references() once per CIF: the references to add, and the
markers of every reference this module manages. An entry of an existing CIF that
matches a marker is dropped before the active ones are added, so a method that is
no longer used loses its reference, and one typed differently (by hand, an older
Olex2, an in-press entry since published) is replaced by the current text.

A new method is one line in _METHOD_REFERENCES; a new way of using one is a line
in methods_used().
"""


def _norm(text):
  return ''.join(str(text).replace('\r', '').split())


# (method tag, reference, markers). The markers identify the entry in a CIF however
# it was typed; an in-press entry leaves "in press" out of them so that its
# published form later replaces it.
_METHOD_REFERENCES = (
  ('NoSpherA2', """Kleemiss, F., Dolomanov, O.V., Bodensteiner, M., Peyerimhoff, N., Midgley, L.,
Bourhis, L.J., Genoni, A., Malaspina, L.A., Jayatilaka, D., Spencer, J.L.,
White, F., Grundkoetter-Stock, B., Steinhauer, S., Lentz, D., Puschmann, H.,
Grabowsky, S. (2021), Chem. Sci., 12, 1675-1692.""", ("1675-1692", "2021")),
  ('Thakkar IAM', """Kleemiss, F., Peyerimhoff, N., Bodensteiner, M. (2024),
J. Appl. Cryst., 57, 161-174.""", ("161-174", "2024")),
  ('RI-fit', """Seifert, L.M., Br\\"ux, D., Piel, T.M., Kleemiss, F. (2026),
Z. Kristallogr. Cryst. Mater., 241, 283-295.""", ("Seifert,L.M.", "283-295")),
  ('MBIS', """Nielsen, A.M.H., Kleemiss, F., Iversen, B.B., Jensen, F. (2026),
IUCrJ, in press.""", ("Nielsen,A.M.H.,Kleemiss", "IUCrJ")),
  ('MBIS', """Verstraelen, T., Vandenbrande, S., Heidar-Zadeh, F., Vanduyfhuys, L.,
Van Speybroeck, V., Waroquier, M., Ayers, P.W. (2016),
J. Chem. Theory Comput., 12, 3894-3912.""", ("Verstraelen", "3894-3912")),
  ('EMBIS', """Nielsen, A.M.H., Jensen, F. (2025), J. Chem. Theory Comput., 21,
8753-8761.""", ("Nielsen", "8753-8761")),
  ('XCW', """Jayatilaka, D. (1998), Phys. Rev. Lett., 80, 798-801.""", ("Jayatilaka", "798-801")),
  ('XCW', """Jayatilaka, D., Grimwood, D.J. (2001), Acta Cryst. A, 57, 76-86.""", ("Jayatilaka", "76-86")),
  ('XCW', """Grimwood, D.J., Jayatilaka, D. (2001), Acta Cryst. A, 57, 87-100.""", ("Grimwood", "87-100")),
)

# generators whose own partition replaces NoSpherA2's, so its partition settings say nothing
_OWN_PARTITION = ('Thakkar IAM', 'SALTED', 'DISCAMB', 'XHARPy')


def methods_used(get, table=''):
  """method tags of _METHOD_REFERENCES behind the active table

  get(key) returns the setting the table was made with ('' when unknown);
  table is its path."""
  low = lambda key: str(get(key) or '').strip().lower()
  made_by = "%s %s" % (get('origin') or '', get('source') or '')
  used = {'NoSpherA2'}
  if 'Thakkar IAM' in made_by:
    used.add('Thakkar IAM')
  if made_by.split()[:1] == ['XCW']:
    used.add('XCW')
    partition = low('XCW.partition')
    ri = partition == 'ri' or low('XCW.tshb') in ('true', '1')
  elif any(g in made_by for g in _OWN_PARTITION) or low('NoSpherA2_SF') in ('false', '0'):
    partition, ri = '', False
  else:
    partition = low('NoSpherA2_Partition')
    ri = partition == 'ri-fit'
  # a .tshb holds RI-fitted densities, whichever route made it (SALTED, RI-Fit, XCW)
  ri = ri or str(table).lower().endswith('.tshb')
  # the RI fit restrains its multipoles to this partition's (-multipole_moments)
  restraint = low('RI_restraint') if ri else ''
  if ri:
    used.add('RI-fit')
  if 'embis' in (partition, restraint):
    used |= {'MBIS', 'EMBIS'}  # EMBIS extends MBIS
  elif 'mbis' in (partition, restraint):
    used.add('MBIS')
  return used


def references_for(used):
  return [ref for tag, ref, _ in _METHOD_REFERENCES if tag in used]


def is_managed(ref, markers):
  """whether a CIF reference entry is one of `markers`' (each a tuple, all must occur)"""
  ref = _norm(ref)
  return any(all(m in ref for m in mk) for mk in markers)


def computing_with(computing, name, generators):
  """_computing_structure_refinement with the generator `name` (or none) in place of any earlier one

  generators: the names a generator can carry there (first words, any case)."""
  generators = set(g.upper() for g in generators)
  parts = [p.strip() for p in str(computing or '').split(';')]
  parts = [p for p in parts if p and p.split()[0].upper() not in generators]
  return '; '.join(parts + ([name] if name else []))


def nsa2_cif_references(aspherical):
  """(references to add, markers of every managed reference, generator citation or None, generator names)

  The settings come from the active table's header; a table made before a key was
  recorded falls back to the live parameter."""
  from NoSpherA2.utilities import _NSA2_CITATIONS, nsa2_table_settings, nsa2_generator_citation
  markers = [tuple(_norm(m) for m in mk) for _, _, mk in _METHOD_REFERENCES]
  markers += [(_norm(ref),) for _, ref in _NSA2_CITATIONS.values()]
  generators = [name for name, _ in _NSA2_CITATIONS.values()]
  if not aspherical:
    return [], markers, None, generators
  from variableFunctions import nsa2_get_param
  settings = nsa2_table_settings() or {}
  def get(key):
    v = settings.get(key.upper())
    if v is None:
      v = nsa2_get_param('file_origin' if key == 'origin' else key)
    return v
  used = methods_used(get, nsa2_get_param('file') or '')
  return references_for(used), markers, nsa2_generator_citation(settings), generators


if __name__ == '__main__':
  def run(table='', **s):
    return methods_used(lambda k: s.get(k.replace('.', '_'), ''), table)
  assert run(source='ORCA 6.1', NoSpherA2_Partition='Hirshfeld', NoSpherA2_SF='True') == {'NoSpherA2'}
  assert run(origin='Thakkar IAM', source='Thakkar IAM', NoSpherA2_Partition='MBIS') == {'NoSpherA2', 'Thakkar IAM'}
  assert run(source='ORCA', NoSpherA2_Partition='EMBIS') == {'NoSpherA2', 'MBIS', 'EMBIS'}
  assert run(source='ORCA', NoSpherA2_Partition='RI-Fit', RI_restraint='MBIS') == {'NoSpherA2', 'RI-fit', 'MBIS'}
  assert run(source='ORCA', NoSpherA2_Partition='Hirshfeld', RI_restraint='MBIS') == {'NoSpherA2'}
  assert run(source='Tonto', NoSpherA2_SF='False', NoSpherA2_Partition='MBIS') == {'NoSpherA2'}
  assert run('a.tshb', origin='SALTED', source='SALTED', RI_restraint='EMBIS') == {'NoSpherA2', 'RI-fit', 'MBIS', 'EMBIS'}
  assert run(origin='XCW', XCW_partition='tfvc', NoSpherA2_Partition='MBIS') == {'NoSpherA2', 'XCW'}
  assert run(origin='XCW', XCW_partition='ri', RI_restraint='Off') == {'NoSpherA2', 'XCW', 'RI-fit'}
  assert run(origin='XCW', XCW_partition='embis') == {'NoSpherA2', 'XCW', 'MBIS', 'EMBIS'}
  assert len(references_for({'NoSpherA2', 'XCW'})) == 4
  markers = [tuple(_norm(m) for m in mk) for _, _, mk in _METHOD_REFERENCES]
  # every reference is recognised by its own markers and by no other entry's
  for tag, ref, mk in _METHOD_REFERENCES:
    assert is_managed(ref, [tuple(_norm(m) for m in mk)]), tag
    assert sum(is_managed(ref, [m]) for m in markers) == 1, tag
  # the published IUCrJ entry and a re-wrapped hand-typed one still count as managed
  assert is_managed("Nielsen, A. M. H., Kleemiss, F., Iversen, B. B., Jensen, F. (2027), IUCrJ, 14, 1-12.", markers)
  assert is_managed("Kleemiss, F. et al.\n(2021), Chem. Sci., 12,\n1675-1692.", markers)
  assert not is_managed("Sheldrick, G.M. (2015), Acta Cryst. C71, 3-8.", markers)
  olex = "olex2.refine 1.5 (Bourhis et al., 2015)"
  assert computing_with(olex + "; ORCA 5.0", "pySCF", ["ORCA", "pySCF"]) == olex + "; pySCF"
  assert computing_with(olex + "; ORCA 6.1", None, ["ORCA"]) == olex
  assert computing_with("", "ORCA 6.1", ["ORCA"]) == "ORCA 6.1"
  print("cif_references self-check ok")
