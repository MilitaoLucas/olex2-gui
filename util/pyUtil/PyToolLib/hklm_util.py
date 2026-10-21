"""(3+1)D .hklm reflection files for the GUI side: h k l m I sigma [batch], fixed 4I4,2F8 or space separated, ended
by 0 0 0 0 or the first line that is neither. Numpy only, so an .hklm source works with any cctbx bundle; the rules
are those of Olex2's THklFile::LoadHklmFromStrings and smtbx.modulation.read_hklm.
"""
import numpy as np


def read_hklm(path):
  """(h (N,3), m (N,), I, sigma)."""
  rows = []
  with open(path, errors="replace") as f:
    for line in f:
      line = line.rstrip("\r\n")
      try:
        if len(line) < 32:
          raise ValueError
        v = [int(line[i:i + 4]) for i in (0, 4, 8, 12)] + [float(line[16:24]), float(line[24:32])]
      except ValueError:
        t = line.split()
        try:
          v = [int(x) for x in t[:4]] + [float(t[4]), float(t[5])]
        except (ValueError, IndexError):
          if rows:
            break
          continue   # header lines
      if not any(v[:4]):
        break
      rows.append(v)
  a = np.array(rows, dtype=float).reshape(-1, 6)
  return a[:, :3].astype(int), a[:, 3].astype(int), a[:, 4], a[:, 5]


def write_main_hkl(hklm_path, out_path):
  """The main reflections (m = 0) as an HKLF 4 file, for everything that reads three indices; returns their number."""
  h, m, i_obs, sig = read_hklm(hklm_path)
  f8 = lambda x: ("%8.2f" % x) if len("%8.2f" % x) <= 8 else ("%8.0f" % x)[:8]
  with open(out_path, "w") as f:
    for (a, b, c), ii, ss in zip(h[m == 0], i_obs[m == 0], sig[m == 0]):
      f.write("%4d%4d%4d%s%s\n" % (a, b, c, f8(ii), f8(ss)))
    f.write("   0   0   0    0.00    0.00\n")
  return int(np.sum(m == 0))
