import os
import cctbx.xray as xray_


class ScattererResolutionError(Exception):
  pass

_ID_RECORD_BYTES = 16          # scatterer_id_big / atomID
_LEGACY_ID_RECORD_BYTES = 8    # scatterer_id_5, written by NoSpherA2 12-29 July 2026
_ID_MARKER = b'SCATTERER_IDS'
SOURCE_LABELS_KEY = b'SOURCE_LABELS'


def _tscb_header_says_ids(header):
    # Substring, not equality: the header is a block of KEY: VALUE lines and the
    # marker is only the first of them, so a table carrying a second line -- 'AD:
    # FALSE', or an ID_BYTES: line -- is still an id table. The other three
    # readers of this format all match by substring; matching by equality here
    # sent such a table down the label branch, where the id bytes were decoded as
    # utf-8.
    return b'SCATTERER_IDS' in header


def _declared_id_bytes(header):
    # The record width the file declares, or None if it declares none. Files
    # written before the key existed fall through to the probe below.
    for line in header.split(b'\n'):
        key, sep, value = line.partition(b':')
        if sep and key.strip().upper() == b'ID_BYTES':
            try:
                return int(value.strip())
            except ValueError:
                return None
    return None


def _probe_id_record_bytes(path, header_length, n_scatterers):
    # The id block is not length-prefixed, but everything after it is: the int32
    # that follows it is the reflection count, and the rest of the file is that
    # many rows of three int32 Miller indices plus one complex<double> per
    # scatterer. Only the true record width makes that come out even, so the file
    # states its own format arithmetically even when it does not state it in the
    # header.
    total = os.path.getsize(path)
    id_block_start = 4 + header_length + 4
    row_bytes = 12 + n_scatterers * 16
    with open(path, 'rb') as f:
        for width in (_ID_RECORD_BYTES, _LEGACY_ID_RECORD_BYTES):
            end = id_block_start + n_scatterers * width
            if end + 4 > total:
                continue
            f.seek(end)
            n_refl = int.from_bytes(f.read(4), byteorder='little', signed=True)
            if n_refl <= 0:
                continue
            if total - (end + 4) == n_refl * row_bytes:
                return width
    return None


def _tscb_id_record_bytes(path, header, header_length, n_scatterers):
    # Reading ids at the wrong width is not detected where the mistake is made:
    # every record after the first is framed from the wrong offset and the
    # failure surfaces much later as a model that does not match its own table.
    # So refuse rather than guess.
    name = os.path.basename(path)
    width = _declared_id_bytes(header)
    if width is None:
        width = _probe_id_record_bytes(path, header_length, n_scatterers)
    if width == _ID_RECORD_BYTES:
        return width
    if width == _LEGACY_ID_RECORD_BYTES:
        raise ScattererResolutionError(
            f"{name} holds 8-byte scatterer ids -- the format NoSpherA2 wrote between "
            "12 and 29 July 2026 -- but this Olex2 reads the 16-byte format. The marker "
            "is the same in both, so nothing else can tell them apart. Recalculate the "
            "table with the current NoSpherA2.")
    if width is None:
        raise ScattererResolutionError(
            f"cannot determine the scatterer id width of {name}: it declares none and "
            "its size fits neither known width, so it is truncated, damaged or written "
            "by a version this Olex2 does not know.")
    raise ScattererResolutionError(
        f"{name} declares ID_BYTES: {width}, which this Olex2 cannot read.")


def read_binary_scatterers(filestream):
    decode_scale = 16 / (0xFFFFFFFF/2)
    raw = filestream.read(_ID_RECORD_BYTES)
    # int.from_bytes(b'', ...) is 0, so a short read would otherwise turn a
    # truncated file into a block of Z=0 atoms rather than into an error.
    if len(raw) != _ID_RECORD_BYTES:
        raise ScattererResolutionError(
            "TSCB file ends in the middle of the scatterer id block; the table is truncated")
    frac_x = int.from_bytes(raw[0:4], byteorder='little', signed=True) * decode_scale
    frac_y = int.from_bytes(raw[4:8], byteorder='little', signed=True) * decode_scale
    frac_z = int.from_bytes(raw[8:12], byteorder='little', signed=True) * decode_scale
    data = int.from_bytes(raw[12:14], byteorder='little', signed=True)
    Z = raw[14]
    reserved = raw[15]
    return xray_.scatterer_id_big(frac_x, frac_y, frac_z, data, Z, reserved)


def read_scatterers_from_tscb(tscb_file):
    scatterer_ids = []
    with open(tscb_file, 'rb') as f:
        header_length = int.from_bytes(f.read(4), byteorder='little')
        header = f.read(header_length)
        n_scatterers = int.from_bytes(f.read(4), byteorder='little')

        if _tscb_header_says_ids(header):
            _tscb_id_record_bytes(tscb_file, header, header_length, n_scatterers)
            for _ in range(n_scatterers):
                scatterer_ids.append(read_binary_scatterers(f))
        else:
            # If the header is not "SCATTERER_IDS", the scatterers are stored as a single
            # space-separated string of labels. In this branch the value just read is not a
            # count of scatterers but the byte size of that payload string (matches the C++
            # writer, which writes payload.size() followed by the raw payload bytes).
            payload_size = n_scatterers
            payload = f.read(payload_size).decode('utf-8')
            scatterer_ids = payload.split(' ')
            
            
    return scatterer_ids

def _text_scatterer_id(token, tsc_file):
    # the text format carries the same two vintages as the binary one: the
    # 8-byte id of July 2026 prints as 16 hex characters, the current one as 32.
    # Without this the constructor's own message names neither the file nor the
    # format, and a table that cannot be read looks like a table that does not
    # match.
    name = os.path.basename(tsc_file)
    try:
        return xray_.scatterer_id_big(token)
    except ValueError:
        if len(token) == 2 * _LEGACY_ID_RECORD_BYTES:
            raise ScattererResolutionError(
                f"{name} holds 8-byte scatterer ids -- the format NoSpherA2 wrote between "
                "12 and 29 July 2026 -- but this Olex2 reads the 16-byte format. "
                "Recalculate the table with the current NoSpherA2.")
        raise ScattererResolutionError(
            f"{name} carries a scatterer id of {len(token)} characters, which is neither "
            "known format, so the table is damaged or was written by a version this Olex2 "
            "does not know.")
    except RuntimeError as error:
        raise ScattererResolutionError(f"{name} carries an unusable scatterer id: {error}")


