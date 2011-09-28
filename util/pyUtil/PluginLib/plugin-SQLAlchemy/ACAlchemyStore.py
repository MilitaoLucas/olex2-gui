import time
import sqlalchemy
from sqlalchemy import create_engine

from olexFunctions import OlexFunctions
OV = OlexFunctions()

datadir = OV.DataDir()
#engine = create_engine('mysql://localhost/db_test', connect_args = {'user':'DIMAS', 'passwd':'fddd-anode'})
#engine = create_engine('sqlite:///:memory:', echo=False)
engine = create_engine('sqlite:///%s/database.sqlite' %datadir)

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey    
metadata = MetaData()

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy.orm import relation, backref
from sqlalchemy.orm import column_property

class Structure(Base):
  __tablename__ = 'structures'
  
  ID = Column(String, primary_key=True)
  path = Column(String(200))
  volume = Column(sqlalchemy.FLOAT)
  cell = Column(String(50))
  formula = Column(String(50))
  atom_count = Column(Integer)
  space_group = Column(String(20))
  z_prime = Column(sqlalchemy.FLOAT)
  r1_shelxl = Column(sqlalchemy.FLOAT)
  r1_olex2refine = Column(sqlalchemy.FLOAT)
  t_shelxl = Column(sqlalchemy.FLOAT)
  t_olex2refine = Column(sqlalchemy.FLOAT)

  def __init__(self,
               ID,
               path,
               volume,
               cell,
               formula,
               atom_count,
               space_group,
               z_prime,
               r1_shelxl,
               r1_olex2refine,
               t_shelxl,
               t_olex2refine,
               ):
    self.ID = ID
    self.path = path
    self.volume= volume
    self.cell = cell
    self.formula = formula
    self.atom_count = atom_count
    self.space_group = space_group
    self.z_prime = z_prime
    self.r1_shelxl = r1_shelxl
    self.r1_olex2refine = r1_olex2refine
    self.t_shelxl = t_shelxl
    self.t_olex2refine = t_olex2refine
    
  def __repr__(self):
    return "<Structure('%s(%s'))>" % (self.ID, self.path)

class Reflections(Base):
  __tablename__ = 'reflections'
  
  ID = Column(String, primary_key=True)
  path = Column(String(200))
  r_int = Column(sqlalchemy.FLOAT)
  completeness = Column(sqlalchemy.FLOAT)

  def __init__(self,
               ID,
               path,
               r_int,
               completeness,
               ):
    self.ID = ID
    self.path = path
    self.r_int = r_int
    self.completeness = completeness
    
  def __repr__(self):
    return "<Reflections('%s(%s'))>" % (self.ID, self.path)
  
  
  def db_commit(self):
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)
    session.commit()
    session.close()
    
  def make_new_db(self):
    self.db_commit()

def get_session():
  from sqlalchemy.orm import sessionmaker
  Session = sessionmaker(bind=engine)
  session = Session()
  return session


Base.metadata.create_all(engine)

#Structure_instance = Structure()
#OV.registerFunction(Structure_instance.make_new_db)
    