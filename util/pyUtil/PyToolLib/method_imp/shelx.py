import os
from Method import Method, Method_refinement, Method_solution
import phil_interface
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import olex
import olx
import glob
import OlexVFS
import ntpath


class Method_shelx(Method):

  def do_run(self, RunPrgObject):
    """Runs any SHELX refinement/solution program
    """
    print 'STARTING SHELX %s with %s' %(
      RunPrgObject.program.program_type, self.name)
    prgName = olx.file.GetName(RunPrgObject.shelx)
    #olex.m("User '%s'" %RunPrgObject.tempPath)
    olx.User("%s" %RunPrgObject.tempPath)
    xl_ins_filename = RunPrgObject.shelx_alias
# This is an ugly fix - but good start
    if 'shelxs86' in prgName:
      print 'STARTING SHELX86 modifications'
      import fileinput, string, sys
      for line in fileinput.input(xl_ins_filename.lower()+'.ins',inplace=1):
        if 'REM' in line:
          continue
        sys.stdout.write(line)
# This is super ugly but what can I do?
# This really be a function rather than a separate file but I can not get it to work yet?
    if prgName in ('shelxs', 'xs', 'shelxs86', 'shelxs13'):
      import fileinput, string, sys
      for line in fileinput.input(xl_ins_filename.lower()+'.ins',inplace=1):
        if 'DISP' in line:
          continue
        sys.stdout.write(line)
    commands = [xl_ins_filename.lower()]  #This is correct!!!!!!
    #sys.stdout.graph = RunPrgObject.Graph()
    if self.command_line_options:
      commands += self.command_line_options.split()
    success = olx.Exec(prgName, *commands, q=(not RunPrgObject.params.snum.shelx_output))
    if not success:
      raise RuntimeError(
        'you may be using an outdated version of %s' %(prgName))
    olx.WaitFor('process') # uncomment me!

    additions = ['', '_a', '_b', '_c', '_d', '_e']
    self.failure = True
    for add in additions:
      p = "%s%s.res" %(xl_ins_filename, add)
      if os.path.exists(p):
        if os.path.getsize(p) != 0:
          self.failure = False
          break
    olx.User(RunPrgObject.filePath)


class Method_shelx_solution(Method_shelx, Method_solution):
  """Inherits methods specific to shelx solution programs
  """
  def observe(self, RunPrgObject):
    import Analysis
    self.observer = Analysis.ShelXS_graph(RunPrgObject.program, RunPrgObject.method)
    OV.registerCallback("procout", self.observer.observe)


