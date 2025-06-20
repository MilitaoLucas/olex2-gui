import math
import numpy as np
from olexFunctions import OV
import os
import olx
import olexex
from cctbx import sgtbx
from cctbx_olex_adapter import OlexCctbxAdapter
from NoSpherA2 import cubes_maps
from cctbx import maptbx
from cctbx import miller
from cctbx.array_family import flex

model_file = os.path.join(OV.BaseDir(), "PhAI_model.pth")
if not os.path.exists(model_file):
  #end the script
  raise FileNotFoundError("PhAI model file not found. Please download the model from the PhAI repository and place it in the base directory to use it.")

#check if we have torch and einops installed
try:
  import torch
  import torch.nn as nn
  from einops.layers.torch import Rearrange
except ImportError or ModuleNotFoundError:
  selection = olx.Alert("torch not found",
                          """Error: No working torch installation found!.
Do you want to install this now?""", "YN", False)
  if selection == 'Y':
    olexex.pip("torch")
    olexex.pip("einops")
    import torch
    import torch.nn as nn
    from einops.layers.torch import Rearrange
  else:
    print("Please install torch and einops inside the DataDir() manually, keeping in mind the version compatibility with installed numpy, scipy and pillow!")


class ConvolutionalBlock(nn.Module):
    def __init__(self, filters, kernel_size, padding):
        super().__init__()

        self.act = nn.GELU()

        self.conv1 = nn.Conv3d(filters, filters, kernel_size = kernel_size, padding = padding)
        self.conv2 = nn.Conv3d(filters, filters, kernel_size = kernel_size, padding = padding)

        self.norm1 = nn.GroupNorm(filters, filters)
        self.norm2 = nn.GroupNorm(filters, filters)

    def forward(self, x):
        identity = x

        x = self.conv1(x)
        x = self.act(x)
        x = self.norm1(x)

        x = self.conv2(x)
        x = self.act(x)
        x = self.norm2(x)

        x = x + identity
        return x

class MLPLayer(nn.Module):
    def __init__(self, token_nr, dim, dim_exp, mix_type):
        super().__init__()

        self.act    = nn.GELU()

        self.norm1  = nn.GroupNorm(token_nr, token_nr)

        if mix_type == 'token':
            self.layer1 = nn.Conv1d(kernel_size = 1, in_channels = token_nr, out_channels = dim_exp)
            self.layer2 = nn.Conv1d(kernel_size = 1, in_channels = dim_exp, out_channels = token_nr)
        else:
            self.layer1 =  nn.Linear(dim , dim_exp)
            self.layer2 =  nn.Linear(dim_exp, dim)

        self.mix_type = mix_type

    def forward(self, x):
        identity = x

        x = self.norm1(x)

        x = self.layer1(x)
        x = self.act(x)
        x = self.layer2(x)

        x = x + identity

        return x

class PhAINeuralNetwork(nn.Module):
    def __init__(self, *, max_index, filters, kernel_size, cnn_depth, dim, dim_exp, dim_token_exp, mlp_depth, reflections):
        super().__init__()

        hkl           = [max_index*2+1, max_index+1, max_index+1]
        mlp_token_nr  = filters
        padding       = int((kernel_size - 1) / 2)

        self.net_a = nn.Sequential(
            Rearrange('b x y z  -> b 1 x y z '),

            nn.Conv3d(1, filters, kernel_size = kernel_size, padding=padding),
            nn.GELU(),
            nn.GroupNorm(filters, filters)
        )

        self.net_p = nn.Sequential(
            Rearrange('b x y z  -> b 1 x y z '),

            nn.Conv3d(1, filters, kernel_size = kernel_size, padding=padding),
            nn.GELU(),
            nn.GroupNorm(filters, filters)
        )

        self.net_convolution_layers = nn.Sequential(
            *[nn.Sequential(
                ConvolutionalBlock(filters, kernel_size = kernel_size, padding = padding),
            ) for _ in range(cnn_depth)],
        )

        self.net_projection_layer = nn.Sequential(
            Rearrange('b c x y z  -> b c (x y z)'),
            nn.Linear(hkl[0]*hkl[1]*hkl[2], dim),
        )

        self.net_mixer_layers = nn.Sequential(
            *[nn.Sequential(
                MLPLayer(mlp_token_nr, dim, dim_token_exp, 'token'),
                MLPLayer(mlp_token_nr, dim, dim_exp      , 'channel'),
            ) for _ in range(mlp_depth)],
            nn.LayerNorm(dim),
        )

        self.net_output = nn.Sequential(
            Rearrange('b t x -> b x t'),
            nn.AdaptiveAvgPool1d(1),
            Rearrange('b x 1 -> b x'),

            nn.Linear(dim, reflections*2),
            Rearrange('b (c h) -> b c h ', h = reflections),
        )

    def forward(self, input_amplitudes, input_phases):

        a = self.net_a(input_amplitudes)
        p = self.net_p(input_phases)

        x = a + p

        x = self.net_convolution_layers(x)

        x = self.net_projection_layer(x)

        x = self.net_mixer_layers(x)

        phases = self.net_output(x)

        return phases

