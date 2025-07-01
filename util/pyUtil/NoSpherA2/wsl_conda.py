import subprocess
import os
import sys
from pathlib import Path
from olexFunctions import OlexFunctions
import time
OV = OlexFunctions()

# TOOO: Test if linux system
class WSLAdapter(object):
  """Adapter for handling WSL (Windows Subsystem for Linux) operations."""
  def __init__(self, is_wsl=None, disto_list=None):
    self.is_windows = (sys.platform[:3] == "win")
    self.disto_list = []
    try:
      self.is_wsl = is_wsl if is_wsl is not None else self.check_wsl()
    except RuntimeError as e:
      print(f"Error checking WSL status: {e}")
      self.is_wsl = False
      return
    self.creationflags = subprocess.CREATE_NO_WINDOW if sys.platform[:3] == "win" else 0
    if disto_list is not None:
      self.disto_list = disto_list
    else:
      if self.is_wsl:
        self.disto_list = self.get_wsl_distro_list()
      else:
        self.disto_list = ["native"]

  def check_wsl(self):
    """Check if the script is running on a Windows system with WSL available."""
    if not self.is_windows:
      return False
    # Check if WSL is installed
    try:
      subprocess.run(["wsl", "--version"], capture_output=True, text=True, check=True)
      return True
    except (subprocess.CalledProcessError, FileNotFoundError):
      raise RuntimeError("WSL is not installed or not configured properly. Please install WSL to use this feature.")
  
  def clean_distro_name(self, distro_name):
    """Clean up distro name by removing null bytes and extracting just the name."""
    # Remove null bytes
    cleaned = ''.join(c for c in distro_name if c != '\x00')
    
    # Extract just the distro name without state info
    if '(' in cleaned:
        cleaned = cleaned.split('(')[0].strip()
        
    return cleaned
  
  def get_wsl_distro_list(self):
    """Get a list of installed WSL distributions."""
    if len(self.disto_list) > 0:
      return self.disto_list
    try:
      result = subprocess.run(["wsl", "--list", "--verbose"], capture_output=True, text=True, check=True)
      if "no installed distributions" in result.stdout:
        print("No WSL distributions are installed.")
        return []
      lines = result.stdout.strip().splitlines()
      if len(lines) > 0:
          lines = lines[1:]  # Skip header line
      
      # Parse each line to extract distribution names and states
      distros = []
      for line in lines:
          line = line.replace('\x00', '')  # Remove null bytes
          # Remove extra whitespace and split by multiple spaces
          parts = [part for part in line.strip().split() if part]
          if len(parts) >= 2:
              offset = 0
              if parts[0] == "*":
                offset = 1  # Skip the '*' character indicating the default distro
              # Format: NAME STATE VERSION
              distro_name = parts[offset]
              distro_state = parts[1 + offset]
              #skip Docker Desktop distros
              if distro_name == "docker-desktop":
                continue
              if distro_name == "docker-desktop-data":
                continue
              distro_info = f"{distro_name} ({distro_state})"
              distros.append(self.clean_distro_name(distro_info))

      return distros
    except subprocess.CalledProcessError as e:
      print(f"Error retrieving WSL distributions: {e}")
      return []
    
  def convert_windows_path_to_wsl(self, windows_path):
    """Convert Windows path to WSL path format."""
    path_str = str(windows_path)
    # Handle drive letters (C:\ -> /mnt/c/)
    if len(path_str) >= 3 and path_str[1] == ':' and path_str[2] == '\\':
      drive_letter = path_str[0].lower()
      remaining_path = path_str[3:].replace('\\', '/')
      return f"/mnt/{drive_letter}/{remaining_path}"
    else:
      # Just convert backslashes to forward slashes
      return path_str.replace('\\', '/')
    
  def call_command(self, command, tail_output = False, output_file=Path(".xharpy_olex2") / "sucrose" / "gpaw.txt"):
    """Calls a command in WSL and returns the output."""
    if not self.is_wsl:
      result = subprocess.run(" ".join(command), shell=True, capture_output=True, text=True)
      if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
      return result.stdout.strip()
    try:
      wsl_cmd = ["wsl"]
      selected_distro = OV.GetParam("snum.NoSpherA2.distro", None)
      if selected_distro not in self.disto_list:
        print("Selected WSL distribution is not available. Using default: Ubuntu.")
        selected_distro = None
      if selected_distro is not None and selected_distro != "None":
        wsl_cmd.extend(["-d", selected_distro])
      if not tail_output:
        return subprocess.run(
          " ".join(wsl_cmd + [command]),
          shell=True,
          capture_output=True,
          text=True,
          check=True,
          creationflags=self.creationflags
        )
      else:
        result = subprocess.Popen(
          " ".join(wsl_cmd + [command]),
          shell=True,
        )
        wsl_path = os.path.join("\\\\wsl.localhost",
                                selected_distro if selected_distro else "Ubuntu",
                                str(output_file).lstrip('/'))
        time.sleep(1.0) #give the calculation a moment to start
        tries = 0
        # Wait for the output file to be created
        while not os.path.exists(wsl_path):
          time.sleep(0.5)
          tries += 1
          if tries >= 60: #lets give it 30 seconds to start
            print("Failed to locate the output file at "+str(wsl_path))
            OV.SetVar('NoSpherA2-Error',"Wfn-Output not found!")
            raise NameError('Wfn-Output not found!')
        with open(wsl_path, "r") as f:
          while result.poll() is None:
            x = None
            try:
              x = f.read()
            except:
              pass
            if x:
              print(x, end='')
            time.sleep(0.15)
  
    except subprocess.CalledProcessError as e:
      print(f"Error executing WSL command: {command}")
      print(f"Error output: {e.stderr}")
      raise e
  
  def call_command_return(self, command):
    """Calls a command in WSL and returns the output."""
    if not self.is_wsl:
      result = subprocess.run(" ".join(command), shell=True, capture_output=True, text=True)
      if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
      return result.stdout.strip()
    try:
      wsl_cmd = ["wsl"]
      selected_distro = OV.GetParam("snum.NoSpherA2.distro", None)
      if selected_distro is not None and selected_distro != "None":
        wsl_cmd.extend(["-d", selected_distro])
      result = subprocess.run(
          " ".join(wsl_cmd + [command]),
          shell=True,
          capture_output=True,
          text=True,
          check=True,
          creationflags=self.creationflags
      )
        
      return result.stdout.strip()
  
    except subprocess.CalledProcessError as e:
      print(f"Error executing WSL command: {command}")
      print(f"Error output: {e.stderr}")
      raise e
    
  def copy_from_possible_wsl(self, source, destination):
    """Copies a file or directory, handling WSL paths if necessary."""
    if self.is_wsl:
      source_wsl = self.convert_windows_path_to_wsl(source)
      destination_wsl = self.convert_windows_path_to_wsl(destination)
      command = f"cp {source_wsl} {destination_wsl}"
    else:
      command = f"cp {source} {destination}"
    
    try:
      self.call_command(command)
    except subprocess.CalledProcessError as e:
      print(f"Error copying {source} to {destination}: {e}")
      raise e
    
  def copy_to_possible_wsl(self, source, destination):
    """Copies a file or directory to WSL, handling paths if necessary."""
    destination_path = self.convert_windows_path_to_wsl(destination) if self.is_wsl else destination
    command = f"cp {source} {destination_path}"
    
    try:
      self.call_command(command)
    except subprocess.CalledProcessError as e:
      print(f"Error copying {source} to {destination_path}: {e}")
      raise e
    
