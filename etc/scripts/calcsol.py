from __future__ import division

import os
import sys
import shutil
import re
import olex
import olx
import olex_core
from olexFunctions import OlexFunctions
OV = OlexFunctions()

import cctbx.masks
from cctbx import maptbx, miller, sgtbx, xray
from cctbx.array_family import flex
from scitbx.math import approx_equal_relatively
from libtbx.utils import xfrange

"""
self.solvent_accessible_volume = self.n_solvent_grid_points() \
        / self.mask.data.size() * self.xray_structure.unit_cell().volume()

"""

def xray_structure(self, construct_restraints=False):
  self.cell = self.olx_atoms.getCell()
  self.space_group = "hall: "+str(olx.xf_au_GetCellSymm("hall"))
  create_cctbx_xray_structure = cctbx_controller.create_cctbx_xray_structure(
    self.cell,
    self.space_group,
    self.olx_atoms.iterator(),
    restraints_iter=restraints_iter,
    constraints_iter=None
  )
  return xray_structure

class mask(object):
  def __init__(self):
    self.xray_structure = xray_structure
    self.params = OV.Params().snum.masks
    
  def compute(self,
              solvent_radius,
              shrink_truncation_radius,
              ignore_hydrogen_atoms=False,
              crystal_gridding=None,
              grid_step=None,
              resolution_factor=1/4,
              atom_radii_table=None,
              use_space_group_symmetry=False):
    if grid_step is not None: d_min = None
    else: d_min = self.fo2.d_min()
    if crystal_gridding is None:
      self.crystal_gridding = maptbx.crystal_gridding(
        unit_cell=self.xray_structure.unit_cell(),
        space_group_info=self.xray_structure.space_group_info(),
        step=grid_step,
        d_min=d_min,
        resolution_factor=resolution_factor,
        symmetry_flags=sgtbx.search_symmetry_flags(
          use_space_group_symmetry=use_space_group_symmetry))
    else:
      self.crystal_gridding = crystal_gridding
    if use_space_group_symmetry:
      atom_radii = cctbx.masks.vdw_radii(
        self.xray_structure, table=atom_radii_table).atom_radii
      asu_mappings = self.xray_structure.asu_mappings(
        buffer_thickness=flex.max(atom_radii)+solvent_radius)
      scatterers_asu_plus_buffer = flex.xray_scatterer()
      frac = self.xray_structure.unit_cell().fractionalize
      for sc, mappings in zip(
        self.xray_structure.scatterers(), asu_mappings.mappings()):
        for mapping in mappings:
          scatterers_asu_plus_buffer.append(
            sc.customized_copy(site=frac(mapping.mapped_site())))
      xs = xray.structure(crystal_symmetry=self.xray_structure,
                          scatterers=scatterers_asu_plus_buffer)
    else:
      xs = self.xray_structure.expand_to_p1()
    self.vdw_radii = cctbx.masks.vdw_radii(xs, table=atom_radii_table)
    self.mask = cctbx.masks.around_atoms(
      unit_cell=xs.unit_cell(),
      space_group_order_z=xs.space_group().order_z(),
      sites_frac=xs.sites_frac(),
      atom_radii=self.vdw_radii.atom_radii,
      gridding_n_real=self.crystal_gridding.n_real(),
      solvent_radius=solvent_radius,
      shrink_truncation_radius=shrink_truncation_radius)
    if use_space_group_symmetry:
      tags = self.crystal_gridding.tags()
      tags.tags().apply_symmetry_to_mask(self.mask.data)
    self.flood_fill = cctbx.masks.flood_fill(
      self.mask.data, self.xray_structure.unit_cell())
    self.exclude_void_flags = [False] * self.flood_fill.n_voids()
    self.solvent_accessible_volume = self.n_solvent_grid_points() \
        / self.mask.data.size() * self.xray_structure.unit_cell().volume()

  def n_voids(self):
    return self.flood_fill.n_voids()

  def n_solvent_grid_points(self):
    return sum([self.mask.data.count(i+2) for i in range(self.n_voids())
                if not self.exclude_void_flags[i]])

  def show_summary(self, log=None):
    if log is None: log = sys.stdout
    print >> log, "use_set_completion: %s" %self.use_set_completion
    print >> log, "solvent_radius: %.2f" %(self.mask.solvent_radius)
    print >> log, "shrink_truncation_radius: %.2f" %(
      self.mask.shrink_truncation_radius)
    print >> log, "van der Waals radii:"
    self.vdw_radii.show(log=log)
    print >> log
    print >> log, "Total solvent accessible volume / cell = %.1f Ang^3 [%.1f%%]" %(
      self.solvent_accessible_volume,
      100 * self.solvent_accessible_volume /
      self.xray_structure.unit_cell().volume())
    n_voids = self.n_voids()
    print >> log
    self.flood_fill.show_summary(log=log)
    if n_voids == 0: return
    print >> log
    print >> log, "Void  Vol/Ang^3  #Electrons"
    grid_points_per_void = self.flood_fill.grid_points_per_void()
    com = self.flood_fill.centres_of_mass_frac()
    electron_counts = self.electron_counts_per_void()
    for i in range(self.n_voids()):
      void_vol = (
        self.xray_structure.unit_cell().volume() * grid_points_per_void[i]) \
               / self.crystal_gridding.n_grid_points()
      formatted_site = ["%6.3f" % x for x in com[i]]
      print >> log, "%4i" %(i+1),
      print >> log, "%10.1f     " %void_vol,
      print >> log, "%7.1f" %electron_counts[i]

def calcsol():
  print "Calculating Solvent Accessible Volume"
  print "Test"
  params = OV.Params().snum.masks
  print params
  
  mask.compute(self,solvent_radius=params.solvent_radius,
               shrink_truncation_radius=params.shrink_truncation_radius,
               resolution_factor=params.resolution_factor,
               atom_radii_table=olex_core.GetVdWRadii(),
               use_space_group_symmetry=True)               
  mask.show_summary(self)
  
OV.registerFunction(calcsol)