class Method_shelx_refinement(Method_shelx, Method_refinement):
  """Inherits methods specific to shelx refinement programs
  """

  def __init__(self, phil_object):
    Method.__init__(self, phil_object)
    self.cif = {}

  def pre_refinement(self, RunPrgObject):
    if OV.GetParam("snum.refinement.use_solvent_mask"):
      import cctbx_olex_adapter
      from smtbx import masks
      from libtbx import easy_pickle
      #from iotbx.shelx import hklf
      filepath = OV.StrDir()
      modified_intensities = None
      modified_hkl_path = "%s/%s-mask.hkl" %(OV.FilePath(), OV.FileName())
      if OV.HKLSrc():
        fab_path = ".".join(OV.HKLSrc().split(".")[:-1]) + ".fab"
      method = "smbtx"
      if "_sq" in fab_path:
        method="SQUEEZE"
      f_mask, f_model = None, None
      # backward compatibility - just in case
      if not OV.HKLSrc() == modified_hkl_path:
        olx.SetVar('snum.masks.original_hklsrc', OV.HKLSrc())
      else:
        olx.SetVar('snum.masks.original_hklsrc', '')
      if OV.GetParam("snum.refinement.recompute_mask_before_refinement") or not os.path.exists(fab_path):
        if OV.HKLSrc() == modified_hkl_path:
          _ = "You can't calculate a mask on an already masked file!"
          OlexVFS.write('mask_notification.htm',_,1)
          raise Exception(_)

        if method == "SQUEEZE":
          olex.m("spy.OlexPlaton(q)")
          Method_refinement.pre_refinement(self, RunPrgObject)
          return

        cctbx_olex_adapter.OlexCctbxMasks()
        if olx.current_mask.flood_fill.n_voids() > 0:
          f_mask = olx.current_mask.f_mask()
          f_model = olx.current_mask.f_model()
        else:
          _ = "There are no voids!"
          print _
          OV.SetParam("snum.refinement.use_solvent_mask", False)
          olex.m('delins ABIN')
          OlexVFS.write_to_olex('mask_notification.htm',_,1)
      #elif os.path.exists("%s/%s-f_mask.pickle" %(filepath, OV.FileName())):
        #f_mask = easy_pickle.load("%s/%s-f_mask.pickle" %(filepath, OV.FileName()))
        #f_model = easy_pickle.load("%s/%s-f_model.pickle" %(filepath, OV.FileName()))
      if f_mask is not None:
        cctbx_adapter = cctbx_olex_adapter.OlexCctbxAdapter()
        fo2 = cctbx_adapter.reflections.f_sq_obs_filtered
        if f_mask.size() < fo2.size():
          f_model = f_model.generate_bijvoet_mates().customized_copy(
            anomalous_flag=fo2.anomalous_flag()).common_set(fo2)
          f_mask = f_mask.generate_bijvoet_mates().customized_copy(
            anomalous_flag=fo2.anomalous_flag()).common_set(fo2)
        elif f_mask.size() > fo2.size():
          # this could happen with omit instruction
          f_mask = f_mask.common_set(fo2)
          f_model = f_model.common_set(fo2)
          if f_mask.size() != fo2.size():
            raise RuntimeError("f_mask array doesn't match hkl file")
      if f_mask is not None:
        with open(fab_path, "w") as f:
          for i,h in enumerate(f_mask.indices()):
            line = "%d %d %d " %h + "%.4f %.4f" % (f_mask.data()[i].real, f_mask.data()[i].imag)
            print >> f, line
          print >> f, "0 0 0 0.0 0.0"
      #else:
        #print "No mask present"
    Method_refinement.pre_refinement(self, RunPrgObject)

  def post_refinement(self, RunPrgObject):
    before_mask = olx.GetVar('snum.masks.original_hklsrc', '')
    if before_mask:
      olx.UnsetVar('snum.masks.original_hklsrc')
      if OV.HKLSrc() != before_mask:
        OV.HKLSrc(before_mask)
        OV.File()
    suggested_weight = olx.Ins('weight1')
    if suggested_weight != 'n/a':
      if len(suggested_weight.split()) == 1:
        suggested_weight += ' 0'
      OV.SetParam('snum.refinement.suggested_weight', suggested_weight)
    self.gather_refinement_information()
    self.writeRefinementInfoIntoRes(self.cif)
    params = {
      'snum.refinement.max_peak' : 'peak',
      'snum.refinement.max_hole' : 'hole',
      'snum.refinement.max_shift_site' : 'max_shift',
      'snum.refinement.max_shift_site_atom' : 'max_shift_object',
      'snum.refinement.max_shift_over_esd' : 'max_shift/esd',
      'snum.refinement.max_shift_over_esd_atom' : 'max_shift/esd_object',
      'snum.refinement.max_shift_u' : 'max_dU',
      'snum.refinement.max_shift_u_atom' : 'max_dU_object',
      'snum.refinement.flack_str' : 'flack',
      'snum.refinement.goof' : "s",
    }
    for k,v in params.iteritems():
      v = olx.Lst(v)
      if v == 'n/a':  v = 0
      OV.SetParam(k, v)


  def gather_refinement_information(self):
    cif = {}
    cif.setdefault('_refine_ls_R_factor_all', olx.Lst('R1all'))
    cif.setdefault('_refine_ls_R_factor_gt', olx.Lst('R1'))
    cif.setdefault('_refine_ls_wR_factor_ref', olx.Lst('wR2'))
    cif.setdefault('_refine_ls_goodness_of_fit_ref', olx.Lst('s'))
    cif.setdefault('_refine_ls_shift/su_max', olx.Lst('max_shift/esd'))
    cif.setdefault('_refine_ls_shift/su_mean', olx.Lst('mean_shift/esd'))
    cif.setdefault('_reflns_number_total', olx.Lst('ref_total'))
    cif.setdefault('_reflns_number_gt', olx.Lst('ref_4sig'))
    cif.setdefault('_refine_ls_number_parameters', olx.Lst('params_n'))
    cif.setdefault('_refine_ls_number_restraints', olx.Lst('restraints_n'))
    cif.setdefault('_refine_ls_abs_structure_Flack', olx.Lst('flack'))
    cif.setdefault('_refine_diff_density_max', olx.Lst('peak'))
    cif.setdefault('_refine_diff_density_min', olx.Lst('hole'))
    self.cif = cif

  def observe(self, RunPrgObject):
    import Analysis
    self.observer = Analysis.ShelXL_graph(RunPrgObject.program, RunPrgObject.method)
    OV.registerCallback("procout", self.observer.observe)

  def getFlack(self):
    flack = olx.Lst('flack')
    if flack == "n/a":
      flack = None

    return flack

