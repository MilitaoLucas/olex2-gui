from tomli_w import dump
def write_orca_input(self,xyz,basis_name=None,method=None,relativistic=None,charge=None,mult=None,strategy=None,convergence=None,part=None, efield=None):
    output_toml = dict()
    output_toml["verbosity"] = 2
    coordinates_fn = os.path.join(self.full_dir, f"{self.name}.xyz") 
    software = OV.GetParam("snum.NoSpherA2.source")
    ECP = False
    if basis_name == None:
        basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    if "ECP" in basis_name:
        ECP = True
    if xyz:
        self.write_xyz_file()
    xyz = open(coordinates_fn,"r")
    self.input_fn = os.path.join(self.full_dir, f"{self.name}.inp")
    inp = open(self.input_fn,"w")
    if method == None:
        method = OV.GetParam('snum.NoSpherA2.method')
    ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
    output_toml["threads"] = int(ncpus)
    control = "! NoPop MiniPrint "


    grid = OV.GetParam('snum.NoSpherA2.becke_accuracy')
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
            software = OV.GetParam("snum.NoSpherA2.Hybrid.software_Part%d"%part)
        elif software == "fragHAR":
            software = "ORCA 5.0"
        if software == "ORCA 5.0" or software == "ORCA 6.0":
            SCNL = OV.GetParam('snum.NoSpherA2.ORCA_SCNL')
            if SCNL == True:
                if method != "wB97X":
                    control += method + ' SCNL '
                else:
                    control += method + '-V SCNL '
            else:
                if method == "DSD-BLYP":
                    control += method + ' D3BJ def2-TZVPP/C '
                    mp2_block += "%mp2 Density relaxed RI true end"
                else:
                    control += method + ' '
            grids = self.write_grids_5(method, grid)
        else:
            control += method + ' '
            grids = self.write_grids_4(method, grid)
    if convergence == None:
        convergence = OV.GetParam('snum.NoSpherA2.ORCA_SCF_Conv')
    if convergence == "NoSpherA2SCF":
        conv = "LooseSCF"
    else:
        conv = convergence
    if strategy == None:
        strategy = OV.GetParam('snum.NoSpherA2.ORCA_SCF_Strategy')
    control += grids + conv + ' ' + strategy
    if relativistic == None:
        relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
    if method == "BP86" or method == "PBE" or method == "PWLDA":
        if relativistic == True:
            t = OV.GetParam('snum.NoSpherA2.ORCA_Relativistic')
            if t == "DKH2":
                control += " DKH2 SARC/J RI"
            elif t == "ZORA":
                control += " ZORA SARC/J RI"
            elif t == "ZORA/RI":
                control += " ZORA/RI SARC/J RI"
            elif t == "IORA":
                control += " IORA SARC/J RI"
            else:
                control += " IORA/RI SARC/J RI"
        else:
            control += " def2/J RI"
    else:
        if relativistic == True:
            t = OV.GetParam('snum.NoSpherA2.ORCA_Relativistic')
            if t == "DKH2":
                control += " DKH2 SARC/J RIJCOSX"
            elif t == "ZORA":
                control += " ZORA SARC/J RIJCOSX"
            elif t == "IORA":
                control += " IORA SARC/J RIJCOSX"
            elif t == "ZORA/RI":
                control += " ZORA/RI SARC/J RIJCOSX"
            elif t == "IORA/RI":
                control += " IORA/RI SARC/J RIJCOSX"
            else:
                print("============= Relativity kind not known! Will use ZORA! =================")
                control += " ZORA SARC/J RIJCOSX"
        else:
            control += " def2/J RIJCOSX"
    Solvation = OV.GetParam('snum.NoSpherA2.ORCA_Solvation')
    if Solvation != "Vacuum" and Solvation != None:
        control += " CPCM(" + Solvation + ") "
    GBW_file = OV.GetParam("snum.NoSpherA2.ORCA_USE_GBW")
    if "5.0" not in OV.GetParam("snum.NoSpherA2.source") and "6.0" not in OV.GetParam("snum.NoSpherA2.source"):
        GBW_file = False
    if GBW_file == False:
        control += " AIM "
    if charge == None:
        charge = OV.GetParam('snum.NoSpherA2.charge')
    if mult == None:
        mult = OV.GetParam('snum.NoSpherA2.multiplicity')
    if mult == 0:
        mult = 1
    if "5.0" in software or "6.0" in software:
        inp.write(control + ' NOTRAH\n%pal\n' + cpu + '\nend\n' + mem + '\n%coords\n        CTyp xyz\n        charge ' + charge + "\n        mult " + mult + "\n        units angs\n        coords\n")
    else:
        inp.write(control + '\n%pal\n' + cpu + '\nend\n' + mem + '\n%coords\n        CTyp xyz\n        charge ' + charge + "\n        mult " + mult + "\n        units angs\n        coords\n")
    atom_list = []
    i = 0
    for line in xyz:
        i = i+1
        if i > 2:
            atom = line.split()
            if atom[0] == "D":
                atom[0] = "H"
                line = line.replace("D", "H")
            if atom[0] == "T":
                atom[0] = "H"
                line = line.replace("T", "H")
            inp.write(line)
            if not atom[0] in atom_list:
                atom_list.append(atom[0])
    xyz.close()
    inp.write("   end\nend\n")
    if mp2_block != "":
        inp.write(mp2_block+'\n')
    if ECP == False:
        basis_set_fn = os.path.join(self.parent.basis_dir, basis_name)
        basis = open(basis_set_fn,"r")
        inp.write("%basis\n")
        for i in range(0, len(atom_list)):
            atom_type = "newgto " + atom_list[i] + '\n'
            inp.write(atom_type)
            temp_atom = atom_list[i] + ":" + basis_name
            basis.seek(0, 0)
            while True:
                line = basis.readline()
                if not line:
                    raise RecursionError("Atom not found in the basis set!")
                if line == '':
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
            while (not "}" in line_run):
                shell_line = line_run.split()
                if type == "turbomole=":
                    n_primitives = shell_line[0]
                    shell_type = shell_line[1]
                elif type == "gamess-us=":
                    n_primitives = shell_line[1]
                    shell_type = shell_line[0]
                shell_gaussian = "    " + shell_type.upper() + "   " + n_primitives + "\n"
                inp.write(shell_gaussian)
                for n in range(0, int(n_primitives)):
                    if type == "turbomole=":
                        inp.write("  " + str(n + 1) + "   " + basis.readline().replace("D", "E"))
                    else:
                        inp.write(basis.readline().replace("D", "E"))
                line_run = basis.readline()
            inp.write("end\n")
        basis.close()
        inp.write("end\n")
    Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
    run = None
    damping = OV.GetParam('snum.NoSpherA2.ORCA_DAMP')
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
            scf_block += f"   Guess MORead\n   MOInp \"zero.gbw\"\n"
    if Full_HAR == True:
        run = OV.GetVar('Run_number')
        source = OV.GetParam('snum.NoSpherA2.source')
        if source == "Hybrid":
            run = 0
        if run > 1:
            if os.path.exists(os.path.join(self.full_dir, self.name + "2.gbw")):
                scf_block += f"   Guess MORead\n   MOInp \"{self.name}2.gbw\""
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
