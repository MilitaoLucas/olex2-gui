from __future__ import division

import os, sys
import olx
import OlexVFS
import time
import math
from cStringIO import StringIO

from PeriodicTable import PeriodicTable
try:
  olx.current_hklsrc
except:
  olx.current_hklsrc = None
  olx.current_hklsrc_mtime = None
  olx.current_reflections = None
  olx.current_mask = None
  olx.current_space_group = None
  olx.current_observations = None

import olex
import olex_core

import time
import cctbx_controller as cctbx_controller
from cctbx import maptbx, miller, uctbx, crystal
from libtbx import easy_pickle, utils

from olexFunctions import OlexFunctions
OV = OlexFunctions()
from scitbx.math import distributions

from History import hist

global twin_laws_d
twin_laws_d = {}

from scitbx.math import continued_fraction
from boost import rational
from cctbx import sgtbx, xray
from cctbx.array_family import flex
import smtbx.utils

import numpy
import itertools
import operator
import fractions
from cctbx_olex_adapter import OlexCctbxAdapter


class twin_rules:
  def __init__(self,space,twin_axis,hkl_rotation,angle,fom,rbasf=[0.5,0.5,0]):
    self.space=space
    self.twin_axis=twin_axis
    self.hkl_rotation=hkl_rotation
    self.angle=angle
    self.fom=fom
    self.rbasf=rbasf



class OlexCctbxTwinLaws(OlexCctbxAdapter):

  def __init__(self):
    #super(OlexCctbxTwinLaws, self).__init__()    
    OV.registerFunction(self.run,True,'twin')
    OV.registerFunction(self.run_from_gui,True,'twin')

  def run_from_gui(self):
    print "Searching for Twin laws..."
    olx.Cursor("busy", "Searching for Twin laws...")
    self.run()
    olx.Cursor()
  
  def run(self): 
    from PilTools import MatrixMaker
    global twin_laws_d

    OlexCctbxAdapter.__init__(self)
    if OV.GetParam('snum.refinement.use_solvent_mask'):
      txt = "Sorry, using solvent masking and twinning is not supported yet."
      print(txt)
      html = "<tr><td></td><td><b>%s</b></td></tr>" %txt
      OV.write_to_olex('twinning-result.htm', html, False)
      OV.UpdateHtml()
      return

    use_image = ""
    MM = MatrixMaker()
    self.twin_laws_d = {}
    law_txt = ""
    l = 0
    self.twin_law_gui_txt = ""
    r_list=[]
    self.filename = olx.FileName()
    
    model = self.xray_structure()
    threshold=0
    hkl_sel_num=50
    hkl,f_calc,f_obs,f_uncertainty,leastSquare=self.get_differences()
    
    rank=numpy.argsort(leastSquare)[::-1]
    hkl_sel = numpy.copy(hkl[rank[:hkl_sel_num],:])

    twin_laws=self.find_twin_laws(hkl,f_calc,f_obs,hkl_sel,model)    
    ordered_twins=sorted(twin_laws,key=lambda x: x.rbasf[1], reverse=False)
    top_twins=ordered_twins[:10]
    lawcount=0
    for i, twin_law in enumerate(top_twins):
      basf=twin_law.rbasf[0]
      r=twin_law.rbasf[1]
      r_diff=twin_law.rbasf[2]
      lawcount += 1
      filename="%s_twin%02d.hkl"%(OV.FileName(), lawcount)
      self.make_hklf5(filename, twin_law.hkl_rotation, hkl, f_obs,f_uncertainty)
      self.twin_laws_d.setdefault(lawcount, {})

      r_no, basf_no, f_data, history = self.run_twin_ref_shelx(twin_law.hkl_rotation.flatten(), basf)
      
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

      txt = [{'txt':"R=%.2f%%, -%.2f%%" %((float(r)*100),(float(r_diff)*100)),
              'font_colour':font_color},
             {'txt':"basf=%s" %str(basf),
              'font_colour':font_color_basf}]
      states = ['on', 'off']
      for state in states:
        image_name, img  = MM.make_3x3_matrix_image(name, twin_law.hkl_rotation.flatten(), txt, state)

      #law_txt += "<zimg src=%s>" %image_name

      self.twin_laws_d[lawcount] = {'number':lawcount,
                                    'law':twin_law.hkl_rotation,
                                    'R1':r,
                                    'BASF':basf,
                                    'law_image':img,
                                    'law_txt':law_txt,
                                    'law_image_name':image_name,
                                    'name':name,
                                    'ins_file':f_data,
                                    'history':history,
                                    }
      l += 1
    #r_list.sort()
    law_txt = ""
    self.twin_law_gui_txt = ""
    i = 0
    html = "<tr><td></td><td>"
    for r, run, basf in r_list:
      i += 1
      image_name = self.twin_laws_d[run].get('law_image_name', "XX")
      use_image = "%son.png" %image_name
      img_src = "%s.png" %image_name
      name = self.twin_laws_d[run].get('name', "XX")
      #href = 'spy.on_twin_image_click(%s)'
      href = 'spy.on_twin_image_click(%s)>>spy.reset_twin_law_img()>>html.Update' %(i,)
      law_txt = "<a href='%s'><zimg src=%s></a>&nbsp;" %(href, image_name)
      self.twin_law_gui_txt += "%s" %(law_txt)
      control = "IMG_%s" %image_name.upper()

      html += '''
<a href='%s' target='Apply this twin law'><zimg name='%s' border="0" src="%s"></a>&nbsp;
    ''' %(href, control, img_src)
    if not use_image:
      return
    html += "</td></tr>"
    p = os.path.join(OV.StrDir(), 'twinning-result.htm')
    with open(p, 'w') as wFile:
      wFile.write(html)
    OV.CopyVFSFile(use_image, "%s.png" %image_name,2)
    #OV.Refresh()
    #if OV.IsControl(control):
    #  OV.SetImage(control,use_image)
    OV.UpdateHtml()
    twin_laws_d = self.twin_laws_d
    import cPickle as pickle
    p = os.path.join(OV.StrDir(), 'twin_laws_d.pickle')
    with open( p, "wb" ) as out:
      pickle.dump( twin_laws_d, out )
    
    
    