class Method_shelxt(Method_shelx_solution):
  def pre_solution(self, RunPrgObject):
    pass
#    OlexVFS.delete("solution_output.htm")

  def post_solution(self, RunPrgObject):
    if not OV.HasGUI():
      return
    import gui.tools
    debug = bool(OV.GetParam('olex2.debug',False))
    f = os.sep.join([OV.StrDir(), "temp", OV.FileName() + '.lxt'])
    if os.path.exists(f):
      f = open(f, 'r').readlines()
    else:
      return
    res_l = []
    i = 0
    for line in f:
      if "Rweak" not in line:
        i += 1
        continue
      for j in xrange(len(f) -i):
        if "Assign" not in f[i+j]:
          res_l.append(f[i+j])
        else:
          break

    s_blank = gui.tools.TemplateProvider.get_template('xt_output_table', force=debug)
    href = res_l[0][37:50].strip()

    d = {
      'td1':"<b>%s</b>" %res_l[0][0:6].strip(),
      'td2':"<b>%s</b>" %res_l[0][7:12].strip(),
      'td3':"<b>%s</b>" %res_l[0][13:20].strip(),
      'td4':"<b>%s</b>" %res_l[0][21:37].strip(),
      'td5':"<b>%s</b>" %href,
      'td6':"<b>%s</b>" %res_l[0][49:58].strip()
    }
    s = s_blank%d

    g = glob.glob(os.sep.join([OV.StrDir(), "temp", "*.res"]))
    i = 0
    for item in g:
      short_p = ntpath.basename(item)
      if len(g) == 1:
        s = "<tr><td>ShelXT returned one solution: %s</td></tr>" %short_p
        break
      hkl = olx.file.ChangeExt(item, 'hkl')

      sg = "<b>%s</b>" %(res_l[i+1][37:50].strip())
      href = '''
<a href="file.copy('%s','%s.res')>>file.copy('%s','%s.hkl')>>reap %s">%s</a>''' %(item, OV.FileName(), hkl, OV.FileName(), OV.FileFull(), sg)

      orientation = res_l[i+1][21:37].strip()
      flack = res_l[i+1][50:58].strip()
      R1 = res_l[i+1][0:6].strip()
      Rweak = res_l[i+1][7:12].strip()
      Alpha = res_l[i+1][13:20].strip()

      if not flack:
        flack = "---"

      else:
        try:
          if 0.4 < float(flack) < 0.6:
            flack = "<font color='red'>%s</font>" %flack
          elif -0.1 < float(flack) < 0.1:
            flack = "<font color='green'>%s</font>" %flack
          elif float(flack) < -0.2:
            flack = "<font color='red'>%s</font>" %flack
        except:
          flack = "---"

      d = {
        'td1':"%s" %R1,
        'td2':"%s" %Rweak,
        'td3':"%s" %Alpha,
        'td4':"%s" %orientation,
        'td5':"<b>%s</b>" %href,
        'td6':"%s" %flack
      }

      s += s_blank %d
      i += 1
    RunPrgObject.post_prg_output_html_message = s
    olex.m('delins list')
    olex.m('addins list 4')

