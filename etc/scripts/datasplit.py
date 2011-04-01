#!/usr/bin/python

import sys
import os
import string
import glob
import sets
import datetime
import time
import shutil

#testing path
path = os.getcwd() #"/home/xray/building/datasplit/work"

def file_finder(path, sfrm, file_ext):
  sfrm_copy_files = []
  sfrm_copy_files = (glob.glob('%s/%s*.%s'%(path, sfrm, file_ext)))
  sfrm_copy_files.sort()
  return sfrm_copy_files

# Family Tree
# This is to find all the files that relate to our ins file and move to the relevant directory
# To do this we start by looking for prp (last created), abs, p4p, ls.
def family_tree(path, file_seeker, sfrm):
  print "Family Tree", path, file_seeker
  for fileseek in file_seeker:
    print "fileseek", fileseek
    rfile = open("%s"%(fileseek), 'r')
    lines = {}
    i = 0
    for line in rfile:
      lines[i] = line.strip()
      i+=1

    rfile.close()
    i=0
    for i in lines:
      #print i, lines[i]
      try:
        if "XPREP - DATA PREPARATION" in lines[i]:
          hkl_filename = lines[i+2].split()[1]
          print "prp File Type;  hkl is :", hkl_filename
          continue
        if "File" in lines[i] and "set up as follows:" in lines[i]:
          ins_filename = lines[i].split(' ')[1].split('.')[0] #File 01abs.ins set up as follows:
          print "prp File Type; ins filename: ", ins_filename
          if ins_filename == sfrm:
            "Source match"
            return hkl_filename
        if "Reading file" in lines[i] and ".raw" in lines[i]:
          raw_from_abs = lines[i].split()[-1].split('.')[0]
          print "Input raw: ", raw_from_abs
        if "Corrected reflections written to file " in lines[i]: #/media/data2/ALS/egc023/work/egc023_10_0m.hkl
          hkl_from_abs = lines[i].split()[-1].split('/')[-1].split('.')[0]
          print "hkl_from_abs: ", hkl_from_abs
          print "returning: ", fileseek, sfrm, hkl_from_abs, raw_from_abs
          if sfrm == hkl_from_abs:
            print "returning: ", fileseek, hkl_from_abs, raw_from_abs
            return fileseek.split('/')[-1].split('.')[0]
      except OSError:
        print "error", OSError
  return


try:
  os.mkdir('%s/datasplit'%(path))
  sfrm_copy_files = file_finder(path, '*', '*')
  for sfrm_copy in sfrm_copy_files:
    try:
      shutil.copy("%s"%(sfrm_copy), "%s/datasplit/%s"%(path, os.path.split(sfrm_copy)[-1]))
    except shutil.Error():
      print "Copy Failed", shutil.Error()
      sys.exit(-2)
except OSError:
  print "ARRRRRRRrrgh I already exist", OSError
  sys.exit(-1)
  
path = path + '/datasplit'
sfrm_files = (glob.glob('%s/*.ins'%path))
#print sfrm_files
sfrm_files.sort()
unq_filename = sets.Set()
for path_filename_ext in sfrm_files:
  filename_ext = os.path.split(path_filename_ext)[-1]
  filename = os.path.splitext(filename_ext)[0]
  print filename
  unq_filename.add(filename)
print unq_filename

# Creating folder and files
run_inc = 1
base_path = path
for sfrm in unq_filename:
  if(os.path.exists('%s/%s'%(base_path, sfrm))):
    print "Failed to make %s directory, as already present - incrementing"%sfrm
    run_inc = 1
    while True:
      if(os.path.exists('%s/%s_%2.2d'%(base_path, sfrm, run_inc))):
        print "Failed to make %s_%2.2d directory, as already present - incrementing\n"%(sfrm, run_inc)
        run_inc += run_inc
      else:
        os.mkdir('%s/%s_%2.2d'%(base_path, sfrm, run_inc))
        sfrm_copy_files = file_finder(path, sfrm, '*')
        for sfrm_copy in sfrm_copy_files:
          try:
            print "Move with inc"
            shutil.move("%s"%(sfrm_copy), "%s/%s_%2.2d/%s"%(path, sfrm, run_inc, os.path.split(sfrm_copy)[-1]))
          except shutil.Error():
            print "Moe with inc Failed", shutil.Error()

        break
  else :
    os.mkdir('%s/%s'%(base_path, sfrm))
    sfrm_copy_files = file_finder(path, sfrm, '*')
    for sfrm_copy in sfrm_copy_files:
      try:
        #print "Moving"
        shutil.move("%s"%(sfrm_copy), "%s/%s/%s"%(path, sfrm, os.path.split(sfrm_copy)[-1]))
      except shutil.Error():
        print "Move Failed", shutil.Error()
    file_seek = []
    file_seek = file_finder(path, '*', 'prp')
    hkl_filename = family_tree(path, file_seek, sfrm)
    sfrm_copy_files = file_finder(path, hkl_filename, '*')
    for sfrm_copy in sfrm_copy_files:
      try:
        #print "Moving"
        shutil.move("%s"%(sfrm_copy), "%s/%s/%s"%(path, sfrm, os.path.split(sfrm_copy)[-1]))
      except shutil.Error():
        print "Move failed", shutil.Error()
    file_seek = []
    file_seek = file_finder(path, '*', 'abs')
    abs_filename = family_tree(path, file_seek, hkl_filename)
    sfrm_copy_files = file_finder(path, abs_filename, '*')
    for sfrm_copy in sfrm_copy_files:
      try:
        #print "Moving"
        shutil.move("%s"%(sfrm_copy), "%s/%s/%s"%(path, sfrm, os.path.split(sfrm_copy)[-1]))
      except shutil.Error():
        print "Move Failed", shutil.Error()
    
    



"""
prp HEAD
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+  XPREP - DATA PREPARATION & RECIPROCAL SPACE EXPLORATION - Version 2008/2  +
+  COPYRIGHT(c) 2008 Bruker-AXS                         All Rights Reserved  +
+  egc023_01_0m                          started at 16:30:54 on 03-Mar-2011  +
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

prp written out as

File 01abs.ins set up as follows:

ABS

we want
 Reading file egc023_A_0m.raw
 
With this we know the ls file m_ls
"""


