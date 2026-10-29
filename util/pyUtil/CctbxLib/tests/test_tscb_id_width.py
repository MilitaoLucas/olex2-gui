"""Tests for the .tscb scatterer-id width probe and the header matching around it.

Needs cctbx, so run it under the Olex2/libtbx interpreter, not plain python:

    call <cctbx build>/setpaths.bat && libtbx.python tests/test_tscb_id_width.py

Background: the marker SCATTERER_IDS named an 8-byte record before 29 July 2026
and a 16-byte one after, with nothing in the file to tell them apart. These
fixtures are the two layouts, byte for byte, plus the headers that used to be
mismatched between the four readers of the format.
"""
import os
import struct
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "NoSpherA2"))

import tsc_scatterer_resync as m
import tscb_rename


def _id16(Z, frac, data=0, reserved=0):
    scale = (0xFFFFFFFF / 2) / 16
    return (struct.pack("<iii", *[int(round(c * scale)) for c in frac])
            + struct.pack("<hBB", data, Z, reserved))


def _id8(Z, frac):
    # scatterer_id_5: one packed uint64, Z in the low byte, each coordinate
    # quantised to 16 bits over [-16, 16).
    val = Z
    for i, c in enumerate(frac):
        val |= (int(round(c * 65535 / 16)) & 0xFFFF) << (8 + 16 * i)
    return struct.pack("<Q", val)


def _write_tscb(path, header, records, n_refl=3, n_cols=None):
    """A whole, self-consistent .tscb: header, id block, then n_refl rows of
    three int32 Miller indices plus one complex<double> per column."""
    if n_cols is None:
        n_cols = len(records)
    with open(path, "wb") as f:
        f.write(struct.pack("<i", len(header)))
        f.write(header)
        f.write(struct.pack("<i", len(records)))
        for r in records:
            f.write(r)
        f.write(struct.pack("<i", n_refl))
        for h in range(n_refl):
            f.write(struct.pack("<iii", h, 0, 1))
            f.write(b"\0" * (16 * n_cols))


def _atoms():
    return [(6, (0.1, 0.2, 0.3)), (8, (0.4, 0.5, 0.6)), (7, (-0.1, 0.25, 0.75))]


def test_probe_accepts_current_16_byte_table(tmp):
    path = os.path.join(tmp, "new.tscb")
    _write_tscb(path, b"SCATTERER_IDS", [_id16(z, c) for z, c in _atoms()])
    ids = m.read_scatterers(path)
    assert len(ids) == 3, len(ids)
    assert [i.get_z() for i in ids] == [6, 8, 7], [i.get_z() for i in ids]


def test_probe_names_the_legacy_8_byte_table(tmp):
    path = os.path.join(tmp, "old.tscb")
    _write_tscb(path, b"SCATTERER_IDS", [_id8(z, c) for z, c in _atoms()])
    try:
        m.read_scatterers(path)
        assert False, "expected ScattererResolutionError"
    except m.ScattererResolutionError as e:
        assert "8-byte" in str(e), str(e)
        assert "July 2026" in str(e), str(e)


def test_multi_line_header_is_still_an_id_table(tmp):
    # The bug this guards: matching the header with == sent a table carrying any
    # second line down the label branch, which decoded the id bytes as utf-8.
    path = os.path.join(tmp, "ad.tscb")
    _write_tscb(path, b"SCATTERER_IDS\nAD: FALSE", [_id16(z, c) for z, c in _atoms()])
    ids = m.read_scatterers(path)
    assert [i.get_z() for i in ids] == [6, 8, 7], ids
    assert tscb_rename.tscb_uses_scatterer_ids(path), "rename guard must see the ids too"


def test_declared_width_is_believed_without_probing(tmp):
    # A file that declares its width does not need a well-formed tail to be read,
    # which is the point of declaring it.
    path = os.path.join(tmp, "declared.tscb")
    header = b"SCATTERER_IDS\nID_BYTES: 16"
    with open(path, "wb") as f:
        f.write(struct.pack("<i", len(header)))
        f.write(header)
        f.write(struct.pack("<i", 3))
        for z, c in _atoms():
            f.write(_id16(z, c))
    ids = m.read_scatterers(path)
    assert [i.get_z() for i in ids] == [6, 8, 7], ids
    assert m._declared_id_bytes(header) == 16


def test_declared_legacy_width_is_refused(tmp):
    path = os.path.join(tmp, "declared8.tscb")
    header = b"SCATTERER_IDS\nID_BYTES: 8"
    _write_tscb(path, header, [_id8(z, c) for z, c in _atoms()])
    try:
        m.read_scatterers(path)
        assert False, "expected ScattererResolutionError"
    except m.ScattererResolutionError as e:
        assert "8-byte" in str(e), str(e)


def test_truncated_id_block_is_an_error_not_zeroes(tmp):
    # int.from_bytes(b'', 'little') is 0, so without the guard a truncated file
    # reads as a block of Z=0 atoms.
    path = os.path.join(tmp, "cut.tscb")
    header = b"SCATTERER_IDS\nID_BYTES: 16"
    with open(path, "wb") as f:
        f.write(struct.pack("<i", len(header)))
        f.write(header)
        f.write(struct.pack("<i", 3))
        f.write(_id16(6, (0.1, 0.2, 0.3)))
        f.write(_id16(8, (0.4, 0.5, 0.6))[:9])
    try:
        m.read_scatterers(path)
        assert False, "expected ScattererResolutionError"
    except m.ScattererResolutionError as e:
        assert "truncated" in str(e), str(e)


