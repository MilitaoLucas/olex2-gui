import os
import sys
import olex
import olx
import gui
import shutil
import time
import subprocess
import hashlib
from pathlib import Path
import numpy as np
from smtbx.refinement.constraints.nomore import (
  NoMoReConstraint, PhononData
)
from smtbx.refinement.constraints.nomore.frequency_partition import create_strategy

from olexFunctions import OV
from PluginTools import PluginTools as PT

if OV.HasGUI():
  get_template = gui.tools.TemplateProvider.get_template

try:
  from_outside = False
  p_path = os.path.dirname(os.path.abspath(__file__))
except Exception as e:
  from_outside = True
  p_path = os.path.dirname(os.path.abspath("__file__"))

d = {}
for line in open(os.path.join(p_path, 'def.txt')).readlines():
  line = line.strip()
  if not line or line.startswith("#"):
    continue
  d[line.split("=")[0].strip()] = line.split("=")[1].strip()

p_name = d['p_name']
p_htm = d['p_htm']
p_img = eval(d['p_img'])
p_scope = d['p_scope']


def _strategy_params_for(strategy_name):
  """Return the current snum.* params dict for the given strategy name."""
  if strategy_name == 'thermal':
    return {
      'medium_factor': float(OV.GetParam('snum.NoMoRe.thermal.medium_factor', 1.5)),
      'high_factor':   float(OV.GetParam('snum.NoMoRe.thermal.high_factor', 2.0)),
    }
  elif strategy_name == 'fixed':
    params = {
      'high_limit': float(OV.GetParam('snum.NoMoRe.fixed.high_limit', 1000.0)),
    }
    medium_limit = OV.GetParam('snum.NoMoRe.fixed.medium_limit', None)
    n_refined    = OV.GetParam('snum.NoMoRe.fixed.n_refined', None)
    if medium_limit is not None:
      params['medium_limit'] = float(medium_limit)
    if n_refined is not None:
      params['n_refined'] = int(n_refined)
    return params
  elif strategy_name == 'sensitivity':
    return {
      'low_threshold':  float(OV.GetParam('snum.NoMoRe.sensitivity.low_threshold', 0.90)),
      'high_threshold': float(OV.GetParam('snum.NoMoRe.sensitivity.high_threshold', 0.99)),
    }
  return {}


def _compute_scales_hash(phonon_path: Path, strategy_name: str, params: dict) -> str:
  """Hash of phonon file content + strategy + params — used to detect stale scales."""
  import json
  h = hashlib.md5()
  h.update(phonon_path.read_bytes())
  h.update(strategy_name.encode())
  h.update(json.dumps(params, sort_keys=True).encode())
  return h.hexdigest()


def build_constraint():
  """Build a NoMoReConstraint from snum.NoMoRe.* params. Returns None if unavailable."""
  filename = OV.GetParam('snum.NoMoRe.filename', '')
  if not filename:
    return None
  phonon_path = Path(OV.FilePath()) / filename
  if not phonon_path.exists():
    print(f'NoMoRe: phonon file not found: {phonon_path}')
    return None

  strategy_name = OV.GetParam('snum.NoMoRe.strategy', 'thermal')
  if strategy_name not in ('thermal', 'fixed', 'sensitivity'):
    print(f'NoMoRe: unknown strategy "{strategy_name}", skipping')
    return None

  params = _strategy_params_for(strategy_name)
  current_hash = _compute_scales_hash(phonon_path, strategy_name, params)

  # Attempt warm-start from stored scales if the hash matches
  initial_scales = None
  stored_hash = OV.GetParam('snum.NoMoRe.scales_hash', '')
  print('Current scales hash', stored_hash)
  if stored_hash == current_hash:
    scales_str = OV.GetParam('snum.NoMoRe.scales', '')
    print(scales_str)
    if scales_str:
      try:
        import json
        initial_scales = np.array(json.loads(scales_str), dtype=float)
      except Exception:
        initial_scales = None

  phonon_data = PhononData.load(phonon_path)
  strategy = create_strategy(strategy_name, params)
  return NoMoReConstraint(phonon_data, strategy, initial_scales=initial_scales)


def save_scales(constraint):
  """Persist refined scale factors to snum.NoMoRe.* params after convergence."""
  import json
  scales = constraint.get_refined_scales()
  filename = OV.GetParam('snum.NoMoRe.filename', '')
  strategy_name = OV.GetParam('snum.NoMoRe.strategy', 'thermal')
  params = _strategy_params_for(strategy_name)
  phonon_path = Path(OV.FilePath()) / filename
  current_hash = _compute_scales_hash(phonon_path, strategy_name, params)
  OV.SetParam('snum.NoMoRe.scales', json.dumps(scales.tolist()))
  OV.SetParam('snum.NoMoRe.scales_hash', current_hash)


class NoMoRe(PT):
  def __init__(self):
    self.p_name = p_name
    self.p_htm = p_htm
    self.p_img = p_img
    self.p_scope = p_scope
    self.p_path = p_path
    print("NoMoRe plugin loaded")
    self._load_phil()
    self.register_methods()

  def _load_phil(self):
    phil_path = os.path.join(p_path, 'NoMoRe.phil')
    with open(phil_path, 'r', encoding='utf-8') as f:
      phil = f.read()
    olx.phil_handler.adopt_phil(phil_string=phil)
    olx.phil_handler.rebuild_index()

  def register_methods(self):
    OV.registerFunction(self.build_thermal, True, "nomore")
    OV.registerFunction(self.build_fixed, True, "nomore")
    OV.registerFunction(self.build_sensitivity, True, "nomore")
    OV.registerFunction(self.print, True, "nomore")
    OV.registerFunction(self.remove, True, "nomore")

  def build_thermal(self, filename, medium_factor=1.5, high_factor=2.0):
    OV.SetParam('snum.NoMoRe.filename', filename)
    OV.SetParam('snum.NoMoRe.strategy', 'thermal')
    OV.SetParam('snum.NoMoRe.thermal.medium_factor', float(medium_factor))
    OV.SetParam('snum.NoMoRe.thermal.high_factor', float(high_factor))
    OV.SetParam('snum.NoMoRe.enabled', True)

  def build_fixed(self, filename, high_limit=1000.0, medium_limit=None, n_refined=None):
    OV.SetParam('snum.NoMoRe.filename', filename)
    OV.SetParam('snum.NoMoRe.strategy', 'fixed')
    OV.SetParam('snum.NoMoRe.fixed.high_limit', float(high_limit))
    if medium_limit is not None:
      OV.SetParam('snum.NoMoRe.fixed.medium_limit', float(medium_limit))
    if n_refined is not None:
      OV.SetParam('snum.NoMoRe.fixed.n_refined', int(n_refined))
    OV.SetParam('snum.NoMoRe.enabled', True)

  def build_sensitivity(self, filename, low_threshold=0.90, high_threshold=0.99):
    OV.SetParam('snum.NoMoRe.filename', filename)
    OV.SetParam('snum.NoMoRe.strategy', 'sensitivity')
    OV.SetParam('snum.NoMoRe.sensitivity.low_threshold', float(low_threshold))
    OV.SetParam('snum.NoMoRe.sensitivity.high_threshold', float(high_threshold))
    OV.SetParam('snum.NoMoRe.enabled', True)

  def remove(self):
    OV.SetParam('snum.NoMoRe.enabled', False)

  def print(self):
    c = build_constraint()
    if c is not None:
      print(c.current_frequencies())

nomore_instance = NoMoRe()