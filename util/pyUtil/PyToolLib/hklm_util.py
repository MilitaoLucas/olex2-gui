"""(3+1)D .hklm reflection files for the GUI side: h k l m I sigma [batch], fixed 4I4,2F8 or space separated, ended
by 0 0 0 0; lines that are neither are headers before the data and skipped (and reported) after it. Numpy only,
so an .hklm source works with any cctbx bundle; the rules are those of Olex2's THklFile::LoadHklmFromStrings and smtbx.modulation.read_hklm.
"""
import numpy as np


def read_hklm(path):
  """(h (N,3), m (N,), I, sigma)."""
  rows, bad = [], []
  with open(path, errors="replace") as f:
    for n, line in enumerate(f, 1):
      line = line.rstrip("\r\n")
      try:
        if len(line) < 32:
          raise ValueError
        v = [int(line[i:i + 4]) for i in (0, 4, 8, 12)] + [float(line[16:24]), float(line[24:32])]
      except ValueError:
        t = line.split()
        if not t:
          continue
        try:
          v = [int(x) for x in t[:4]] + [float(t[4]), float(t[5])]
        except (ValueError, IndexError):
          if rows:   # before the data a header; after it skipped, not the end of the file
            bad.append((n, line))
          continue
      if not any(v[:4]):
        break
      rows.append(v)
  if bad:
    print("hklm: skipped %d unreadable line(s) in %s, the first is line %d: %r" % (len(bad), path, *bad[0]))
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


def split_tsc_main(src, scale, dst):
  """The rows of a NoSpherA2 table made with -hkl_scale whose indices are all multiples of scale (the main
  reflections), written to dst as an ordinary table: indices / scale, same format, header and scatterers.
  Returns (rows in src, rows written)."""
  raw = open(src, "rb").read()
  if raw.startswith((b"TITLE:", b"SCATTERERS:", b"SCATTERER_IDS:")):
    head, sep, body = raw.partition(b"DATA:")
    out, n, kept = [], 0, 0
    for line in body.split(b"\n"):
      t = line.split(None, 3)
      if len(t) < 3:
        out.append(line)
        continue
      n += 1
      h = [int(v) for v in t[:3]]
      if all(v % scale == 0 for v in h):
        out.append(b"%d %d %d %s" % (h[0] // scale, h[1] // scale, h[2] // scale, t[3] if len(t) > 3 else b""))
        kept += 1
    open(dst, "wb").write(head + sep + b"\n".join(out))
    return n, kept
  i4 = lambda o: int(np.frombuffer(raw, "<i4", 1, o)[0])
  o = 4 + i4(0)
  count = i4(o)
  ids = b"SCATTERER_IDS" in raw[4:o]
  end = o + 4 + (16 * count if ids else count)   # ids: 16 bytes each; labels: count is the payload size
  n_scat = count if ids else len(raw[o + 4:end].split())
  rec = np.frombuffer(raw, np.dtype([("h", "<i4", 3), ("f", "<c16", n_scat)]), i4(end), end + 4)
  main = rec[np.all(rec["h"] % scale == 0, axis=1)].copy()
  main["h"] //= scale
  open(dst, "wb").write(raw[:end] + np.int32(len(main)).tobytes() + main.tobytes())
  return len(rec), len(main)
