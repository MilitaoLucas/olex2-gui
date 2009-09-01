import sys
import olx
import OlexVFS
import time
from History import *
from my_refine_util import *
from PeriodicTable import PeriodicTable
import olexex
try:
  olx.current_reflection_filename
except:
  olx.current_reflection_filename = None
  olx.current_reflections = None

import olex
#import olex_core
import time
import cctbx_controller as cctbx_controller

from olexFunctions import OlexFunctions
OV = OlexFunctions()


class OlexRefinementModel(object):
  def __init__(self):
    olex_refinement_model = OV.GetRefinementModel(True)
    self._atoms = {}
    self.id_for_name = {}
    asu = olex_refinement_model['aunit']
    for residue in asu['residues']:
      for atom in residue['atoms']:
        i = atom['tag']
        self._atoms.setdefault(i, atom)
        element_type = atom['type']
        name_to_post = str("%s%i" %(element_type, i))
        self.id_for_name.setdefault(name_to_post, atom['aunit_id'])
    self._cell = olex_refinement_model['aunit']['cell']
    self.exptl = olex_refinement_model['exptl']
    self._afix = olex_refinement_model['afix']
    self._model= olex_refinement_model
    #a = self.afix_iterator()
    #r = self.restraint_iterator()

  def iterator(self):
    for i, atom in self._atoms.items():
      name = str(atom['label'])
      element_type = str(atom['type'])
      #name_to_post = str("%s%i" %(element_type, i))
      xyz = atom['crd'][0]
      occu = atom['occu']
      adp = atom.get('adp',None)
      if adp is None:
        uiso = atom.get('uiso')[0]
        u = (uiso,)
      else: u = adp[0]
      if name[:1] != "Q":
        yield name, xyz, occu, u, element_type

  def afix_iterator(self):
    for afix in self._afix:
      mn = afix['afix']
      m, n = divmod(mn, 10)
      pivot = afix['pivot']
      dependent = afix['dependent']
      pivot_neighbours = [i for i in self._atoms[pivot]['neighbours'] if not i in dependent]
      bond_length = afix['d']
      uiso = afix['u']
      yield m, n, pivot, dependent, pivot_neighbours, bond_length

  def restraint_iterator(self):
    for restraint_type in ('dfix','dang','flat','chiv'):
      for restraint in self._model[restraint_type]:
        kwds = dict(
          i_seqs = [i[0] for i in restraint['atoms']],
          sym_ops = [i[1] for i in restraint['atoms']],
          value = restraint['value'],
          weight = 1/math.pow(restraint['esd1'],2),
        )
        yield restraint_type, kwds

  def getCell(self):
    return [self._cell[param][0] for param in ('a','b','c','alpha','beta','gamma')]


class OlexCctbxAdapter(object):
  def __init__(self):
    if OV.HasGUI():
      sys.stdout.refresh = True
    self._xray_structure = None
    self.olx_atoms = OlexRefinementModel()
    try:
      self.initialise_reflections()
    except Exception, err:
      print err
      return

  def __del__(self):
    sys.stdout.refresh = False

  def xray_structure(self):
    if self._xray_structure is not None:
      return self._xray_structure
    else:
      return cctbx_controller.create_cctbx_xray_structure(
        self.cell,
        self.space_group,
        self.olx_atoms.iterator(),
        restraint_iterator=self.olx_atoms.restraint_iterator())

  def initialise_reflections(self):
    self.cell = self.olx_atoms.getCell()
    self.space_group = str(olx.xf_au_GetCellSymm())
    reflections = olx.HKLSrc()
    if reflections != olx.current_reflection_filename:
      olx.current_reflection_filename = reflections
      olx.current_reflections = cctbx_controller.reflections(self.cell, self.space_group, reflections)
    if olx.current_reflections:
      self.reflections = olx.current_reflections
    else:
      try:
        olx.current_reflections = cctbx_controller.reflections(self.cell, self.space_group, reflections)
      except Exception, err:
        print err
      self.reflections = olx.current_reflections

  def post_peaks(self, fft_map):
    from cctbx import maptbx
    from  libtbx.itertbx import izip
    fft_map.apply_volume_scaling()
    peaks = fft_map.peak_search(
      parameters=maptbx.peak_search_parameters(
	peak_cutoff=0.1,
	min_distance_sym_equiv=1.0,
	max_clusters=30,
	),
      verify_symmetry=False
      ).all()
    
    i = 0
    for xyz, height in izip(peaks.sites(), peaks.heights()):
      if i < 3:
        if self.verbose: print "Position of peak %s = %s, Height = %s" %(i, xyz, height)
      i += 1
      id = olx.xf_au_NewAtom("%.2f" %(height), *xyz)
      #if olx.xf_au_SetAtomCrd(id, *xyz)=="true":
      if id != '-1':
        olx.xf_au_SetAtomU(id, "0.06")
      if i == 100:
        break
    olx.xf_EndUpdate()
    olx.Compaq('-a')
    olx.Refresh()
    #olx.Compaq()