def read_scatterers_from_tsc(tsc_file):
    # The header is keyed, not positional: discamb2tsc writes a SYMM: line, so
    # the third line was 'SYMM: expanded' and 'expanded' was resolved as a
    # scatterer label. The lookup then failed and the refinement carried on
    # spherically, which is what update_tsc_file already does correctly. DATA:
    # ends the header, so a file without the key is not read past it.
    scatterer_ids = []
    with open(tsc_file, 'r') as f:
        for line in f:
            if line.startswith('DATA:'):
                break
            if not line.startswith(('SCATTERERS:', 'SCATTERER_IDS:')):
                continue
            line = line.split()
            header, scatterers = line[0], line[1:]
            is_id = header == 'SCATTERER_IDS:'
            for scat in scatterers:
                if is_id:
                    scatterer_ids.append(_text_scatterer_id(scat, tsc_file))
                else:
                    scatterer_ids.append(scat)
            break
    return scatterer_ids


def read_scatterers(tsc_file):
    # a caller may still hold the path as bytes, the way the refinement once
    # passed it to the C++ builder; the readers and the error messages want str
    if isinstance(tsc_file, bytes):
        tsc_file = os.fsdecode(tsc_file)
    if tsc_file.endswith('.tscb'):
        return read_scatterers_from_tscb(tsc_file)
    elif tsc_file.endswith('.tshb'):
        # densities: smtbx.structure_factors.direct.tshb. Version 4 keys every
        # record by scatterer id, as a .tscb; older files by label
        import io
        from smtbx.structure_factors.direct import tshb
        atoms = tshb.read(tsc_file)[1]
        if atoms and atoms[0].key is not None:
            return [read_binary_scatterers(io.BytesIO(a.key)) for a in atoms]
        return [a.label for a in atoms]
    else:
        return read_scatterers_from_tsc(tsc_file)

def read_header_lines(tsc_file):
    """The KEY: VALUE lines of a tsc/tscb header as a dict, keys upper-cased.

    Lines without a colon (the id marker) are skipped; a repeated key keeps
    the first occurrence, which is the order compose_header writes replacements
    in.
    """
    if isinstance(tsc_file, bytes):
        tsc_file = os.fsdecode(tsc_file)
    if tsc_file.endswith(('.tscb', '.tshb')):
        with open(tsc_file, 'rb') as f:
            f.read(_binary_prefix(tsc_file))
            header_length = int.from_bytes(f.read(4), byteorder='little')
            raw = f.read(header_length).decode('utf-8', 'replace').split('\n')
    else:
        raw = []
        with open(tsc_file, 'r') as f:
            for line in f:
                if line.startswith('DATA:'):
                    break
                raw.append(line)
    header = {}
    for line in raw:
        key, sep, value = line.partition(':')
        if sep:
            header.setdefault(key.strip().upper(), value.strip())
    return header


def write_header_lines(tsc_file, lines):
    """Add KEY: VALUE lines to the header, replacing older lines of the same
    key; the scatterer block and the data are copied through untouched.

    A value is flattened to one line: cctbx's reader stops at the first empty
    header line and takes a line without a colon for the id marker, so a
    newline inside a value would end or corrupt the header for it.
    """
    if isinstance(tsc_file, bytes):
        tsc_file = os.fsdecode(tsc_file)
    lines = [' '.join((l.decode('utf-8') if isinstance(l, bytes) else str(l)).split())
             for l in lines if str(l).strip()]
    if not lines:
        return
    import shutil
    tmp = tsc_file + '.header.tmp'
    if tsc_file.endswith(('.tscb', '.tshb')):
        with open(tsc_file, 'rb') as f, open(tmp, 'wb') as g:
            g.write(f.read(_binary_prefix(tsc_file)))
            header_length = int.from_bytes(f.read(4), byteorder='little')
            header = f.read(header_length)
            header = compose_header(header, _tscb_header_says_ids(header), lines)
            g.write(len(header).to_bytes(4, byteorder='little'))
            g.write(header)
            shutil.copyfileobj(f, g)
    else:
        replaced = set(l.split(':', 1)[0].strip().upper() for l in lines)
        with open(tsc_file, 'r') as f, open(tmp, 'w') as g:
            for line in f:
                if line.startswith('DATA:'):
                    for l in lines:
                        g.write(l + '\n')
                    g.write(line)
                    break
                if line.split(':', 1)[0].strip().upper() not in replaced:
                    g.write(line)
            shutil.copyfileobj(f, g)
    os.replace(tmp, tsc_file)


def _binary_prefix(tsc_file):
    # a .tshb puts "TSHB" and its version before the header length a .tscb starts with
    return 8 if tsc_file.endswith('.tshb') else 0


def _header_key(line):
    return line.split(b':', 1)[0].strip().upper()


def compose_header(header, want_ids, extra_lines=None):
    """The header to write back: the lines the file already carried, with the
    marker made to agree with the kind of block now in it, and any line the
    caller supplies replacing an older line of the same key.

    The marker is a bare word rather than a KEY: VALUE line, and every reader
    looks for it as a substring anywhere in the header, so it is filtered out
    and put back rather than edited in place.
    """
    # the binary header is bytes and the text one is str, and callers pass
    # whichever they are holding, so a line is taken in either form
    extra_lines = [l.encode('utf-8') if isinstance(l, str) else l
                   for l in (extra_lines or []) if l.strip()]
    if not extra_lines and _tscb_header_says_ids(header) == bool(want_ids):
        # nothing to decide, so keep the bytes exactly as they were found rather
        # than normalising whitespace nobody asked about
        return header
    replaced = set(_header_key(l) for l in extra_lines)
    kept = [l for l in header.split(b'\n')
            if l.strip() and l.strip() != _ID_MARKER
            and _header_key(l) not in replaced]
    lines = ([_ID_MARKER] if want_ids else []) + extra_lines + kept
    return b'\n'.join(lines)


