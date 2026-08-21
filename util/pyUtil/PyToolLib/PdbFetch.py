"""Fetching an entry from the PDB, model and structure factors.

Two things come back from https://files.rcsb.org for a given entry code: the
model as mmCIF, which Olex2 reads directly, and, when the depositors provided
them, the observed structure factors as a separate mmCIF. The latter are of no
use to Olex2 in that form, so they are converted to a SHELX .hkl here.

The deposited quantity is normally an amplitude, F and sigma(F), while HKLF 4
wants an intensity. Propagating the error through I = F^2 gives
sigma(I) = 2 F sigma(F), which is the first-order result and what everything
downstream assumes. A few entries deposit intensities instead; those are taken
as they are, since converting them to amplitudes and back would only lose the
weak and negative reflections.

Entries are put in a folder of the user's choosing rather than beside the
program: a protein and its structure factors run to tens of megabytes, and
where that goes is not ours to decide. The choice is remembered in
user.pdb.download_dir.
"""
import os
import olex
import olx
from olexFunctions import OV

PDB_FILE_URL = "https://files.rcsb.org/download/%s.cif"
PDB_SF_URL = "https://files.rcsb.org/download/%s-sf.cif"

# a download of this size or more is worth telling the user about
PROGRESS_THRESHOLD = 2*1024*1024


def normalise_code(code):
  """The entry code as the RCSB writes it, or None if it cannot be one.

  Classic codes are four characters starting with a digit; the extended form
  is pdb_ followed by eight. Anything else is a typing mistake and is better
  refused here than turned into a 404 the user has to interpret.
  """
  if code is None:
    return None
  code = str(code).strip().strip("'\"")
  if not code:
    return None
  if code.lower().startswith("pdb_"):
    rest = code[4:]
    if len(rest) == 8 and rest.isalnum():
      return "pdb_" + rest.lower()
    return None
  if len(code) == 4 and code.isalnum() and code[0].isdigit():
    return code.upper()
  return None


def get_download_dir(ask=True):
  """Where entries are put, asking once and remembering the answer."""
  d = OV.GetParam('user.pdb.download_dir')
  if d and os.path.isdir(d):
    return d
  if not ask:
    return None
  start = d or OV.GetParam('user.folder_view_root') or os.path.expanduser("~")
  d = olx.ChooseDir("Where should PDB entries be downloaded to?", start)
  if not d or d == 'None':
    return None
  OV.SetParam('user.pdb.download_dir', d)
  return d


def set_download_dir():
  """Ask for the folder again, from the GUI."""
  start = OV.GetParam('user.pdb.download_dir') or os.path.expanduser("~")
  d = olx.ChooseDir("Where should PDB entries be downloaded to?", start)
  if d and d != 'None':
    OV.SetParam('user.pdb.download_dir', d)
  return OV.GetParam('user.pdb.download_dir')


def _download(url, dest, what):
  """Fetch url into dest. Returns True, or False if it is not there.

  Anything other than a missing file is raised: a proxy problem or a broken
  connection is worth a traceback, while an entry with no structure factors
  is an ordinary thing that the caller carries on without.
  """
  import urllib.error
  import HttpTools
  try:
    res = HttpTools.make_url_call(url, http_timeout=30)
  except urllib.error.HTTPError as e:
    if e.code == 404:
      return False
    raise
  size = 0
  try:
    size = int(res.headers.get('Content-Length', 0))
  except (TypeError, ValueError):
    size = 0
  loud = size >= PROGRESS_THRESHOLD
  if loud:
    olx.Echo("Downloading %s, %.1f MB" % (what, size/(1024.0*1024.0)))
  got, next_report = 0, 10
  with open(dest, 'wb') as out:
    while True:
      chunk = res.read(256*1024)
      if not chunk:
        break
      out.write(chunk)
      got += len(chunk)
      if loud and size:
        pc = 100.0*got/size
        if pc >= next_report:
          olx.Echo("  %s: %d%%" % (what, int(pc)))
          next_report = int(pc/10)*10 + 10
  return True


def _find_refln_block(model):
  """The first block that carries reflection indices.

  Entries measured at several wavelengths deposit one block per dataset; the
  first is taken, which is what every other program does with them.
  """
  for name in model:
    block = model[name]
    if "_refln.index_h" in block or "_refln_index_h" in block:
      return block
  return None


