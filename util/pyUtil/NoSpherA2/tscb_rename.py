import os
import hashlib
import re
import struct
import tempfile


_LABEL_CHARS = r"A-Za-z0-9_'"
_MAX_TSCB_BYTES = 1024 * 1024 * 1024
_MAX_SCATTERER_BYTES = 256 * 1024 * 1024
_MAX_SCATTERER_TOKENS = 2_000_000


def _tokenize_whitespace_segment(text):
  # Guarded tokenizer: each iteration advances `index`, and we cap both
  # iterations and token count to avoid pathological input behavior.
  tokens = []
  text_len = len(text)
  index = 0
  iterations = 0
  max_iterations = text_len + 1

  while index < text_len:
    iterations += 1
    if iterations > max_iterations:
      raise ValueError("Scatterer tokenization exceeded safe iteration limit")

    while index < text_len and text[index].isspace():
      index += 1
    if index >= text_len:
      break

    token_start = index
    while index < text_len and not text[index].isspace():
      index += 1
    tokens.append(text[token_start:index])

    if len(tokens) > _MAX_SCATTERER_TOKENS:
      raise ValueError("Scatterer token count exceeds safe limit")

  return tokens


def _find_scatterers_segment(scatterer_text):
  start_match = re.search(r"(^|\r?\n)(Scatterers:\s*)", scatterer_text)
  if start_match is None:
    stripped = scatterer_text.strip()
    if not stripped:
      return None
    leading_ws = len(scatterer_text) - len(scatterer_text.lstrip())
    trailing_ws = len(scatterer_text.rstrip())
    return leading_ws, trailing_ws

  segment_start = start_match.end(2)
  end_match = re.search(r"\r?\n(?:Symm|Data):\s*", scatterer_text[segment_start:])
  if end_match is None:
    return None

  segment_end = segment_start + end_match.start()
  return segment_start, segment_end


def _locate_scatterers_block(tscb_bytes):
  if len(tscb_bytes) > _MAX_TSCB_BYTES:
    raise ValueError("TSCB file is too large")
  if len(tscb_bytes) < 12:
    raise ValueError("TSCB file is too short")

  header_len = struct.unpack_from("<i", tscb_bytes, 0)[0]
  if header_len < 0:
    raise ValueError("Invalid TSCB header length")

  scatterer_len_offset = 4 + header_len
  if scatterer_len_offset + 4 > len(tscb_bytes):
    raise ValueError("Invalid TSCB header length")

  scatterer_len = struct.unpack_from("<i", tscb_bytes, scatterer_len_offset)[0]
  if scatterer_len < 0:
    raise ValueError("Invalid TSCB scatterer block length")

  scatterer_start = scatterer_len_offset + 4
  scatterer_end = scatterer_start + scatterer_len
  if scatterer_len > _MAX_SCATTERER_BYTES:
    raise ValueError("TSCB scatterer block is too large")
  if scatterer_end < scatterer_start:
    raise ValueError("Invalid TSCB scatterer block bounds")
  if scatterer_end > len(tscb_bytes):
    raise ValueError("Invalid TSCB scatterer block length")

  return scatterer_len_offset, scatterer_start, scatterer_end


def extract_scatterer_labels(scatterer_text):
  segment_bounds = _find_scatterers_segment(scatterer_text)
  if segment_bounds is None:
    return []
  segment_start, segment_end = segment_bounds
  if segment_start < 0 or segment_end < segment_start or segment_end > len(scatterer_text):
    raise ValueError("Invalid scatterer segment bounds")
  return _tokenize_whitespace_segment(scatterer_text[segment_start:segment_end])


def remap_scatterer_text(scatterer_text, rename_map):
  if not rename_map:
    return scatterer_text, 0

  keys = [key for key in rename_map if key]
  if not keys:
    return scatterer_text, 0

  segment_bounds = _find_scatterers_segment(scatterer_text)
  if segment_bounds is None:
    return scatterer_text, 0

  segment_start, segment_end = segment_bounds
  if segment_start < 0 or segment_end < segment_start or segment_end > len(scatterer_text):
    raise ValueError("Invalid scatterer segment bounds")
  scatterers_segment = scatterer_text[segment_start:segment_end]
  tokens = _tokenize_whitespace_segment(scatterers_segment)
  replacement_count = 0
  updated_tokens = []
  for token in tokens:
    replacement = rename_map.get(token, token)
    if replacement != token:
      replacement_count += 1
    updated_tokens.append(replacement)

  if replacement_count == 0:
    return scatterer_text, 0

  updated_segment = " ".join(updated_tokens)
  updated_text = scatterer_text[:segment_start] + updated_segment + scatterer_text[segment_end:]
  return updated_text, replacement_count


def rewrite_tscb_scatterers(tscb_path, rename_map):
  with open(tscb_path, "rb") as file_handle:
    tscb_bytes = file_handle.read()

  scatterer_len_offset, scatterer_start, scatterer_end = _locate_scatterers_block(tscb_bytes)
  scatterer_bytes = tscb_bytes[scatterer_start:scatterer_end]

  encoding = "utf-8"
  try:
    scatterer_text = scatterer_bytes.decode("utf-8")
  except UnicodeDecodeError:
    encoding = "latin-1"
    scatterer_text = scatterer_bytes.decode("latin-1")

  updated_text, replacement_count = remap_scatterer_text(scatterer_text, rename_map)
  if replacement_count == 0:
    return 0

  updated_scatterer_bytes = updated_text.encode(encoding)
  rebuilt = bytearray()
  rebuilt.extend(tscb_bytes[:scatterer_len_offset])
  rebuilt.extend(struct.pack("<i", len(updated_scatterer_bytes)))
  rebuilt.extend(updated_scatterer_bytes)
  rebuilt.extend(tscb_bytes[scatterer_end:])
  updated_file_hash = hashlib.sha256(rebuilt).hexdigest()

  temp_fd, temp_path = tempfile.mkstemp(prefix="tscb_rename_", suffix=".tmp", dir=os.path.dirname(tscb_path) or None)
  try:
    with os.fdopen(temp_fd, "wb") as temp_file:
      temp_file.write(rebuilt)
    os.replace(temp_path, tscb_path)
  finally:
    if os.path.exists(temp_path):
      os.remove(temp_path)

  return replacement_count, updated_file_hash


def read_tscb_scatterer_labels(tscb_path):
  scatterer_text = read_tscb_scatterer_text(tscb_path)
  return extract_scatterer_labels(scatterer_text)


def read_tscb_scatterer_text(tscb_path):
  with open(tscb_path, "rb") as file_handle:
    tscb_bytes = file_handle.read()

  _, scatterer_start, scatterer_end = _locate_scatterers_block(tscb_bytes)
  scatterer_bytes = tscb_bytes[scatterer_start:scatterer_end]

  try:
    scatterer_text = scatterer_bytes.decode("utf-8")
  except UnicodeDecodeError:
    scatterer_text = scatterer_bytes.decode("latin-1")

  return scatterer_text