def update_tsc_file(tsc_file, scatterers, extra_header_lines=None):
    extra = [l.decode('utf-8') if isinstance(l, bytes) else l
             for l in (extra_header_lines or []) if str(l).strip()]
    replaced = set(l.split(':', 1)[0].strip().upper() for l in extra)
    new_data = ""
    with open(tsc_file, 'r') as f:
        for line in f:
            if not (line.startswith('SCATTERER_IDS:') or line.startswith('SCATTERERS:')):
                # a line the caller is about to write is dropped here rather
                # than left to appear twice, since nothing downstream says
                # which of two lines with one key wins
                if line.split(':', 1)[0].strip().upper() not in replaced:
                    new_data += line
                continue

            for extra_line in extra:
                new_data += extra_line.rstrip('\n') + '\n'
            if isinstance(scatterers[0], str):
                new_data += "SCATTERERS: "
                new_data += " ".join([f"{label}" for label in scatterers]) + "\n"
            else:
                # to_hex_string, not a format specifier: an id is wider than
                # the machine integer the old format assumed, and formatting it
                # as one silently truncated it
                new_data += "SCATTERER_IDS: "
                new_data += " ".join(s.to_hex_string() for s in scatterers) + "\n"
            break

        new_data += f.read()  # Append the rest of the file

    with open(tsc_file, 'w') as f:
        f.write(new_data)

def update_tscb_file(tscb_file, scatterers, extra_header_lines=None):
    with open(tscb_file, "r+b") as f:
        header_length = int.from_bytes(f.read(4), byteorder='little')
        header = f.read(header_length)
        n_scatterers = int.from_bytes(f.read(4), byteorder='little')

        # A file opened for update must be repositioned between a read and a
        # write; without it the write lands wherever the read buffer left the
        # underlying position, not where the last read logically ended. Here
        # that put the ids one slot late, so every column ended up described by
        # the id of the atom before it -- silently, and permanently, since the
        # file is then written back to disk.
        id_block_start = 4 + header_length + 4
        payload_start = 4 + header_length

        # The two in-place paths below return before the header is composed, so
        # they are only available when the caller has nothing to put in it.
        if (_tscb_header_says_ids(header) and not isinstance(scatterers[0], str)
                and not extra_header_lines):
            _tscb_id_record_bytes(tscb_file, header, header_length, n_scatterers)
            #As the number of scatterers did not change, the lenght of the representation does not change, so we can just overwrite the scatterer IDs in place.
            if n_scatterers != len(scatterers):
                raise ValueError(f"Number of scatterers in TSCB file ({n_scatterers}) does not match the provided list ({len(scatterers)}).")
            f.seek(id_block_start)
            for scat in scatterers:
                payload = scat.to_bytes()
                if len(payload) != 16:
                    raise ValueError(
                        f"scatterer id serialised to {len(payload)} bytes, expected 16; "
                        "refusing to write a table whose ids would not line up")
                f.write(payload)
            return
        elif (not _tscb_header_says_ids(header) and isinstance(scatterers[0], str)):
            # In the label case the int just read is the byte size of the payload,
            # not a count of scatterers, so it is the size that decides whether the
            # block can be overwritten where it lies. A payload of any other size
            # falls through to the resize path below; comparing it against the
            # number of labels instead would reject renames that fit perfectly.
            new_payload = " ".join(str(scat) for scat in scatterers).encode('utf-8')
            if len(new_payload) == n_scatterers and not extra_header_lines:
                f.seek(payload_start)
                f.write(len(new_payload).to_bytes(4, byteorder='little'))
                f.write(new_payload)
                return
            
        #We have to change the size of the file, thus we need to first save the data written at the end
        if _tscb_header_says_ids(header):
            f.seek(_tscb_id_record_bytes(tscb_file, header, header_length, n_scatterers)
                   * n_scatterers, 1)
        else: 
            f.seek(n_scatterers, 1) 
        data = f.read() #Save data that comes after the scatterer IDs or labels
        f.seek(0)
        
        # The header keeps every line it came with; only the marker follows the
        # kind of block. Rewriting it as a bare marker dropped everything else
        # the writer had put there -- 'AD: FALSE' among them -- so a resync
        # quietly changed what the table claimed about itself.
        is_labels = isinstance(scatterers[0], str)
        new_header = compose_header(header, not is_labels, extra_header_lines)
        f.write(len(new_header).to_bytes(4, byteorder='little'))
        f.write(new_header)
        if is_labels:
            new_payload = " ".join(str(scat) for scat in scatterers).encode('utf-8')
            f.write(len(new_payload).to_bytes(4, byteorder='little'))
            f.write(new_payload)
        else: #AtomID case
            f.write(len(scatterers).to_bytes(4, byteorder='little'))
            for scat in scatterers:
                f.write(scat.to_bytes())

        f.write(data) #Write the rest of the data back to the file
        # a block that shrank would otherwise leave the tail of the old file
        # beyond it. Readers count their way through and would not notice, but
        # the id width is worked out from the file size, and stray bytes make
        # that arithmetic come out to no known width at all.
        f.truncate()

def update_tshb_file(tshb_file, ids):
    # the densities stay as they are; only each record's id key follows the atom.
    # A label-keyed .tshb has nothing to update: a label does not go stale.
    from smtbx.structure_factors.direct import tshb
    header, atoms = tshb.read(tshb_file)
    if not atoms or atoms[0].key is None or len(ids) != len(atoms) or isinstance(ids[0], str):
        raise ScattererResolutionError(
            "%s: %d ids for %d records; only an id-keyed .tshb takes new ids"
            % (os.path.basename(tshb_file), len(ids), len(atoms)))
    # write() puts FRAME and UNITS first itself
    header = dict((k, v) for k, v in header.items() if k not in ("FRAME", "UNITS"))
    atoms = [a._replace(key=bytes(i.to_bytes())) for a, i in zip(atoms, ids)]
    tmp = tshb_file + ".tmp"
    tshb.write(tmp, atoms, header)
    os.replace(tmp, tshb_file)

