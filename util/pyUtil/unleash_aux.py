# just a set of utilities, may be for the future :) Oleg

import sys
import os
import time
import zipfile
import shutil

class IndexFile:
    def __init__(self, name, properties, isdir, size, epochTime, parent=None):
        self.name = name
        self.properties = properties
        self.size = size
        self.isdir = isdir
        self.epochTime = epochTime
        self.parent = parent
        self.files = []
    def add(self, name, properties):
        if not self.isdir:
            raise "A folder expected, but file is found"
        #check if not already exists here        
        for file in self.files:
            if file.name == name:
                return file
        full_name = self.getFullName() + name
        names = name.split('/')
        last_dir = self
        for i in range(0, len(names)-1) :
            last_dir = last_dir.add(names[i], None)
        #check if not already exists in the destination
        if last_dir != self:
            file = last_dir._find(names[-1])
            if file:
                return file
        stat = os.stat(full_name)
        i_f = IndexFile(names[-1], properties, os.path.isdir(full_name), stat.st_size, stat.st_mtime, last_dir)
        last_dir.files.append(i_f)
        return i_f
    def getLevel(self):
        level = 0
        p = parent
        while p.parent:
            level += 1
            p = p.parent            
        return level
    def _find(self, name):
        for file in self.files:
            if file.name == name:
                return file
        return None
    def _normaliseName(self):
        if self.isdir:
            return self.name + '/';
        return self.name
    def getFullName(self):
        if not self.parent:
            return self.name + '/';
        nl = [self._normaliseName()]
        p = self.parent
        while p.parent:
            nl.append(p._normaliseName())
            p = p.parent
        nl.append(p._normaliseName()) #root name
        nl.reverse()
        return ''.join(nl)
            
    def toFile(self, out, level=-1):
        for file in self.files:
            file._toFile(out, level+1)
    def _toFile(self, out, level):
        indent = "\t"*level
        print(indent + self.name, file=out)
        if self.properties:
            props = ';'.join(self.properties)
        else:
            props = ''
        print("%s%i,%i,{%s}" %(indent, self.epochTime, self.size, props), file=out)
        self.toFile(out, level)
                 
        
class FileIndex:
    def __init__(self, rootDir):
        self.rootDir = rootDir
        self.root = IndexFile(self.rootDir, None, True, -1, -1)
    def save(self, fileName):
        ind_file = open(fileName, "wb")
        self.root.toFile(ind_file)
        ind_file.close()
    
    
class BinFile:
    actionNone = 0
    actionRename = 1
    actionExtractForUpdate = 2
    actionExtendIndex = 4
    
    def __init__(self, parent, name, properties, alias = None, action=actionNone, destination=None):
        self.parent = parent        
        self.name = name
        self.properties = properties
        self.alias = alias
        self.action = action
        self.destination = destination
        self.fulldest = parent.destinationDir + '/' + destination
        if (action & BinFile.actionRename) == BinFile.actionRename and alias == None:
            raise "Action rename requires an alias"
        if (action & BinFile.actionExtractForUpdate) == BinFile.actionExtractForUpdate and destination == None:
            raise "Action extract requires a destination folder"
    def run(self, indexFile=None):
        if (self.action & BinFile.actionExtendIndex) == BinFile.actionExtendIndex and indexFile == None:
            raise "Action extend plugin requres an index"
        if (self.action & BinFile.actionExtractForUpdate) == BinFile.actionExtractForUpdate:
            zf = zipfile.ZipFile(self.parent.sourceDir + '/' + self.name)           
            #extract the files
            if not os.path.exists(self.fulldest):
                os.makedirs(self.fulldest)
            for file in zf.namelist():
                if file[-1] == '/':
                    os.makedirs(self.fulldest + '/' + file)
                else:
                    out_dir = '/'.join( file.split('/')[:-1] )
                    if out_dir and not os.path.exists(self.fulldest + '/' + out_dir):                    
                        os.makedirs(self.fulldest + '/' + out_dir)
                out_file = open(self.fulldest + '/' + file, "wb")
                out_file.write( zf.read(file) )
                out_file.close()
                file_time = time.mktime( zf.getinfo(file).date_time + (0,1,-1))
                os.utime(self.fulldest + '/' + file, (file_time,file_time))
            # update the index if required            
            if (self.action & BinFile.actionExtendIndex) == BinFile.actionExtendIndex:
                indf = indexFile.add(self.destination, None)
                for file in zf.namelist():
                    if file[-1] != '/':
                        indf.add(file, self.properties)
        if (self.action & BinFile.actionRename) == BinFile.actionRename:
            shutil.copy2(self.parent.sourceDir + '/' + self.name, self.fulldest + '/' + self.alias)
            if (self.action & BinFile.actionExtendIndex) == BinFile.actionExtendIndex:
                if self.destination:
                    indexFile.add(self.destination + '/' + self.alias, self.properties)
                else:
                    indexFile.add(self.alias, self.properties)
        
        
class BinFiles:
    def __init__(self, srcDir, destDir):
        self.sourceDir = srcDir
        self.destinationDir = destDir
        self.files = []
    def new(self, name, properties, alias = None, action=BinFile.actionNone, destination=None):
        bf = BinFile(self, name, properties, alias, action, destination)        
        self.files.append( bf )
        return bf
    def execute(self, indexFile):
        for file in self.files:
            file.run(indexFile)

ind = FileIndex('E:/tmp/dtest')
#ind.root.add('1.bmp', ['test', 'sss'])
#ind.root.add('DATA', []).add('c70.res', [])
#ind.root.add('DATA/phazni.res', ['yeah'])

bf = BinFiles("e:/tmp/stest", "e:/tmp/dtest")
bf.new('AutoChem.zip', ['auto-chem'], None, BinFile.actionExtractForUpdate|BinFile.actionExtendIndex, 'test')
bf.new('test.py', ['test-chem'], "grand.py", BinFile.actionRename|BinFile.actionExtendIndex, '')
bf.execute(ind.root)

ind.save('E:/index.tst')