def test_garbage_width_is_reported_as_unknown(tmp):
    path = os.path.join(tmp, "odd.tscb")
    _write_tscb(path, b"SCATTERER_IDS", [b"\1" * 12 for _ in range(3)])
    try:
        m.read_scatterers(path)
        assert False, "expected ScattererResolutionError"
    except m.ScattererResolutionError as e:
        assert "cannot determine" in str(e), str(e)


def test_label_table_is_untouched_by_any_of_this(tmp):
    path = os.path.join(tmp, "lab.tscb")
    payload = b"C1 C2 O1"
    with open(path, "wb") as f:
        f.write(struct.pack("<i", 0))
        f.write(struct.pack("<i", len(payload)))
        f.write(payload)
    assert m.read_scatterers(path) == ["C1", "C2", "O1"]
    assert not tscb_rename.tscb_uses_scatterer_ids(path)
    # a same-size rename is written where it lies, a different-size one resizes
    m.update_scatterers_in_file(path, ["C9", "C2", "O1"])
    assert m.read_scatterers(path) == ["C9", "C2", "O1"]
    m.update_scatterers_in_file(path, ["C1a", "C2", "O1"])
    assert m.read_scatterers(path) == ["C1a", "C2", "O1"]


def test_id_table_rewrite_keeps_the_reflection_block(tmp):
    path = os.path.join(tmp, "rw.tscb")
    _write_tscb(path, b"SCATTERER_IDS", [_id16(z, c) for z, c in _atoms()])
    with open(path, "rb") as f:
        tail_before = f.read()[-4 - 3 * (12 + 3 * 16):]
    ids = m.read_scatterers(path)
    m.update_scatterers_in_file(path, ids)
    with open(path, "rb") as f:
        tail_after = f.read()[-4 - 3 * (12 + 3 * 16):]
    assert tail_before == tail_after, "the reflection block must survive a resync"


def test_resync_keeps_the_whole_header(tmp):
    # a resize used to reduce the header to a bare marker or to nothing, dropping
    # AD: and anything else the writer had declared about the table
    path = os.path.join(tmp, "hdr.tscb")
    header = b"AD: FALSE" + bytes([10])
    payload = b"C1 C2 O1"
    with open(path, "wb") as f:
        f.write(struct.pack("<i", len(header)))
        f.write(header)
        f.write(struct.pack("<i", len(payload)))
        f.write(payload)
    m.update_scatterers_in_file(path, ["C1a", "C2", "O1"])
    with open(path, "rb") as f:
        blob = f.read()
    head = struct.unpack_from("<i", blob, 0)[0]
    assert blob[4:4 + head] == header, blob[4:4 + head]
    assert m.read_scatterers(path) == ["C1a", "C2", "O1"]


def test_shrinking_label_block_truncates_the_file(tmp):
    # without f.truncate() the tail of the longer file stays behind. No reader
    # counting its way through notices, but the id width is worked out from the
    # file size, and stray bytes make that arithmetic match no known width.
    path = os.path.join(tmp, "shrink.tscb")
    header = b"AD: FALSE"
    payload = b"C1_long C2_long O1_long"
    with open(path, "wb") as f:
        f.write(struct.pack("<i", len(header)))
        f.write(header)
        f.write(struct.pack("<i", len(payload)))
        f.write(payload)
    m.update_scatterers_in_file(path, ["C1", "C2", "O1"])
    assert m.read_scatterers(path) == ["C1", "C2", "O1"]
    expected = 4 + len(header) + 4 + len(b"C1 C2 O1")
    assert os.path.getsize(path) == expected, os.path.getsize(path)


def test_compose_header_replaces_by_key_and_keeps_the_rest():
    nl = bytes([10])
    header = b"SCATTERER_IDS" + nl + b"AD: FALSE" + nl + b"SOURCE_LABELS: stale"
    lines = m.compose_header(header, True, [b"SOURCE_LABELS: C1 C2"]).split(nl)
    assert lines[0] == b"SCATTERER_IDS", lines
    assert b"SOURCE_LABELS: C1 C2" in lines, lines
    assert b"SOURCE_LABELS: stale" not in lines, lines
    assert b"AD: FALSE" in lines, lines


def test_source_labels_survive_an_id_rewrite(tmp):
    # the ingest conversion keeps what the generator called each column, and it
    # must reach the header even though the id block is the same size as before
    # -- the in-place path would return without composing a header at all.
    path = os.path.join(tmp, "src.tscb")
    _write_tscb(path, b"SCATTERER_IDS", [_id16(z, c) for z, c in _atoms()])
    ids = m.read_scatterers(path)
    m.update_scatterers_in_file(path, ids,
                                extra_header_lines=["SOURCE_LABELS: C1 O1 N1"])
    with open(path, "rb") as f:
        blob = f.read()
    head = struct.unpack_from("<i", blob, 0)[0]
    assert b"SOURCE_LABELS: C1 O1 N1" in blob[4:4 + head], blob[4:4 + head]
    assert [i.get_z() for i in m.read_scatterers(path)] == [6, 8, 7]


def run_all():
    tests = [(name, fn) for name, fn in sorted(vars(sys.modules[__name__]).items())
             if name.startswith("test_") and callable(fn)]
    failures = []
    for name, fn in tests:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                fn(tmp) if fn.__code__.co_argcount == 1 else fn()
                print("PASS %s" % name)
            except Exception as e:
                failures.append(name)
                print("FAIL %s: %s" % (name, e))
    print("\n%d/%d passed" % (len(tests) - len(failures), len(tests)))
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    run_all()
