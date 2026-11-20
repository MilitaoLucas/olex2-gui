
import olex

def makeSpecialCifCharacter(txt):
  txt = txt.replace(r"\a", r"&alpha;")
  txt = txt.replace(r"\A", r"&Alpha;")
  txt = txt.replace(r"\b", r"&beta;")
  txt = txt.replace(r"\B", r"&Beta;")
  txt = txt.replace(r"\c", r"&chi;")
  txt = txt.replace(r"\C", r"&Chi;")
  txt = txt.replace(r"\d", r"&Delta;")
  txt = txt.replace(r"\D", r"&delta;")
  txt = txt.replace(r"\e", r"&epsilon;")
  txt = txt.replace(r"\E", r"&Epsilon;")
  txt = txt.replace(r"\f", r"&phi;")
  txt = txt.replace(r"\F", r"&Phi;")
  txt = txt.replace(r"\g", r"&gamma;")
  txt = txt.replace(r"\G", r"&Gamma;")
  txt = txt.replace(r"\h", r"&eta;")
  txt = txt.replace(r"\H", r"&Eta;")

  txt = txt.replace(r"\k", r"&kappa;")
  txt = txt.replace(r"\K", r"&Kappa;")
  txt = txt.replace(r"\l", r"&lambda;")
  txt = txt.replace(r"\L", r"&Lambda;")
  txt = txt.replace(r"\m", r"&nu;")
  txt = txt.replace(r"\M", r"&Mu;")
  txt = txt.replace(r"\n", r"&nu;")
  txt = txt.replace(r"\N", r"&Nu;")
  txt = txt.replace(r"\o", r"&omicron;")
  txt = txt.replace(r"\O", r"&Omicron;")
  txt = txt.replace(r"\p", r"&phi;")
  txt = txt.replace(r"\P", r"&Phi;")
  txt = txt.replace(r"\q", r"&theta;")
  txt = txt.replace(r"\Q", r"&Theta;")
  txt = txt.replace(r"\r", r"&rho;")
  txt = txt.replace(r"\R", r"&Rho;")
  txt = txt.replace(r"\\sim", "&asymp;").replace(r"\s", r"&sigma;")
  txt = txt.replace(r"\S", r"&Sigma;")
  txt = txt.replace(r"\t", r"&tau;")
  txt = txt.replace(r"\T", r"&Tau;")
  txt = txt.replace(r"\u", r"&upsilon;")
  txt = txt.replace(r"\U", r"&Upsilon;")
  txt = txt.replace(r"\w", r"&omega;")
  txt = txt.replace(r"\W", r"&Omega;")
  txt = txt.replace(r"\x", r"&chi;")
  txt = txt.replace(r"\X", r"&Chi;")
  txt = txt.replace(r"\y", r"&psi;")
  txt = txt.replace(r"\Y", r"&Psi;")
  txt = txt.replace(r"\z", r"&zeta;")
  txt = txt.replace(r"\Z", r"&Zeta;")
  # process <sup>, primitive
  txt = txt.replace("^2^", "<sup>2</sup>")
  return txt

REFERENCE_VARS = ('olex2_reference_long', 'solution_reference_long',
                  'refinement_reference_long')

def report_references():
  """([Olex2, solution, refinement], [the other references]) for the HTML
  report. The first three keep their places (the footer text cites them as
  [1]-[3]); the others are the generated ones in the CIF's
  _publ_section_references (ED N-Beam, NoSpherA2 and its wavefunction program,
  dispersion refinement ...), minus those already among the first three."""
  import olx
  from olexFunctions import OV
  key = lambda ref: ''.join(ref.split())
  first = [olx.GetVar(name, '') for name in REFERENCE_VARS]
  seen = set(key(ref) for ref in first if ref)
  more = []
  refs = OV.get_cif_item('_publ_section_references', '') or ''
  if refs in ('?', '.'):
    refs = ''
  for chunk in refs.replace('\r', '').split('\n\n'):
    ref = chunk.strip()
    if ref and key(ref) not in seen:
      seen.add(key(ref))
      more.append(ref)
  return first, more

