
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
  olex.registerFunction(further_references, False, "report")