def update_scatterers_in_file(tsc_file, scatterers, extra_header_lines=None):
    # Rewriting the table is the one action here that can damage it, and when
    # it goes wrong nothing else says so: the file stays the right shape, the
    # numbers stay plausible, and the refinement simply describes the wrong
    # atoms from then on. It is rare and cheap, so it says that it happened.
    kind = 'labels' if isinstance(scatterers[0], str) else 'ids'
    print("Updating the %d scatterer %s in %s"
          % (len(scatterers), kind, os.path.basename(tsc_file)))
    if tsc_file.endswith('.tshb'):
        update_tshb_file(tsc_file, scatterers)
    elif tsc_file.endswith('.tscb'):
        update_tscb_file(tsc_file, scatterers, extra_header_lines)
    else:
        update_tsc_file(tsc_file, scatterers, extra_header_lines)


def convert_labels_to_ids(labels, model_labels, model_ids):
  # Assuming the order of the atoms in the model is the same as the order of the model_ids,
  # we can create a mapping from label to id.
    if len(model_labels) != len(model_ids):
      raise ScattererResolutionError(
        f"model label count ({len(model_labels)}) does not match model id count ({len(model_ids)})")

    # Case-insensitively, as the table reader itself matches labels: it upper-
    # cases both sides. Matching more strictly here does not make anything
    # safer, it just reports a mismatch the reader does not have -- and a
    # reported mismatch is what sends this down the recovery path.
    label_to_id = {}
    for label, atom_id in zip(model_labels, model_ids):
        key = label.upper()
        if key in label_to_id:
          raise ScattererResolutionError(f"duplicate atom label '{label}' in current model")
        label_to_id[key] = atom_id

    missing = [label for label in labels if label.upper() not in label_to_id]
    if missing:
      resolved = _match_by_residue_triple(labels, model_labels, model_ids)
      if resolved is not None:
        return resolved
      raise ScattererResolutionError(
        f"{len(missing)} label(s) from the table file were not found in the current model "
        f"(renamed?): {missing[:5]}{'...' if len(missing) > 5 else ''}")

    return [label_to_id[label.upper()] for label in labels]


def _residue_triple(name):
  """(atom, chain, residue) from either naming order, or None.

  A protein atom is written two ways. Olex2 names it chain first, 'A:H1_1',
  while the CIF handed to the table generator names it atom first, 'N_A:1', so
  a table made for a protein matches none of the model's labels even though
  both sides mean the same atom. Anything without both a chain and a residue -
  every small molecule - returns None and is left to the exact match.
  """
  if ':' not in name:
    return None
  head, _, tail = name.partition(':')
  if '_' in head:                          # atom first: LABEL_CHAIN:RESI
    atom, _, chain = head.rpartition('_')
    residue = tail
  else:                                    # chain first: CHAIN:LABEL_RESI
    chain = head
    atom, _, residue = tail.rpartition('_')
  if not atom or not chain or not residue:
    return None
  return (atom.upper(), chain.upper(), residue.upper())


def _match_by_residue_triple(labels, model_labels, model_ids):
  """Ids for labels written in the other naming order, or None to give up.

  Deliberately all or nothing. Rewriting a form factor table against the wrong
  atoms leaves a file of the right shape holding plausible numbers, and the
  refinement then describes the wrong model with nothing to say so, which is
  why a partial or ambiguous match is refused rather than patched up.
  """
  # atoms outside a residue (solvent, ions) carry the same label on both sides
  index = {}
  for label, atom_id in zip(model_labels, model_ids):
    key = _residue_triple(label) or label.upper()
    if key in index:
      return None
    index[key] = atom_id
  out = []
  for label in labels:
    key = _residue_triple(label) or label.upper()
    if key not in index:
      return None
    out.append(index[key])
  print("Table labels are in the other residue naming order; matched all %d "
        "on chain, residue and atom" % len(out))
  return out


_MAX_POSITIONAL_RESYNC_SHIFT_ANGSTROM = 2.0
# how near a symmetry image of the tabulated site an atom must be to count as moved there
_MAX_SYMMETRY_MOVE_RESIDUAL_ANGSTROM = 0.5
# beyond this an atom was moved by hand, not by a refinement, and is named
_MANUAL_MOVE_ANGSTROM = 0.5


def _move_candidates(space_group):
  """(R, t, xyz) for every operation move, compaq, sgen -m or transform with a
  group matrix can have applied; in a group without a centre also each one
  composed with an inversion, which is what inv -f does. Identity first."""
  import numpy as np
  from cctbx import sgtbx
  ops = list(space_group.all_ops())
  if not space_group.is_centric():
    inversion = sgtbx.rt_mx('-x,-y,-z')
    ops += [inversion.multiply(op) for op in space_group.all_ops()]
  out = []
  for op in ops:
    assert op.r().den() == 1, op.as_xyz()
    out.append((np.array(op.r().num(), dtype=int).reshape(3, 3),
                np.array(op.t().as_double()), op.mod_positive().as_xyz()))
  return out