class CondaAdapter:
  def __init__(self, wsl_adapter, conda_env_name=None):
    """Initializes the CondaAdapter with a specific conda environment name."""
    self.wsl_adapter = wsl_adapter
    self.have_conda = False
    self.ran_check = False
    self.envs = []
    self.conda_env_name = None
    if conda_env_name is not None:
      self.set_conda_env_name(conda_env_name)
    if not self.check_conda_installed(True):
      if len(self.envs) == 0:
        print("No conda environments found. Please create a conda environment before using this feature.\nTry 'Get pyscf' or 'Get XHARPy' ")
      raise RuntimeError("Conda is not installed or not configured properly. Please install Conda to use this feature.")
    
  def copy(self, conda_env_name=None):
    """Creates a copy of the CondaAdapter object with the same attributes."""
    new_adapter = CondaAdapter(self.wsl_adapter, self.conda_env_name)
    new_adapter.envs = self.envs.copy() if self.envs else []
    new_adapter.have_conda = self.have_conda
    new_adapter.ran_check = self.ran_check
    if conda_env_name is not None:
      new_adapter.set_conda_env_name(conda_env_name)
    return new_adapter

  def check_conda_installed(self, force = False):
    """Checks if conda is installed in the WSL environment."""
    if not self.have_conda and not force:
      return False
    if len(self.envs) > 0:
      return True
    try:
      self.get_available_conda_envs()  # This will raise an error if conda is not installed
      return True
    except subprocess.CalledProcessError:
      raise RuntimeError("Conda is not installed or not configured properly. Please install Conda to use this feature.")
    
  def set_conda_env_name(self, conda_env_name):
    if conda_env_name is None:
      raise ValueError("Conda environment name cannot be None.")
    if not isinstance(conda_env_name, str):
      raise TypeError("Conda environment name must be a string.")
    if not conda_env_name.strip():
      raise ValueError("Conda environment name cannot be an empty string.")
    if conda_env_name not in self.get_available_conda_envs():
      raise ValueError(f"Conda environment '{conda_env_name}' does not exist.\nAvailable environments: {self.get_available_conda_envs()}")
    self.conda_env_name = conda_env_name

  def get_available_conda_envs(self) -> list:
    """Returns a list of available conda environments."""
    if len(self.envs) > 0:
      return self.envs
    try:
      if self.ran_check:
        print("No Conda environments found. Please create a conda environment before using this feature.\nTry 'Get pyscf' or 'Get XHARPy' ")
        return self.envs
      output = self.wsl_adapter.call_command_return("bash -i -c 'micromamba env list'")
      for line in output.splitlines():
        line = line.strip()
        if line.startswith("#") or not line.strip() or line.startswith("base") or line.startswith("Name"):
          continue
        parts = line.split()
        if len(parts) > 1:
          self.envs.append(parts[0])
      self.have_conda = True
      self.ran_check = True
      return self.envs
    except subprocess.CalledProcessError as e:
      print(f"Error retrieving conda environments: {e}")
      self.ran_check = True
      return []

  def call_command(self, command, in_folder=None, tail_output=False, output_file=None):
    """Runs a command in the specified conda environment."""
    conda_command = f"micromamba run -n {self.conda_env_name} {command}"
    if in_folder is not None:
      command = f"cd {in_folder} && {conda_command}"
    else:
      command = conda_command
    self.wsl_adapter.call_command(f'bash -i -c "{command}"', tail_output=tail_output, output_file=output_file)
    