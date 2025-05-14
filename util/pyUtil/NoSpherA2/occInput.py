from tomli_w import dump
from typing import Union
from dataclasses import dataclass
import numpy as np
import json
import os

# GLOBAL VARIABLES
with open("periodic_table.json", "r") as f:
    PERIODIC_TABLE = json.load(f)

ANGULAR_MOMENTUM_DICT = {
    's': 0,
    'p': 1,
    'd': 2,
    'f': 3,
    'g': 4,
    'h': 5,
}

#### END GLOBAL VARIABLES ####
@dataclass
class Shell:
    def __init__(self, angular_momentum: int, matrix: np.ndarray):
        self.exponents = np.ndarray
        self.coefficients = []
        self.function_type = "gto"
        self.region = "valence"
        self.angular_momentum = angular_momentum
        self.parse_matrix(matrix)

    def parse_matrix(self, matrix: np.ndarray):
        self.exponents = matrix[:, 0].tolist()
        self.coefficients = matrix[:, 1].tolist()

    def as_dict(self):
        retdict = {
            "function_type": self.function_type,
            "region": self.region,
            "angular_momentum": [self.angular_momentum],
            "exponents": self.exponents,
            "coefficients": [self.coefficients]
        }
        return retdict

    def __repr__(self):
        return f"{self.as_dict()}"

@dataclass()
class Basis:
    def __init__(self):
        self.elements = {}

    def add_shell(self, atom: int, shell: dict):
        atom = str(atom)
        if not atom in self.elements:
            self.elements[atom] = dict()
        if not "electron_shells" in self.elements[atom]:
            self.elements[atom]["electron_shells"] = []
        skey = list(shell.keys())[0]
        angular_momentum = ANGULAR_MOMENTUM_DICT[skey]
        self.elements[f"{atom}"]["electron_shells"].append(Shell(angular_momentum, shell[skey]).as_dict())

    def add_element(self, atom: Union[str, int], shells: list):
        if atom is str:
            atom = str(PERIODIC_TABLE[atom])
        atom = str(atom)
        for i in shells:
            self.add_shell(atom, i)

    def as_dict(self):
        return {
            "molssi_bse_schema": {
                "schema_type": "complete",
                "schema_version": "0.1"
            },
            "elements": {
                atom: self.elements[atom] for atom in self.elements
            }
        }

with open("periodic_table.json", "r") as pt:
    PERIODIC_TABLE = json.load(pt)

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
    if xyz:
        self.write_xyz_file()
    coordinates_fn = os.path.join(self.full_dir, f"{self.name}.xyz")
    atoms = treat_xyz(coordinates_fn)
    output_toml["scf"]["input"] = coordinates_fn
    ECP = False
    if basis_name is None:
        basis_name = OV.GetParam("snum.NoSpherA2.basis_name")
    output_toml["scf"]["basis"] = basis_name
    self.input_fn = os.path.join(self.full_dir, f"{self.name}.toml")
    if method is None:
        method = OV.GetParam("snum.NoSpherA2.method")
    output_toml["scf"]["method"] = method
    ncpus = OV.GetParam("snum.NoSpherA2.ncpus")
    output_toml["threads"] = int(ncpus)
    solvation = OV.GetParam('snum.NoSpherA2.occ_solvation')
    if solvation != "vacuum" and not solvation is None:
        output_toml["scf"]["solvent"] = solvation.lower()
    if charge is None:
        charge = OV.GetParam('snum.NoSpherA2.charge')
    output_toml["scf"]["charge"] = int(charge)
    if mult is None:
        mult = OV.GetParam('snum.NoSpherA2.multiplicity')
    output_toml["scf"]["multiplicity"] = int(mult)

