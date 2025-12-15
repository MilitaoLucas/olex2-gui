import json
from pathlib import Path
from typing import Union

def read_constant(name: str) -> Union[dict, list]:
  cdir = Path.cwd()
  const_dir = cdir / "constant_files"
  if not name.endswith(".json"):
    name += ".json"
  if (file_path := const_dir  / name).exists():
    with open(file_path, "r") as f:
      constant = json.load(f)
  else:
    raise FileExistsError("No such file.")
  return constant

PERIODIC_TABLE = read_constant("periodc_table")