def _refln_columns(block):
  """(h, k, l, value, sigma, status, is_intensity) from either dictionary.

  Amplitudes are the usual deposit, but some entries hold intensities, and
  those are used directly: squaring an amplitude that was itself derived from
  a negative intensity would not give the measurement back.
  """
  def col(*names):
    for n in names:
      if n in block:
        return block[n]
    return None

  h = col("_refln.index_h", "_refln_index_h")
  k = col("_refln.index_k", "_refln_index_k")
  l = col("_refln.index_l", "_refln_index_l")
  if h is None or k is None or l is None:
    return None
  status = col("_refln.status", "_refln_status")

  v = col("_refln.F_squared_meas", "_refln_F_squared_meas",
          "_refln.intensity_meas", "_refln_intensity_meas")
  s = col("_refln.F_squared_sigma", "_refln_F_squared_sigma",
          "_refln.intensity_sigma", "_refln_intensity_sigma")
  if v is not None and s is not None:
    return (h, k, l, v, s, status, True)

  v = col("_refln.F_meas_au", "_refln_F_meas_au", "_refln.F_meas", "_refln_F_meas")
  s = col("_refln.F_meas_sigma_au", "_refln_F_meas_sigma_au",
          "_refln.F_sigma", "_refln_F_sigma")
  if v is not None and s is not None:
    return (h, k, l, v, s, status, False)
  if v is not None:
    # Amplitudes with no sigma column, which older depositions do - 5RXN is
    # one. Refused rather than given an invented sigma: the weights would be
    # a fiction, and every standard uncertainty computed from them would
    # inherit it without saying so.
    return (h, k, l, v, None, status, False)
  return None


def sf_cif_to_hkl(src, dst, scale=None):
  """Write the deposited structure factors of src as a SHELX .hkl.

  Returns a dictionary describing what was written, or None if src holds
  nothing usable. The free-set flags of _refln.status are written beside the
  file, since a .hkl has nowhere to record them.
  """
  import iotbx.cif
  block = _find_refln_block(iotbx.cif.reader(file_path=src).model())
  if block is None:
    return None
  cols = _refln_columns(block)
  if cols is None:
    return None
  h, k, l, val, sig, status, is_intensity = cols
  if sig is None:
    raise ValueError(
      "this entry deposits structure factors without standard uncertainties, "
      "which a refinement needs for its weights")

  rows, free, dropped, unusable = [], [], 0, 0
  for i in range(len(h)):
    st = str(status[i]).strip() if status is not None else "o"
    # 'x' is excluded by the depositors, '-' systematically absent
    if st in ("x", "-"):
      dropped += 1
      continue
    try:
      v, s = float(val[i]), float(sig[i])
    except ValueError:
      unusable += 1        # '?' or '.', a reflection with no measurement
      continue
    if is_intensity:
      i_obs, i_sig = v, s
    else:
      i_obs, i_sig = v*v, 2*v*s
    if i_sig <= 0:
      # A reflection with no uncertainty cannot be weighted - smtbx asserts
      # sigma > 0 and stops the refinement outright. It arises here whenever
      # the deposited sigma(F) is zero, or F itself is, since sigma(I) is
      # 2 F sigma(F) and either factor kills it.
      unusable += 1
      continue
    rows.append((int(h[i]), int(k[i]), int(l[i]), i_obs, i_sig))
    if st == "f":
      free.append(len(rows) - 1)
  if not rows:
    return None

  # HKLF 4 holds intensity and sigma in F8.2, and an overflowing field runs
  # into its neighbour with no complaint from anyone. Eight characters take
  # 99999.99 at most, and only -9999.99 once a sign is needed, so the two
  # ends are tested separately. Scaled down to fit rather than truncated: a
  # common factor on I and sigma(I) is absorbed by the scale factor and
  # changes no refined quantity.
  if scale is None:
    hi = max(max(r[3], r[4]) for r in rows)
    lo = min(min(r[3], r[4]) for r in rows)
    scale = 1.0
    while hi*scale >= 1e5 or -lo*scale >= 1e4:
      scale /= 10.0
  # F8.2 resolves 0.01, so any sigma below 0.005 is written as exactly zero -
  # and a zero sigma is not a weak reflection, it is one smtbx refuses to
  # weight at all (SMTBX_ASSERT(sigma > 0)). Scaling the data down to fit the
  # field is what pushes them under. Floored at the format's own resolution,
  # which is the most precise statement the file can carry.
  floored = 0
  with open(dst, 'w') as out:
    for (hh, kk, ll, i_obs, i_sig) in rows:
      s = i_sig*scale
      if s < 0.01:
        s = 0.01
        floored += 1
      out.write("%4d%4d%4d%8.2f%8.2f\n" % (hh, kk, ll, i_obs*scale, s))
    out.write("%4d%4d%4d%8.2f%8.2f\n" % (0, 0, 0, 0, 0))

  free_file = None
  if free:
    free_file = os.path.splitext(dst)[0] + ".free"
    with open(free_file, 'w') as out:
      out.write("# indices the depositors held out of refinement\n")
      for idx in free:
        out.write("%d %d %d\n" % rows[idx][:3])
  return {
    'reflections': len(rows),
    'scale': scale,
    'dropped': dropped,
    'unusable': unusable,
    'free': len(free),
    'free_file': free_file,
    'sigma_floored': floored,
    'intensities_deposited': is_intensity,
  }