class OlexCctbxRefine(OlexCctbxAdapter):
  def __init__(self, max_cycles=None, verbose=False):
    OlexCctbxAdapter.__init__(self)
    self.verbose = verbose
    PT = PeriodicTable()
    self.pt = PT.PeriodicTable()
    self.olx = olx
    self.cycle = 0
    self.tidy = True
    self.auto = True
    self.debug = False
    self.film = False
    self.max_cycles = max_cycles * 10
    self.do_refinement = True
    if OV.HasGUI() and OV.GetParam('snum.refinement.graphical_output'):
      import Analysis
      self.plot = Analysis.smtbx_refine_graph()
    else: self.plot = None

  def run(self):
    t0 = time.time()
    olx.Kill('$Q')
    print "++++ Refining using the CCTBX with a maximum of %i cycles++++" %self.max_cycles
    #self.do_refinement = False
    self.refine_with_cctbx()
    try:
      self.post_peaks(self.refinement.f_obs_minus_f_calc_map(0.4))
    except Exception, err:
      print err
    try:  
      self.R1 = self.refinement.r1()
      OV.SetVar('cctbx_R1',self.R1)
    except Exception, err:
      print err

    #cctbxmap_type = 'None'
    #cctbxmap_resolution = 0.4
    #try:
      #cctbxmap_type = OV.FindValue('snum_cctbx_map_type')
      #if cctbxmap_type == "--":
        #cctbxmap_type = None
      #else:
        #cctbxmap_resolution = float(olx.GetValue('snum_cctbxmap_resolution'))
    #except:
      #pass

    olx.Compaq()
    #if cctbxmap_type and cctbxmap_type !='None': 
      #self.write_grid_file(cctbxmap_type, cctbxmap_resolution)

    dt = time.time() - t0
    print "++++ Finished in %.3f s" %dt
    #print "++++ Refine in XL with L.S.0"
    #olex.m('refine 0')
    filename = olx.FileName()
    olx.File('%s.res' %filename)
    print "Done."

  def refine_with_cctbx(self):
    lambda_ = self.olx_atoms.exptl.get('radiation', 0.71073)
    self.refinement = cctbx_controller.refinement(
      f_sq_obs=self.reflections.f_sq_obs,
      xray_structure=self.xray_structure(),
      lambda_=lambda_,
      max_cycles=self.max_cycles)
    self.refinement.on_cycle_finished = self.feed_olex
    self.cycle += 1
    try:
      self.update_refinement_info("Starting...")
      self.refinement.start()
      R1 = self.refinement.r1()
    except Exception,err:
      print err
      if self.cycle < self.max_cycles:
        if self.do_refinement:
          self.refine_with_cctbx()

  def feed_olex(self, structure, minimiser):
    self.auto = False
    self.cycle += 1
    msg = "Refinement Cycle: %i" %(self.cycle-1)
    print msg
    
    self.update_refinement_info(msg=msg)
    
    if self.film:
      n = str(self.cycle)
      if int(n) < 10:
        n = "0%s" %n
      olx.Picta(r"%s0%s.bmp 1" %(self.film, n))
    reset_refinement = False
    ## Feed Model
    u_total  = 0
    u_atoms = []
    i = 1
    for name, xyz, u, ueq, symbol in self.refinement.iter_scatterers():
      if len(u) == 6:
        u_trans = (u[0], u[1], u[2], u[5], u[4], u[3])
      else:
        u_trans = u
      id = self.olx_atoms.id_for_name[name]
      olx.xf_au_SetAtomCrd(id, *xyz)
      olx.xf_au_SetAtomU(id, *u_trans)
      u_total += u[0]
      if self.tidy:
        if u[0] > 0.09:
          #reset_refinement = True
          olx.Name("%s Q" %name)
      u_average = u_total/i

    if reset_refinement:
      raise Exception("Atoms with SillyU Deleted")

    if self.auto:
      for name, xyz, u, symbol in self.refinement.iter_scatterers():
        if symbol == 'H': continue
        id = self.olx_atoms.id_for_name[name]
        selbst_currently_present = curr_formula.get(symbol, 0)
        #print name, u[0]
        if u[0] < u_average * 0.8:
