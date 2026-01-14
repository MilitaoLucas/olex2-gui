import os
import olex
import olexex
import olx
import gui
import numpy as np
from iotbx.cif import reader
from cctbx import uctbx, adptbx
from cctbx_olex_adapter import OlexCctbxAdapter
from scitbx import matrix

from olexFunctions import OV
debug = OV.IsDebugging()
u_list = ['11', '22', '33', '12', '13', '23']
c_list = ['111', '112', '113', '122', '123', '133', '222', '223', '233', '333']
d_list = ['1111', '1112', '1113', '1122', '1123', '1133', '1222', '1223', '1233', '1333', '2222', '2223', '2233', '2333', '3333']

if OV.HasGUI():
  get_template = gui.tools.TemplateProvider.get_template

try:
  p_path = os.path.dirname(os.path.abspath(__file__))
except Exception as e:
  if debug:
    print(f"Error getting __file__: {e}")
  p_path = os.path.dirname(os.path.abspath("__file__"))


def list_to_matrix(U):
    """Convert 6-element ADP list to 3x3 symmetric matrix."""
    U11, U22, U33, U12, U13, U23 = U
    return np.array([
        [U11, U12, U13],
        [U12, U22, U23],
        [U13, U23, U33]
    ])

def similarity_index(U1_list, U2_list, uc=None):
    if uc is not None:
      # Transform U1 and U2 to CIF coordinates
      U1_list = adptbx.u_cart_as_u_cif(uc, U1_list)
      U2_list = adptbx.u_cart_as_u_cif(uc, U2_list)
    U1 = list_to_matrix(U1_list)
    U2 = list_to_matrix(U2_list)
    
    # Check if matrices are positive definite
    try:
        # Attempt Cholesky decomposition (only works for positive definite matrices)
        np.linalg.cholesky(U1)
        np.linalg.cholesky(U2)
    except np.linalg.LinAlgError:
        # Return a sentinel value or handle specially
        eigvals1 = np.linalg.eigvals(U1)
        eigvals2 = np.linalg.eigvals(U2)
        print("Non-positive definite ADP tensor detected. Eigenvalues: ", eigvals1, eigvals2)
        return float('nan')  # or some other indicator

    # Rest of the function proceeds safely
    try:
      U1_inv = np.linalg.inv(U1)
      U2_inv = np.linalg.inv(U2)
      
      det_U1_inv = np.linalg.det(U1_inv)
      det_U2_inv = np.linalg.det(U2_inv)
      
      if det_U1_inv <= 0 or det_U2_inv <= 0:
        print("Negative determinant in ADP calculation")
        return float('nan')
          
      sum_inv = U1_inv + U2_inv
      det_sum_inv = np.linalg.det(sum_inv)
      
      if det_sum_inv <= 0:
        print("Negative determinant in sum of inverse ADPs")
        return float('nan')
          
      R12 = (2**1.5) * (det_U1_inv * det_U2_inv)**0.25 / det_sum_inv**0.5
      S12 = 100 * (1 - R12)
      return S12
    except Exception as e:
      if debug:
        print(f"Exception in similarity index calculation: {e}")
      print("Error in similarity index calculation")
      return float('nan')

