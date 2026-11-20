"""References the CIF carries for the NoSpherA2 methods a refinement used.

CifInfo asks nsa2_cif_reference_keys() once per CIF: the works to cite, and every
work this module manages. A managed work that is no longer used leaves the CIF;
the texts, and the recognition of a work however it was typed (by hand, an older
Olex2, an in-press entry since published), come from References
(etc/CIF/references.bib).

A new method is one line in _METHOD_REFERENCES (and its paper in
references.bib); a new way of using one is a line in methods_used().
"""
import References


# (method tag, key of the paper in etc/CIF/references.bib)
_METHOD_REFERENCES = (
  ('NoSpherA2', 'nosphera2'),
  ('Thakkar IAM', 'thakkar-iam'),
  ('RI-fit', 'ri-fit'),
  ('MBIS', 'mbis-nosphera2'),
  ('MBIS', 'mbis'),
  ('EMBIS', 'embis'),
  ('XCW', 'xcw-beryllium'),
  ('XCW', 'xcw-theory'),
  ('XCW', 'xcw-oxalic-acid'),
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


def reference_keys_for(used):
  return [key for tag, key in _METHOD_REFERENCES if tag in used]


def references_for(used):
  return [References.cif(key) for key in reference_keys_for(used)]


def computing_with(computing, name, generators):
  """_computing_structure_refinement with the generator `name` (or none) in place of any earlier one

  generators: the names a generator can carry there (first words, any case)."""
  generators = set(g.upper() for g in generators)
  parts = [p.strip() for p in str(computing or '').split(';')]
  parts = [p for p in parts if p and p.split()[0].upper() not in generators]
  return '; '.join(parts + ([name] if name else []))


def nsa2_cif_reference_keys(aspherical):
  """(keys to cite, keys of every managed work, (generator name, key) or None, generator names)

  The settings come from the active table's header; a table made before a key was
  recorded falls back to the live parameter."""
  from NoSpherA2.utilities import _NSA2_CITATIONS, nsa2_table_settings, nsa2_generator
  managed = [key for _, key in _METHOD_REFERENCES] + [key for _, key in _NSA2_CITATIONS.values()]
  generators = [name for name, _ in _NSA2_CITATIONS.values()]
  if not aspherical:
    return [], managed, None, generators
  from variableFunctions import nsa2_get_param
  settings = nsa2_table_settings() or {}
  def get(key):
    v = settings.get(key.upper())
    if v is None:
      v = nsa2_get_param('file_origin' if key == 'origin' else key)
    return v
  used = methods_used(get, nsa2_get_param('file') or '')
  return reference_keys_for(used), managed, nsa2_generator(settings), generators


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
  # every reference is recognised as its own work and as no other
  for tag, key in _METHOD_REFERENCES:
    assert References.identify(References.cif(key)) == [key], tag
  # the published IUCrJ entry and a re-wrapped hand-typed one are still recognised
  assert References.identify("Nielsen, A. M. H., Kleemiss, F., Iversen, B. B., Jensen, F. (2027), IUCrJ, 14, 1-12.") == ['mbis-nosphera2']
  assert References.identify("Kleemiss, F. et al.\n(2021), Chem. Sci., 12,\n1675-1692.") == ['nosphera2']
  assert References.identify("Sheldrick, G.M. (2015), Acta Cryst. C71, 3-8.") == ['shelxl']
  olex = "olex2.refine 1.5 (Bourhis et al., 2015)"
  assert computing_with(olex + "; ORCA 5.0", "pySCF", ["ORCA", "pySCF"]) == olex + "; pySCF"
  assert computing_with(olex + "; ORCA 6.1", None, ["ORCA"]) == olex
  assert computing_with("", "ORCA 6.1", ["ORCA"]) == "ORCA 6.1"
  print("cif_references self-check ok")