#          print "  ------> PROMOTE?"
          promote_to = element_d[symbol].get('+1', symbol)
          currently_present = curr_formula.get(promote_to, 0)
          max_possible = element_d[promote_to].get('max_number')
          if self.debug: olx.Sel(name)
          if self.debug: print "Promote %s to a %s. There are %.2f present, and  %.2f are allowed" %(name, promote_to, currently_present, max_possible),
          if currently_present < max_possible:
            olx.xf_au_SetAtomlabel(id, promote_to)
            curr_formula[promote_to] = currently_present + 1
            curr_formula[symbol] = selbst_currently_present - 1
            if self.debug: print " OK"
          else:
            if self.debug: print " X"
        if u[0] > u_average * 1.5:
#          print "  DEMOTE? <-------"
          #reset_refinement = True
          demote_to = element_d[symbol].get('-1', symbol)
          currently_present = curr_formula.get(demote_to, 0)
          max_possible = element_d[demote_to].get('max_number')
          if self.debug: olx.Sel(name)
          if self.debug: print "Demote %s to a %s. There are %.2f present, and %.2f are allowed" %(name, demote_to, currently_present, max_possible),
          if curr_formula.get(demote_to, 0) < element_d[demote_to].get('max_number'):
            olx.xf_au_SetAtomlabel(id, demote_to)
            curr_formula[demote_to] = currently_present + 1
            curr_formula[symbol] = selbst_currently_present - 1
            if self.debug: print "OK"
          else:
            if self.debug: print " X"
    olx.Sel('-u')
    olx.xf_EndUpdate()
    if reset_refinement:
      raise Exception("Atoms promoted")

  def update_refinement_info(self, msg="Unknown"):
    txt = "Last refinement with <b>smtbx-refine</b>: No refinement info available yet.<br>Status: %s" %msg
    OlexVFS.write_to_olex('refinedata.htm', txt)

  def write_grid_file(self, type, resolution):
    import olex_xgrid
    if type == "DIFF":
      m = self.refinement.get_difference_map(resolution)
    elif type == "FOBS":
      m = self.refinement.get_f_obs_map(resolution)
    else:
      return
    s = m.last()
    olex_xgrid.Init(s[0], s[1], s[2])
    for i in range (s[0]-1):
      for j in range (s[1]-1):
        for k in range (s[2]-1):
          olex_xgrid.SetValue( i,j,k,m[i,j,k])
    olex_xgrid.InitSurface(True)


