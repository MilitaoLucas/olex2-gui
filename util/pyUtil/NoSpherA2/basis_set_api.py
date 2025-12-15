#!/usr/bin/env python3

import os
#import urllib.request
#import urllib.parse
from threading import Thread

from NoSpherA2.data.constants import PERIODIC_TABLE
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

        ELEMENTS = PERIODIC_TABLE

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