class Method_shelx_direct_methods(Method_shelx_solution):

  def post_solution(self, RunPrgObject):
    Method_shelx_solution.post_solution(self, RunPrgObject)
    self.get_XS_TREF_solution_indicators(RunPrgObject)

    if not OV.HasGUI():
      return
    import gui.tools
    debug = bool(OV.GetParam('olex2.debug',False))
    RunPrgObject.post_prg_output_html_message = "Ralpha=%s, Nqual=%s, CFOM=%s" %(RunPrgObject.Ralpha,RunPrgObject.Nqual,RunPrgObject.CFOM)
    if OV.GetParam('user.solution.run_auto_vss'):
      RunPrgObject.please_run_auto_vss = True

  def get_XS_TREF_solution_indicators(self, RunPrgObject):
    """Gets the TREF solution indicators from the .lst file and prints values in Olex2.
    """
    lstPath = "%s/%s.lst" %(OV.FilePath(), OV.FileName())
    if os.path.exists(lstPath):
      import lst_reader
      lstValues = lst_reader.reader(path=lstPath).values()

      RunPrgObject.Ralpha = lstValues.get('Ralpha','')
      RunPrgObject.Nqual = lstValues.get('Nqual','')
      RunPrgObject.CFOM = lstValues.get('CFOM','')


class Method_shelxd(Method_shelx_solution):

  def calculate_defaults(self):
    """Defines controls in Olex2 for each argument in self.args and then calculates
    sensible default values for PLOP and FIND based on the cell volume.
    """
    Method.calculate_defaults(self) # Define controls in Olex2
    #volume = float(olex.f("Cell(volume)"))
    volume = float(olx.xf.au.GetCellVolume())
    n = int(volume/18) * 0.7
    nmin = int(n * 0.8)
    nmid = int(n * 1.2)
    nmax = int(n * 1.4)

    try:
      OV.SetVar('settings_find_na', nmin)
      OV.SetVar('settings_plop_a', nmin)
      OV.SetVar('settings_plop_b', nmid)
      OV.SetVar('settings_plop_c', nmax)
    except:
      pass

  def extraHtml(self):
    """Makes the HTML for a button to interrupt ShelXD.
    """
    import htmlTools
    button_d = {
      'name':'STOP_DUAL_SPACE',
      'value':'STOP',
      'width':50,
      'height':28,
      'onclick':r'spy.stopShelx()',
    }
    button_html = htmlTools.make_input_button(button_d)
    html = '''
  <tr>%s<td>%s</td></tr>
  ''' %(htmlTools.make_table_first_col(), button_html)
    return html

  def pre_solution(self, RunPrgObject):
    args = Method_shelx_solution.pre_solution(self, RunPrgObject)
    volume = float(olx.xf.au.GetCellVolume())
    n = int(volume/18) * 0.7
    nmin = int(n * 0.8)
    nmax = int(n * 1.2)
    nmaxx = int(n * 1.4)
    if 'FIND' not in args:
      args += 'FIND %i\n' %nmin
    if 'PLOP' not in args:
      args += 'PLOP %i %i %i\n' %(nmin, nmax, nmaxx)
    if 'MIND' not in args:
      args += 'MIND 1 -0.1\n'
    if 'NTRY' not in args:
      args += 'NTRY 100\n'
    return args

  def do_run(self, RunPrgObject):
    """Makes Olex listen to the temporary directory before running the executable
    so that intermediate solutions will be displayed onscreen.
    """
    listen_file = '%s/%s.res' %(RunPrgObject.tempPath,RunPrgObject.hkl_src_name)
    OV.Listen(listen_file)
    Method_shelx_solution.do_run(self, RunPrgObject)

  def post_solution(self, RunPrgObject):
    """Stops listening to the temporary directory
    """
    olex.m("stop listen")
    Method_shelx_solution.post_solution(self, RunPrgObject)
    for i in xrange(int(olx.xf.au.GetAtomCount())):
      olx.xf.au.SetAtomU(i, "0.06")