class OlexCctbxSolve(OlexCctbxAdapter):
  def __init__(self):
    OlexCctbxAdapter.__init__(self)
    self.peak_normaliser = 1200 #fudge factor to get cctbx peaks on the same scale as shelx peaks

  def runChargeFlippingSolution(self, hkl_path, verbose='highly', solving_interval=60):
    import time
    t1 = time.time()
    from smtbx.ab_initio import charge_flipping
    from cctbx import maptbx
    from  libtbx.itertbx import izip
    try:
      from crys3d import wx_map_viewer
    except ImportError:
      wx_map_viewer = None
      
    t2 = time.time()
    print 'imports took %0.3f ms' %((t2-t1)*1000.0)
    # Get the reflections from the specified path
    f_obs = self.reflections.f_obs
    data = self.reflections.f_sq_obs

    # merge them (essential!!)
    merging = f_obs.merge_equivalents()
    f_obs = merging.array()
    f_obs.show_summary()

    # charge flipping iterations
    if OV.HasGUI():
      sys.stdout.refresh = True
    flipping = charge_flipping.basic_iterator(f_obs, delta=None)
    solving = charge_flipping.solving_iterator(
      flipping,
      yield_during_delta_guessing=True,
      yield_solving_interval=solving_interval)
    charge_flipping_loop(solving, verbose=verbose)
    sys.stdout.refresh = False

    # play with the solutions
    expected_peaks =  data.unit_cell().volume()/18.6/len(data.space_group())
    expected_peaks *= 1.3
    if solving.f_calc_solutions:
      # actually only the supposedly best one
      f_calc, shift, cc_peak_height = solving.f_calc_solutions[0]
      fft_map = f_calc.fft_map(
          symmetry_flags=maptbx.use_space_group_symmetry)
      # 3D display of the electron density iso-contours
      if wx_map_viewer is not None:
        wx_map_viewer.display(fft_map)
      # search and print Fourier peaks
      peaks = fft_map.peak_search(
        parameters=maptbx.peak_search_parameters(
          min_distance_sym_equiv=1.0,
          max_clusters=expected_peaks,),
        verify_symmetry=False
        ).all()
      for q,h in izip(peaks.sites(), peaks.heights()):
        yield q,h
    else:
      print "*** No solution found ***"

  def post_single_peak(self, xyz, height, cutoff=1.0, auto_assign=False):
    if height/self.peak_normaliser < cutoff:
      return
    sp = (height/self.peak_normaliser)
     
    if not auto_assign:
      id = olx.xf_au_NewAtom("%.2f" %(sp), *xyz)
      #if olx.xf_au_SetAtomCrd(id, *xyz)=="true":
      if id != '-1':
        olx.xf_au_SetAtomU(id, "0.06")
    else:
      max_Z = 0
      for element in auto_assign:
        Z = self.pt[element].get('Z', 0)
        if self.pt[element].get('Z', 0) > max_Z: max_Z = Z
      please_assign = False
      for element in auto_assign:
        if element == "H":
          continue
        Z = self.pt[element].get('Z', 0)
        if (sp-sp*0.1) < Z < (sp + sp*0.1):
          please_assign = True
          break
        elif sp > Z and Z == max_Z:
          please_assign = True
          break
      if please_assign:
        id = olx.xf_au_NewAtom(element, *xyz)
        #olx.xf_au_SetAtomCrd(id, *xyz)
        #olx.xf_au_SetAtomOccu(id, 1)
        auto_assign[element]['count'] -= 1
        if auto_assign[element]['count'] == 0:
          del auto_assign[element]
          return
      else:
        if sp > 2:
          id = olx.xf_au_NewAtom("C", *xyz)
          #olx.xf_au_SetAtomCrd(id, *xyz)
          return
      id = olx.xf_au_NewAtom("%.2f" %(sp), *xyz)
      #if olx.xf_au_SetAtomCrd(id, *xyz)=="true":
      if id != '-1':
        olx.xf_au_SetAtomU(id, "0.06")


class OlexCctbxGraphs(OlexCctbxAdapter):
  def __init__(self, graph, n_bins=None):
    OlexCctbxAdapter.__init__(self)
    self.graph = graph
    self.n_bins = n_bins

  def run(self):
    bitmap = 'working'

    if self.graph == "wilson":
      wilson = cctbx_controller.wilson_statistics(self.xray_structure(), self.reflections, self.n_bins)
      return wilson

    elif self.graph == "completeness":
      completeness = cctbx_controller.completeness_statistics(self.reflections, self.n_bins)
      return completeness

    elif self.graph == "cumulative":
      cumulative_distribution = cctbx_controller.cumulative_intensity_distribution(self.reflections, self.n_bins)
      return cumulative_distribution

    elif self.graph == "f_obs_f_calc":
      f_obs_f_calc = cctbx_controller.f_obs_vs_f_calc(self.xray_structure(), self.reflections)
      return f_obs_f_calc

    elif self.graph == "sys_absent":
      return cctbx_controller.sys_absent_intensity_distribution(self.reflections)

    #elif self.fun == "reflection_stats":
      #cctbx_controller.reflection_statistics(stt(olx.xf_au_GetCell()),
                                             #olx.xf_au_GetCellSymm(),
                                             #r"%s/%s" %(olx.FilePath(), olx.FileName()))
    else:
      pass
    OV.DeleteBitmap('%s' %(bitmap))

