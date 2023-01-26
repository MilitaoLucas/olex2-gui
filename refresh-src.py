import sys
import os

git_cmd = ("C:/Program Files/Git/bin", "git.exe", "pull")
svn_cmd = ("C:/Program Files/TortoiseSVN/bin", "svn.exe", "update")

# set PATH so that git/svn could be called without full path
cmds = [git_cmd, svn_cmd]
for path, cmd, arg in cmds:
  os.environ['PATH'] = "%s%s%s" %(path, os.pathsep, os.environ['PATH'])
#git needs this to be able to use pagent
os.environ['GIT_SSH'] = "C:/Program Files/PuTTY/plink.exe"

dev_dir = "c:/devel"
svn_dir = os.path.join(dev_dir, "svn")
#public repos
cctbx_dir = os.path.join(dev_dir, "cctbx", "cctbx_latest", "modules", "cctbx_project")
olex2_dir_trunk = os.path.join(svn_dir, "olex2", "trunk")
olex2_dir_release = os.path.join(svn_dir, "olex2", "branches", "1.5")
base_dir = "c:/devel/rundir-py3"
#Olex2 insternal repositories
acd_dir = os.path.join(base_dir, "util", "pyUtil", "AC6d")
aced_dir = os.path.join(base_dir, "util", "pyUtil", "ACEDd")
olex2_i_dir_trunk = os.path.join(svn_dir, "olex2pro", "trunk")
olex2_i_dir_release = os.path.join(svn_dir, "olex2pro", "branches", "1.5")

dirs = [
  (cctbx_dir, git_cmd),
  (olex2_dir_trunk, git_cmd),
  (olex2_dir_release, git_cmd),
  (base_dir, svn_cmd),
  (acd_dir, git_cmd),
  (aced_dir, svn_cmd),
  (olex2_i_dir_trunk, svn_cmd),
  (olex2_i_dir_release, svn_cmd),
 ]

if __name__ == '__main__':
  processed = []
  failed = []
  cd = os.getcwd()
  try:
    for d,c in dirs:
      if not os.path.exists(d):
        print("Skipping: %s" %d)
        continue
      os.chdir(d)
      cmd = c[1] + " " + c[2]
      rv = os.system(c[1] + " " + c[2])
      if rv != 0:
        print("Failed (%s): %s" %(rv, d))
        failed.append(d)
      else:
        print("Done: %s" %d)
        processed.append(d)
    if failed:
      print("Failed on this:")
      print("\n".join(failed))
    else:
      print("All repositories have been updated")
  finally:
    os.chdir(cd)
