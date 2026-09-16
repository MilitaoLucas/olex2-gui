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
    else:
        return read_scatterers_from_tsc(tsc_file)

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

def update_scatterers_in_file(tsc_file, scatterers, extra_header_lines=None):
    # Rewriting the table is the one action here that can damage it, and when
    # it goes wrong nothing else says so: the file stays the right shape, the
    # numbers stay plausible, and the refinement simply describes the wrong
    # atoms from then on. It is rare and cheap, so it says that it happened.
    kind = 'labels' if isinstance(scatterers[0], str) else 'ids'
    print("Updating the %d scatterer %s in %s"
          % (len(scatterers), kind, os.path.basename(tsc_file)))
    if tsc_file.endswith('.tscb'):
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
  index = {}
  for label, atom_id in zip(model_labels, model_ids):
    triple = _residue_triple(label)
    if triple is None:
      return None
    if triple in index:
      return None
    index[triple] = atom_id
  out = []
  for label in labels:
    triple = _residue_triple(label)
    if triple is None or triple not in index:
      return None
    out.append(index[triple])
  print("Table labels are in the other residue naming order; matched all %d "
        "on chain, residue and atom" % len(out))
  return out


_MAX_POSITIONAL_RESYNC_SHIFT_ANGSTROM = 2.0


def resolve_id_mapping_with_positional_fallback(read_scatterer_ids, internal_scatterer_ids, unit_cell,
                                                 max_shift_angstrom=_MAX_POSITIONAL_RESYNC_SHIFT_ANGSTROM):
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

  Returns file_to_model: for each column, the index of the model atom it
  belongs to.
  """
  from cctbx.xray import ext

  if len(read_scatterer_ids) != len(internal_scatterer_ids):
    raise ScattererResolutionError(
      f"scatterer count changed (file has {len(read_scatterer_ids)}, "
      f"model has {len(internal_scatterer_ids)})")

  model = [ext.scatterer_id_big(i) for i in internal_scatterer_ids]
  file_to_model = []
  for column, old_id in enumerate(read_scatterer_ids):
    old = ext.scatterer_id_big(old_id)
    best, best_d, next_d = None, None, None
    for j, new in enumerate(model):
      if old.get_z() != new.get_z() or old.get_data() != new.get_data():
        continue
      d = unit_cell.mod_short_distance(old.get_crd(), new.get_crd())
      if best_d is None or d < best_d:
        best, best_d, next_d = j, d, best_d
      elif next_d is None or d < next_d:
        next_d = d
    if best is None or best_d > max_shift_angstrom:
      raise ScattererResolutionError(
        f"column {column}: no atom of the same element and part within "
        f"{max_shift_angstrom} A of where the table says it was; aborting "
        "without modifying the TSC/TSCB file")
    # a rival nearly as close means it cannot be told which atom this is, and
    # guessing would put a whole column of contributions on the wrong atom
    if next_d is not None and next_d < 2 * best_d:
      raise ScattererResolutionError(
        f"column {column}: two atoms are comparably close ({best_d:.3f} A and "
        f"{next_d:.3f} A); refusing to guess which one it is")
    file_to_model.append(best)

  if len(set(file_to_model)) != len(file_to_model):
    raise ScattererResolutionError(
      "two table columns resolved to the same atom; the table does not "
      "describe this model")
  return file_to_model


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
    return [ids.index(x) for x in internal_scatterer_ids]

  try:
    return [file_entries.index(x) for x in internal_scatterer_ids]
  except ValueError:
    # The ids no longer match exactly, which any refinement causes; match on
    # what survives a move instead.
    file_to_model = resolve_id_mapping_with_positional_fallback(
      file_entries, internal_scatterer_ids, unit_cell)
    internal_to_tsc = [None] * len(internal_scatterer_ids)
    for column, model_index in enumerate(file_to_model):
      internal_to_tsc[model_index] = column
    return internal_to_tsc
