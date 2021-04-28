import os
from Method import Method_solution
import phil_interface
from olexFunctions import OV
import olex
import olex_core
import olx

class Method_Superflip(Method_solution):

  def __init__(self, phil_object):
    Method_solution.__init__(self, phil_object)
    self.to_cleanup = []
    prefix = "settings.superflip"
    defaults = {
      'repeatmode' : 'never',
      'repeatmode.trials' : '1',
      'max_cycles' : '10000',
      'fastfft' : 'false',
      'data.normalize': 'local',
      'data.nresshells': '100',
      'data.weakratio': '0.2',
      'resolution.limit': 'false',
      'resolution.units': 'd',
      'resolution.high': '100',
      'resolution.low': '0',
      'data.missing.process': 'bound',
      'data.missing.rlim': '0.4',
      'data.missing.ubound': '4',
      'convergence.mode': 'normal',
      'convergence.threshold': '0.8',
      'delta.method': 'auto',
      'delta.value': '1.3',
      'convergence.polish': 'true',
      'convergence.polish.cycles': '5',
      'symmetry.derive': 'use',
      'symmetry.search': 'average',
      'cleanup': 'true',
      'use_centering' : 'true'
    }
    for k,v in defaults.items():
      olx.SetVar("%s.%s" %(prefix,k), v)


  def pre_solution(self, RunPrgObject):
    pass

  def create_input(self):
    self.derive_symmetry = olx.GetVar('settings.superflip.symmetry.search') != 'no' and\
          olx.GetVar('settings.superflip.symmetry.derive') == 'use'
    input = []
    input.append('title ' + olx.Title())
    sg = olx.xf.au.GetCellSymm()
    sg_info = olex_core.SGInfo(sg, False)
    if not self.derive_symmetry:
      cellp = olx.xf.au.GetCell().split(',')
      system = sg_info['System']
      if system == 'Monoclinic':
        axis = sg_info['Axis']
        if axis == 'a':
          cellp[4] = cellp[5] = '90'
        elif axis == 'b':
          cellp[3] = cellp[5] = '90'
        elif axis == 'c':
          cellp[3] = cellp[4] =  '90'
      elif system == 'Cubic' or system == 'Tetragonal' or system == 'Orthorhombic':
        cellp[3] = cellp[4] = cellp[5] = '90'
        if system == 'Cubic':
          cellp[0] = cellp[1] = cellp[2]
        elif system == 'Tetragonal':
          cellp[0] = cellp[1]
      elif system == 'Hexagonal' or system == 'Trigonal':
        cellp[3] = cellp[4] = '90'
        cellp[5] = '120'
      input.append('cell ' + ' '.join(cellp))
    else:
      input.append('cell ' + olx.xf.au.GetCell().replace(',', ' '))
    input.append('lambda %s' %olx.xf.exptl.Radiation())

    input.append('symmetry')
    if self.derive_symmetry:
      input.append("+X +Y +Z")
    else:
      for i in sg_info['MatricesAll']:
        input.append(olex_core.MatrixToString(i))
    input.append('endsymmetry')

    input.append('centers')
    input.append("0 0 0")
    if (not self.derive_symmetry) or (olx.GetVar('settings.superflip.use_centering') == 'true'):
      for i in sg_info['Lattice']['Translations']:
        input.append("%s %s %s" %i)
    input.append('endcenters')


    v = olx.GetVar('settings.superflip.repeatmode')
    if v == 'trials':
      input.append("repeatmode %s" %olx.GetVar('settings.superflip.repeatmode.trials'))
    else:
      input.append("repeatmode %s" %v)
    input.append('maxcycles %s'\
                   %olx.GetVar('settings.superflip.max_cycles'))
    if olx.GetVar('settings.superflip.fastfft') == 'true':
      input.append('fastfft yes')
    else:
      input.append('fastfft no')
    input.append('voxel AUTO')
    input.append('weakratio %s' %olx.GetVar('settings.superflip.data.weakratio'))
    v = olx.GetVar('settings.superflip.data.missing.process')
    if v == 'zero':
      input.append("missing zero")
    elif v == 'float':
      input.append("missing float %s" %olx.GetVar('settings.superflip.data.missing.rlim'))
    else:
      input.append("missing %s %s %s"  %(v,
                                       olx.GetVar('settings.superflip.data.missing.rlim'),
                                       olx.GetVar('settings.superflip.data.missing.ubound')))

    if olx.GetVar('settings.superflip.resolution.limit') == 'true':
      input.append('resunit %s' %olx.GetVar('settings.superflip.resolution.units'))
      input.append('reslimit %s %s' %(olx.GetVar('settings.superflip.resolution.high'),
                                      olx.GetVar('settings.superflip.resolution.low')))

    v =  olx.GetVar('settings.superflip.data.normalize')
    input.append('normalize %s' %v)
    if v == 'local':
      input.append('nresshells %s' %olx.GetVar('settings.superflip.data.nresshells'))

    input.append("convergencemode %s %s" %(
      olx.GetVar('settings.superflip.convergence.mode'),
      olx.GetVar('settings.superflip.convergence.threshold'))
      )

    v = olx.GetVar('settings.superflip.convergence.polish')
    if v == 'true':
      input.append('polish yes %s' %olx.GetVar('settings.superflip.convergence.polish.cycles'))
    else:
      input.append('polish no')

    self.file_name = olx.FileName()
    input.append('searchsymmetry %s' %olx.GetVar('settings.superflip.symmetry.search'))
    input.append('derivesymmetry %s' %olx.GetVar('settings.superflip.symmetry.derive'))
    input.append('outputfile %s.m81' %self.file_name)
    #setup edma
    input.append('inputfile %s.m81' %self.file_name)
    input.append('export %s.ins' %self.file_name)
    input.append('composition %s' %olx.xf.GetFormula('unit'))
    input.append('maxima all')
    input.append('plimit 1.5 sigma')
    input.append('chlimit 0.25')
    input.append('scale fractional')
    input.append('centerofcharge yes')
    input.append('fullcell no')
    input.append('numberofatoms guess')
    input.append('dataformat shelx')
    self.tmp_hkl = os.path.join(olx.FilePath(), "superflip.hkl")
    self.to_cleanup.append(self.tmp_hkl)
    from cctbx_olex_adapter import OlexCctbxAdapter
    from iotbx import shelx
    cctbx_adaptor = OlexCctbxAdapter()
    with open(self.tmp_hkl, "w") as x:
      shelx.hklf.miller_array_export_as_shelx_hklf(cctbx_adaptor.reflections.f_sq_obs, x)
    input.append('fbegin %s' %olx.file.GetName(self.tmp_hkl))
    input.append('endf')
    self.input_file_name = os.path.normpath("%s.sfi" %(self.file_name))
    try:
      input_file = open(self.input_file_name, 'w+')
      input_file.write('\n'.join(input))
      input_file.close()
      self.to_cleanup.append(self.input_file_name)
      self.to_cleanup.append("%s.m81" %self.file_name)
      self.to_cleanup.append("%s.sflog" %self.file_name)
      self.to_cleanup.append(".coo")
    except:
      raise
    return ""

  def do_run(self, RunPrgObject):
    self.create_input()
    if olx.Exec("superflip", self.input_file_name):
      olx.WaitFor("process")
      if olx.Exec("edma", self.input_file_name):
        olx.WaitFor("process")
        ZERR = 'ZERR %s %s' %(olx.xf.au.GetZ(),
                            olx.xf.au.GetCell('esd').replace(',', ' '))
        if OV.HasGUI():
          freeze_status = olx.Freeze()
          olx.Freeze(True)
        try:
          olx.Atreap("%s.ins" %self.file_name)
          if self.derive_symmetry:
            log_file_name = "%s.sflog" %self.file_name
            if os.path.exists(log_file_name):
              log_file = open(log_file_name, "r")
              for l in log_file:
                if "Hall symbol:" in l:
                  l = l.strip()
                  hall_symbol = l.split(':')[1]
                  olx.ChangeSG("%s" %hall_symbol)
                  break
              log_file.close()
              if OV.HasGUI():
                olex.m("spy.run_skin sNumTitle")
            else:
              print("Could not locate the SF log file, aborting symmetry processing")
          olx.Compaq(a=True)
          olx.AddIns("%s" %ZERR)
          olx.File("%s.res" %self.file_name)
        finally:
          if OV.HasGUI():
            olx.Freeze(freeze_status)

  def post_solution(self, RunPrgObject):
    if olx.GetVar('settings.superflip.cleanup') == 'true':
      for f in self.to_cleanup:
        if os.path.exists(f):
          try:
            os.remove(f)
          except:
            print("Failed to remove: %s" %f)


