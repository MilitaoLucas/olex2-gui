"""Tests for tsc_scatterer_resync.py on the 16-byte scatterer_id_big.

The module imports cctbx, so these run inside olex2c (or any libtbx python),
not a bare interpreter: E:/lk1029/rs_t.py runs this file through runpy.
No pytest; run_all() prints PASS/FAIL per test and raises if any failed.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cctbx import uctbx, xray
import tsc_scatterer_resync as m

CELL = uctbx.unit_cell((10, 10, 10, 90, 90, 90))  # 0.001 fractional = 0.01 A


def _id(z, crd, data=0):
    return xray.ext.scatterer_id_big(crd[0], crd[1], crd[2], data, z, 0)


def _hex(ids):
    return [i.to_hex_string() for i in ids]


def _write_tscb_ids(path, ids, header=b"SCATTERER_IDS\nID_BYTES: 16", n_refl=None,
                    id_bytes=None):
    # n_refl given: append that many zero reflection rows so the file size
    # states the id width (the probe path); id_bytes overrides the records
    # (legacy 8-byte files)
    records = id_bytes if id_bytes is not None else [bytes(i.to_bytes()) for i in ids]
    with open(path, "wb") as f:
        f.write(len(header).to_bytes(4, "little"))
        f.write(header)
        f.write(len(records).to_bytes(4, "little"))
        for r in records:
            f.write(r)
        if n_refl is not None:
            f.write(n_refl.to_bytes(4, "little"))
            f.write(b"\0" * (n_refl * (12 + 16 * len(records))))


def _write_tscb_labels(path, labels):
    header = b"LABELS"
    payload = " ".join(labels).encode("utf-8")
    with open(path, "wb") as f:
        f.write(len(header).to_bytes(4, "little"))
        f.write(header)
        f.write(len(payload).to_bytes(4, "little"))
        f.write(payload)


def _raises(fn, *args):
    try:
        fn(*args)
    except m.ScattererResolutionError as e:
        return str(e)
    raise AssertionError("expected ScattererResolutionError")


A = [_id(6, (0.10, 0.20, 0.30)), _id(6, (0.40, 0.20, 0.30)), _id(8, (0.50, 0.50, 0.50))]


# --- reading and rewriting the tables ---------------------------------------

def test_tsc_text_roundtrip_ids(tmp):
    path = os.path.join(tmp, "a.tsc")
    with open(path, "w") as f:
        f.write("TITLE: x\nSCATTERER_IDS: %s\nSymm: x,y,z\nDATA:\n0 0 1 1,0\n" % " ".join(_hex(A)))
    assert _hex(m.read_scatterers(path)) == _hex(A)
    moved = [_id(6, (0.11, 0.20, 0.30)), A[1], A[2]]
    m.update_scatterers_in_file(path, moved)
    assert _hex(m.read_scatterers(path)) == _hex(moved)
    text = open(path).read()
    assert "Symm: x,y,z" in text and "0 0 1 1,0" in text
    assert not os.path.exists(os.path.join(tmp, "a_new.tsc"))


def test_tsc_text_legacy_8byte_refused(tmp):
    path = os.path.join(tmp, "a.tsc")
    with open(path, "w") as f:
        f.write("SCATTERER_IDS: 0000000000000001 0000000000000002\nDATA:\n")
    assert "8-byte" in _raises(m.read_scatterers, path)


def test_tsc_text_roundtrip_labels(tmp):
    path = os.path.join(tmp, "b.tsc")
    with open(path, "w") as f:
        f.write("SYMM: expanded\nSCATTERERS: C1 C2 O1\nDATA:\n")
    assert m.read_scatterers(path) == ["C1", "C2", "O1"]


def test_tscb_roundtrip_ids_declared(tmp):
    path = os.path.join(tmp, "a.tscb")
    _write_tscb_ids(path, A)
    assert _hex(m.read_scatterers(path)) == _hex(A)
    moved = [A[0], _id(6, (0.41, 0.20, 0.30)), A[2]]
    m.update_scatterers_in_file(path, moved)
    assert _hex(m.read_scatterers(path)) == _hex(moved)


def test_tscb_roundtrip_ids_probed(tmp):
    # no ID_BYTES line: the width follows from the reflection block's size,
    # and an in-place rewrite keeps that block intact
    path = os.path.join(tmp, "a.tscb")
    _write_tscb_ids(path, A, header=b"SCATTERER_IDS", n_refl=2)
    size = os.path.getsize(path)
    assert _hex(m.read_scatterers(path)) == _hex(A)
    m.update_scatterers_in_file(path, A[::-1])
    assert _hex(m.read_scatterers(path)) == _hex(A[::-1])
    assert os.path.getsize(path) == size


def test_tscb_labels_to_ids_keeps_reflections(tmp):
    # label table -> id table changes the block size; the tail must follow
    path = os.path.join(tmp, "c.tscb")
    _write_tscb_labels(path, ["C1", "C2", "O1"])
    tail = (1).to_bytes(4, "little") + b"\x07" * (12 + 3 * 16)
    with open(path, "ab") as f:
        f.write(tail)
    m.update_scatterers_in_file(path, A)
    assert _hex(m.read_scatterers(path)) == _hex(A)
    with open(path, "rb") as f:
        assert f.read().endswith(tail)


def test_tscb_legacy_8byte_refused(tmp):
    path = os.path.join(tmp, "a.tscb")
    _write_tscb_ids(path, None, header=b"SCATTERER_IDS", id_bytes=[b"\1" * 8] * 3)
    with open(path, "ab") as f:  # one reflection, so the probe finds width 8
        f.write((1).to_bytes(4, "little") + b"\0" * (12 + 3 * 16))
    assert "8-byte" in _raises(m.read_scatterers, path)


def test_tscb_width_undeterminable_refused(tmp):
    path = os.path.join(tmp, "a.tscb")
    _write_tscb_ids(path, A, header=b"SCATTERER_IDS")
    assert "cannot determine" in _raises(m.read_scatterers, path)


def test_tscb_roundtrip_labels(tmp):
    path = os.path.join(tmp, "b.tscb")
    _write_tscb_labels(path, ["C1", "C2", "O1"])
    assert m.read_scatterers(path) == ["C1", "C2", "O1"]
    m.update_scatterers_in_file(path, ["C1x", "C2", "O1"])
    assert m.read_scatterers(path) == ["C1x", "C2", "O1"]


# --- labels -----------------------------------------------------------------

def test_convert_labels_to_ids_success():
    assert m.convert_labels_to_ids(["C1", "O1"], ["C1", "C2", "O1"], [100, 200, 300]) == [100, 300]


def test_convert_labels_to_ids_case_insensitive():
    assert m.convert_labels_to_ids(["c1"], ["C1", "O1"], [100, 300]) == [100]


def test_convert_labels_to_ids_rename_raises():
    _raises(m.convert_labels_to_ids, ["C1", "O1"], ["C1a", "C2", "O1"], [100, 200, 300])


def test_convert_labels_to_ids_duplicate_raises():
    _raises(m.convert_labels_to_ids, ["C1"], ["C1", "C1", "O1"], [100, 200, 300])


def test_mapping_labels_by_identity_not_order():
    # the table's column order is its writer's, not the model's
    got = m.resolve_scatterer_mapping(["O1", "C1", "C2"], ["C1", "C2", "O1"], A, CELL)
    assert got == [1, 2, 0], got


def test_mapping_labels_renamed_raises():
    _raises(m.resolve_scatterer_mapping, ["C1", "C2", "O1"], ["C1a", "C2", "O1"], A, CELL)


# --- ids --------------------------------------------------------------------

def test_mapping_exact_ids_permuted():
    got = m.resolve_scatterer_mapping([A[2], A[0], A[1]], ["C1", "C2", "O1"], A, CELL)
    assert got == [1, 2, 0], got


def test_mapping_exyz_pair_takes_columns_in_turn():
    # an EXYZ pair has one id twice; each atom takes its own column
    o = _id(8, (0.5, 0.5, 0.5))
    got = m.resolve_scatterer_mapping([o, A[0], o], ["O1", "C1", "O2"], [o, A[0], o], CELL)
    assert got == [0, 1, 2], got


def test_mapping_small_shift_follows_atoms():
    # a refinement shifts every atom a little; the table is in another order
    model = [_id(6, (0.1005, 0.20, 0.30)), _id(6, (0.40, 0.2004, 0.30)), _id(8, (0.50, 0.50, 0.5003))]
    got = m.resolve_scatterer_mapping([A[1], A[2], A[0]], ["C1", "C2", "O1"], model, CELL)
    assert got == [2, 0, 1], got


def test_mapping_large_shift_rejected():
    # both carbons moved 5 A, away from either old site; two free carbons
    # left, so the last-free-atom rule does not apply: refused
    model = [_id(6, (0.10, 0.70, 0.30)), _id(6, (0.40, 0.70, 0.30)), A[2]]
    assert "within" in _raises(m.resolve_scatterer_mapping, A, ["C1", "C2", "O1"], model, CELL)


def test_mapping_last_free_atom_of_kind_taken_however_far():
    # one carbon moved 3 A by hand; it is the only carbon left, so it is that column
    model = [A[0], _id(6, (0.70, 0.20, 0.30)), A[2]]
    got = m.resolve_scatterer_mapping(A, ["C1", "C2", "O1"], model, CELL)
    assert got == [0, 1, 2], got


def test_mapping_element_mismatch_rejected():
    model = [A[0], A[1], _id(7, (0.50, 0.50, 0.50))]
    _raises(m.resolve_scatterer_mapping, A, ["C1", "C2", "N1"], model, CELL)


def test_mapping_part_mismatch_rejected():
    # same element and site, other part (the data field): not the same atom
    model = [A[0], A[1], _id(8, (0.50, 0.50, 0.50), data=2)]
    _raises(m.resolve_scatterer_mapping, A, ["C1", "C2", "O1"], model, CELL)


def test_mapping_ambiguous_pair_refused():
    # both carbons now sit 0.05 A either side of where C1 was and C2's old
    # site is empty: neither is twice as close as the other
    model = [_id(6, (0.105, 0.20, 0.30)), _id(6, (0.095, 0.20, 0.30)), A[2]]
    assert "comparably close" in _raises(m.resolve_scatterer_mapping, A, ["C1", "C2", "O1"], model, CELL)


def test_mapping_swap_follows_position():
    # documented behaviour: two same-element atoms that swapped sites are
    # followed by site, not by name -- an id carries no name to tell them by
    a, b = (0.500, 0.500, 0.500), (0.500, 0.500, 0.501)
    old = [_id(6, a), _id(6, b)]
    model = [_id(6, (0.5, 0.5, 0.50101)), _id(6, (0.5, 0.5, 0.50001))]
    got = m.resolve_scatterer_mapping(old, ["C1", "C2"], model, CELL)
    assert got == [1, 0], got


def run_all():
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    failures = []
    for name, fn in tests:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                fn(tmp) if fn.__code__.co_argcount == 1 else fn()
                print("PASS %s" % name)
            except Exception as e:
                failures.append(name)
                print("FAIL %s: %r" % (name, e))
    print("\n%d/%d passed" % (len(tests) - len(failures), len(tests)))
    # raise rather than sys.exit: olex2c replaces sys.exit
    if failures:
        raise AssertionError("failed: %s" % ", ".join(failures))


if __name__ == "__main__":
    run_all()
