import olx
import olex
import olexex
import os
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import gui
debug = bool(OV.GetParam("olex2.debug", False))

def get_existing_fvar_dropdown_items():
  FvarNum=0
  while OV.GetFVar(FvarNum) is not None:
    FvarNum+=1
  items = ""
  for i in range(FvarNum):
    i += 1
    items += "%s;" %(i+1)
  return items
OV.registerFunction(get_existing_fvar_dropdown_items, False, "gui.disorder")

def set_part_colour(part = None):
  if not part:
    part = set(olexex.OlexRefinementModel().disorder_parts()) - {0}
    part =  " ".join(map(str, part))
  d = {'part': part}
  cmds = gui.tools.TemplateProvider.get_template('set_part_colour_cmds') %d
  OV.runCommands(cmds=cmds.split("\n"))
OV.registerFunction(set_part_colour, False, "gui.disorder")

def get_selected_atom_info():
  cmd = "info"
  a = gui.tools.scrub(cmd)[1:]
  return _parse_atom_table(a)

def set_pC():
  cmds = gui.tools.TemplateProvider.get_template('set_pC', force=debug)
  OV.runCommands(cmds=cmds.split("\n"))
OV.registerFunction(set_pC, False, "gui.disorder")

def set_pA_or_pB(part):
  import gui
  val_parts = OV.GetControlValue('SPLIT_PARTS', None)
  val_fvars = OV.GetControlValue('SPLIT_FVARS', None)
  val_restraints = OV.GetControlValue('SPLIT_RESTRAINTS', None)
  d = get_selected_atom_info()
  atoms = d

  if val_restraints != "--":
    d.setdefault("restraints", val_restraints)

  if val_parts != "auto":
    if part == "A":
      d.setdefault("part",  val_parts.split("/")[0].strip())
    else:
      d.setdefault("part",  val_parts.split("/")[1].strip())
  else:
    if part == "A":
      d.setdefault("part",  "1")
    else:
      d.setdefault("part",  "2")
    
  if val_fvars != "auto":
    if part == "A":
      d.setdefault("fvar",  val_fvars)
    else:
      d.setdefault("fvar",  f"-{val_fvars}")
  else:
    if part == "A":
      d.setdefault("fvar",  "2")
    else:
      d.setdefault("fvar",  "-2")

  for atom in atoms:
    olex.m(f"sel {atom}")
  cmds = gui.tools.TemplateProvider.get_template('set_pA_or_pB', force=debug) % d
  OV.runCommands(cmds=cmds.split("\n"))

  for atom in atoms:
    olex.m(f"sel {atom}")
    if atom.startswith("Q"):
      olex.m(f"name C")
  olex.m("sel -u")

OV.registerFunction(set_pA_or_pB, False, "gui.disorder")

def set_mode_fit():
  cmd = "mode fit -s"
  val_parts = OV.GetControlValue('SPLIT_PARTS', None)
  val_fvars = OV.GetControlValue('SPLIT_FVARS', None)
  val_restraints = OV.GetControlValue('SPLIT_RESTRAINTS', None)

  if val_restraints != "--":
    cmd += " %s" %val_restraints

  if val_parts != "auto":
    cmd += " -p=%s" % val_parts.split("/")[0].strip()

  if val_fvars != "auto":
    cmd += " -v=%s" % val_fvars

  olex.m(cmd)

OV.registerFunction(set_mode_fit, False, "gui.disorder")


def _parse_atom_table(lines):
  atoms = {}
  headers = None
  in_table = False

  for line in lines:
    line = line.strip()
    if not line:
      continue

    if line.startswith("Atom Type"):
      headers = line.split()
      in_table = True
      continue

    if line.startswith("Mean Uiso"):
      break

    if in_table:
      parts = line.split()
      if len(parts) == len(headers):
        atom_name = parts[0]
        atoms[atom_name] = dict(zip(headers[1:], parts[1:]))

  return atoms