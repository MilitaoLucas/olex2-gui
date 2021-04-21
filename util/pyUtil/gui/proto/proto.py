##https://stackabuse.com/a-sqlite-tutorial-with-python/

import os
import gui
import olex
import olx
from olexFunctions import OV
p_path = os.path.dirname(os.path.abspath(__file__))
import sqlite3

def _deal_with_phil(operation='read'):
  user_phil_file = os.path.join(OV.DataDir(), "proto_user.phil")
  phil_file = os.path.join(p_path, "proto.phil")
  if operation == "read":
    phil = open(phil_file, 'r').read()
    olx.phil_handler.adopt_phil(phil_string=phil)
    if os.path.exists(user_phil_file):
      olx.phil_handler.update(phil_file=user_phil_file)
  elif operation == "save":
    phil_files = [user_phil_file]
    for phil in phil_files:
      olx.phil_handler.save_param_file(
        file_name=phil, scope_name='proto', diff_only=True)


def db_connect():
  db_location = OV.GetParam('proto.db_location', None)
  if "()" in db_location:
    base = db_location.split('()')
    _ = getattr(OV, base[0])
    path = _()
    db_location = os.path.join(path, base[1])

  db_name = OV.GetParam('proto.db_name', None)
  db_path = os.path.join(db_location, db_name)
  if not os.path.exists(db_path):
    print("There is no proto db")
    return
  con = sqlite3.connect(db_path)
  print("Connected to %s." % db_path)
  return con

def drop_proto():
  sql = """DROP TABLE proto"""
  return sql

def cp(number):
  number = int(number)
  cmd = "split -r=SAME -p1=%i -p2=%i -s1=A -s2=B" %(number, number+1)
  olex.m(cmd)
OV.registerFunction(cp,False,'proto')


def cleanup_proto_disorder(min_occu=0.03):
  cmd = "sel atoms where occu < %s" %min_occu
  olex.m(cmd)
  cmd = "sel"
  atoms = []
  _ = gui.tools.scrub(cmd)[1:]
  for item in _:
    if not item:
      continue
    else:
      if "Angle" in item:
        item = item.split("Angle")[0]
      if item:
        a = item.split()
        for atom in a:
          atoms.append(atom)

  t = " ".join(atoms)
  olex.m("kill %s" %t)
  
  atoms = [w.replace('B', 'C') for w in atoms]
  atoms = [w.replace('A', 'B') for w in atoms]
  atoms = [w.replace('C', 'A') for w in atoms]

  t = " ".join(atoms)

  olex.m("sel %s" %t)
  olex.m("PART 0 11")

def solve_with_proto(new_ins, sg=None):
  ins_fn = OV.FileFull()
  with open(ins_fn,'r') as wFile:
    ins = wFile.readlines()
  if sg:
    if sg == "C2/c":
      FVAR_line = "FVAR 0.05 0.5 0.5 0.5"
  CELL = ZERR = FVAR = None
  for line in ins:
    if line.startswith("CELL"):
      CELL = line
    elif line.startswith("ZERR"):
      ZERR = line
    elif line.startswith("FVAR"):
      if FVAR_line:
        FVAR = FVAR_line
      else:
        FVAR = line
    if CELL and ZERR:
      break
  new_ins_l = new_ins.split("\n")
  t = ""
  for line in new_ins_l:
    if line.startswith("CELL"):
      line = CELL + "\n"
    elif line.startswith("ZERR"):
      line = ZERR + "\n"
    t += line + "\n"
  with open(ins_fn,'w') as wFile:
    wFile.write(t)
  print("< Switching to %s >" %ins_fn)
  olx.Atreap(ins_fn)
  

def create_proto_db():
  sql = """
    CREATE TABLE proto (
      id integer PRIMARY KEY,
      name text NOT NULL,
      path text,
      formula text NOT NULL,
      space_group text NOT NULL,
      cell_a float NOT NULL,
      cell_b float NOT NULL,
      cell_c float NOT NULL,
      cell_alpha float NOT NULL,
      cell_beta float NOT NULL,
      cell_gamma float NOT NULL,
      cell_volume float NOT NULL,
      class text,
      ins text NOT NULL)"""
  return sql

