import time
import sqlalchemy
import os
import shutil
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

from olexFunctions import OlexFunctions
OV = OlexFunctions()

#datadir = OV.DataDir()
#copy_from_full = False
#db = OV.GetParam('hptools.batch.database')
#p = '%s/%s.sqlite' %(datadir, db)

#if not os.path.exists(p) and db:
  #copy_from_full = True

#if copy_from_full:
  #full_db = '%s/DatabaseRunFull.sqlite' %datadir
  #if os.path.exists(full_db):
    #try:
      #shutil.copyfile(full_db, p)
    #except:
      #pass
#engine = create_engine('sqlite:///%s' %p)

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey    
metadata = MetaData()

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy.orm import relation, backref
from sqlalchemy.orm import column_property

class Structure(Base):
  __tablename__ = 'structures'
  
  ID = Column(String)
  path = Column(String(200), primary_key=True)
  volume = Column(sqlalchemy.FLOAT)
  cell = Column(String(50))
  formula = Column(String(50))
  atom_count = Column(sqlalchemy.FLOAT)
  space_group = Column(String(20))
  z_prime = Column(sqlalchemy.FLOAT)
  r1_original = Column(sqlalchemy.FLOAT)
  ata_original = Column(sqlalchemy.FLOAT)
  max_Z = Column(sqlalchemy.INT)
  twin = Column(String(50))
  
  def __init__(self,
               ID,
               path,
               volume,
               cell,
               formula,
               atom_count,
               space_group,
               z_prime,
               r1_original,
               ata_original,
               max_Z,
               twin,
               ):
    self.ID = ID
    self.path = path
    self.volume= volume
    self.cell = cell
    self.formula = formula
    self.atom_count = atom_count
    self.space_group = space_group
    self.z_prime = z_prime
    self.r1_original = r1_original
    self.ata_original = ata_original
    self.max_Z = max_Z
    self.twin = twin
    
  def __repr__(self):
    return "<Structure('%s(%s'))>" % (self.ID, self.path)

class Reflections(Base):
  __tablename__ = 'reflections'
  
  ID = Column(String)
  path = Column(String(200), primary_key=True)
  r_int = Column(sqlalchemy.FLOAT)
  ios = Column(sqlalchemy.FLOAT)
  completeness = Column(sqlalchemy.FLOAT)
  structure_id = Column(Integer, ForeignKey('structures.ID'))
  structure = relationship("Structure", backref=backref('reflections', order_by=ID))
  
  def __init__(self,
               ID,
               path,
               r_int,
               ios,
               completeness,
               ):
    self.ID = ID
    self.path = path
    self.r_int = r_int
    self.ios = ios
    self.completeness = completeness
    
  def __repr__(self):
    return "<Reflections('%s(%s'))>" % (self.ID, self.path)


class ac2_oda(Base):
  __tablename__ = 'ac2_oda'

  ID = Column(String, primary_key=True)
  path = Column(String(200))
  r1_before = Column(sqlalchemy.FLOAT)
  r1_oda = Column(sqlalchemy.FLOAT)
  r1_ac2 = Column(sqlalchemy.FLOAT)
  ata_before = Column(sqlalchemy.FLOAT)
  ata_oda = Column(sqlalchemy.FLOAT)
  ata_ac2 = Column(sqlalchemy.FLOAT)
  t_oda = Column(sqlalchemy.FLOAT)
  t_ac2 = Column(sqlalchemy.FLOAT)
  solution_name_oda = Column(String)
  solution_name_ac2 = Column(String)
  
  def __init__(self,
               ID,
               path,
               r1_before,
               r1_oda,
               r1_ac2,
               ata_before,
               ata_oda,
               ata_ac2,
               t_oda,
               t_ac2,
               solution_name_oda,
               solution_name_ac2
               ):
    self.ID = ID
    self.path = path
    self.r1_before = r1_before
    self.r1_oda = r1_oda
    self.r1_ac2 = r1_ac2
    self.ata_before = ata_before
    self.ata_oda = ata_oda
    self.ata_ac2 = ata_ac2
    self.t_oda = t_oda
    self.t_ac2 = t_ac2
    self.solution_oda = solution_name_oda
    self.solution_ac2 = solution_name_ac2
    
  def __repr__(self):
    return "<ac2_oda('%s(%s'))>" % (self.ID, self.path)



class ac2(Base):
  __tablename__ = 'ac2'

  ID = Column(String)
  path = Column(String(200), primary_key=True)
  r1_original = Column(sqlalchemy.FLOAT)
  r1_ac2 = Column(sqlalchemy.FLOAT)
  ata_original = Column(sqlalchemy.FLOAT)
  ata_ac2 = Column(sqlalchemy.FLOAT)
  solution_ac2 = Column(String)
  time_ac2 = Column(sqlalchemy.FLOAT)
  achieved_ac2 = Column(String)
  formula_ac2 = Column(String)
  match_ac2 = Column(String)
  
  def __init__(self,
               ID,
               path,
               r1_original,
               r1_ac2,
               ata_original,
               ata_ac2,
               solution_ac2,
               time_ac2,
               achieved_ac2,
               formula_ac2,
               match_ac2,
               ):
    self.ID = ID
    self.path = path
    self.r1_original = r1_original
    self.r1_ac2 = r1_ac2
    self.ata_original = ata_original
    self.ata_ac2 = ata_ac2
    self.solution_ac2 = solution_ac2
    self.time_ac2 = time_ac2
    self.achieved_ac2 = achieved_ac2
    self.formula_ac2 = formula_ac2
    self.match_ac2 = match_ac2
    
  def __repr__(self):
    return "<ac2('%s(%s'))>" % (self.ID, self.path)