#    self.make_gui()

  def run_twin_ref_shelx(self, law, basf):
    #law_ins = ' '.join(str(i) for i in law[:9])
    #print "Testing: %s" %law_ins
    #file_path = olx.FilePath()
    #olx.Atreap("%s/notwin.ins" %file_path, b=True)
    #OV.AddIns("TWIN " + law_ins+" 2")
    #OV.AddIns("BASF %f"%basf)

    #curr_prg = OV.GetParam('snum.refinement.program')
    #curr_method = OV.GetParam('snum.refinement.method')
    #curr_cycles = OV.GetParam('snum.refinement.max_cycles')
    #OV.SetMaxCycles(5)
    #if curr_prg != 'olex2.refine':
    #  OV.set_refinement_program(curr_prg, 'CGLS')
    #OV.File("%s.ins" %self.filename)
    rFile = open(olx.FileFull(), 'r')
    f_data = rFile.readlines()
    rFile.close()
    #OV.SetParam('snum.init.skip_routine','True')

    #OV.SetParam('snum.refinement.program','olex2.refine')
    #OV.SetParam('snum.refinement.method','Gauss-Newton')

#    try:
#      from RunPrg import RunRefinementPrg
#      a = RunRefinementPrg()
#      self.R1 = a.R1
#      self.wR2 = a.wR2
#      his_file = a.his_file
#
#      OV.SetMaxCycles(curr_cycles)
#      OV.set_refinement_program(curr_prg, curr_method)
#    finally:
#      OV.SetParam('snum.init.skip_routine','False')


    #r = olx.Lst("R1")
    #olex_refinement_model = OV.GetRefinementModel(False)
    #if olex_refinement_model.has_key('twin'):
    #  basf = olex_refinement_model['twin']['basf'][0]
    #else:
    #  basf = "n/a"

    return None, None, f_data, None

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
    """
    works out the figure of merit
    """
    q = numpy.zeros((15))
    dcopy = numpy.zeros((numpy.shape(mdisag)[0]))
    fom = 0.0
    bc = 0

    #bad = numpy.rint(hkl)+numpy.rint(v) - hkl
    neighbours = list(itertools.combinations_with_replacement(numpy.arange(-1,2,dtype=numpy.float64),3))
    bad = numpy.zeros((len(neighbours), numpy.shape(mdisag)[0], 3))
    d1s = numpy.zeros((len(neighbours), numpy.shape(mdisag)[0]))
    mdisag_rint = numpy.rint(mdisag)
    for i, neighbour in enumerate(neighbours):
      bad[i,:,:] = numpy.dot(mdisag_rint+neighbour - mdisag, GS.T)
      d1s[i,:] = numpy.sqrt(numpy.sum(bad[i,:,:]*bad[i,:,:], axis=1))

    neighbours_min = numpy.zeros((numpy.shape(mdisag)[0], 3), dtype=numpy.float64)
    for i in range(numpy.shape(mdisag)[0]):
      neighbours_min[i,:] = bad[numpy.argmin(d1s[:,i]),i,:]
      
    bad_min = numpy.dot(mdisag_rint+neighbours_min - mdisag, GS.T)
    d_min = numpy.sqrt(numpy.sum(bad_min*bad_min, axis=1))      
    
    dcopy = numpy.copy(d_min)
    dsum = numpy.sum(dcopy)
    
    for i, q_i in enumerate(q):
      q[i]=dsum/(float(numpy.shape(mdisag)[0])-float(bc))
      fom=q[i]
      if (fom<.002):
        break
      else:
        bc+=1
        jp = numpy.argmax(dcopy)         
        dsum = dsum - dcopy[jp]
        dcopy[jp] = 0.

    fom=1000.*fom
    q=1000.0*q      
    
    return fom
    

  def get_differences(self):
    """;
    Returns the hkl, fcalc, fobs, uncertainty and the signed difference
    """
    fot,fct=self.get_fo_sq_fc()
    weights = self.compute_weights(fot, fct)
    scale_factor = fot.scale_factor(fct, weights=weights)
    fot = fot.apply_scaling(factor=1/(scale_factor))
    leastSquare = (fot.data()-fct.norm().data())/fot.sigmas()
    hkl=numpy.array(fot.indices())
    fobs=numpy.array(fot.data())
    fcalc=numpy.array(fct.norm().data())
    funcertainty=numpy.array(fot.sigmas())
    leastSquare=numpy.array(leastSquare)

    return hkl,fcalc,fobs,funcertainty,leastSquare

  def getMetrical(self, model):
    gl=model.unit_cell().metrical_matrix()
    g = numpy.zeros((3,3))
    for i in range(3):
      g[i,i] = gl[i]
    g[0,1] = gl[3]
    g[0,2] = gl[4]
    g[1,2] = gl[5]
    g[1,0] = gl[3]
    g[2,0] = gl[4]
    g[2,1] = gl[5]
    return g

  def find_twin_laws(self,hkl_all,f_calc,f_obs, hkl, model):
    always_basf=True
    do_long=False
    do_very_long=False
    number_laws=4
    twin_laws=[]
    cctbx_twin_laws = cctbx_controller.twin_laws(self.reflections)

    for twin_law in cctbx_twin_laws:
      law = twin_law.as_double_array()[0:9]
      law=numpy.around(numpy.reshape(numpy.array(law),(3,3)),decimals=3)
      #basf1, r1 = self.basf_estimate(law, hkl_all, f_calc, f_obs)
      [basf, r,r_diff]=self.basf_quicker_integral(law, hkl_all, f_calc, f_obs)
      if(basf<0.1):
        continue
      twin_laws+=[twin_rules("Integral",[],law,0,0,[basf,r,r_diff])]

      
    if twin_laws:
      print ("Found Integral Twins")
      if len(twin_laws)>number_laws:
        return twin_laws
      else:
        print ("Few Integral twin laws, investigating twofold non-integral twin laws")
    else:
      print ("No Integral twin laws, investigating twofold non-integral twin laws")
    
    rotation_fraction=2
    size=5
    threshold=0.002

    twin_laws+=self.find_twin_axes(hkl,model,threshold,size,rotation_fraction)
    #if twin_laws:
    #  if always_basf:
    #    for twin_law in twin_laws:
    #      rbasf=self.basf_estimate(twin_law.hkl_rotation, hkl_all, f_calc, f_obs)       
    #      twin_law.rbasf=rbasf
    #  return twin_laws
    if not twin_laws:
      print ("No Highly likely twofold axes, rotation fraction increased")
      olx.Refresh()
      rotation_fraction=24
      twin_laws=self.find_twin_axes(hkl,model,threshold,size,rotation_fraction)

    if (not twin_laws) and do_long:
      print ("No Highly likely low-index axes, indexes and threshold increased")
      olx.Refresh()
      size=12
      threshold=0.01
      twin_laws=self.find_twin_axes(hkl,model,threshold,size,rotation_fraction)

    if (not twin_laws) and do_very_long:
      print ("No Likely axes, threshold increased. Note these twin laws are unlikely to provide improvement")
      olx.Refresh()
      threshold=1
      twin_laws=self.find_twin_axes(hkl,model,threshold,size,rotation_fraction)
    
    if twin_laws and always_basf:
      for twin_law in twin_laws:
        rbasf=self.basf_estimate(twin_law.hkl_rotation, hkl_all, f_calc, f_obs)       
        twin_law.rbasf=rbasf
    if twin_laws:
      
      olex.m("html.ItemState * 0 tab* 2 tab-tools 1 logo1 1 index-tools* 1 info-title 1")
      olex.m("html.ItemState h2-tools-twinning 1")
      print ("Twin Laws Found - See the Twinning Tab")
      olx.Refresh()
    return twin_laws

  def basf_estimate(self,twin_law,hkl,Fc_sq,Fo_sq):
    basf_lower=0
    basf_upper=1
    max_trials=100
    accuracy=0.01
    hkl_new=numpy.dot(twin_law, hkl.T).T
    num_data=numpy.shape(hkl)[0]
    twin_component=numpy.zeros(num_data)
    
    #the below is an ugly hash at what it should be
    #crystal_symmetry=crystal.symmetry
    fo2,fc = self.get_fo_sq_fc()
    obs=self.observations.detwin(
      fo2.crystal_symmetry().space_group(),
      fo2.anomalous_flag(),
      fc.indices(),
      fc.as_intensity_array().data())
    
    #data_set=self.reflections.f_sq_obs.unique_under_symmetry() #this is a silly attempt just to get the crystal symmetry
    
    for i, hkl_new_i in enumerate(hkl_new): #no real way to bypass this for non-integer hkl due to needing to ignore non-integral hkl
      if(numpy.any(numpy.abs(numpy.rint(hkl_new_i)-hkl_new_i)>0.1)):
        # skip non-integers
        continue
      hkl_new_i=numpy.rint(hkl_new_i)
      loc=numpy.where((hkl[:,0]==hkl_new_i[0]) & (hkl[:,1]==hkl_new_i[1]) & (hkl[:,2]==hkl_new_i[2]))[0]
      #diff = numpy.sum(numpy.abs(hkl_new_i - hkl),axis=1) #diff = numpy.sum(numpy.abs(hkl_new[i,:] - hkl),axis=1)
      #loc = numpy.argmin(diff)
      #if(diff[loc]<0.1):
        # adding contribution from overlap
        #twin_component[loc]=Fc_sq[i]
      if loc:
        twin_component[loc]=Fc_sq[i]
      else:
        index=flex.miller_index()
        index.append(hkl_new_i.astype(int))
        
        #this is a botch to get the symmetry/anomaly correct as I don't understand them
        miller_set=miller.set(crystal_symmetry=fo2.crystal_symmetry(),
              indices=index,
              anomalous_flag=fo2.anomalous_flag())        
        #new_thing=miller.set(crystal_symmetry, index)
        miller_set=miller_set.map_to_asu()
        
        index=miller_set.indices()
        hkl_symmetric=numpy.array(index)[0]
        loc=numpy.where((hkl[:,0]==hkl_symmetric[0]) & (hkl[:,1]==hkl_symmetric[1]) & (hkl[:,2]==hkl_symmetric[2]))[0]
        if loc:
          twin_component[loc]=Fc_sq[i]
        else:
          bad_hkl=hkl_symmetric
        
    
    if numpy.max(twin_component)==0:
      return [0,0.5,0.5]
        
    basf_r=self.find_basf_r(Fo_sq,Fc_sq,twin_component)
    
    return basf_r

  def basf_quicker_integral(self,twin_law,hkl,Fc_sq,Fo_sq): #a quicker version of basf_quicker, specifically for integral twin laws as then we know every hkl is integral
    basf_lower=0
    basf_upper=1
    max_trials=100
    accuracy=0.01
    hkl_new=numpy.rint(numpy.dot(twin_law, hkl.T).T)
    num_data=numpy.shape(hkl)[0]
    twin_component=numpy.zeros(num_data)
    
    for i, hkl_new_i in enumerate(hkl_new): 
      #diff = numpy.sum(numpy.abs(hkl_new[i,:] - hkl),axis=1)
      loc=numpy.where((hkl[:,0]==hkl_new_i[0]) & (hkl[:,1]==hkl_new_i[1]) & (hkl[:,2]==hkl_new_i[2]))[0]
      #loc = numpy.argmin(diff)
      if loc:
        twin_component[loc]=Fc_sq[i]
        
    basf_r=self.find_basf_r(Fo_sq,Fc_sq,twin_component)
    
    return basf_r
      
  def find_basf_r(self,Fo_sq,Fc_sq, twin_component):
    basf_lower=0
    basf_upper=1
    trials=0
    max_trials=100
    accuracy=0.01    
    r_lower=self.r_from_basf(basf_lower,Fo_sq,Fc_sq,twin_component)
    r_upper=self.r_from_basf(basf_upper,Fo_sq,Fc_sq,twin_component)
    r_0=r_lower
    if r_upper>r_lower:
      #prioritise lower over upper basf value
      basf_minimum=basf_lower
      r_minimum=r_lower
    else:
      basf_minimum=basf_upper
      r_minimum=r_upper
    #need to establish a minimum, which could be at 0, before we can employ the golden section search
    while trials<max_trials and basf_upper-basf_lower>accuracy:
      basf_new=basf_lower+2/(3+math.sqrt(5))*(basf_upper-basf_lower)
      r_new=self.r_from_basf(basf_new,Fo_sq,Fc_sq,twin_component)
      if r_new<r_minimum:
        basf_minimum=basf_new
        r_minimum=r_new
        break
      #assumption - it will be less than one of the upper and lower bounds. If it were above both, it's a weird upper-peak which breaks our assumption of a single lower peak.
      elif r_new<=r_upper:
        #we only need to replace the 'upper' value, as the lower one will be the minimum if this is the case (it's not below the minimum and is below the upper)
        basf_upper=basf_new
        r_upper=r_new
      elif r_new<=r_lower:
        basf_lower=basf_new
        r_lower=r_new
      else: 
        print "error: basf midpoint has higher r value. Setting as highest basf"
        basf_upper=basf_new
        r_upper=r_new        
      trials+=1
      
    #this only runs if we have a minimum not at 0 or 1
    while trials<max_trials and basf_upper-basf_lower>accuracy:
      basf_new=basf_lower+basf_upper-basf_minimum
      r_new=self.r_from_basf(basf_new,Fo_sq,Fc_sq,twin_component)
      if r_new<=r_minimum:
        if basf_minimum<basf_new:
          basf_lower=basf_minimum
          r_lower=r_minimum
          basf_minimum=basf_new
          r_minimum=r_new
        elif basf_minimum>basf_new:
          basf_upper=basf_minimum
          r_upper=r_minimum
          basf_minimum=basf_new
          r_minimum=r_new
        else:
          print "basf equivalent, breaking"
          break
      else: #r_new>r_minimum
        if basf_minimum<basf_new:
          basf_upper=basf_new
          r_upper=r_new
        elif basf_minimum>basf_new:
          basf_lower=basf_new
          r_lower=r_new
        else:
          print "basf equivalent, breaking"
          break      
      trials +=1
      
    r_difference=r_0-r_minimum
    
    return [basf_minimum, r_minimum, r_difference]
    

  def r_from_basf(self,basf,Fo_sq,Fc_sq,twin_component):
    fcalc=(1-basf)*Fc_sq+basf*twin_component
    scale = numpy.sum(Fo_sq)/numpy.sum(fcalc)
    fcalc = scale * fcalc
    R = numpy.sum(numpy.abs(numpy.sqrt(numpy.maximum(Fo_sq,0))-numpy.sqrt(fcalc)))/numpy.sum(numpy.sqrt(numpy.maximum(Fo_sq,0)))
    return R
      



  def find_twin_axes(self, hkl, model,threshold,size,rotation_fraction):
    metrical_matrix=self.getMetrical(model)
    metrical_inverse=numpy.linalg.inv(metrical_matrix)
    orthogonalization_matrix=numpy.reshape(numpy.array(model.unit_cell().orthogonalization_matrix()),(3,3))
    orthogonalization_inverse=numpy.linalg.inv(orthogonalization_matrix)
    reciprocal_orthogonalization_matrix=orthogonalization_inverse.T
    reciprocal_orthogonalization_inverse=numpy.linalg.inv(reciprocal_orthogonalization_matrix)
    perfect_reflection_number=math.exp(-13)
    possible_twin_laws=[]

    #angle and the sine and cosine of that, for use in the rotation formula
    base_rotation_angle=2.*math.pi/rotation_fraction

    for twin_axis in itertools.product(numpy.arange(-size,size+1),numpy.arange(-size,size+1),range(size+1)):
          reciprocal_law=False
          #skip inverse axes
          if(twin_axis[2]==0):
            if(twin_axis[1]<0):
              continue
            if(twin_axis[1]==0):
              if(twin_axis[0]<=0):
                continue
          if(fractions.gcd(fractions.gcd(twin_axis[0],twin_axis[1]),twin_axis[2])!=1):
            continue
          
          #using the rodrigues formula to generate the matrices, the O^-1RO for that in lattice coordinates
          rotation_matrix_lattice_base=self.make_lattice_rotation(twin_axis,base_rotation_angle,orthogonalization_matrix,reciprocal_orthogonalization_matrix)
          recip_rot_lat_base=self.make_lattice_rotation(twin_axis,base_rotation_angle,reciprocal_orthogonalization_matrix,reciprocal_orthogonalization_matrix)

          new_hkl=hkl.copy()
          rec_hkl=hkl.copy()

          #this is the rotation matrix in the lattice coordinates! due to quirks and transforming a vector into cartesian space, rotating and
          #transforming back being a O^-1 R O type, we can square and more for 'bigger' angles.
          for r in numpy.arange(1,rotation_fraction): #every part of this loop relies on the previous completing the hkl rotations - this is for efficiency (about 10%)

            #reciprocal axis
            rec_hkl=numpy.dot(rec_hkl,recip_rot_lat_base.T)
            rec_hkl_displacement=self.find_fom(rec_hkl, metrical_inverse) #note to self - these metrical matrices are the same, as they work on reciprocal hkl only.

            #real axis
            new_hkl=numpy.dot(rotation_matrix_lattice_base,new_hkl.T).T #correct
            hkl_displacement=self.find_fom(new_hkl, metrical_inverse)

            if (rec_hkl_displacement<threshold and rec_hkl_displacement>perfect_reflection_number):
              reciprocal_rotation_lattice=numpy.linalg.matrix_power(recip_rot_lat_base,r)
              possible_twin_laws+=[twin_rules("Reciprocal",twin_axis,numpy.around(reciprocal_rotation_lattice,decimals=3),r*base_rotation_angle,rec_hkl_displacement)]
              reciprocal_law=True

            if (hkl_displacement<threshold and hkl_displacement>perfect_reflection_number):
              rotation_matrix_lattice=numpy.linalg.matrix_power(rotation_matrix_lattice_base,r)
              possible_twin_laws+=[twin_rules("Direct",twin_axis,numpy.around(rotation_matrix_lattice,decimals=3),r*base_rotation_angle,hkl_displacement)]

    return possible_twin_laws
  
  def make_lattice_rotation(self, axis, angle,axis_orthog, reciprocal_orthogonalization_matrix):
    cosine_value=math.cos(angle)
    sine_value=math.sin(angle)
    reciprocal_orthogonalization_inverse=numpy.linalg.inv(reciprocal_orthogonalization_matrix)

    axis_cartesian=numpy.dot(axis_orthog,axis)
    axis_unit_cartesian=axis_cartesian/numpy.linalg.norm(axis_cartesian)
    cross_product_matrix=numpy.array([[0,-axis_unit_cartesian[2],axis_unit_cartesian[1]],[axis_unit_cartesian[2],0,-axis_unit_cartesian[0]],[-axis_unit_cartesian[1],axis_unit_cartesian[0],0]],dtype=float)
    matrix=numpy.eye(3)+sine_value*cross_product_matrix+(1-cosine_value)*numpy.linalg.matrix_power(cross_product_matrix,2)
    matrix_lattice=numpy.dot(reciprocal_orthogonalization_inverse,numpy.dot(matrix,reciprocal_orthogonalization_matrix))
    
    return matrix_lattice

  def find_fom(self, falsehkl, metrical):
    hkl_dropped=numpy.floor(falsehkl)
    adjacents=numpy.array([[0,0,0],[1,0,0],[0,1,0],[1,1,0],[0,0,1],[1,0,1],[0,1,1],[1,1,1]])
    distances=numpy.full(numpy.shape(falsehkl)[0],1000)
    for i in numpy.arange(0,8):
      hkl_adjacent=hkl_dropped+adjacents[i]
      displacement=falsehkl-hkl_adjacent
      size=numpy.sqrt(numpy.multiply(displacement,numpy.dot(metrical,displacement.T).T).sum(1))
      distances=numpy.minimum(distances,size)
    sortedDist=numpy.sort(distances)
    filtered=sortedDist[:-15]
    return numpy.average(filtered)
    

  def make_hklf5(self, filename, twin_law, hkl, fo,sigmas):  
    """
    convert hklf4 file to hklf5 file
    """
    #Pulled directly from Pascal's, then edited to generate its own second component hkl, as some files don't have avlues for all
    
    hklf = open(filename,'w')
    hkl_new = numpy.dot(twin_law, hkl.T).T
    rounded_hkl_new=numpy.rint(hkl_new).astype(int)
    
    scale = 99999.99/numpy.max(fo) # keep Fo in the scale of F8.2

    check1=True

    for i, hkl_new_i in enumerate(hkl_new):
      if(numpy.any(numpy.abs(numpy.rint(hkl_new_i)-hkl_new_i)>0.1)):
        hklf.write("%4d%4d%4d%8.2f%8.2f%4d\n"%(hkl[i,0],hkl[i,1], hkl[i,2], fo[i]*scale, sigmas[i]*scale, 1))
        continue
      # looking where is the overlap
      diff = numpy.sum(numpy.abs(hkl_new[i] - rounded_hkl_new[i]))

      if(diff<0.1):
        # adding contribution from overlap
        hklf.write("%4d%4d%4d%8.2f%8.2f%4d\n"%(rounded_hkl_new[i,0],rounded_hkl_new[i,1], rounded_hkl_new[i,2], fo[i]*scale, sigmas[i]*scale, -2))
        hklf.write("%4d%4d%4d%8.2f%8.2f%4d\n"%(hkl[i,0],hkl[i,1], hkl[i,2], fo[i]*scale, sigmas[i]*scale, 1))
      else:
        hklf.write("%4d%4d%4d%8.2f%8.2f%4d\n"%(hkl[i,0],hkl[i,1], hkl[i,2], fo[i]*scale, sigmas[i]*scale, 1))
      
    hklf.write("%4d%4d%4d\n"%(0,0,0))
    hklf.close()
    