def get_add_to_proto_sql():
  return sql

def find_in_proto(volume=None, tol=None, group=None, sg=None):
  if not volume:
    volume = olx.xf.au.GetCellVolume()
  formula = olx.xf.au.GetFormula()
  space_group = olx.xf.au.GetCellSymm()    
 
  if not tol:
    tol = OV.GetParam('proto.tolerance')
  if not group:
    group = OV.GetParam('proto.class')
    if not group:
      group = "auto"
    if group == "auto":
      if "I" in formula:
        group = "ZnI"
      elif "Br" in formula:
        group = "ZnBr"
      elif "Cl" in formula:
        group = "ZnCl"
      else:
        group = ""
    elif group == "any":
      group = ""

  if not sg:
    sg = OV.GetParam('proto.sg')
    if not sg:
      sg = "auto"
    if sg == "auto":
      sg = space_group
    elif sg == "any":
      sg = ""
  
  retVal = []
  con = db_connect()
  cur = con.cursor()
  tol_abs = int(float(volume) * int(tol)/100)
  if not group and not sg:
    sql = "SELECT id, name, ins, space_group, class, cell_volume FROM proto WHERE abs(cell_volume-%s) <= %s" %(volume, tol_abs)
  elif group and not sg:
    sql = "SELECT id, name, ins, space_group, class, cell_volume FROM proto WHERE abs(cell_volume-%s) <= %s AND class = '%s'" %(volume, tol_abs, group)
  elif group and sg:
    sql = "SELECT id, name, ins, space_group, class, cell_volume FROM proto WHERE abs(cell_volume-%s) <= %s AND class = '%s' AND space_group = '%s'" %(volume, tol_abs, group, sg)
  elif not group and sg:
    sql = "SELECT id, name, ins, space_group, class, cell_volume FROM proto WHERE abs(cell_volume-%s) <= %s AND space_group = '%s'" %(volume, tol_abs, sg)
    
  cur.execute(sql)
  res = cur.fetchall()
  print("= PROTO with Class: %s, SG: %s, V: %.1f (+/- %s%%) ================" %(group, sg, float(volume), tol))
  if res:
    for re in res:
      msg = "%s | %s | %.0f A^3: %s" %(re[3], re[4], re[5], re[1] )
      print(msg)
      retVal.append((re[2],msg,sg))
  else:
    print("Nothing found in proto!")
  print("= END PROTO ================\n")
  return retVal    

def add_to_proto(p_class):
  con = db_connect()
  cur = con.cursor()

  sql = "INSERT INTO proto (name, formula, space_group, cell_a, cell_b, cell_c, cell_alpha, cell_beta, cell_gamma, cell_volume,  class, ins) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"

  #try:
    #cur.execute(drop_proto())
  #except:
    #pass
  #try:
    #cur.execute(create_proto_db())
  #except:
    #pass
  _ = os.path.join(OV.FilePath(), OV.FileName() + ".ins")
  with open(_, 'r') as t:
    t = t.read()
  cell = olx.xf.au.GetCell()
  cell_l = cell.split(",")
  formula = olx.xf.au.GetFormula()
  space_group = olx.xf.au.GetCellSymm()
  cell_a = float(cell_l[0])
  cell_b = float(cell_l[1])
  cell_c = float(cell_l[2])
  cell_alpha = float(cell_l[3])
  cell_beta = float(cell_l[4])
  cell_gamma = float(cell_l[5])
  cell_volume = olx.xf.au.GetCellVolume()
  proto_class = p_class

  cur.execute(sql, (OV.FileName(),
                    formula,
                    space_group,
                    cell_a,
                    cell_b,
                    cell_c,
                    cell_alpha,
                    cell_beta, 
                    cell_gamma,
                    cell_volume,
                    proto_class,
                    t,
                    ))

  con.commit()    
  con.close()

_deal_with_phil("read")
OV.registerFunction(add_to_proto,False,'proto')
OV.registerFunction(find_in_proto,False,'proto')
OV.registerFunction(solve_with_proto,False,'proto')
OV.registerFunction(cleanup_proto_disorder,False,'proto')