def _symmetry_matches(olds, model, unit_cell, ops, tolerance, identity_tolerance):
  """For each id in olds, (model index, op index) of the atom on a symmetry
  image of its site, or None. The nearest image over all ops wins, so a group
  operation beats a merely nearby identity match; failing that the identity
  alone may reach identity_tolerance, as a refinement shift does. A different
  atom of the same element and part nearly as close makes it ambiguous.

  Numpy over chunks of columns: a stale protein table asks for every column
  against every atom under every operation, which is 1e8 distances. The
  nearest lattice image is taken componentwise, which is exact at these
  distances for any cell that is not extremely oblique."""
  import numpy as np
  g = unit_cell.metrical_matrix()      # aa bb cc ab ac bc
  metric = np.array([[g[0], g[3], g[4]], [g[3], g[1], g[5]], [g[4], g[5], g[2]]])
  sites = np.array([m.get_crd() for m in model])
  kind = np.array([(m.get_z(), m.get_data()) for m in model])
  x = np.array([o.get_crd() for o in olds])
  okind = np.array([(o.get_z(), o.get_data()) for o in olds])

  def nearest_two(d2):
    if d2.shape[1] < 2:
      return np.zeros(len(d2), dtype=int), np.sqrt(d2[:, 0]), np.full(len(d2), np.inf)
    two = np.argpartition(d2, 1, axis=1)[:, :2]
    rows = np.arange(len(d2))
    a, b = d2[rows, two[:, 0]], d2[rows, two[:, 1]]
    first = np.where(a <= b, two[:, 0], two[:, 1])
    return first, np.sqrt(np.minimum(a, b)), np.sqrt(np.maximum(a, b))

  out = [None] * len(olds)
  # only an atom of the same element and part can be a column's atom
  for this_kind in set(map(tuple, okind)):
    cand = np.flatnonzero((kind == this_kind).all(axis=1))
    if not len(cand):
      continue
    s = sites[cand]

    def d2_to(rows, rot, t):
      dd = (x[rows].dot(rot.T) + t)[:, None, :] - s[None, :, :]
      dd -= np.round(dd)
      return (dd.dot(metric) * dd).sum(axis=2)

    members = np.flatnonzero((okind == this_kind).all(axis=1))
    for start in range(0, len(members), 256):
      rows = members[start:start + 256]
      identity = d2_to(rows, ops[0][0], ops[0][1])
      j_id, d_id, r_id = nearest_two(identity)
      # within a tenth of an angstrom of its own site and clear of any other atom:
      # no image can be nearer without two atoms overlapping, so skip the search
      plain = (d_id <= 0.1) & (r_id >= 2 * d_id)
      for c in np.flatnonzero(plain):
        out[rows[c]] = (int(cand[j_id[c]]), 0)
      rest = np.flatnonzero(~plain)
      if not len(rest):
        continue
      best, best_op = identity[rest], np.zeros((len(rest), len(cand)), dtype=int)
      for k in range(1, len(ops)):
        d2 = d2_to(rows[rest], ops[k][0], ops[k][1])
        better = d2 < best
        best = np.where(better, d2, best)
        best_op[better] = k
      j_sym, d_sym, r_sym = nearest_two(best)
      for i, c in enumerate(rest):
        if d_sym[i] <= tolerance and r_sym[i] >= 2 * d_sym[i]:
          out[rows[c]] = (int(cand[j_sym[i]]), int(best_op[i, j_sym[i]]))
        elif d_id[c] <= identity_tolerance and r_id[c] >= 2 * d_id[c]:
          out[rows[c]] = (int(cand[j_id[c]]), 0)
  return out


class _HklIndex(object):
  """Row of each Miller index in a table; -1 where the table has none."""
  _B = 1 << 20

  def __init__(self, hkl):
    import numpy as np
    keys = self._keys(hkl)
    self.order = np.argsort(keys, kind='stable')
    self.sorted = keys[self.order]

  def _keys(self, hkl):
    import numpy as np
    h = np.asarray(hkl, dtype=np.int64) + self._B
    return (h[:, 0] << 42) | (h[:, 1] << 21) | h[:, 2]

  def find(self, hkl):
    import numpy as np
    keys = self._keys(hkl)
    pos = np.searchsorted(self.sorted, keys)
    pos[pos == len(self.sorted)] = 0
    hit = self.sorted[pos] == keys
    return np.where(hit, self.order[pos], -1)


def _rotated_rows(index, hkl, rot, conjugate_ok):
  """For each row h, the row holding h.R and whether its value has to be
  conjugated (-h.R stored instead); -1 where neither is in the table.

  The table is atom-centred: an atom moved by (R, t) has f_new(h) = f_old(h.R),
  which is exactly what the structure factor already reads for that atom's
  symmetry copy, so an expanded table holds every row a reachable h needs.
  f(-k) = conj f(k) holds only without dispersion in the values (AD: TRUE).
  """
  import numpy as np
  k = hkl.dot(rot)
  rows = index.find(k)
  conj = np.zeros(len(rows), dtype=bool)
  if conjugate_ok:
    miss = rows < 0
    if miss.any():
      alt = index.find(-k[miss])
      conj[np.flatnonzero(miss)[alt >= 0]] = True
      rows[miss] = alt
  return rows, conj


def _conjugate_token(token):
  re_part, sep, im_part = token.partition(',')
  if not sep:
    return token
  im_part = im_part[1:] if im_part.startswith('-') else '-' + im_part.lstrip('+')
  return re_part + ',' + im_part


def _tscb_layout(path):
  """(offset of the id block, offset of the first row, row dtype, row count)."""
  import numpy as np
  with open(path, 'rb') as f:
    header_length = int.from_bytes(f.read(4), byteorder='little')
    header = f.read(header_length)
    n_columns = int.from_bytes(f.read(4), byteorder='little')
    width = _tscb_id_record_bytes(path, header, header_length, n_columns)
    id_start = 4 + header_length + 4
    f.seek(id_start + n_columns * width)
    n_refl = int.from_bytes(f.read(4), byteorder='little', signed=True)
    payload = f.tell()
  row = np.dtype([('h', '<i4', (3,)), ('f', '<c16', (n_columns,))])
  if os.path.getsize(path) != payload + n_refl * row.itemsize:
    raise ScattererResolutionError(
      "%s is not the size its own counts give; not rotating it" % os.path.basename(path))
  return id_start, payload, row, n_refl


def _tsc_rows(path):
  with open(path, 'r') as f:
    lines = f.read().split('\n')
  start = next(i for i, l in enumerate(lines) if l.startswith('DATA:')) + 1
  return lines[:start], [l.split() for l in lines[start:] if l.strip()]


def _complete_rows(index, hkl, rotations, conjugate_ok):
  """Rows whose whole orbit is in the table. Only these can ever be read:
  the loader asserts every h.R_s (or -h.R_s) of a reflection it serves."""
  import numpy as np
  complete = np.ones(len(hkl), dtype=bool)
  for rot in rotations:
    k = hkl.dot(rot)
    found = index.find(k) >= 0
    if conjugate_ok:
      found |= index.find(-k) >= 0
    complete &= found
  return complete


def _reorient_tscb(path, rotated, new_ids):
  import numpy as np
  import shutil
  id_start, payload, row, n_refl = _tscb_layout(path)
  tmp = path + '.reorient.tmp'
  shutil.copyfile(path, tmp)
  try:
    data = np.memmap(tmp, dtype=row, mode='r+', offset=payload, shape=(n_refl,))
    for column, rows, conj in rotated:
      old = np.array(data['f'][:, column])
      new = np.zeros_like(old)
      ok = rows >= 0
      new[ok] = old[rows[ok]]
      new[conj] = np.conj(new[conj])
      data['f'][:, column] = new
    data.flush()
    del data
    with open(tmp, 'r+b') as f:
      f.seek(id_start)
      for scat in new_ids:
        f.write(scat.to_bytes())
    shutil.copyfile(path, path + '.bak')
    os.replace(tmp, path)
  finally:
    if os.path.exists(tmp):
      os.remove(tmp)