class OlexCctbxTwinLaws(OlexCctbxAdapter):
  
  def __init__(self):
    OlexCctbxAdapter.__init__(self)
    self.run()

  def run(self):
    from PilTools import MatrixMaker
    a = MatrixMaker()
    twin_laws = cctbx_controller.twin_laws(self.reflections)
    r_list = []
    l = 0
    self.twin_law_gui_txt = ""
    if not twin_laws:
      print "There are no possible twin laws"
      
      html = "<tr><td></td><td>"
      html += "<b>%There are no possible Twin Laws%</b>"
      OV.write_to_olex('twinning-result.htm', html, False)
      OV.htmlReload()
      return
    
    lawcount = 0
    self.twin_laws_d = {}
    law_txt = ""
    self.run_backup_shelx()
    twin_double_laws = [(1, 0, 0, 0, 1, 0, 0, 0, 1)]
    for twin_law in twin_laws:
      law_double = twin_law.as_double_array()
      twin_double_laws.append(law_double)
    for twin_law in twin_double_laws:
      lawcount += 1
      self.twin_laws_d.setdefault(lawcount, {})
      self.twin_law_gui_txt = ""
      r, basf, f_data, history_refinement, history_solution = self.run_twin_ref_shelx(twin_law)
      try:
        float(r)
      except:
        r = 0.99
      r_list.append((r, lawcount, basf))
      name = "law%i" %lawcount
      font_color = "#444444"
      if basf == "n/a":
        font_color_basf = "blue"
      elif float(basf) < 0.1:
        font_color_basf = "red"
        basf = "%.2f" %float(basf)
      else:
        font_color_basf = "green"
        basf = "%.2f" %float(basf)
      txt = [{'txt':"R=%.2f%%" %(float(r)*100),
              'font_colour':font_color}, 
              {'txt':"basf=%s" %str(basf), 
               'font_colour':font_color_basf}]
      image_name, img  = a.make_3x3_matrix_image(name, twin_law, txt)
      #law_txt += "<zimg src=%s>" %image_name
      law_straight = ""
      for x in xrange(9):
        law_straight += " %s" %(law_double)[x]

      self.twin_laws_d[lawcount] = {'number':lawcount, 
                                    'law':twin_law, 
                                    'law_double':law_double, 
                                    'law_straight':law_straight, 
                                    'R1':r, 
                                    'BASF':basf,
                                    'law_image':img,
                                    'law_txt':law_txt,
                                    'law_image_name':image_name,
                                    'name':name,
                                    'ins_file':f_data,
                                    'history_solution':history_solution,
                                    'history_refinement':history_refinement
                                  }
#      href = 'spy.on_twin_image_click(%s)'
#      href = 'spy.revert_history -solution="%s" -refinement="%s"' %(history_solution, history_refinement)
#      law_txt = "<a href='%s'><zimg src=%s></a>&nbsp;" %(href, image_name)
#      self.twin_law_gui_txt += "%s" %(law_txt)
#      self.make_gui()
      l += 1
    r_list.sort()
    law_txt = ""
    self.twin_law_gui_txt = ""
    i = 0
    html = "<tr><td></td><td>"
    for r, run, basf in r_list:
      i += 1
      image_name = self.twin_laws_d[run].get('law_image_name', "XX")
      name = self.twin_laws_d[run].get('name', "XX")
      href = 'spy.on_twin_image_click(%s)'
      href = 'spy.revert_history -solution="%s" -refinement="%s">>HtmlReload' %(self.twin_laws_d[i].get('history_solution'), self.twin_laws_d[i].get('history_refinement'))
      law_txt = "<a href='%s'><zimg src=%s></a>&nbsp;" %(href, image_name)
      self.twin_law_gui_txt += "%s" %(law_txt)
      
      html += '''
<a href='%s' target='Apply this twin law'><zimg border="0" src="%s"></a>&nbsp;
    ''' %(href, image_name)
    html += "</td></tr>"
    OV.write_to_olex('twinning-result.htm', html, False)
    OV.htmlReload()
