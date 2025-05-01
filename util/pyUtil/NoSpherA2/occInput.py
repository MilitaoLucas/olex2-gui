from tomli_w import dump
import json 
with open("periodic_table.json", "r") as pt:
    PERIODIC_TABLE = json.load(pt)

def get_atoms_from_xyz(xyz: str) -> set:
    with open(xyz, "r") as f:
        xyz_list = f.readlines()
    return {atom for i in xyz_list if (atom := i.split()[0]) in PERIODIC_TABLE.keys()}
    
def treat_xyz(path: str) -> set:
    atom_set = set()
    with open(path, "r") as f:
        xyz = f.read().splitlines()
        
    fixed_lines = [xyz[0], xyz[1]]
    for i, line in enumerate(xyz):
        if i > 1:
            line = line.replace("D", "H").replace("T", "H")
            atom = line.split()
            fixed_lines.append(line)
            atom_set.add(atom[0])
            
    with open(path, "w") as f:
        f.write("\n".join(fixed_lines))
    return atom_set


def write_occ_input(
    self,
    xyz,
    basis_name=None,
    method=None,
    relativistic=None,
    charge=None,
    mult=None,
    strategy=None,
    convergence=None,
    part=None,
    efield=None,
):
    output_toml = dict()
    output_toml["verbosity"] = 2
    coordinates_fn = os.path.join(self.full_dir, f"{self.name}.xyz")
    software = OV.GetParam("snum.NoSpherA2.source")
    ECP = False
    if basis_name == None:
        basis_name = OV.GetParam("snum.NoSpherA2.basis_name")
    if "ECP" in basis_name:
        ECP = True
    if xyz:
        self.write_xyz_file()
    self.input_fn = os.path.join(self.full_dir, f"{self.name}.toml")
    inp = open(self.input_fn, "w")
    if method == None:
        method = OV.GetParam("snum.NoSpherA2.method")
    ncpus = OV.GetParam("snum.NoSpherA2.ncpus")
    output_toml["threads"] = int(ncpus)

    grid = OV.GetParam("snum.NoSpherA2.becke_accuracy")
    mp2_block = ""
    if method == "HF":
        if mult != 1 and OV.GetParam("snum.NoSpherA2.ORCA_FORCE_ROKS") == True:
            control += " ROHF "
        else:
            control += " rhf "
        grids = ""
    else:
        if mult != 1 and OV.GetParam("snum.NoSpherA2.ORCA_FORCE_ROKS") == True:
            control += " ROKS "
        if software == "Hybrid":
            software = OV.GetParam("snum.NoSpherA2.Hybrid.software_Part%d" % part)
        elif software == "fragHAR":
            software = "ORCA 5.0"
        if software == "ORCA 5.0" or software == "ORCA 6.0":
            SCNL = OV.GetParam("snum.NoSpherA2.ORCA_SCNL")
            if SCNL == True:
                if method != "wB97X":
                    control += method + " SCNL "
                else:
                    control += method + "-V SCNL "
            else:
                if method == "DSD-BLYP":
                    control += method + " D3BJ def2-TZVPP/C "
                    mp2_block += "%mp2 Density relaxed RI true end"
                else:
                    control += method + " "
            grids = self.write_grids_5(method, grid)
        else:
            control += method + " "
            grids = self.write_grids_4(method, grid)
    if convergence == None:
        convergence = OV.GetParam("snum.NoSpherA2.ORCA_SCF_Conv")
    if convergence == "NoSpherA2SCF":
        conv = "LooseSCF"
    else:
        conv = convergence
    if strategy == None:
        strategy = OV.GetParam("snum.NoSpherA2.ORCA_SCF_Strategy")
    control += grids + conv + " " + strategy
    Solvation = OV.GetParam("snum.NoSpherA2.ORCA_Solvation")
    if Solvation != "Vacuum" and Solvation != None:
        control += " CPCM(" + Solvation + ") "
    GBW_file = OV.GetParam("snum.NoSpherA2.ORCA_USE_GBW")
    if "5.0" not in OV.GetParam("snum.NoSpherA2.source") and "6.0" not in OV.GetParam(
        "snum.NoSpherA2.source"
    ):
        GBW_file = False
    if GBW_file == False:
        control += " AIM "
    if charge == None:
        charge = OV.GetParam("snum.NoSpherA2.charge")
    if mult == None:
        mult = OV.GetParam("snum.NoSpherA2.multiplicity")
    if mult == 0:
        mult = 1
    if "5.0" in software or "6.0" in software:
        inp.write(
            control
            + " NOTRAH\n%pal\n"
            + cpu
            + "\nend\n"
            + mem
            + "\n%coords\n        CTyp xyz\n        charge "
            + charge
            + "\n        mult "
            + mult
            + "\n        units angs\n        coords\n"
        )
    else:
        inp.write(
            control
            + "\n%pal\n"
            + cpu
            + "\nend\n"
            + mem
            + "\n%coords\n        CTyp xyz\n        charge "
            + charge
            + "\n        mult "
            + mult
            + "\n        units angs\n        coords\n"
        )
    atom_list = treat_xyz(coordinates_fn)
    if mp2_block != "":
        inp.write(mp2_block + "\n")
    if ECP == False:
        basis_set_fn = os.path.join(self.parent.basis_dir, basis_name)
        basis = open(basis_set_fn, "r")
        inp.write("%basis\n")
        for i in range(0, len(atom_list)):
            atom_type = "newgto " + atom_list[i] + "\n"
            inp.write(atom_type)
            temp_atom = atom_list[i] + ":" + basis_name
            basis.seek(0, 0)
            while True:
                line = basis.readline()
                if not line:
                    raise RecursionError("Atom not found in the basis set!")
                if line == "":
                    continue
                if line[0] == "!":
                    continue
                if "keys=" in line:
                    key_line = line.split(" ")
                    type = key_line[key_line.index("keys=") + 2]
                if temp_atom in line:
                    break
            line_run = basis.readline()
            if "{" in line_run:
                line_run = basis.readline()
            while not "}" in line_run:
                shell_line = line_run.split()
                if type == "turbomole=":
                    n_primitives = shell_line[0]
                    shell_type = shell_line[1]
                elif type == "gamess-us=":
                    n_primitives = shell_line[1]
                    shell_type = shell_line[0]
                shell_gaussian = (
                    "    " + shell_type.upper() + "   " + n_primitives + "\n"
                )
                inp.write(shell_gaussian)
                for n in range(0, int(n_primitives)):
                    if type == "turbomole=":
                        inp.write(
                            "  "
                            + str(n + 1)
                            + "   "
                            + basis.readline().replace("D", "E")
                        )
                    else:
                        inp.write(basis.readline().replace("D", "E"))
                line_run = basis.readline()
            inp.write("end\n")
        basis.close()
        inp.write("end\n")
    Full_HAR = OV.GetParam("snum.NoSpherA2.full_HAR")
    run = None
    damping = OV.GetParam("snum.NoSpherA2.ORCA_DAMP")
    scf_block = ""
    if damping:
        scf_block += "   CNVZerner true\n"
        if strategy == "SlowConv":
            scf_block += "   DampMax 0.9\n"
        elif strategy == "VerySlowConv":
            scf_block += "   DampMax 0.975\n"
        elif strategy == "NormalConv":
            scf_block += "   DampMax 0.8\n"
        elif strategy == "EasyConv":
            scf_block += "   DampMax 0.72\n"
    if not efield == None:
        amp = float(efield[1:])
        direction = efield[0]
        if direction == "x":
            scf_block += f"    EField {amp}, 0.0, 0.0"
        elif direction == "y":
            scf_block += f"    EField 0.0, {amp}, 0.0"
        elif direction == "z":
            scf_block += f"    EField 0.0, 0.0, {amp}"
        if direction != "0":
            scf_block += f'   Guess MORead\n   MOInp "zero.gbw"\n'
    if Full_HAR == True:
        run = OV.GetVar("Run_number")
        source = OV.GetParam("snum.NoSpherA2.source")
        if source == "Hybrid":
            run = 0
        if run > 1:
            if os.path.exists(os.path.join(self.full_dir, self.name + "2.gbw")):
                scf_block += f'   Guess MORead\n   MOInp "{self.name}2.gbw"'
                if convergence == "NoSpherA2SCF":
                    scf_block += "\n   TolE 3E-5\n   TolErr 1E-4\n   Thresh 1E-9\n   TolG 3E-4\n   TolX 3E-4"
            elif convergence == "NoSpherA2SCF":
                scf_block += "   TolE 3E-5\n   TolErr 1E-4\n   Thresh 1E-9\n   TolG 3E-4\n   TolX 3E-4"
        else:
            if convergence == "NoSpherA2SCF":
                scf_block += "   TolE 3E-5\n   TolErr 1E-4\n   Thresh 1E-9\n   TolG 3E-4\n   TolX 3E-4"
    else:
        if convergence == "NoSpherA2SCF":
            scf_block += "   TolE 3E-5\n   TolErr 1E-4\n   Thresh 1E-9\n   TolG 3E-4\n   TolX 3E-4"
    if scf_block != "":
        inp.write(f"%scf\n{scf_block}\nend\n")
    inp.close()