def _reorient_tsc(path, rotated, new_ids):
  import shutil
  head, rows = _tsc_rows(path)
  head = ["SCATTERER_IDS: " + " ".join(s.to_hex_string() for s in new_ids)
          if l.startswith('SCATTERER_IDS:') else l for l in head]
  for column, src, conj in rotated:
    old = [r[3 + column] for r in rows]
    for i, r in enumerate(rows):
      if src[i] < 0:
        r[3 + column] = '0.00000000e+00,0.00000000e+00'
      else:
        r[3 + column] = _conjugate_token(old[src[i]]) if conj[i] else old[src[i]]
  tmp = path + '.reorient.tmp'
  with open(tmp, 'w') as f:
    f.write('\n'.join(head) + '\n')
    for r in rows:
      f.write(' '.join(r) + '\n')
  shutil.copyfile(path, path + '.bak')
  os.replace(tmp, path)


def _real_spherical_harmonics(lmax, u):
  """real_spherical_harmonics of harmonic_expansion.h at the unit vectors u
  (n x 3): column l*l + l + m holds Y_lm, the same convention and order."""
  import numpy as np
  x, y, z = u[:, 0], u[:, 1], u[:, 2]
  rho = np.sqrt(x*x + y*y)
  pole = rho == 0
  safe = np.where(pole, 1., rho)
  cp, sp = np.where(pole, 1., x/safe), np.where(pole, 0., y/safe)
  cm, sm = [np.ones_like(x)], [np.zeros_like(x)]
  for m in range(1, lmax + 1):
    cm.append(cm[m - 1]*cp - sm[m - 1]*sp)
    sm.append(sm[m - 1]*cp + cm[m - 1]*sp)
  p = {(0, 0): np.ones_like(x)}
  for m in range(1, lmax + 1):
    p[m, m] = -(2*m - 1)*rho*p[m - 1, m - 1]
  for m in range(lmax):
    p[m + 1, m] = (2*m + 1)*z*p[m, m]
  for m in range(lmax + 1):
    for l in range(m + 2, lmax + 1):
      p[l, m] = ((2*l - 1)*z*p[l - 1, m] - (l + m - 1)*p[l - 2, m])/(l - m)
  out = np.empty((len(x), (lmax + 1)**2))
  for l in range(lmax + 1):
    n = np.sqrt((2*l + 1)/(4*np.pi))
    out[:, l*l + l] = n*p[l, 0]
    for m in range(1, l + 1):
      n /= np.sqrt((l + m)*(l - m + 1))
      a = np.sqrt(2.)*(-1 if m % 2 else 1)*n*p[l, m]
      out[:, l*l + l + m] = a*cm[m]
      out[:, l*l + l - m] = a*sm[m]
  return out


def _rotate_tshb_shells(shells, q):
  """rotate_shells of harmonic_expansion.h: the shells of rho(r) rewritten for
  rho(Q^-1 r), Q orthogonal, so that the form factor at h becomes the old one
  at h.R. c'_m = int Y_m(u) sum_n c_n Y_n(Q^T u) du, by Gauss-Legendre in
  cos theta (l + 1 points) times 2l + 1 equal steps in phi, exact for the
  degree 2l of the integrand; an improper Q needs no special case. One matrix
  per l serves every shell of that l."""
  import numpy as np
  matrices, out = {}, []
  for sh in shells:
    l = sh.l
    if l == 0:
      out.append(sh)
      continue
    if l not in matrices:
      ct, w = np.polynomial.legendre.leggauss(l + 1)
      phi = 2*np.pi*np.arange(2*l + 1)/(2*l + 1)
      st = np.sqrt(np.maximum(0., 1 - ct*ct))
      u = np.stack([np.outer(st, np.cos(phi)).ravel(), np.outer(st, np.sin(phi)).ravel(),
                    np.repeat(ct, 2*l + 1)], axis=1)
      v = u.dot(q)                                    # Q^T u, row by row
      v /= np.linalg.norm(v, axis=1)[:, None]
      block = slice(l*l, (l + 1)**2)
      yu = _real_spherical_harmonics(l, u)[:, block]
      yv = _real_spherical_harmonics(l, v)[:, block]
      weight = np.repeat(w, 2*l + 1)*2*np.pi/(2*l + 1)
      matrices[l] = (yu*weight[:, None]).T.dot(yv)
    out.append(sh._replace(c=[float(x) for x in matrices[l].dot(sh.c)]))
  return out


def _reorient_tshb(path, plan, model_ids, unit_cell, ops):
  """The records of plan rotated with their atoms and keyed by the atoms'
  current ids, as _reorient_tscb does for columns. Rotated here and written,
  not left to the C++ reader: it rotates a record it finds on an image only in
  memory, and once the ids are brought up to date after the refinement the
  next load finds the record by id and no longer rotates it."""
  import numpy as np
  import shutil
  from smtbx.structure_factors.direct import tshb
  header, atoms = tshb.read(path)
  o = np.array(unit_cell.orthogonalization_matrix()).reshape(3, 3)
  f = np.array(unit_cell.fractionalization_matrix()).reshape(3, 3)
  for column, model_index, k in plan:
    shells = atoms[column].shells
    if (ops[k][0] != np.eye(3, dtype=int)).any():
      shells = _rotate_tshb_shells(shells, o.dot(ops[k][0]).dot(f))
    atoms[column] = atoms[column]._replace(
      shells=shells, key=bytes(model_ids[model_index].to_bytes()))
  # write() puts FRAME and UNITS first itself
  header = dict((k, v) for k, v in header.items() if k not in ("FRAME", "UNITS"))
  tmp = path + '.reorient.tmp'
  try:
    tshb.write(tmp, atoms, header)
    shutil.copyfile(path, path + '.bak')
    os.replace(tmp, path)
  finally:
    if os.path.exists(tmp):
      os.remove(tmp)


