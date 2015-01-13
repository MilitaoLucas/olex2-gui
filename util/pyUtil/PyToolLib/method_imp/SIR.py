import os
from Method import Method_solution
import phil_interface
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import olx

class Method_SIR(Method_solution):

  def do_run(self, RunPrgObject):
    from olexsir import Sir

    print 'STARTING %s %s with %s' %(
      RunPrgObject.program.name,
      RunPrgObject.program.program_type, self.name)
    RunPrgObject.solve = True
    sirversion = RunPrgObject.program.versions
    sirfile = "%s.sir"%(OV.FileName())
    filename = OV.FileName()
    Z = float(olx.xf.au.GetZ())
    cell = ''.join(olx.xf.au.GetCell().split(','))
    hklfile = OV.HKLSrc().split(os.sep)[-1]
    contents = ''
    for item in olx.xf.GetFormula('list').split(","):
        item = item.split(":")
        item[1] = int(float(item[1]) * Z)
        contents += "%s %i " %(item[0], item[1])

    oxs = Sir()
    (data, inv, phase) = oxs.getDirectives()

    filein = open(olx.FileFull(),'r')
    filedata = filein.readlines()
    filein.close()
    esd = []
    for line in filedata:
      if 'zerr ' in line.lower():
        esd = line.split()

    if len(esd) > 2:
        del esd[1]
        del esd[0]
        try:
            oxs.setDirectives(errors = ' '.join(esd))
        except TypeError:
            pass

    oxs.setDirectives(cell=cell, SPACEGROUP=olx.xf.au.GetCellSymm(),
            Format='(3i4,2f8.0)', contents=contents, Reflections=hklfile)

    opts = {}
    for instruction in self.instructions():
        if OV.FindValue('settings_%s' %instruction.name) in (True, 'True', 'true'):
            if instruction.name not in ('Gui', 'Data', 'Phase', 'Misc'):
                opts[instruction.name] = True
            for option in self.options(instruction.name):
                value = OV.FindValue('settings_%s_%s'%(instruction.name, option.name))
                if value not in ('', 'None', None):
                    if option.name in ('Fvalues', 'RELAX'):
                        value = str(value)
                        opts[value] = True
                    else:
                        opts[option.name] = value

    if self.name in 'Direct Methods':
      if RunPrgObject.program.name in 'SIR2002' or RunPrgObject.program.name in 'SIR97':
        oxs.setDirectives(Tangent=None)
      else:
        oxs.setDirectives(Tangent=True)
    elif self.name in 'Patterson Method':
        oxs.setDirectives(Patterson=True)

    oxs.setDirectives(**opts)

    if OV.FindValue('settings_Gui') in (True, 'True', 'true'):
        oxs.Gui = True
        print 'Starting with GUI'
    else:
        oxs.Gui = False
        print 'Starting without GUI'

    if oxs.write(filename, data, inv, phase):
        resfile = r"%s/%s.res" %(olx.FilePath(), OV.FileName())
        if os.path.exists(resfile):
          os.remove(resfile)
        oxs.Exec(sirfile, sirversion)
        OV.DeleteBitmap('solve')
        if not os.path.exists(resfile):
          self.sort_out_sir2011_res_file()
#        olx.Atreap(resfile) #No need to reap, it will be reaped anyway!
    else:
        print 'No *.sir File!'

  def sort_out_sir2011_res_file(self):
    import glob
    import shutil
    g = glob.glob(r"%s/*.%s" %(OV.FilePath(), "res"))
    for item in g:
      f = item.split(".res")[0]
      f = "%s.res" %f[:-3]
      shutil.copyfile(item, f)
      os.remove(item)


sir_dm_phil = phil_interface.parse("""
name = 'Direct Methods'
  .type=str
atom_sites_solution=direct
  .type=str
instructions {
  Gui
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Data
  .optional=True
  {
    values {
        Fvalues = *FOSQUARED FOBS
          .type = choice
          .caption = 'F\xc2\xb2/Fo\n'
        RHOMAX = 0.25
          .type = float
        RESMAX = None
          .type = float
        BFACTOR = None
          .type = float
          .caption = 'BFAC'
        SFACTORS = None
          .type = str
          .caption = 'SFAC'
    }
    default=True
      .type=bool
    }
  Phase
  .optional=True
    {
      values {
        SIZE=*None xs s m l xl xxl
          .type = choice
        ITERATION=None
          .type = int
        CYCLE=None
          .type = int
        FRAGMENT=None
          .type = str
          .caption = 'FRAG'
        RESIDUAL=None
          .type = float
          .caption = 'R %'
          }
      default=False
        .type=bool
      }
  Misc
  .optional=True
    {
      values {
        RELAX=*None RELAX UNRELAX
          .type = choice
        NREFLECTION = None
          .type = float
          .caption = 'NREF'
        RECORD = None
          .type = int
        EXPAND = None
          .type = float
        GMIN = None
          .type = float
          }
      default=False
        .type=bool
      }
  Tangent
  .optional=True
  {
    values {
        STRIAL=None
          .type = int
          .caption = 'STRIAL     '
        TRIAL=None
          .type = int
    }
    default=False
      .type=bool
    }
  Cochran
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nquartets
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nolsq
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nosigma
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Electrons
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  }
""")

sir_patt_phil = phil_interface.parse("""
name = 'Patterson Method'
  .type=str
atom_sites_solution=heavy
  .type=str
instructions {
  Gui
  .optional=True
  {
    values {}
    default=True
      .type=bool
    }
  Data
  .optional=True
  {
    values {
        Fvalues = *FOSQUARED FOBS
          .type = choice
          .caption = 'F\xc2\xb2/Fo\n'
        RHOMAX = 0.25
          .type = float
        RESMAX = None
          .type = float
        BFACTOR = None
          .type = float
          .caption = 'BFAC'
        SFACTORS = None
          .type = str
          .caption = 'SFAC'
    }
    default=True
      .type=bool
    }
  Phase
  .optional=True
    {
      values {
        SIZE=*None xs s m l xl xxl
          .type = choice
        ITERATION=None
          .type = int
        CYCLE=None
          .type = int
        FRAGMENT=None
          .type = str
          .caption = 'FRAG'
        RESIDUAL=None
          .type = float
          .caption = 'R %'
          }
      default=False
        .type=bool
      }
  Misc
  .optional=True
    {
      values {
        RELAX=*None RELAX UNRELAX
          .type = choice
        NREFLECTION = None
          .type = float
          .caption = 'NREF'
        RECORD = None
          .type = int
        EXPAND = None
          .type = float
        GMIN = None
          .type = float
          }
      default=False
        .type=bool
      }
  Patterson
  .optional=True
  {
    values {
        PEAKS=None
          .type = int
    }
    default=False
      .type=bool
    }
  Cochran
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nquartets
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nolsq
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nosigma
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Electrons
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  }
""")
