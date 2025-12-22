#!/usr/bin/env python3

import os
#import urllib.request
#import urllib.parse
from threading import Thread
from threads import ThreadEx
from threads import ThreadRegistry
from olexFunctions import OV

class GetBSEThread(ThreadEx):
    instance = None
    def __init__(self, name="BSEGetter"):
        ThreadRegistry().register(GetBSEThread)
        Thread.__init__(self)
        self.name = name
        GetBSEThread.instance = self
        
    def make_call(self, url):
        import HttpTools
        try:
          print(url)
          res = HttpTools.make_url_call(url, http_timeout=5)
        except Exception as err:
          print(err)
          return None
        return res
    
    def get_BSE_Z_basis_source(self, Z, basis_name, source="gamess_us"):
        main_bse_url = "https://www.basissetexchange.org"
        base_url = os.environ.get('BSE_API_URL', main_bse_url)
        
        headers = {
            'User-Agent': 'Olex2_basis_Set modification',
            'From': 'flo@olexsys.org'
        }

        ELEMENTS = {
            1: "H", 2: "He", 3: "Li", 4: "Be", 5: "B", 6: "C", 7: "N", 8: "O", 9: "F", 10: "Ne",
            11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P", 16: "S", 17: "Cl", 18: "Ar",
            19: "K", 20: "Ca", 21: "Sc", 22: "Ti", 23: "V", 24: "Cr", 25: "Mn", 26: "Fe",
            27: "Co", 28: "Ni", 29: "Cu", 30: "Zn", 31: "Ga", 32: "Ge", 33: "As", 34: "Se",
            35: "Br", 36: "Kr", 37: "Rb", 38: "Sr", 39: "Y", 40: "Zr", 41: "Nb", 42: "Mo",
            43: "Tc", 44: "Ru", 45: "Rh", 46: "Pd", 47: "Ag", 48: "Cd", 49: "In", 50: "Sn",
            51: "Sb", 52: "Te", 53: "I", 54: "Xe", 55: "Cs", 56: "Ba", 57: "La", 58: "Ce",
            59: "Pr", 60: "Nd", 61: "Pm", 62: "Sm", 63: "Eu", 64: "Gd", 65: "Tb", 66: "Dy",
            67: "Ho", 68: "Er", 69: "Tm", 70: "Yb", 71: "Lu", 72: "Hf", 73: "Ta", 74: "W",
            75: "Re", 76: "Os", 77: "Ir", 78: "Pt", 79: "Au", 80: "Hg", 81: "Tl", 82: "Pb",
            83: "Bi", 84: "Po", 85: "At", 86: "Rn", 87: "Fr", 88: "Ra", 89: "Ac", 90: "Th",
            91: "Pa", 92: "U", 93: "Np", 94: "Pu", 95: "Am", 96: "Cm", 97: "Bk", 98: "Cf",
            99: "Es", 100: "Fm", 101: "Md", 102: "No", 103: "Lr", 104: "Rf", 105: "Db",
            106: "Sg", 107: "Bh", 108: "Hs", 109: "Mt", 110: "Ds", 111: "Rg", 112: "Cn",
            113: "Nh", 114: "Fl", 115: "Mc", 116: "Lv", 117: "Ts", 118: "Og"
        }

        ELEMENTS_BY_SYMBOL = {symbol: z for z, symbol in ELEMENTS.items()} #neat GPT trick to inverse the key and value in ELEMENTS

        url = f"{base_url}/api/basis/{basis_name}/format/{source}/?version=0&elements={Z}"
        #req = urllib.request.Request(url, headers=headers)
        
        newgto_line_orca = f"newgto {ELEMENTS[Z]}\n"
        data = self.make_call(url)
        #print(data)
        data = data.read().decode('utf-8')
        #try:
        #    with urllib.request.urlopen(req) as response:
        #        if response.status != 200:
        #            raise RuntimeError("Could not obtain data from the BSE.")
        #        data = response.read().decode('utf-8')
        #except Exception as e:
        #    raise RuntimeError(f"Error fetching data: {e}")
        with open("result.dat", "w") as out:
            out.write(data)
        with open("result.dat", "r") as gto:
            switch = False
            for line in gto:
                if switch and line.startswith("\n"):
                    switch = False
                    newgto_line_orca += "end"
                if line.startswith("S"):
                    switch = True
                if switch:
                    newgto_line_orca += line
        return newgto_line_orca 