def _refuse_partial_tshb_move(path, plan, unmatched, ops):
  """Some records of a .tshb are on a rotated symmetry image of their sites,
  but not every record has an atom. Refused rather than left to the matching
  after it: the C++ reader would rotate the moved records for this load only,
  and the ids written after the refinement would make every later load read
  them unrotated, with nothing to say so."""
  import numpy as np
  moved = [column for column, _, k in plan if (ops[k][0] != np.eye(3, dtype=int)).any()]
  if not moved:
    return
  from smtbx.structure_factors.direct import tshb
  labels = [a.label for a in tshb.read(path)[1]]
  who = ("no atom, in place or on a symmetry image, matches %s"
         % " ".join(labels[c] for c in unmatched)) if unmatched else \
        "two records claim the same atom"
  raise ScattererResolutionError(
    "%s: the densities of %s would have to be rotated onto a symmetry image of "
    "their sites, but %s. A .tshb is rotated along only when every record has "
    "its atom; recalculate the densities, or undo the move."
    % (os.path.basename(path), " ".join(labels[c] for c in moved), who))


def reorient_moved_columns(tsc_file, model_ids, unit_cell, space_group,
                           tolerance=_MAX_SYMMETRY_MOVE_RESIDUAL_ANGSTROM, write=True):
  """Rotate the form factors of atoms that move, compaq, sgen -m, inv or
  transform took to a symmetry-equivalent site, instead of recalculating.

  A column's id records where its atom was when the table was made. An atom
  now on a symmetry image (R, t) of that site has the density rotated by R, so
  its column becomes f(h.R) row by row (see _rotated_rows) and takes the
  atom's current id. A pure translation needs nothing: the values are
  atom-centred. Label tables carry no positions and are left alone, and so is
  a table any column of which then has no atom, in place or on an image. The
  previous file is kept as <table>.bak. An id-keyed .tshb is matched the same
  way and its moved records' shells are rotated by Q = O R O^-1, as the C++
  reader rotates them in memory; a .tshb in which a record on a rotated image
  meets one with no atom is refused (ScattererResolutionError).

  Returns (rotated, refused, zeroed): [(model index, xyz)] of the columns
  rotated; model indices of atoms that did move by symmetry but whose column
  could not be rotated because a row the refinement can read has no h.R in
  the table; and how many unreachable row values were set to zero. With
  write=False the same answer is given and the file is not touched.
  """
  import numpy as np
  entries = read_scatterers(tsc_file)
  if not entries or isinstance(entries[0], str):
    return [], [], 0
  is_tshb = tsc_file.endswith('.tshb')
  header = read_header_lines(tsc_file)
  if not is_tshb and not tsc_file.endswith('.tscb') \
      and header.get('SYMM', '').lower() != 'expanded':
    return [], [], 0
  model_keys = dict((m.to_hex_string(), j) for j, m in enumerate(model_ids))
  ops = _move_candidates(space_group)
  # All or nothing: only a table every column of which then has its atom - in
  # place, shifted as by a refinement, or on a symmetry image - is touched. An
  # arbitrary rotation still puts the odd H near some image of some site, and
  # rotating that one column would rewrite a table that fits nothing.
  plan, claimed, pending = [], [], []
  for column, old in enumerate(entries):
    j = model_keys.get(old.to_hex_string())
    if j is None:
      pending.append(column)
    else:
      claimed.append(j)
  matches = _symmetry_matches([entries[c] for c in pending], model_ids, unit_cell, ops,
                              tolerance, _MAX_POSITIONAL_RESYNC_SHIFT_ANGSTROM) if pending else []
  unmatched = []
  for column, match in zip(pending, matches):
    if match is None:
      unmatched.append(column)
      continue
    claimed.append(match[0])
    if match[1] != 0:
      plan.append((column, match[0], match[1]))
  if unmatched or len(set(claimed)) != len(claimed):
    if is_tshb:
      _refuse_partial_tshb_move(tsc_file, plan, unmatched, ops)
    return [], [], 0
  if not plan:
    return [], [], 0
  if is_tshb:
    # densities, not rows: every rotation can be done, nothing is zeroed
    if write:
      _reorient_tshb(tsc_file, plan, model_ids, unit_cell, ops)
    return [(model_index, ops[k][2]) for column, model_index, k in plan], [], 0

  if tsc_file.endswith('.tscb'):
    id_start, payload, row, n_refl = _tscb_layout(tsc_file)
    hkl = np.array(np.memmap(tsc_file, dtype=row, mode='r', offset=payload,
                             shape=(n_refl,))['h'], dtype=np.int64)
  else:
    hkl = np.array([r[:3] for r in _tsc_rows(tsc_file)[1]], dtype=np.int64)
  index = _HklIndex(hkl)
  # filling a missing h.R from -h.R is exact only without dispersion in the
  # values; which rows the loader can read follows its own rule, which falls
  # back on -h unless the table says AD: FALSE in a group without a centre
  conjugate_ok = header.get('AD', '').upper() != 'TRUE'
  loader_conjugates = not (header.get('AD', '').upper() == 'FALSE'
                           and not space_group.is_centric())
  rotations = [ops[k][0] for k in range(len(space_group.all_ops()))]
  complete = _complete_rows(index, hkl, rotations, loader_conjugates)

  rotated, done, refused, zeroed = [], [], [], 0
  new_ids = list(entries)
  for column, model_index, k in plan:
    rows, conj = _rotated_rows(index, hkl, ops[k][0], conjugate_ok)
    if (complete & (rows < 0)).any():
      refused.append(model_index)
      continue
    rotated.append((column, rows, conj))
    done.append((model_index, ops[k][2]))
    new_ids[column] = model_ids[model_index]
    zeroed += int((rows < 0).sum())
  if rotated and write:
    if tsc_file.endswith('.tscb'):
      _reorient_tscb(tsc_file, rotated, new_ids)
    else:
      _reorient_tsc(tsc_file, rotated, new_ids)
  return done, refused, zeroed