class Peanut():
  def __init__(self):
    self.p_path = p_path
    self.old_adps = []
    self.showing_diff = False
    self.old_arad = -1
    self.old_brad = -1

    print("Init successfull")
    
  def make_diff_cif(self, cif1, cif2, out=None):
    """
    Make a difference CIF file between two CIF files.
    """
    from iotbx.cif import reader
    from cctbx import uctbx, adptbx
    
    # Read the CIF files
    cif1_data = reader(file_path=cif1).model()
    cif2_data = reader(file_path=cif2).model()
    
    # Get the first block from each CIF file
    block1 = list(cif1_data.keys())[0]
    block2 = list(cif2_data.keys())[0]
    
    # Extract unit cell parameters for both structures
    cell_params1 = [
        float(cif1_data[block1].get('_cell_length_a')[0]),
        float(cif1_data[block1].get('_cell_length_b')[0]),
        float(cif1_data[block1].get('_cell_length_c')[0]),
        float(cif1_data[block1].get('_cell_angle_alpha')[0]),
        float(cif1_data[block1].get('_cell_angle_beta')[0]),
        float(cif1_data[block1].get('_cell_angle_gamma')[0])
    ]
    unit_cell1 = uctbx.unit_cell(cell_params1)
    
    cell_params2 = [
        float(cif2_data[block2].get('_cell_length_a')[0]),
        float(cif2_data[block2].get('_cell_length_b')[0]),
        float(cif2_data[block2].get('_cell_length_c')[0]),
        float(cif2_data[block2].get('_cell_angle_alpha')[0]),
        float(cif2_data[block2].get('_cell_angle_beta')[0]),
        float(cif2_data[block2].get('_cell_angle_gamma')[0])
    ]
    unit_cell2 = uctbx.unit_cell(cell_params2)
    
    # Extract atom sites
    atoms1 = cif1_data[block1].get('_atom_site_label')
    atoms2 = cif2_data[block2].get('_atom_site_label')
    
    # Check if we have anisotropic displacement parameters
    has_aniso1 = '_atom_site_aniso_label' in cif1_data[block1]
    has_aniso2 = '_atom_site_aniso_label' in cif2_data[block2]
    
    results = {}
    
    if has_aniso1 and has_aniso2:
        # Extract anisotropic displacement parameters
        aniso_atoms1 = cif1_data[block1].get('_atom_site_aniso_label')
        aniso_atoms2 = cif2_data[block2].get('_atom_site_aniso_label')
        
        # Get Uij parameters
        u11_1 = cif1_data[block1].get('_atom_site_aniso_U_11')
        u22_1 = cif1_data[block1].get('_atom_site_aniso_U_22')
        u33_1 = cif1_data[block1].get('_atom_site_aniso_U_33')
        u12_1 = cif1_data[block1].get('_atom_site_aniso_U_12')
        u13_1 = cif1_data[block1].get('_atom_site_aniso_U_13')
        u23_1 = cif1_data[block1].get('_atom_site_aniso_U_23')
        
        u11_2 = cif2_data[block2].get('_atom_site_aniso_U_11')
        u22_2 = cif2_data[block2].get('_atom_site_aniso_U_22')
        u33_2 = cif2_data[block2].get('_atom_site_aniso_U_33')
        u12_2 = cif2_data[block2].get('_atom_site_aniso_U_12')
        u13_2 = cif2_data[block2].get('_atom_site_aniso_U_13')
        u23_2 = cif2_data[block2].get('_atom_site_aniso_U_23')
        
        # Calculate differences for atoms that exist in both files
        common_atoms = set(aniso_atoms1).intersection(set(aniso_atoms2))
        
        for atom in common_atoms:
            for i,a in enumerate(aniso_atoms1):
              if a == atom:
                idx1 = i
            for i,a in enumerate(aniso_atoms2):
              if a == atom:
                idx2 = i
            
            # Create Uij tensors for both structures
            u_cart1 = (
                float(u11_1[idx1]), float(u22_1[idx1]), float(u33_1[idx1]),
                float(u12_1[idx1]), float(u13_1[idx1]), float(u23_1[idx1])
            )
            
            u_cart2 = (
                float(u11_2[idx2]), float(u22_2[idx2]), float(u33_2[idx2]),
                float(u12_2[idx2]), float(u13_2[idx2]), float(u23_2[idx2])
            )
            
            # If the unit cells are different, transform the ADPs from structure 2 to structure 1's reference frame
            if unit_cell1.parameters() != unit_cell2.parameters():
                # Convert Ucart2 to Ustar2
                u_star2 = adptbx.u_cart_as_u_star(unit_cell2, u_cart2)
                
                # If needed, apply any symmetry operations or transformations between cells here
                # For example, if there's a known transformation matrix between the two structures
                
                # Convert Ustar2 to Ucart1 reference frame
                u_cart2_transformed = adptbx.u_star_as_u_cart(unit_cell1, u_star2)
            else:
                u_cart2_transformed = u_cart2
            
            # Calculate differences
            diff_u = [u_cart1[i] - u_cart2_transformed[i] for i in range(6)]
            
            results[atom] = {
                'dU11': diff_u[0],
                'dU22': diff_u[1],
                'dU33': diff_u[2],
                'dU12': diff_u[3],
                'dU13': diff_u[4],
                'dU23': diff_u[5]
            }
    else:
        # Handle isotropic case (Uiso or Biso)
        for i, atom in enumerate(atoms1):
            if atom in atoms2:
                idx2 = atoms2.index(atom)
                
                # Try to get Uiso values
                uiso1 = cif1_data[block1].get('_atom_site_U_iso_or_equiv')
                uiso2 = cif2_data[block2].get('_atom_site_U_iso_or_equiv')
                
                if uiso1 and uiso2:
                    results[atom] = {'dUiso': float(uiso1[i]) - float(uiso2[idx2])}
                else:
                    # Try to get Biso values and convert to Uiso if needed
                    biso1 = cif1_data[block1].get('_atom_site_B_iso_or_equiv')
                    biso2 = cif2_data[block2].get('_atom_site_B_iso_or_equiv')
                    
                    if biso1 and biso2:
                        # B = 8π²U, so U = B/(8π²)
                        results[atom] = {'dBiso': float(biso1[i]) - float(biso2[idx2])}
    
    
    
    # Write results to file if requested
    if out is not None:
        # Instead of trying to modify the existing CIF, create a new one
        from iotbx.cif import model
        result_cif = model.cif()
        result_block = model.block()
        result_cif[block1] = result_block
        
        # Copy cell parameters from the first structure
        for cell_param in ['_cell_length_a', '_cell_length_b', '_cell_length_c', 
                          '_cell_angle_alpha', '_cell_angle_beta', '_cell_angle_gamma']:
            if cell_param in cif1_data[block1]:
                result_block[cell_param] = cif1_data[block1][cell_param]
        
        # Create a single loop for all atoms and their parameters
        loop = model.loop()
        
        if has_aniso1 and has_aniso2:
            # For anisotropic ADPs
            # Define all columns for the loop
            loop_columns = {
                '_atom_site_label': [],
                '_atom_site_aniso_U_11': [],
                '_atom_site_aniso_U_22': [],
                '_atom_site_aniso_U_33': [],
                '_atom_site_aniso_U_12': [],
                '_atom_site_aniso_U_13': [],
                '_atom_site_aniso_U_23': []
            }
            
            # Fill the dictionary with data
            for atom, diff in results.items():
                loop_columns['_atom_site_label'].append(atom)
                loop_columns['_atom_site_aniso_U_11'].append(str(diff['dU11']))
                loop_columns['_atom_site_aniso_U_22'].append(str(diff['dU22']))
                loop_columns['_atom_site_aniso_U_33'].append(str(diff['dU33']))
                loop_columns['_atom_site_aniso_U_12'].append(str(diff['dU12']))
                loop_columns['_atom_site_aniso_U_13'].append(str(diff['dU13']))
                loop_columns['_atom_site_aniso_U_23'].append(str(diff['dU23']))
                
            loop.add_columns(loop_columns)
        else:
            # For isotropic case
            if any('dUiso' in diff for diff in results.values()):
                # Define columns as a dictionary
                loop_columns = {
                    '_atom_site_label': [],
                    '_atom_site_U_iso_or_equiv_diff': []
                }

                # Fill the dictionary with data
                for atom, diff in results.items():
                    if 'dUiso' in diff:
                        loop_columns['_atom_site_label'].append(atom)
                        loop_columns['_atom_site_U_iso_or_equiv_diff'].append(str(diff['dUiso']))

                # Add columns to loop
                loop.add_columns(loop_columns)
            elif any('dBiso' in diff for diff in results.values()):
                # Define columns as a dictionary
                loop_columns = {
                    '_atom_site_label': [],
                    '_atom_site_B_iso_or_equiv_diff': []
                }

                # Fill the dictionary with data
                for atom, diff in results.items():
                    if 'dBiso' in diff:
                        loop_columns['_atom_site_label'].append(atom)
                        loop_columns['_atom_site_B_iso_or_equiv_diff'].append(str(diff['dBiso']))

                # Add columns to loop
                loop.add_columns(loop_columns)
        result_block.add_loop(loop)
        # Write the modified CIF to the output file
        with open(out, 'w') as f:
            f.write(str(result_cif))
    
    return results

  def show_MSDS(self):
    self.old_arad = OV.GetParam("user.atoms.azoom",1)
    self.old_brad = OV.GetParam("user.bonds.bzoom",1)
    olex.m("AZoom 0")
    olex.m("BRad 0.1")
    s = OV.GetVar('Peanut_scale',"1.0")
    a = OV.GetVar('Peanut_anh','all')
    t = OV.GetVar('Peanut_type',"rmsd")
    q = OV.GetVar('Peanut_quality', "5")
    olex.m(f"MSDSView -s={s} -a={a} -t={t} -q={q}")

  def remove_MSDS(self):
    if self.showing_diff:
      self.hide_diff()
    else:
      try:
        olex.m("kill MSDS")
        olex.m(f"AZoom {self.old_arad}")
        olex.m(f"BRad {self.old_brad/100}")
      except Exception as e:
        if debug:
          print(e)
        print("MSDS is not running, nothing to hide")
  
  def show_diff(self, cif1 = None):
    """
    Show the difference between the current model and the cif given.
    
    cif1: path to cif file to subtract (optional, if not given, a file dialog will open)
    """
    # If there is no cif given, select a file using file dialog
    if cif1 is None:
      fn = olx.FileName()
      folder = os.path.dirname(os.path.abspath(fn))
      cif1 = olx.FileOpen("Select cif to subtract", "*.cif", folder, "")
    if cif1 == '':
      print("No CIF file selected, cannot show difference.")
      return
    # Read the CIF files
    cif1_data = reader(file_path=cif1).model()
    
    # Get the first block from each CIF file
    block1 = list(cif1_data.keys())[0]
    
    cell_params1 = [
      float(cif1_data[block1].get('_cell_length_a').split('(')[0]),
      float(cif1_data[block1].get('_cell_length_b').split('(')[0]),
      float(cif1_data[block1].get('_cell_length_c').split('(')[0]),
      float(cif1_data[block1].get('_cell_angle_alpha').split('(')[0]),
      float(cif1_data[block1].get('_cell_angle_beta').split('(')[0]),
      float(cif1_data[block1].get('_cell_angle_gamma').split('(')[0])
    ]
    unit_cell1 = uctbx.unit_cell(cell_params1)
    
    iso_atoms = cif1_data[block1].get('_atom_site_label')
    # Check if we have anisotropic displacement parameters
    ueq = cif1_data[block1].get('_atom_site_U_iso_or_equiv')
    
    aniso_atoms1 = cif1_data[block1].get('_atom_site_aniso_label')
    u_1 = []
    C_anharm_site = None
    D_anharm_site = None
    c_1 = []
    d_1 = []
    # Get Uij parameters
    for u_comp in u_list:
      u_1.append(cif1_data[block1].get(f'_atom_site_aniso_U_{u_comp}'))
    
    try:
      #anharmonic contributions
      C_anharm_site = cif1_data[block1].get('_atom_site_anharm_GC_C_label')
      for c_comp in c_list:
        c_1.append(cif1_data[block1].get(f'_atom_site_anharm_GC_C_{c_comp}'))
    except:
      print("No anharmonic 3rd order in the cif")
        
    try:
      D_anharm_site = cif1_data[block1].get('_atom_site_anharm_GC_D_label')
      for d_comp in d_list:
        d_1.append(cif1_data[block1].get(f'_atom_site_anharm_GC_D_{d_comp}'))
    except:
      print("No anharmonic 4th order in the cif")
    
    ref_mod = olexex.OlexRefinementModel(False)
    olx_atoms = ref_mod.atoms()
    uc = uctbx.unit_cell(ref_mod.getCell())
    
    ## Feed Model
    def iter_scatterers():
      for a in olx_atoms:
        label = a['label']
        u:list[float] = []
        if 'uiso' in a:
          u = list(adptbx.u_iso_as_u_cart(a['uiso'][0]))
          self.old_adps.append([a['uiso'][0]])
          olx.Anis(f"{label}", h=True)
        elif 'adp' in a:
          u = list(a['adp'][0])
          self.old_adps.append(u.copy())
        # find the position in the ADP loop of the cif and subtract the ADPs
        idx1 = next((i for i, a_ in enumerate(aniso_atoms1) if a_ == label), -1)
        if idx1 != -1:
          # Create Uij tensor
          u_cart_1 = adptbx.u_cif_as_u_cart(unit_cell1, [float(str(u_[idx1]).split('(')[0]) for u_ in u_1])
          u_cart_1 = [u_cart_1[0], u_cart_1[1], u_cart_1[2], u_cart_1[5], u_cart_1[4], u_cart_1[3]]
          print(f"{label:<6} | {similarity_index(u_cart_1, u, uc):>14.2f}")
          for i,u_val in enumerate(u_cart_1):
            u[i] -= u_val
        else:
          idx1 = next((i for i, a_ in enumerate(iso_atoms) if a_ == label), -1)
          if idx1 != -1:
            u_eq = float(str(ueq[idx1]).split('(')[0])
            u_ = adptbx.u_iso_as_u_cart(u_eq)
            print(f"{label:<6} | {similarity_index(u_, u, uc):>14.2f}")
        if C_anharm_site is not None:
          idx1 = next((i for i, a_ in enumerate(C_anharm_site) if a_ == label), -1)
          if idx1 != -1:
            if len(u) < 16:
              u += [0.0] * (16 - len(u))
            for i in range(11):
              u[i+6] -= float(str(c_1[i][idx1]).split('(')[0])
        if D_anharm_site is not None:
          idx1 = next((i for i, a_ in enumerate(D_anharm_site) if a_ == label), -1)
          if idx1 != -1:
            if len(u) < 31:
              u += [0.0] * (31 - len(u))
            for i in range(16):
              u[i+16] -= float(str(d_1[i][idx1]).split('(')[0])
        yield (u)
    self.old_arad = OV.GetParam("user.atoms.azoom",1)
    self.old_brad = OV.GetParam("user.bonds.bzoom",1)
    olex.m("AZoom 0")
    olex.m("BRad 0.1")
    self.showing_diff = True
    print("Table of Similarity Indices S12 (harmonic part only):")
    print("\n{:<6}|{:^14}".format("Atom", "S12 /%"))
    print("-" * 23)  # Separator line
    for this_atom_id,u in enumerate(iter_scatterers()):
      olx.xf.au.SetAtomU(olx_atoms[this_atom_id]['aunit_id'], *u)
    print("-" * 23)  # Separator line

    olx.xf.EndUpdate()
    if OV.HasGUI():
      olx.Refresh()
    scale = OV.GetVar('Peanut_scale',"1.0")
    anh = OV.GetVar('Peanut_anh','all')
    typ = OV.GetVar('Peanut_type',"rmsd")
    qual = OV.GetVar('Peanut_quality', "5")
    olex.m(f"MSDSView -s={scale} -a={anh} -t={typ} -q={qual}")
    
  def hide_diff(self):
    olex.m("kill MSDS")
    if not self.showing_diff:
      print("Not showing a difference model")
      return
    ref_mod = olexex.OlexRefinementModel(False)
    olx_atoms = ref_mod.atoms()
    ## Feed Model
    self.showing_diff = False
    olex.m(f"AZoom {self.old_arad}")
    olex.m(f"BRad {self.old_brad/100}")
    for this_atom_id, a in enumerate(olx_atoms):
      if len(self.old_adps[this_atom_id]) == 1:
        olex.m(f"isot {a['label']}")
      olx.xf.au.SetAtomU(a['aunit_id'], *self.old_adps[this_atom_id])
    self.old_adps = []

    olx.xf.EndUpdate()
    if OV.HasGUI():
      olx.Refresh()
    

PI = Peanut()
OV.registerFunction(PI.make_diff_cif, False, "Peanut")
OV.registerFunction(PI.show_diff, False, "Peanut")
OV.registerFunction(PI.hide_diff, False, "Peanut")
OV.registerFunction(PI.show_MSDS, False, "Peanut")
OV.registerFunction(PI.remove_MSDS, False, "Peanut")