#    self.make_gui()

  def run_backup_shelx(self):
    self.filename = olx.FileName()
    olx.DelIns("TWIN")
    olx.DelIns("BASF")
    olx.File("notwin.ins")

  def run_twin_ref_shelx(self, law):
    print "Testing: %s" %str(law)
    law_ins = ""
    for i in xrange(9):
      law_ins += " %s" %str(law[i])
    olx.Atreap("-b notwin.ins")
    olx.User("'%s'" %olx.FilePath())
    if law != (1, 0, 0, 0, 1, 0, 0, 0, 1):
      OV.AddIns("TWIN %s" %law_ins) 
      OV.AddIns("BASF %s" %"0.5")
    olx.LS('CGLS 1')
    olx.File("%s.ins" %self.filename)
    rFile = open(olx.FileFull(), 'r')
    f_data = rFile.readlines()
    #prg = OV.GetParam('snum.refinement.program') ## This currently only works with SHELX
    prg = "ShelXL"
    try:
      olx.Exec(r"%s '%s'" %(prg, olx.FileName()))
    except:
      prg = "XL"
      olx.Exec(r"%s '%s'" %(prg, olx.FileName()))
      
    olx.WaitFor('process')
    olx.Atreap(r"-b %s/%s.res" %(olx.FilePath(), olx.FileName()))
    r = olx.Lst("R1")
    basf = olx.Lst("BASF")
    if r != 0:
      res = hist.create_history()
      history_refinement = res.split(";")[1]
      history_solution = res.split(";")[0]
    return r, basf, f_data, history_refinement, history_solution

  def twinning_gui_def(self):
    if not self.twin_law_gui_txt:
      lines = ['search_for_twin_laws']
      tools = ['search_for_twin_laws_t1']
    else:
      lines = ['search_for_twin_laws', 'twin_laws']
      tools = ['search_for_twin_laws_t1', 'twin_laws']

    tbx = {"twinning":
           {"category":'tools',
            'tbx_li':lines
          }
         }

    tbx_li = {'search_for_twin_laws':{"category":'analysis', 
                                      'image':'cctbx', 
                                      'tools':['search_for_twin_laws_t1']
                                      },
                                      'twin_laws':{"category":'analysis', 
                                                   'image':'cctbx', 
                                                   'tools':['twin_laws']
                                                 }																			
                                    }

    tools = {'search_for_twin_laws_t1':{'category':'analysis', 
                                        'display':"%Search for Twin Laws%",
                                        'colspan':1,
                                        'hrefs':['spy.OlexCctbxTwinLaws()']
                                        },
                                        'twin_laws':
                                        {'category':'analysis', 
                                         'colspan':1,
                                         'before':self.twin_law_gui_txt, 
                                       }
                                      }
    return {"tbx":tbx,"tbx_li":tbx_li,"tools":tools}

  def make_gui(self):
    gui = self.twinning_gui_def()
    from GuiTools import MakeGuiTools 
    a = MakeGuiTools(tool_fun="single", tool_param=gui)
    a.run()
    OV.UpdateHtml()
OV.registerFunction(OlexCctbxTwinLaws)


def charge_flipping_loop(solving, verbose=True):
  HasGUI = OV.HasGUI()
  plot = None
  timing = True
  if timing:
    t0 = time.time()
  if HasGUI and OV.GetParam('snum.solution.graphical_output'):
    import Analysis
    plot = Analysis.ChargeFlippingPlot()
  OV.SetVar('stop_current_process',False)

  previous_state = None
  for flipping in solving:
    if OV.FindValue('stop_current_process',False):
      break
    if solving.state is solving.guessing_delta:
      # Guessing a value of delta leading to subsequent good convergence
      if verbose:
        if previous_state is solving.solving:
          print "** Restarting (no phase transition) **"
        elif previous_state is solving.evaluating:
          print "** Restarting (no sharp correlation map) **"
      if verbose == "highly":
        if previous_state is not solving.guessing_delta:
          print "Guessing delta..."
          print "%10s | %10s | %10s | %10s | %10s"\
                % ('delta', 'R', 'c_tot', 'c_flip', 'c_tot/c_flip')
          print "-"*64
        rho = flipping.rho_map
        c_tot = rho.c_tot()
        c_flip = rho.c_flip(flipping.delta)
        # to compare with superflip output
        c_tot *= flipping.fft_scale; c_flip *= flipping.fft_scale
        print "%10.4f | %10.3f | %10.1f | %10.1f | %10.2f"\
              % (flipping.delta, flipping.r1_factor(),
                 c_tot, c_flip, c_tot/c_flip)
        
    elif solving.state is solving.solving:
      # main charge flipping loop to solve the structure
      if verbose=="highly":
        if previous_state is not solving.solving:
          print
          print "Solving..."
          print "with delta=%.4f" % flipping.delta
          print
          print "%5s | %10s | %10s" % ('#', 'R1', 'c_tot/c_flip')
          print '-'*33
        r1 = flipping.r1_factor()
        r = flipping.c_tot_over_c_flip()
        print "%5i | %10.3f | %10.3f" % (solving.iteration_index, r1, r)
        
    elif solving.state is solving.finished:
      break
    
    if plot is not None: plot.run_charge_flipping_graph(flipping, solving, previous_state)
    previous_state = solving.state
  
  if timing:
    print "Total Time: %.2f s" %(time.time() - t0)

def on_twin_image_click(run_number):
  # arguments is a list
  # options is a dictionary
  
  
  a = OlexCctbxTwinLaws()
  file_data = a.twin_laws_d[int(run_number)].get("ins_file")
  wFile = open(olx.FileFull(), 'w')
  wFile.writelines(file_data)
  wFile.close()
  olx.Atreap(olx.FileFull())
  OV.UpdateHtml()
OV.registerFunction(on_twin_image_click)
