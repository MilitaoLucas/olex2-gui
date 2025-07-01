import os
import olex
import olx
import time
from olexFunctions import OlexFunctions
# Custom Imports
import subprocess
from pathlib import Path, PurePosixPath
import textwrap
from wsl_conda import WSLAdapter, CondaAdapter

OV = OlexFunctions()

class xharpy:
  def __init__(self, g_WSLAdapter:WSLAdapter=None, g_CondaAdapter:CondaAdapter=None):
    """Initialize the xharpy class with WSL and Conda adapters."""
    self.wsl_adapter = g_WSLAdapter if g_WSLAdapter else WSLAdapter()
    self.conda_adapter = g_CondaAdapter.copy() if g_CondaAdapter else CondaAdapter(self.wsl_adapter, conda_env_name="xharpy")
    OV.registerFunction(self.calculate_tsc_cli,True,"NoSpherA2")

  def calculate_tsc_cli(self, cif = None):
    # Generate a cif file
    if cif is None:
        olex.m("CreateCif()")
        base_path = Path(OV.FilePath()) / olx.FileName() 
        input_cif_path = base_path.with_suffix('.cif')
        if not input_cif_path.exists():
            print(f"Input CIF file {input_cif_path} does not exist.")
            return
    else:
        input_cif_path = Path(cif)
        base_path = os.path.join(os.path.dirname(cif), olx.FileName()) 
        if not input_cif_path.exists():
            print(f"Input CIF file {input_cif_path} does not exist.")
            return
    
    work_folder_wsl = PurePosixPath("/tmp/.xharpy_olex2") / olx.FileName()
    
    try:
      self.wsl_adapter.call_command(f"mkdir -p {work_folder_wsl.parent}")
    except subprocess.CalledProcessError:
      print(f"Failed to create directory {work_folder_wsl.parent}. It may already exist.")
    try:
      self.wsl_adapter.call_command(f"mkdir -p {work_folder_wsl}")
    except subprocess.CalledProcessError:
      print(f"Failed to create directory {work_folder_wsl}. It may already exist.")

    work_cif_path = work_folder_wsl / "fromolex.cif"
    output_work_tsc_path = work_folder_wsl / "xharpy.tsc"

    self.wsl_adapter.copy_from_possible_wsl(input_cif_path, work_cif_path)
    
    script_string = self.produce_gpaw_script()
    script_path = Path(base_path+'.py')
  
    script_path.write_text(script_string)
    print(f"Script written to {script_path}")
    
    print("Cleaning up old files in WSL...")
    try:
      self.wsl_adapter.call_command(f"rm -f {work_folder_wsl}/*.tsc")
      self.wsl_adapter.call_command(f"rm -f {work_folder_wsl}/*.gpw")
      self.wsl_adapter.call_command(f"rm -f {work_folder_wsl}/*.txt")
    except subprocess.CalledProcessError as e:
      print(f"Error cleaning up old files: {e}")
    # copy script to WSL
    script_path_work_folder = work_folder_wsl / "xharpy_script.py"
    self.wsl_adapter.copy_from_possible_wsl(script_path, script_path_work_folder)
    print("running GPAW calculation in WSL...")
    self.conda_adapter.call_command(f"python {script_path_work_folder}", in_folder=work_folder_wsl, tail_output=True, output_file=work_folder_wsl / "gpaw.txt")
    
    output_tsc_path = os.path.join(OV.FilePath(), olx.FileName() + ".tsc")
    #output_tsc_path_wsl_final = work_folder_wsl / "xharpy_final.tsc"    
    for try_n in range(10):
      try:
        self.wsl_adapter.copy_to_possible_wsl(output_work_tsc_path, output_tsc_path)
        break
      except subprocess.CalledProcessError as e:
        print(f"Attempt {try_n + 1}: Failed to copy output TSC file. Retrying...")
        time.sleep(1)
    else:
      print("Failed to copy output TSC file after multiple attempts.")
      return

    print(f"Output TSC file created at {output_tsc_path}")

  def produce_gpaw_script(self):
    """Generates a template for GPAW calculations."""
    functional = OV.GetParam("snum.NoSpherA2.method")
    grid_spacing = OV.GetParam("snum.NoSpherA2.xharpy.grid_spacing")
    kpoint1 = OV.GetParam("snum.NoSpherA2.xharpy.k_points1")
    kpoint2 = OV.GetParam("snum.NoSpherA2.xharpy.k_points2")
    kpoint3 = OV.GetParam("snum.NoSpherA2.xharpy.k_points3")
    gamma = str(OV.GetParam("snum.NoSpherA2.xharpy.k_points_centre_gamma"))
    reload = str(OV.GetParam("snum.NoSpherA2.xharpy.reload"))
    template = textwrap.dedent(f"""
      from xharpy import cif2tsc
      from pathlib import Path                     

      export_dict = {{
          'f0j_source': 'gpaw_mpi',
          'core': 'constant',
          'resolution_limit': 'cif'
      }}

      computation_dict = {{
          'symm_equiv': 'once',
          'gridinterpolation': 4, 
          'xc': '{functional}',
          'txt': 'gpaw.txt',
          'mode': 'fd',
          'h': {grid_spacing},
          'convergence':{{'density': 1e-5}},
          'kpts': {{'size': ({kpoint1}, {kpoint2}, {kpoint3}), 'gamma': {gamma}}},
          'symmetry': {{'symmorphic': False}},
          'nbands': -2,
          'save_file': 'gpaw_result.gpw'
      }}

      cif2tsc(
          tsc_path='xharpy.tsc',
          cif_path='fromolex.cif',
          cif_dataset=0,
          export_dict=export_dict,
          computation_dict=computation_dict,

      )
      """)
          #reload={reload},
    return template