def fetch_entry(code=None, dest=None, load=True):
  """Download an entry, convert its structure factors, and open it."""
  if not code:
    code = OV.GetUserInput(1, "PDB entry code", "")
  code = normalise_code(code)
  if not code:
    olx.Echo("Not a PDB entry code. Use a four-character code such as 1EJG.",
             m="error")
    return ""
  load = OV.get_bool_from_any(load)

  base = dest or get_download_dir()
  if not base:
    olx.Echo("No folder chosen, nothing downloaded.", m="warning")
    return ""
  folder = os.path.join(base, code)
  if not os.path.exists(folder):
    os.makedirs(folder)

  model = os.path.join(folder, code + ".cif")
  if not os.path.exists(model):
    olx.Echo("Fetching %s from the PDB" % code)
    try:
      if not _download(PDB_FILE_URL % code, model, code + ".cif"):
        olx.Echo("There is no entry %s in the PDB." % code, m="error")
        if os.path.exists(model):
          os.remove(model)
        return ""
    except Exception as e:
      if os.path.exists(model):
        os.remove(model)
      olx.Echo("Could not fetch %s: %s" % (code, str(e)), m="error")
      return ""

  hkl = os.path.join(folder, code + ".hkl")
  if not os.path.exists(hkl):
    sf = os.path.join(folder, code + "-sf.cif")
    got_sf = os.path.exists(sf)
    if not got_sf:
      try:
        got_sf = _download(PDB_SF_URL % code, sf, code + "-sf.cif")
      except Exception as e:
        olx.Echo("Could not fetch the structure factors: %s" % str(e),
                 m="warning")
        got_sf = False
      if not got_sf and os.path.exists(sf):
        os.remove(sf)
    if got_sf:
      olx.Echo("Converting the deposited structure factors")
      try:
        info = sf_cif_to_hkl(sf, hkl)
      except Exception as e:
        olx.Echo("Could not read the structure factors: %s" % str(e),
                 m="error")
        info = None
      if info is None:
        if os.path.exists(hkl):
          os.remove(hkl)
        olx.Echo("%s-sf.cif holds no usable reflections." % code, m="warning")
      else:
        _report(code, info)
    else:
      olx.Echo("No structure factors are deposited for %s." % code,
               m="warning")

  if load:
    olex.m("reap '%s'" % model)
    # after the model, not before: HKLSrc applies to whatever is loaded, and
    # setting it first would attach the reflections to the previous structure
    if os.path.exists(hkl):
      OV.HKLSrc(hkl)
  return folder


def _report(code, info):
  olx.Echo("%s: %d reflections written" % (code, info['reflections']))
  if info['intensities_deposited']:
    olx.Echo("  intensities were deposited and are used as they are")
  else:
    olx.Echo("  from amplitudes: I = F^2, sigma(I) = 2 F sigma(F)")
  if info['scale'] != 1.0:
    olx.Echo("  scaled by %g to fit the SHELX F8.2 fields" % info['scale'])
  if info['dropped']:
    olx.Echo("  %d reflection(s) excluded by _refln.status" % info['dropped'])
  if info['unusable']:
    olx.Echo("  %d reflection(s) had no measurement" % info['unusable'])
  if info['free']:
    olx.Echo("  %d free-set reflection(s) listed in %s"
             % (info['free'], os.path.basename(info['free_file'])))


olex.registerFunction(fetch_entry, False, 'pdb')
olex.registerFunction(set_download_dir, False, 'pdb')
olex.registerFunction(get_download_dir, False, 'pdb')