# model definition
model_args = {
     'max_index' : 10,
       'filters' : 96,
   'kernel_size' : 3,
     'cnn_depth' : 6,
           'dim' : 1024,
       'dim_exp' : 2048,
 'dim_token_exp' : 512,
     'mlp_depth' : 8,
   'reflections' : 1205,
}

model = PhAINeuralNetwork(**model_args)
state = torch.load(model_file, weights_only = True)
model.load_state_dict(state)

def randomize_output(output):
    shape = output[0].shape
    rand_mask = torch.randint(0, 2, shape)
    output[0][rand_mask == 1] = -180.
    output[0][rand_mask == 0] = 0.
    return output

def phases(output_phases):
    bin_size = 180.0
    offset   = bin_size / 2
    #bin_nr   = int(360 / bin_size)
    output_phases = output_phases.permute(0,2,1)
    output_phases = torch.argmax(output_phases, dim=2)
    return offset + (output_phases*bin_size) - 180.00 - (bin_size/2)

def reindex_monoclinic(H):
    #to: (-h, h), (0, k), (0, l)
    #bug: -2, -1, 0 -> -2, 1, 0 (incorrect) corrected?
    H_new = np.array([[0, 0, 0]], dtype=int)
    symm_eq = [(-1,1,-1), (1,-1,1), (-1,-1,-1)]
    for h in H:
        if h[1] < 0 or h[2] < 0:
            for eq in symm_eq:
                h_new = (h[0]*eq[0], h[1]*eq[1], h[2]*eq[2])
                if h_new[1] >= 0 and h_new[2] >= 0:
                    H_new = np.append(H_new, np.array([[h[0]*eq[0], h[1]*eq[1], h[2]*eq[2]]]), axis=0)
                    break
        else:
            H_new = np.append(H_new, np.array([[h[0], h[1], h[2]]]), axis=0)
    H_new = np.delete(H_new, 0, axis=0)
    for i in range(len(H_new)):
        if H_new[i][2] == 0 and H_new[i][0] < 0: #locus layer = hk0 and not -hk0
            H_new[i][0] = -H_new[i][0]
    
    return H_new    

def prepare_reflections(H, F):
    for i in range(len(F)):
      F[i] = F[i]/np.max(F)
    H_reind = reindex_monoclinic(H)
    sort_array = np.lexsort((H_reind[:, 2], H_reind[:, 1], H_reind[:, 0]))
    H_reind = H_reind[sort_array]
    F = F[sort_array]

    H_final = np.array([[0, 0, 0]])
    F_final = np.array([])
    group = [F[0]]
    H_curr = H_reind[0]

    for i in range(len(H_reind)):
      if (H_reind[i] == H_curr).all():
        group.append(F[i])
      else:
        H_final = np.append(H_final, np.array([H_curr]), axis=0)
        F_final = np.append(F_final, sum(group) / len(group))
        H_curr = H_reind[i]
        group = [F[i]]
    H_final = np.append(H_final, np.array([H_curr]), axis=0)
    F_final = np.append(F_final, sum(group) / len(group))
    H_final = np.delete(H_final, 0, axis=0)
    
    max_F_final = max(F_final)
    F_final = F_final / max_F_final
    
    return H_final, F_final


