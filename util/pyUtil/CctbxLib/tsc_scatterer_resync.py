import os
import cctbx.xray as xray_


class ScattererResolutionError(Exception):
  pass

def read_binary_scatterers(filestream):
    decode_scale = 16 / (0xFFFFFFFF/2)
    frac_x = int.from_bytes(filestream.read(4), byteorder='little', signed=True) * decode_scale
    frac_y = int.from_bytes(filestream.read(4), byteorder='little', signed=True) * decode_scale
    frac_z = int.from_bytes(filestream.read(4), byteorder='little', signed=True) * decode_scale
    data = int.from_bytes(filestream.read(2), byteorder='little', signed=True)
    Z = int.from_bytes(filestream.read(1), byteorder='little')
    reserved = int.from_bytes(filestream.read(1), byteorder='little')
    return xray_.scatterer_id_big(frac_x, frac_y, frac_z, data, Z, reserved)


def read_scatterers_from_tscb(tscb_file):
    scatterer_ids = []
    with open(tscb_file, 'rb') as f:
        header_length = int.from_bytes(f.read(4), byteorder='little')
        header = f.read(header_length)
        n_scatterers = int.from_bytes(f.read(4), byteorder='little')

        if header == b"SCATTERER_IDS":
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
                    scatterer_ids.append(xray_.scatterer_id_big(scat))
                else:
                    scatterer_ids.append(scat)
            break
    return scatterer_ids


def read_scatterers(tsc_file):
    if tsc_file.endswith('.tscb'):
        return read_scatterers_from_tscb(tsc_file)
    else:
        return read_scatterers_from_tsc(tsc_file)

def update_tsc_file(tsc_file, scatterers):
    new_data = ""
    with open(tsc_file, 'r') as f:
        for line in f:
            if not (line.startswith('SCATTERER_IDS:') or line.startswith('SCATTERERS:')):
                new_data += line
                continue
            
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

def update_tscb_file(tscb_file, scatterers):
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

        if (header == b"SCATTERER_IDS"  and not isinstance(scatterers[0], str)):
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
        elif (header == b"" and isinstance(scatterers[0], str)):
            #As the number of scatterers did not change, the lenght of the representation does not change, so we can just overwrite the scatterer labels in place.
            if n_scatterers != len(scatterers):
                raise ValueError(f"Number of scatterers in TSCB file ({n_scatterers}) does not match the provided list ({len(scatterers)}).")
            new_payload = " ".join(str(scat) for scat in scatterers).encode('utf-8')
            if len(new_payload) != n_scatterers:
                raise ValueError(
                    f"label payload changed size ({n_scatterers} -> {len(new_payload)}); "
                    "cannot be overwritten in place")
            f.seek(payload_start)
            f.write(len(new_payload).to_bytes(4, byteorder='little'))
            f.write(new_payload)
            return
            
        #We have to change the size of the file, thus we need to first save the data written at the end
        if (header == b"SCATTERER_IDS"): 
            f.seek(16 * n_scatterers, 1)
        else: 
            f.seek(n_scatterers, 1) 
        data = f.read() #Save data that comes after the scatterer IDs or labels
        f.seek(0)
        
        if isinstance(scatterers[0], str):
            f.write(int(0).to_bytes(4, byteorder='little')) #Label scatteres do not get a header, so we write a 0 length header
            new_payload = " ".join(str(scat) for scat in scatterers).encode('utf-8')
            f.write(len(new_payload).to_bytes(4, byteorder='little'))
            f.write(new_payload)
        else: #AtomID case
            f.write(len(b"SCATTERER_IDS").to_bytes(4, byteorder='little'))
            f.write(b"SCATTERER_IDS")
            f.write(len(scatterers).to_bytes(4, byteorder='little'))
            for scat in scatterers:
                f.write(scat.to_bytes())
                
        f.write(data) #Write the rest of the data back to the file

def update_scatterers_in_file(tsc_file, scatterers):
    # Rewriting the table is the one action here that can damage it, and when
    # it goes wrong nothing else says so: the file stays the right shape, the
    # numbers stay plausible, and the refinement simply describes the wrong
    # atoms from then on. It is rare and cheap, so it says that it happened.
    kind = 'labels' if isinstance(scatterers[0], str) else 'ids'
    print("Updating the %d scatterer %s in %s"
          % (len(scatterers), kind, os.path.basename(tsc_file)))
    if tsc_file.endswith('.tscb'):
        update_tscb_file(tsc_file, scatterers)
    else:
        update_tsc_file(tsc_file, scatterers)


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