def resolve_id_mapping_with_positional_fallback(read_scatterer_ids, internal_scatterer_ids, unit_cell,
                                                 max_shift_angstrom=_MAX_POSITIONAL_RESYNC_SHIFT_ANGSTROM,
                                                 labels=None):
  """Match each table column to the model atom it describes, by identity.

  Used once direct id lookup has failed, which it does after any refinement:
  an id bakes in the quantized fractional coordinate, so moving an atom at all
  changes it. What stays stable is the element, the part and roughly the
  position, so each column is matched on those.

  Matching is by identity and NOT by index. The table's column order is the
  order of whatever wrote it, which is not the model's atom order -- a table
  can begin with a hydrogen where the model begins with the heavy atom. An
  index-wise correspondence looks plausible whenever the elements happen to
  line up and is silently wrong the rest of the time, and since the result is
  written back to the file, being wrong here corrupts the table permanently.

  An atom moved by hand (Fit, a drag) can land nearer a neighbour's site than
  twice its own shift, so columns are matched in rounds: a column takes its
  nearest atom that no column has taken yet once that atom is the only free
  one or half as far as the next, nearest first. The atoms that did not move
  are all taken in the first round, which leaves a moved one as its column's
  only candidate. The last free atom of an element and part takes the last
  column of that kind however far it went. Anything still ambiguous is
  refused.

  Returns file_to_model: for each column, the index of the model atom it
  belongs to. Given the model's labels, the atoms that moved further than a
  refinement shift are named, since their columns still describe the old site.
  """
  from cctbx.xray import ext

  if len(read_scatterer_ids) != len(internal_scatterer_ids):
    raise ScattererResolutionError(
      f"scatterer count changed (file has {len(read_scatterer_ids)}, "
      f"model has {len(internal_scatterer_ids)})")

  model = [ext.scatterer_id_big(i) for i in internal_scatterer_ids]
  kinds = [(new.get_z(), new.get_data()) for new in model]
  candidates, column_kind = [], []
  for old_id in read_scatterer_ids:
    old = ext.scatterer_id_big(old_id)
    kind = (old.get_z(), old.get_data())
    candidates.append(sorted((unit_cell.mod_short_distance(old.get_crd(), model[j].get_crd()), j)
                             for j in range(len(model)) if kinds[j] == kind))
    column_kind.append(kind)

  file_to_model, claimed = [None] * len(candidates), set()
  while True:
    picks = []
    for column, cand in enumerate(candidates):
      if file_to_model[column] is not None:
        continue
      free = [c for c in cand if c[1] not in claimed]
      # a rival nearly as close means it cannot be told which atom this is, and
      # guessing would put a whole column of contributions on the wrong atom.
      # An EXYZ pair of one element (O/O2- in COD 2312749) has one id twice and
      # is no rival to itself: its columns take its atoms in turn, round by round
      rival = [c for c in free[1:]
               if internal_scatterer_ids[c[1]] != internal_scatterer_ids[free[0][1]]] if free else []
      if free and free[0][0] <= max_shift_angstrom and (
          not rival or rival[0][0] >= 2 * free[0][0]):
        picks.append((free[0][0], column, free[0][1]))
    taken = 0
    for d, column, j in sorted(picks):
      if j not in claimed:
        file_to_model[column] = j
        claimed.add(j)
        taken += 1
    if not taken:
      break

  left = [c for c, j in enumerate(file_to_model) if j is None]
  for column in left:
    kind = column_kind[column]
    free = [j for j in range(len(model)) if j not in claimed and kinds[j] == kind]
    if len(free) == 1 and sum(column_kind[c] == kind for c in left) == 1:
      file_to_model[column] = free[0]
      claimed.add(free[0])
      continue
    near = [d for d, j in candidates[column] if j not in claimed][:2]
    if not near or near[0] > max_shift_angstrom:
      raise ScattererResolutionError(
        f"column {column}: no atom of the same element and part within "
        f"{max_shift_angstrom} A of where the table says it was; aborting "
        "without modifying the TSC/TSCB file")
    raise ScattererResolutionError(
      f"column {column}: two atoms are comparably close ({near[0]:.3f} A and "
      f"{near[1]:.3f} A); refusing to guess which one it is")

  if labels is not None:
    moved = [(labels[j], d) for column, j in enumerate(file_to_model)
             for d, k in candidates[column] if k == j and d > _MANUAL_MOVE_ANGSTROM]
    if moved:
      print("Moved since the table was made, columns follow them: %s. Their form "
            "factors are still those of the old sites; recalculate the table if "
            "the move was more than a nudge." % ", ".join("%s (%.2f A)" % m for m in moved))
  return file_to_model


def _columns_in_turn(entries, internal_scatterer_ids):
  """The column of each atom by exact id. An EXYZ pair of one element has one
  id twice, so each atom takes its own column in turn; index() put both on the
  first (2312749: R1 0.0272 and 0.0302 every other round). Ids compare by
  value but hash by identity, hence index() and not a dict."""
  internal_to_tsc, taken = [], set()
  for x in internal_scatterer_ids:
    column = entries.index(x)
    while column in taken:
      column = entries.index(x, column + 1)
    internal_to_tsc.append(column)
    taken.add(column)
  return internal_to_tsc


def resolve_scatterer_mapping(file_entries, model_labels, internal_scatterer_ids, unit_cell):
  """Which table column describes each model atom.

  Returns internal_to_tsc: internal_to_tsc[model_index] is the column of the
  table that belongs to that atom. Reads nothing from disk and writes nothing;
  the caller decides what to do with the mapping.

  A table names its columns either by label or by scatterer id, and neither is
  in the model's atom order, so both are matched by identity. Labels match by
  name, which survives a refinement; ids bake in the coordinate, so they match
  exactly only until the first shift and fall back on element, part and
  position after that.
  """
  if file_entries and isinstance(file_entries[0], str):
    # A label survives a refinement, so this either matches or the atoms were
    # renamed -- in which case a label table carries nothing else to identify
    # its columns by and there is no recovery. Say so rather than guess: the
    # column order is not the model's, so pairing by position would put the
    # columns on the wrong atoms.
    ids = convert_labels_to_ids(file_entries, model_labels, internal_scatterer_ids)
    return _columns_in_turn(ids, internal_scatterer_ids)

  try:
    return _columns_in_turn(file_entries, internal_scatterer_ids)
  except ValueError:
    # The ids no longer match exactly, which any refinement causes; match on
    # what survives a move instead.
    file_to_model = resolve_id_mapping_with_positional_fallback(
      file_entries, internal_scatterer_ids, unit_cell, labels=model_labels)
    internal_to_tsc = [None] * len(internal_scatterer_ids)
    for column, model_index in enumerate(file_to_model):
      internal_to_tsc[model_index] = column
    return internal_to_tsc
