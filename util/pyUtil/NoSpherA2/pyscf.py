import os
import olex
import olx
import time
from olexFunctions import OlexFunctions
# Custom Imports
import subprocess
from pathlib import PurePosixPath
from wsl_conda import WSLAdapter, CondaAdapter

OV = OlexFunctions()

class pyscf:
  def __init__(self, g_WSLAdapter:WSLAdapter=None, g_CondaAdapter:CondaAdapter=None):
    """Initialize the xharpy class with WSL and Conda adapters."""
    self.wsl_adapter = g_WSLAdapter if g_WSLAdapter else WSLAdapter()
    self.conda_adapter = g_CondaAdapter.copy() if g_CondaAdapter else CondaAdapter(self.wsl_adapter, conda_env_name="pyscf")

  def run(self, input = None):
    
    if input is None:
      raise ValueError("Input cannot be None. Please provide a valid input file or path.")
    work_folder_wsl = PurePosixPath("/tmp/.pyscf_olex2") / olx.FileName()
    
    try:
      self.wsl_adapter.call_command(f"mkdir -p {work_folder_wsl.parent}")
    except subprocess.CalledProcessError:
      print(f"Failed to create directory {work_folder_wsl.parent}. It may already exist.")
    try:
      self.wsl_adapter.call_command(f"mkdir -p {work_folder_wsl}")
    except subprocess.CalledProcessError:
      print(f"Failed to create directory {work_folder_wsl}. It may already exist.")
    
    self.wsl_adapter.copy_from_possible_wsl(input, work_folder_wsl / "pyscf_script.py")
    
    print("Cleaning up old files in WSL...")
    try:
      self.wsl_adapter.call_command(f"rm -f {work_folder_wsl}/*_pyscf.log")
    except subprocess.CalledProcessError as e:
      print(f"Error cleaning up old files: {e}")
    # copy script to WSL
    script_path_work_folder = work_folder_wsl / "pyscf_script.py"
    print("running pySCF calculation in WSL...")
    self.conda_adapter.call_command(f"python {script_path_work_folder}", in_folder=work_folder_wsl, tail_output=True, output_file=work_folder_wsl / f"{olx.FileName()}_pyscf.log")

    output_wfn_path = os.path.join(OV.FilePath(), olx.FileName() + ".wfn")
    for try_n in range(10):
      try:
        self.wsl_adapter.copy_to_possible_wsl(work_folder_wsl / f"{olx.FileName()}.wfn", output_wfn_path)
        self.wsl_adapter.copy_to_possible_wsl(work_folder_wsl / f"{olx.FileName()}_pyscf.log", os.path.join(OV.FilePath(), olx.FileName() + ".wfnlog"))
        break
      except subprocess.CalledProcessError as e:
        print(f"Attempt {try_n + 1}: Failed to copy output WFN file. Retrying...")
        time.sleep(1)
    else:
      print("Failed to copy output WFN file after multiple attempts.")
      return

    print(f"Output WFN file created at {output_wfn_path}")