superflip_cf_phil = phil_interface.parse("""
name = 'Charge Flipping'
  .type=str
atom_sites_solution=iterative
  .type=str
  instructions {

  execution
    .optional=False
  {
    values {
      repeatmode= *never nosuccess always trials
        .type=choice
      trials = 1
        .type=int
      maxcycl=10000
        .type=int
      fastfft=False
        .type=bool
      cleanup=True
        .type=bool
    }
    default=True
      .type=bool
  }
  data
    .optional=False
  {
    values {
      normalize=*no wilson local
        .type=choice
      nresshells=100
        .type=int
      weakratio=0.2
        .type=float
    }
    default=True
      .type=bool
  }


  missing
    .optional=True
  {
    values {
      value=zero *float bound boundum
        .type=choice
      resolution_limit=0.4
        .type=float
      uper_bound=4
        .type=float
    }
    default=False
      .type=bool
  }

  resolution
    .optional=True
  {
    values {
      resunit=*d sthl
        .type=choice
      reslimit_high=100
        .type=int
      reslimit_low=0
        .type=int
    }
    default=False
      .type=bool
  }

  convergence
    .optional=False
  {
    values {
      mode=*threshhold normal rvalue charge peakiness
        .type=choice
      threshold=0.8
        .type=float
    }
    default=True
      .type=bool
  }

  delta
    .optional=False
  {
    values {
      value=*AUTO Number
        .type=choice
      Number=1.3
        .type=float
      of=static dynamic *sigma
        .type=choice
    }
    default=True
      .type=bool
  }

  output
    .optional=False
  {
    values {
      derivesymmetry=False
        .type=bool
      limit=25
        .type=float
      polish=True
        .type=bool
      cycles=5
        .type=int
    }
    default=False
      .type=bool
  }
  }

""")