def on_twin_image_click(run_number):
  global twin_laws_d
  if not twin_laws_d:
    import cPickle as pickle
    p = os.path.join(OV.StrDir(), 'twin_laws_d.pickle')
    with open (p, "rb") as infile:
      twin_laws_d = pickle.load(infile)
    for number in twin_laws_d:
      law = twin_laws_d[number]
      im = law.get('law_image')
      OlexVFS.save_image_to_olex(im, "IMG_LAW%s"%number)
    
  twin_law = numpy.array(twin_laws_d[int(run_number)]['law'])
  twin_law_rnd = numpy.rint(twin_law)
  basf=float(twin_laws_d[int(run_number)]['BASF'])
  
  twin_str_l = []
  for row in twin_law:
    for ele in row:
      ele = str(ele)
      if ele == "0.0":
        ele = "0"
      elif ele == "-1.0":
        ele = "-1"
      elif ele == "1.0":
        ele = "1"
      twin_str_l.append("%s" %ele)
  twin_str = " ".join(twin_str_l)

  if(numpy.any(numpy.abs(twin_law-twin_law_rnd)>0.05)):
    print "Using twin law: ", twin_str
    # non integral twin law, need hklf5
    OV.DelIns("TWIN")
    olx.HKLF(2)
    OV.DelIns("BASF")
    OV.AddIns("BASF %f"%basf)
    OV.AddIns("'REM TWIN %s'"%twin_str)
    hklname="%s_twin%02d.hkl"%(OV.FileName(), int(run_number))
    OV.HKLSrc(hklname)
  else:
    OV.DelIns("TWIN")
    olx.HKLF(0)
    OV.DelIns("BASF")
    OV.AddIns("BASF %f"%basf)
    OV.AddIns("TWIN %s"%twin_str)
    
  OV.UpdateHtml()
OV.registerFunction(on_twin_image_click)

def reset_twin_law_img():
  global twin_laws_d
  olex_refinement_model = OV.GetRefinementModel(False)
  if olex_refinement_model.has_key('twin'):
    c = olex_refinement_model['twin']['matrix']
    curr_law = []
    for row in c:
      for el in row:
        curr_law.append(el)
    for i in xrange(3):
      curr_law.append(0.0)
    curr_law = tuple(curr_law)

  else:
    curr_law = (1, 0, 0, 0, 1, 0, 0, 0, 1)
  for law in twin_laws_d:
    name = twin_laws_d[law]['name']
    matrix = twin_laws_d[law]['law']
    if curr_law == matrix:
      OV.CopyVFSFile("%son.png" %name, "%s.png" %name,2)
    else:
      OV.CopyVFSFile("%soff.png" %name, "%s.png" %name,2)
  OV.UpdateHtml()
OV.registerFunction(reset_twin_law_img)

OlexCctbxTwinLaws_instance = OlexCctbxTwinLaws()