shelxs_phil_str = """
esel
  .optional=True
{
  values {
    Emin=1.2
      .type=float
    Emax=5
      .type=float
    dU=0.05
      .type=float
    renorm=.7
      .type=float
    axis=0
      .type=int
  }
  default=False
    .type=bool
}
egen
  .optional=True
{
  values {
    d_min=None
      .type=float
    d_max=None
      .type=float
  }
  default=False
    .type=bool
}
grid
  .optional=True
{
  values {
    sl=None
      .type=float
    sa=None
      .type=float
    sd=None
      .type=float
    dl=None
      .type=float
    da=None
      .type=float
    dd=None
      .type=float
  }
  default=False
    .type=bool
}
command_line
  .optional=False
  .caption='Command line'
{
  values {
    Options=''
      .type=str
  }
  default=True
    .type=bool
}
"""

direct_methods_phil = phil_interface.parse("""
name = 'Direct Methods'
  .type=str
atom_sites_solution=direct
  .type=str
instructions {
  tref {
    values {
      np = 500
        .type=int
      nE = None
        .type=int
      kapscal = None
        .type=float
      ntan = None
        .type=int
      wn = None
        .type=float
    }
    default = True
      .type=bool
  }
  init
    .optional=True
  {
    values {
      nn=None
        .type=int
      nf=None
        .type=int
      s_plus=0.8
        .type=float
      s_minus=0.2
        .type=float
      wr=0.2
        .type=float
    }
    default = False
      .type=bool
  }
  phan
    .optional=True
  {
    values {
      steps = 10
        .type=int
      cool = 0.9
        .type=float
      Boltz = None
        .type=float
      ns = None
        .type=int
      mtpr = 40
        .type=int
      mnqr = 10
        .type=int
    }
    default = False
      .type=bool
  }
  %s
}
""" %shelxs_phil_str, process_includes=True)

shelxt_phil_str = phil_interface.parse("""
name = 'Intrinsic Phasing'
  .type=str
atom_sites_solution=dual
  .type=str
instructions {
  command_line
    .optional=False
    .caption='Command line'
  {
    values {
      Options=''
        .type=str
    }
    default=True
      .type=bool
  }
}
""", process_includes=True)


patterson_phil = phil_interface.parse("""
name = 'Patterson Method'
  .type=str
atom_sites_solution=heavy
  .type=str
instructions {
  patt {
    values {
      nv=None
        .type=int
      dmin=None
        .type=float
      resl=None
        .type=float
      Nsup=None
        .type=int
      Zmin=None
        .type=int
      maxat=None
        .type=int
    }
    default=True
      .type=bool
  }
  vect
    .optional=True
  {
    values {
      X=None
        .type=float
      Y=None
        .type=float
      Z=None
        .type=float
    }
    default=False
      .type=bool
  }
  %s
}
""" %shelxs_phil_str, process_includes=True)