class ac2_1(Base):
  __tablename__ = 'ac2_1'

  ID = Column(String)
  path = Column(String(200), primary_key=True)
  r1_original = Column(sqlalchemy.FLOAT)
  r1_ac2_1 = Column(sqlalchemy.FLOAT)
  ata_original = Column(sqlalchemy.FLOAT)
  ata_ac2_1 = Column(sqlalchemy.FLOAT)
  solution_ac2_1 = Column(String)
  time_ac2_1 = Column(sqlalchemy.FLOAT)
  achieved_ac2_1 = Column(String)
  formula_ac2_1 = Column(String)
  match_ac2_1 = Column(String)
  
  def __init__(self,
               ID,
               path,
               r1_original,
               r1_ac2_1,
               ata_original,
               ata_ac2_1,
               solution_ac2_1,
               time_ac2_1,
               achieved_ac2_1,
               formula_ac2_1,
               match_ac2_1,
               ):
    self.ID = ID
    self.path = path
    self.r1_original = r1_original
    self.r1_ac2_1 = r1_ac2_1
    self.ata_original = ata_original
    self.ata_ac2_1 = ata_ac2_1
    self.solution_ac2_1 = solution_ac2_1
    self.time_ac2_1 = time_ac2_1
    self.achieved_ac2_1 = achieved_ac2_1
    self.formula_ac2_1 = formula_ac2_1
    self.match_ac2_1 = match_ac2_1
    
  def __repr__(self):
    return "<ac2('%s(%s'))>" % (self.ID, self.path)



class oda(Base):
  __tablename__ = 'oda'

  ID = Column(String, primary_key=True)
  path = Column(String(200))
  r1_original = Column(sqlalchemy.FLOAT)
  r1_oda = Column(sqlalchemy.FLOAT)
  ata_original = Column(sqlalchemy.FLOAT)
  ata_oda = Column(sqlalchemy.FLOAT)
  solution_oda = Column(String)
  time_oda = Column(sqlalchemy.FLOAT)
  
  def __init__(self,
               ID,
               path,
               r1_original,
               r1_oda,
               ata_original,
               ata_oda,
               solution_oda,
               time_oda,
               ):
    self.ID = ID
    self.path = path
    self.r1_original = r1_original
    self.r1_oda = r1_oda
    self.ata_original = ata_original
    self.ata_oda = ata_oda
    self.solution_oda = solution_oda
    self.time_oda = time_oda
    
  def __repr__(self):
    return "<oda('%s(%s'))>" % (self.ID, self.path)


class ODAC(Base):
  __tablename__ = 'odac'
  
  ID = Column(String, primary_key=True)
  path = Column(String(200))
  ShelXS_r1_before = Column(sqlalchemy.FLOAT)
  ShelXS_r1_after = Column(sqlalchemy.FLOAT)
  ShelXS_t = Column(sqlalchemy.FLOAT)
  olex2solve_r1_before = Column(sqlalchemy.FLOAT)
  olex2solve_r1_after = Column(sqlalchemy.FLOAT)
  olex2solve_t = Column(sqlalchemy.FLOAT)
  SIR2008_r1_before = Column(sqlalchemy.FLOAT)
  SIR2008_r1_after = Column(sqlalchemy.FLOAT)
  SIR2008_t = Column(sqlalchemy.FLOAT)
  g4_r1_before = Column(sqlalchemy.FLOAT)
  g4_r1_after = Column(sqlalchemy.FLOAT)
  g4_t = Column(sqlalchemy.FLOAT)
  
  def __init__(self,
               ID,
               path,
               ShelXS_r1_before,
               ShelXS_r1_after,
               ShelXS_t,
               olex2solve_r1_before,
               olex2solve_r1_after,
               olex2solve_t,
               SIR2008_r1_before,
               SIR2008_r1_after,
               SIR2008_t,
               g4_r1_before,
               g4_r1_after,
               g4_t,
               ):
    self.ID = ID
    self.path = path
    self.ShelXS_r1_before = ShelXS_r1_before
    self.ShelXS_r1_after = ShelXS_r1_after
    self.ShelXS_t = ShelXS_t
    self.olex2solve_r1_before = olex2solve_r1_before
    self.olex2solve_r1_after = olex2solve_r1_after
    self.olex2solve_t = olex2solve_t
    self.SIR2008_r1_before = SIR2008_r1_before
    self.SIR2008_r1_after = SIR2008_r1_after
    self.SIR2008_t = SIR2008_t
    self.g4_r1_before = g4_r1_before
    self.g4_r1_after = g4_r1_after
    self.g4_t = g4_t
    
  def __repr__(self):
    return "<ODAC('%s(%s'))>" % (self.ID, self.r1_after)
  
  def db_commit(self):
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)
    session.commit()
    session.close()
    
  def make_new_db(self):
    self.db_commit()

def get_session(db=None):
  from sqlalchemy.orm import sessionmaker
  if not db:
    return

  p = '%s/%s.sqlite' %(OV.DataDir(), db)
  engine = create_engine('sqlite:///%s' %p)

  Session = sessionmaker(bind=engine)
  session = Session()
  
  Base.metadata.create_all(engine)

  return session

#Structure_instance = Structure()
#OV.registerFunction(Structure_instance.make_new_db)
    