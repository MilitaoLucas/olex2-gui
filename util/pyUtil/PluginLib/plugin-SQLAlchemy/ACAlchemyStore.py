import time
import sqlalchemy
from sqlalchemy import create_engine

from olexFunctions import OlexFunctions
OV = OlexFunctions()

datadir = OV.DataDir()
#engine = create_engine('mysql://localhost/db_test', connect_args = {'user':'DIMAS', 'passwd':'fddd-anode'})
#engine = create_engine('sqlite:///:memory:', echo=False)
engine = create_engine('sqlite:///%s/database.txt' %datadir)

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey    
metadata = MetaData()

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy.orm import relation, backref
from sqlalchemy.orm import column_property

class Structure(Base):
  __tablename__ = 'structures'
  
  ID = Column(Integer, primary_key=True)
  path = Column(String(200))
  volume = Column(sqlalchemy.FLOAT)
  cell = Column(String(50))
  original_R1= Column(sqlalchemy.FLOAT)
  R1 = Column(sqlalchemy.FLOAT)
  dm_nqual = Column(sqlalchemy.FLOAT)
  dm_ralpha = Column(sqlalchemy.FLOAT)
  dm_VSS = Column(sqlalchemy.FLOAT)
  pm_VSS = Column(sqlalchemy.FLOAT)
  ATA = Column(sqlalchemy.FLOAT)
  VSS = Column(sqlalchemy.FLOAT)
  
  def __init__(self,ID,path,volume=None,cell="", origianl_R1=None, R1=None, dm_nqual=None, dm_ralpha=None, dm_VSS=None, pm_VSS=None, ATA=None, VSS=None):
    self.ID = ID
    self.path = path
    self.volume= volume
    self.cell = cell
    self.origianl_R1=origianl_R1
    self.R1=R1
    self.dm_nqual=dm_nqual
    self.dm_ralpha=dm_ralpha
    self.dm_VSS=dm_VSS
    self.pm_VSS=pm_VSS
    self.ATA=ATA
    self.VSS=VSS
    
  def __repr__(self):
    return "<Structure('%s(%s'))>" % (self.ID, self.path)

  def db_commit(self):
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)
    session.commit()
    session.close()
  
  