#TEXP na [#] nH [0] Ek [1.5]
texp_phil = phil_interface.parse("""
name = 'Structure Expansion'
  .type=str
atom_sites_solution=heavy
  .type=str
instructions {
  texp {
    values {
      na=1
        .type=int
      nH=1
        .type=int
      Ek=1.5
        .type=float
    }
    default=True
      .type=bool
  }
  tref
  .optional=True
  {
    values {
      np = 500
        .type=int
      nE = None
        .type=int
      kapscal = None
        .type=float
      ntan = None
        .type=int
      wn = None
        .type=float
    }
    default=False
      .type=bool
  }
  esel
  .optional=True
  {
    values {
      Emin=1.2
        .type=float
      Emax=5
        .type=float
      dU=0.05
        .type=float
      renorm=.7
        .type=float
      axis=0
        .type=int
    }
    default=False
      .type=bool
  }
  command_line
    .optional=False
    .caption='Command line'
  {
    values {
      Options=''
        .type=str
    }
    default=True
      .type=bool
  }
}
""", process_includes=True)

dual_space_phil = phil_interface.parse("""
name='Dual Space'
  .type=str
atom_sites_solution=dual
  .type=str
instructions {
  ntry
    .optional=True
  {
    values {
      ntry=100
        .type=int
    }
    default=True
      .type=bool
  }
  find
    .optional=True
  {
    values {
      na=0
        .type=int
      ncy=None
        .type=int
    }
    default=True
      .type=bool
  }
  mind
    .optional=True
  {
    values {
      mdis=1.0
        .type=float
      mdeq=2.2
        .type=float
    }
    default=True
      .type=bool
  }
  plop
    .optional=True
  {
    values {
      a=None
        .type=int
        .caption=1
      b=None
        .type=int
        .caption=2
      c=None
        .type=int
        .caption=3
      d=None
        .type=int
        .caption=4
      e=None
        .type=int
        .caption=5
      f=None
        .type=int
        .caption=6
      g=None
        .type=int
        .caption=7
      h=None
        .type=int
        .caption=8
      i=None
        .type=int
        .caption=9
      j=None
        .type=int
        .caption=10
    }
    default=True
      .type=bool
  }
  command_line
    .optional=False
    .caption='Command line'
  {
    values {
      Options=''
        .type=str
    }
    default=True
      .type=bool
  }
}
""")

shelxl_phil_str = """
plan
  .optional=True
{
  values {
    npeaks=20
      .type=int
    d1=None
      .type=float
    d2=None
      .type=float
  }
  default=True
    .type=bool
}
fmap
  .optional=True
{
  values {
    code=2
      .type=int
    axis=None
      .type=int(value_min=1, value_max=3)
    nl=53
      .type=int
  }
  default=True
    .type=bool
}
temp
  .optional=True
{
  values {
    T=None
      .type=int
  }
  default=False
    .type=bool
}
command_line
  .optional=False
  .caption='Command line'
{
  values {
    Options=''
      .type=str
  }
  default=True
    .type=bool
}
"""

def get_LS_phil():
  return phil_interface.parse("""
  name = 'Least Squares'
    .type=str
  instructions {
    ls
      .caption = 'L.S.'
    {
      name='L.S.'
        .type=str
      values {
        nls=4
          .type=int
        nrf=0
          .type=int
        nextra=0
          .type=int
      }
      default=True
        .type=bool
    }
    %s
    acta
    .optional=True
    {
      values {
        two_theta_full=None
          .caption=2thetafull
          .type=float
      }
      default=False
        .type=bool
    }
  }
    """ %shelxl_phil_str, process_includes=True)

def get_CGLS_phil():
  return phil_interface.parse("""
    name = CGLS
      .type=str
    instructions {
      cgls {
        values {
          nls=4
            .type=int
          nrf=0
            .type=int
          nextra=0
            .type=int
        }
        default=True
          .type=bool
      }
      %s
    }
    """ %shelxl_phil_str, process_includes=True)


def post_solution_html(d):
  if not OV.HasGUI():
    return
  import gui.tools
  debug = bool(OV.GetParam('olex2.debug',False))
  t = gui.tools.TemplateProvider.get_template('program_output', force=debug)%d
  f_name = OV.FileName() + "_solution_output.html"
  OlexVFS.write_to_olex(f_name, t)
  olx.html.Update()