def _reference_html(ref):
  ref = ' '.join(ref.split())
  return (ref.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
          .replace('%', '&#37;'))

def references_html():
  """The numbered reference list of the HTML report footer."""
  first, more = report_references()
  return '<ol class="journal_reference">%s</ol>' % ''.join(
    '<li>%s</li>' % _reference_html(ref) for ref in first + more)

def further_references():
  """' Further programs and methods used: [4-6].' when the CIF cites more
  than Olex2 and the solution and refinement programs, else ''."""
  first, more = report_references()
  if not more:
    return ''
  start, end = len(first) + 1, len(first) + len(more)
  label = '[%d]' % start if start == end else '[%d-%d]' % (start, end)
  return ' Further programs and methods used: %s.' % label

_NOT_KNOWN = ('', '?', '.', 'n/a')

def _cif_value(*names):
  from olexFunctions import OV
  for name in names:
    if name.startswith('snum.'):
      val = OV.GetParam(name)
    else:
      val = OV.get_cif_item(name, '')
    val = ' '.join(str(val or '').strip().strip("'\"").split()).rstrip('. ')
    if val.lower() not in _NOT_KNOWN:
      return val
  return ''

def _marked(text):
  return '<span class=replaceThisChar>%s</span>' % _reference_html(text)

def experimental_html():
  """The opening sentences of the HTML report's Experimental paragraph:
  crystallisation, mounting, diffractometer and temperature, each only when
  known, so missing items leave no 'were []' or 'kept at K' behind."""
  import re
  import olex
  from olexFunctions import OV
  formula = olex.f('xf.getFormula(html,2)')
  title = OV.GetParam('snum.report.title') or ''
  compound = formula
  if title:
    compound += ' %s' % _marked('[%s]' % title)

  growth = _cif_value('_exptl_crystal_recrystallization_method')
  mount = _cif_value('_olex2_exptl_crystal_mounting_method',
                     'snum.report.crystal_mounting_method')
  diffractometer = _cif_value('_diffrn_measurement_device_type',
                              'snum.report.diffractometer')
  temperature = _cif_value('_cell_measurement_temperature',
                           '_diffrn_ambient_temperature')

  out = []
  if growth:
    m = re.match(r"^(?:single\s+)?crystals\b[^.]{0,60}?\bwere\s+(?=\S)", growth, re.I)
    if m and '. ' not in growth:
      growth = 'were ' + growth[m.end():]
    elif growth[0].islower():
      if not re.match(r"(?:were|was|are|had|have)\b", growth):
        growth = 'were ' + growth
    else:
      out.append('Single crystals of %s were obtained. %s.' % (compound, _marked(growth)))
      growth = None
    if growth:
      out.append('Single crystals of %s %s.' % (compound, _marked(growth)))
    selected = 'A suitable crystal was selected'
  else:
    selected = 'A suitable single crystal of %s was selected' % compound

  mounted = 'mounted'
  if mount:
    m = re.match(r"^(?:the|this|that|it|each|a|single)\b[^.]{0,40}?\b"
                 r"(?:was|were|has been|have been)\s+", mount, re.I)
    if m and mount[m.end():]:
      mounted = mount[m.end():]
    elif mount[0].islower():
      mounted = mount
    else:
      mounted = 'mounted (%s)' % mount
    mounted = _marked(mounted)
  if diffractometer:
    article = 'an' if diffractometer[:1].lower() in 'aeiou' else 'a'
    out.append('%s and %s on %s %s diffractometer.'
               % (selected, mounted, article, _marked(diffractometer)))
  else:
    out.append('%s and %s.' % (selected, mounted))
  if temperature:
    out.append('The crystal was kept at %s&nbsp;K during data collection.'
               % _reference_html(temperature))
  return '\n  '.join(out)

def handleNA(val, ifna):
  if 'n/a' in val.lower():
    return ifna
  return val

registered = False
if not registered:
  registered = True
  olex.registerFunction(makeSpecialCifCharacter, False, "report")
  olex.registerFunction(handleNA, False, "report")
  olex.registerFunction(references_html, False, "report")
  olex.registerFunction(experimental_html, False, "report")
  olex.registerFunction(further_references, False, "report")


