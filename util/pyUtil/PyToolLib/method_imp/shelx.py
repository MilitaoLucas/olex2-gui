import os
from Method import Method, Method_refinement, Method_solution
import phil_interface
from olexFunctions import OV
import olex
import olx
import glob
import olex_core
import OlexVFS
import ntpath
import cctbx_olex_adapter as COA

class Method_shelx(Method):

  def do_run(self, RunPrgObject):
    """Runs any SHELX refinement/solution program
    """
    print('STARTING SHELX %s with %s' %(
      RunPrgObject.program.program_type, self.name))
    prgName = olx.file.GetName(RunPrgObject.shelx)
    #olex.m("User '%s'" %RunPrgObject.tempPath)
    olx.User("%s" %RunPrgObject.tempPath)
    xl_ins_filename = RunPrgObject.shelx_alias
# This is super ugly but what can I do?
# This really be a function rather than a separate file but I can not get it to work yet?
    if prgName.split('.')[0].lower() in ('shelxs', 'xs', 'shelxs86', 'shelxs13', 'shelxd', 'xm'):
      lines_in = None
      with open(xl_ins_filename.lower()+'.ins', 'r') as x:
        lines_in = x.readlines()
      lines_out = []
      sfac = []
      unit_idx = None
      for line in lines_in:
        l = line.upper()
        if l.startswith('DISP') or l.startswith('REM'):
          continue
        if l.startswith('SFAC'):
          toks = l.split()
          if len(toks) > 2:
            try: # is expanded SFAC?
              float(toks[2])
              sfac.append(toks[1])
            except:
              sfac += toks[1:]
            continue
        elif l.startswith('UNIT'):
          unit_idx = len(lines_out)
        lines_out.append(line)
      if unit_idx is not None:
        lines_out.insert(unit_idx, 'SFAC ' + ' '.join(sfac) + '\n')
      with open(xl_ins_filename.lower()+'.ins', 'w') as x:
        for l in lines_out:
          x.write(l)
    commands = [xl_ins_filename.lower()]  #This is correct!!!!!!
    #sys.stdout.graph = RunPrgObject.Graph()
    set_thread_n = RunPrgObject.program.name.lower() in ['shelxl', 'xl']#, 'shelxt', 'xt']
    thread_n = OV.GetThreadN()
    if self.command_line_options:
      cmds = self.command_line_options.split()
      if not set_thread_n or thread_n < 1:
        commands += cmds
      else:
        commands += [x for x in cmds if not x.startswith("-t")]
    if set_thread_n and thread_n >= 1:
      commands.append("-t%s" %thread_n)

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
    import gui
    if OV.GetParam("snum.refinement.use_solvent_mask"):
      import cctbx_olex_adapter
      from smtbx import masks
      from libtbx import easy_pickle
      #from iotbx.shelx import hklf
      modified_hkl_path = "%s/%s-mask.hkl" %(OV.FilePath(), OV.FileName())
      
      prg = OV.GetParam("snum.refinement.recompute_mask_before_refinement_prg")
      method = gui.tools.GetMaskInfo.get_masking_method()
      lines, fab_path, fab_origin = gui.tools.GetMaskInfo.get_and_check_mask_origin()
      if not lines and not OV.GetParam('snum.refinement.recompute_mask_before_refinement'):
        print ("The existing solvent mask does not match your masking program")
        return True
      f_mask = None
      # backward compatibility - just in case
      if not OV.HKLSrc() == modified_hkl_path:
        olx.SetVar('snum.masks.original_hklsrc', OV.HKLSrc())
      else:
        olx.SetVar('snum.masks.original_hklsrc', '')
      if OV.GetParam("snum.refinement.recompute_mask_before_refinement") or not os.path.exists(fab_path):
        OV.SetVar('current_mask_sqf', "")
        if OV.HKLSrc() == modified_hkl_path:
          _ = "You can't calculate a mask on an already masked file!"
          OlexVFS.write('mask_notification.htm',_,1)
          raise Exception(_)

        if method == "SQUEEZE":
          olex.m("spy.OlexPlaton(q,.cif)")
          fn = OV.HKLSrc().replace(".", "_sq.")
          if os.path.exists(fn):
            OV.HKLSrc(fn)
          Method_refinement.pre_refinement(self, RunPrgObject)
          return
        #else:
          #if "_sq" in OV.HKLSrc():
            #fn = OV.HKLSrc().replace("_sq.", ".")
            #if not os.path.exists(fn):
              #import shutil
              #shutil.copy2(OV.HKLSrc(), fn)
            #OV.HKLSrc(fn)
        olx.stopwatch.run(COA.OlexCctbxMasks)
        if olx.current_mask.flood_fill.n_voids() > 0:
          f_mask = olx.current_mask.f_mask()
        else:
          _ = "There are no voids!"
          print(_)
          OV.SetParam("snum.refinement.use_solvent_mask", False)
          olex.m('delins ABIN')
          OlexVFS.write_to_olex('mask_notification.htm',_,1)
      if f_mask is not None:
        COA.write_fab(f_mask, fab_path)
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
      'snum.refinement.parson_str' : 'parson',
      'snum.refinement.goof' : "s",
    }
    for k,v in params.items():
      v = olx.Lst(v)
      if v == 'n/a':  v = ""
      OV.SetParam(k, v)
    try:
      hkl_stats = olex_core.GetHklStat()
      data = hkl_stats.get('DataCount', None)
      parameters = float(olx.Lst('param_n'))
      OV.SetParam('snum.refinement.parameters', parameters)
      OV.SetParam('snum.refinement.data', data)
    except:
      OV.SetParam('snum.refinement.parameters', None)
      OV.SetParam('snum.refinement.data', None)

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
    cif.setdefault('_refine_ls_number_parameters', olx.Lst('param_n'))
    cif.setdefault('_refine_ls_number_restraints', olx.Lst('restraints_n'))
    parsons_q = olx.Lst('parson')
    if parsons_q == "n/a":
      cif['_refine_ls_abs_structure_Flack'] = olx.Lst('flack')
    else:
      cif['_refine_ls_abs_structure_Flack'] = parsons_q
    cif.setdefault('_refine_diff_density_max', olx.Lst('peak'))
    cif.setdefault('_refine_diff_density_min', olx.Lst('hole'))
    self.cif = cif

  def observe(self, RunPrgObject):
    import Analysis
    self.observer = Analysis.ShelXL_graph(RunPrgObject.program, RunPrgObject.method)
    OV.registerCallback("procout", self.observer.observe)

  def extraHtml(self):
    html = "<!-- #include shelxl-extra gui/tools/shelxl-extra.htm;1 -->"
    return html

