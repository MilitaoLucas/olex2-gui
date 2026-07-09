import os
import tempfile


class ScattererResolutionError(Exception):
  pass


def read_scatterers_from_tsc(tsc_file):
    scatterer_ids = []
    with open(tsc_file, 'r') as f:
        for line in f:
            if line.startswith('SCATTERERS:'):
                parts = line.split()[1:]
                for part in parts:
                    scatterer_ids.append(part)
                break
            if line.startswith('SCATTERER_IDS:'):
                parts = line.split()[1:]
                for part in parts:
                    scatterer_ids.append(int(part,16))
                break
    return scatterer_ids

def read_scatterers_from_tscb(tscb_file):
    scatterer_ids = []
    with open(tscb_file, 'rb') as f:
        header_length = int.from_bytes(f.read(4), byteorder='little')
        header = f.read(header_length)
        n_scatterers = int.from_bytes(f.read(4), byteorder='little')

        if header == b"SCATTERER_IDS":
            for _ in range(n_scatterers):
                scatterer_id = int.from_bytes(f.read(8), byteorder='little')
                scatterer_ids.append(scatterer_id)
        else:
            # If the header is not "SCATTERER_IDS", the scatterers are stored as a single
            # space-separated string of labels. In this branch the value just read is not a
            # count of scatterers but the byte size of that payload string (matches the C++
            # writer, which writes payload.size() followed by the raw payload bytes).
            payload_size = n_scatterers
            payload = f.read(payload_size).decode('utf-8')
            scatterer_ids = payload.split(' ')
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
            if not (line.startswith('SCATTERER_IDS:') or line.startswith('SCATTERERS')):
                new_data += line
                continue
            
            if isinstance(scatterers[0], int):
                new_data += "SCATTERER_IDS: "
                new_data += " ".join([f"{sid:016x}" for sid in scatterers]) + "\n"
                break
            elif isinstance(scatterers[0], str):
                new_data += "SCATTERERS: "
                new_data += " ".join([f"{label}" for label in scatterers]) + "\n"
                break


        new_data += f.read()  # Append the rest of the file

    temp_fd, temp_path = tempfile.mkstemp(prefix="tsc_rewrite_", suffix=".tmp", dir=os.path.dirname(tsc_file) or None)
    try:
      with os.fdopen(temp_fd, 'w') as temp_file:
        temp_file.write(new_data)
      os.replace(temp_path, tsc_file)
    finally:
      if os.path.exists(temp_path):
        os.remove(temp_path)

def update_tscb_file(tscb_file, scatterers):
    with open(tscb_file, "r+b") as f:
        header_length = int.from_bytes(f.read(4), byteorder='little')
        header = f.read(header_length)
        n_scatterers = int.from_bytes(f.read(4), byteorder='little')

        if (header == b"SCATTERER_IDS"  and isinstance(scatterers[0], int)):
            #As the number of scatterers did not change, the lenght of the representation does not change, so we can just overwrite the scatterer IDs in place.
            if n_scatterers != len(scatterers):
                raise ValueError(f"Number of scatterers in TSCB file ({n_scatterers}) does not match the provided list ({len(scatterers)}).")
            for scat in scatterers:
                f.write(scat.to_bytes(8, byteorder='little'))
            return
            
        #We have to change the size of the file, thus we need to first save the data written at the end
        if (header == b"SCATTERER_IDS"): 
            f.seek(8 * n_scatterers, 1)
        else: 
            f.seek(n_scatterers, 1) 
        data = f.read() #Save data that comes after the scatterer IDs or labels
        f.seek(0)
        
        if isinstance(scatterers[0], int):
            f.write(len(b"SCATTERER_IDS").to_bytes(4, byteorder='little'))
            f.write(b"SCATTERER_IDS")
            f.write(len(scatterers).to_bytes(4, byteorder='little'))
            for scat in scatterers:
                f.write(scat.to_bytes(8, byteorder='little'))
        else:
            f.write(int(0).to_bytes(4, byteorder='little')) #Label scatteres do not get a header, so we write a 0 length header
            new_payload = " ".join(str(scat) for scat in scatterers).encode('utf-8')
            f.write(len(new_payload).to_bytes(4, byteorder='little'))
            f.write(new_payload)
            
        f.write(data) #Write the rest of the data back to the file

def update_scatterers_in_file(tsc_file, scatterers):
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

    label_to_id = {}
    for label, atom_id in zip(model_labels, model_ids):
        if label in label_to_id:
          raise ScattererResolutionError(f"duplicate atom label '{label}' in current model")
        label_to_id[label] = atom_id

    missing = [label for label in labels if label not in label_to_id]
    if missing:
      raise ScattererResolutionError(
        f"{len(missing)} label(s) from the table file were not found in the current model "
        f"(renamed?): {missing[:5]}{'...' if len(missing) > 5 else ''}")

    return [label_to_id[label] for label in labels]