def get_PhAI_phases(f_sq_obs, randomize_phases = 0, cycles = 1):
    """
    Get PhAI phases for the loaded file.

    Parameters:
    - randomize_phases: If set to 1, randomizes the initial phases.
    - cycles: Number of cycles to run the phase extension.
    
    Returns:
    - None
    """
    Fs = f_sq_obs.as_amplitude_array().data().as_numpy_array()
    I_max = Fs.max()
    indices = f_sq_obs.indices()
    max_index = model_args['max_index']
    
    hkl_array = []
    for h in range(-max_index, max_index+1):
      for k in range(0, max_index+1):
        for l in range(0, max_index+1):
          if not(h==0 and k==0 and l==0):
            if math.sqrt(h**2+k**2+l**2) <= max_index:
              hkl_array.append([h,k,l])
    hkl_array = np.array(hkl_array,dtype=np.int32)
    
    indices, Fs = prepare_reflections(indices, Fs)

    amplitudes = torch.zeros(1, 21, 11, 11)
    for f, hkl in zip(Fs, indices):
      h, k, l = hkl
      if h < -max_index or h > max_index or k < 0 or k > max_index or l < 0 or l > max_index:
        continue
      if not(h == 0 and k == 0 and l == 0):
        if f != 0:
          amplitudes[0][h+max_index][k][l] = f / I_max
    
    amplitudes_ord = []
    for h in range(-max_index, max_index+1):
      for k in range(0, max_index+1):
        for l in range(0, max_index+1):
          if not(h==0 and k==0 and l==0):
            if math.sqrt(h**2+k**2+l**2) <= max_index:
              amplitudes_ord.append(amplitudes[0][h+max_index][k][l])

    if randomize_phases :
      init_phases = randomize_phases(torch.zeros_like(amplitudes))
    else:
      init_phases = torch.zeros_like(amplitudes)
        
    for i in range(cycles):
      print('cycle: ', i+1)
      if i == 0:
        output = phases(model(amplitudes, init_phases))
      else:
        for j in range(len(amplitudes[0])):
          init_phases[0][hkl_array[j][0]+max_index][hkl_array[j][1]][hkl_array[j][2]] = output[0][j]
        output = phases(model(amplitudes, init_phases))
    
    ph = output[0].cpu().numpy().flatten()
    amplitudes_ord = np.array(amplitudes_ord)
    #multiply Fs with the phases:
    C_Fs = flex.complex_double((amplitudes_ord * np.exp(1j * np.deg2rad(ph))).tolist())
    miller_set = miller.array(
      miller_set=miller.set(
        crystal_symmetry=f_sq_obs.crystal_symmetry(),
        indices=flex.miller_index(hkl_array.tolist()),
        anomalous_flag=False
      ),
      data=C_Fs
    )
    return miller_set

def create_solution_map(max_peaks=15):
  cctbx_adapter = OlexCctbxAdapter()
  f_sq_obs = cctbx_adapter.reflections.f_sq_obs_merged
  guess = get_PhAI_phases(f_sq_obs, randomize_phases=randomize_output, cycles=1)
  guess = guess.expand_to_p1().set_observation_type_xray_amplitude()
  obs_map = guess.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                          resolution_factor=1,
                          grid_step=0.2,
                          f_000=1200).apply_volume_scaling()
  cubes_maps.plot_fft_map(obs_map)
  peaks = obs_map.peak_search(
    parameters=maptbx.peak_search_parameters(
      peak_search_level=2,
      interpolate=False,
      min_distance_sym_equiv=1.0,
      max_clusters=max_peaks),
    verify_symmetry=True
    ).all()
  i = 0
  olx.Kill('$Q', au=True)
  for xyz, height in zip(peaks.sites(), peaks.heights()):
    if i < max_peaks:
      a = olx.xf.uc.Closest(*xyz).split(',')
      if OV.IsEDData():
        pi = "Peak %s = (%.3f, %.3f, %.3f), Height = %.3f e/A, %.3f A away from %s"
      else:
        pi = "Peak %s = (%.3f, %.3f, %.3f), Height = %.3f e/A^3, %.3f A away from %s" % (
          i + 1, xyz[0], xyz[1], xyz[2], height, float(a[1]), a[0])
      print(pi)
    id = olx.xf.au.NewAtom("%.2f" %(height), *xyz)
    if id != '-1':
      olx.xf.au.SetAtomU(id, "0.06")
      i = i+1
    if i == 100 or i >= max_peaks:
      break
  if OV.HasGUI():
    basis = olx.gl.Basis()
    frozen = olx.Freeze(True)
  olx.xf.EndUpdate(True) #clear LST
  olx.Compaq(q=True)
  if OV.HasGUI():
    olx.gl.Basis(basis)
    olx.Freeze(frozen)
  

OV.registerFunction(create_solution_map, False, 'PhAI',)