class Method_shelxt(Method_shelx_solution):
  def pre_solution(self, RunPrgObject):
    pass
#    OlexVFS.delete("solution_output.htm")

  def post_solution(self, RunPrgObject):
    if not OV.HasGUI():
      return
    import gui.tools
    debug = OV.IsDebugging()
    f = os.path.join(OV.StrDir(), "temp", OV.FileName() + '.lxt')
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
      for j in range(len(f) -i):
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

    g = glob.glob(os.path.join(OV.StrDir(), "temp", "*.res"))
    i = 0
    for item in g:
      short_p = ntpath.basename(item)
      if len(g) == 1:
        s = "<tr><td>ShelXT returned one solution: %s</td></tr>" %short_p
        break
      hkl = olx.file.ChangeExt(item, 'hkl')

      sg = "<b>%s</b>" %(res_l[i+1][37:50].strip())
      href = '''
<a href="file.copy('%s','%s.res')>>file.copy('%s','%s.hkl')>>reap '%s'">%s</a>''' %(item, OV.FileName(), hkl, OV.FileName(), OV.FileFull(), sg)

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
    olex.m('compaq -a')

class Method_shelx_direct_methods(Method_shelx_solution):

  def post_solution(self, RunPrgObject):
    Method_shelx_solution.post_solution(self, RunPrgObject)
    self.get_XS_TREF_solution_indicators(RunPrgObject)

    if not OV.HasGUI():
      return
    import gui.tools
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
      'onclick':r'spy.stopProcess()',
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
    for i in range(int(olx.xf.au.GetAtomCount())):
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
display = 'Direct'
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
display = 'Intrinsic Phasing'
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
display = 'Patterson'
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
display = 'Structure Expansion'
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
name = 'Dual Space'
  .type=str
display = 'Dual Space'
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
  display = "L.S."
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
    display = CGLS
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
  debug = OV.IsDebugging()
  t = gui.tools.TemplateProvider.get_template('program_output', force=debug)%d
  f_name = OV.FileName() + "_solution_output.html"
  OlexVFS.write_to_olex(f_name, t)
  OV.UpdateHtml()