def resolve_labels_by_position(file_labels, model_labels):
  # Fallback used only once strict label matching has already failed (e.g. a rename broke the
  # dict lookup in convert_labels_to_ids). Assumes the table file's scatterer order still lines
  # up positionally with the model's current atom order - a safe assumption as long as no atoms
  # were added/removed/reordered, which is exactly the condition strict matching cannot verify
  # once labels no longer match by content.
  if len(file_labels) != len(model_labels):
    raise ScattererResolutionError(
      f"scatterer count changed (file has {len(file_labels)}, model has {len(model_labels)}); "
      "cannot safely recover a renamed-label mapping by position")

  renamed = [(i, file_labels[i], model_labels[i])
             for i in range(len(file_labels)) if file_labels[i] != model_labels[i]]
  return list(range(len(file_labels))), renamed


_MAX_POSITIONAL_RESYNC_SHIFT_ANGSTROM = 2.0


def resolve_id_mapping_with_positional_fallback(read_scatterer_ids, internal_scatterer_ids, unit_cell,
                                                 max_shift_angstrom=_MAX_POSITIONAL_RESYNC_SHIFT_ANGSTROM):
  # Fallback used only once direct id lookup has already failed (get_id_5_16() bakes in quantized
  # fractional coordinates, so simply moving an atom changes its id). Validates position-by-position
  # using the two id-derived fields that ARE stable across a move: the element (Z) and, via a
  # distance bound, plausibility of the coordinate shift for "the same atom moved" rather than
  # "two atoms got swapped/reordered".
  #
  # Known limitation: this cannot distinguish two same-element atoms that were swapped in array
  # position if they happen to sit within max_shift_angstrom of each other - closing that gap would
  # need full assignment/Hungarian-style matching, which is more than the available data (label,
  # Z, count, position) can soundly support, so it is left as a documented residual risk.
  from cctbx.xray import ext

  if len(read_scatterer_ids) != len(internal_scatterer_ids):
    raise ScattererResolutionError(
      f"scatterer count changed (file has {len(read_scatterer_ids)}, "
      f"model has {len(internal_scatterer_ids)})")

  for i, (old_id, new_id) in enumerate(zip(read_scatterer_ids, internal_scatterer_ids)):
    old = ext.scatterer_id_5_16(old_id)
    new = ext.scatterer_id_5_16(new_id)
    if old.get_z() != new.get_z():
      raise ScattererResolutionError(
        f"position {i}: element mismatch (file Z={old.get_z()}, model Z={new.get_z()}); "
        "looks like a reorder/swap rather than a relocation - aborting without modifying "
        "the TSC/TSCB file")
    shift = unit_cell.distance(old.get_crd(), new.get_crd())
    if shift > max_shift_angstrom:
      raise ScattererResolutionError(
        f"position {i}: implausible shift ({shift:.2f} A) for a same-element atom; "
        "aborting without modifying the TSC/TSCB file")

  return list(range(len(internal_scatterer_ids)))


def resolve_scatterer_mapping(file_entries, model_labels, internal_scatterer_ids, unit_cell,
                               allow_rename_recovery):
  """Map model-atom order -> table-file scatterer order, recovering from a renamed label or a
  moved-atom stale id where possible.

  Returns (internal_to_tsc, ids_to_persist_or_None). ids_to_persist is the id list (in model
  order) that the caller should write back to the table file to bring it back in sync; None
  means the table file already matches and needs no rewrite. This function never touches disk
  or any nsa2_* param - the caller is responsible for the actual write and hash refresh.
  """
  if file_entries and isinstance(file_entries[0], str):
    try:
      ids = convert_labels_to_ids(file_entries, model_labels, internal_scatterer_ids)
      internal_to_tsc = [ids.index(x) for x in internal_scatterer_ids]
      return internal_to_tsc, None
    except ScattererResolutionError:
      if not allow_rename_recovery:
        raise
      internal_to_tsc, _renamed = resolve_labels_by_position(file_entries, model_labels)
      return internal_to_tsc, internal_scatterer_ids
  else:
    try:
      internal_to_tsc = [file_entries.index(x) for x in internal_scatterer_ids]
      return internal_to_tsc, None
    except ValueError:
      internal_to_tsc = resolve_id_mapping_with_positional_fallback(
        file_entries, internal_scatterer_ids, unit_cell)
      return internal_to_tsc, internal_scatterer_ids
