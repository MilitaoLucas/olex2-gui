import sys
import os
import subprocess
import pickle
import time

class repo_info:
  def __init__(self, revision, last_updated=None):
    self.revision = revision
    if last_updated is None:
      self.last_updated = time.time()
    else:
      self.last_updated = last_updated

def get_revision(repo_root):
  revision = None
  try:
    git_exe = "git"
    if sys.platform[:3] == 'win':
      git_exe = r"C:\Program Files\Git\bin\git"
    def get_git_revision_short_hash():
      return subprocess.check_output([git_exe, 'rev-parse', '--short', 'HEAD'])
    cur_dir = os.getcwd()
    try:
      os.chdir(repo_root)
      try:
        subprocess.check_call([git_exe, 'pull'])
        revision = get_git_revision_short_hash().strip().decode()
      except subprocess.CallProcessError as x:
        print("Failed to update the repository: %s, aborting" %str(x))
    finally:
      os.chdir(cur_dir)
  except Exception as e:
    print('Unfortunately could not update the revision information: %s' %str(e))
  return revision

cache_data = {}
if __name__ == "__main__":
  if len(sys.argv) != 3:
    print("Usage python3 check_git.py git_root command_to_run")
    exit(0)
  repo_root = sys.argv[1]
  cmd = sys.argv[2]
  revision = get_revision(repo_root)
  if not revision:
    exit(1)
  home = os.path.expanduser("~")
  cache_fn = os.path.join(home, ".cg_cache.pickle")
  if os.path.exists(cache_fn):
    with open(cache_fn, "rb") as cf:
      cache_data = pickle.load(cf)
  ri = cache_data.get(repo_root, None)
  if not ri or ri.revision != revision:
    if os.system(cmd) != 0:
      print("Failed to run the command!")
      exit(1)
  #
  if ri is None:
    ri = repo_info(revision)
    cache_data[repo_root] = ri
  else:
    ri.revision = revision
    ri.las_updated = time.time()
  with open(cache_fn, "wb") as cf:
    pickle.dump(cache_data, file=cf)
  print("OK")
