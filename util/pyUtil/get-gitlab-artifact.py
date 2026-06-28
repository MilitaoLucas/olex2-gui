import os, shutil, zipfile
import requests
from pathlib import Path

headers = {
  "PRIVATE-TOKEN": "glpat-657swJEfC0VRDX-gvlBR02M6MQpvOjEKdTpub3EyOA8.01.170u2pp00",
}
# get user_id: f"{base_url}/user" ["id"]
# get user projects: f"base_url/v4/users/{user_id}/projects"
base_url = "https://gitlab.com/api/v4"

#this dir will be re-created for new artifacts!
www_dir = "/var/www/rsx/website-new/www"

def get_latest_job_id():
  url = f"{base_url}/projects/83460962/jobs?order_by=id&per_page=1"
  with requests.get(url, headers=headers) as response:
    response.raise_for_status()
    job_id = response.json()[0]['id']
    return job_id

def get_artifacts(job_id, out_fn):
  #https://gitlab.com/olexsys/hugo-website-hextra/-/jobs/15065586043/artifacts/download?file_type=archive
  #url = f"https://gitlab.com/olexsys/hugo-website-hextra/-/jobs/{job_id}"
  url = f"https://gitlab.com/olexsys/hugo-website-hextra/-/jobs/{job_id}/artifacts/download?file_type=archive"
  url = f"{base_url}/projects/83460962/jobs/{job_id}/artifacts"
  with requests.get(url, headers=headers, stream=True) as response:
    response.raise_for_status()
    with open(out_fn, "wb") as out:
      for ch in response.iter_content(16*1024):
        out.write(ch)

if __name__ == "__main__":
  try:
    job_id = get_latest_job_id()
    print(f"Last job Id is {job_id}")
  except Exception as e:
    print("Failed to get the last job id: %s" %str(e))
    exit(1)
  home = Path.home()
  atrtifacts_dir = home / "artifacts"
  if not(os.path.exists(atrtifacts_dir)):
    os.mkdir(atrtifacts_dir)
  last_job_id = None
  last_job_fn = atrtifacts_dir / "last_job"
  if os.path.exists(last_job_fn):
    with open(last_job_fn, "r") as f:
      last_job_id = int(f.read())
  if job_id == last_job_id:
    print("Latest job artifacts has already been downloaded, skipping")
    exit(0)
  out_fn = atrtifacts_dir / f"{job_id}.zip"
  if not os.path.exists(out_fn):
    try:
      get_artifacts(job_id=job_id, out_fn=out_fn)
    except Exception as e:
      print("Failed to get the artifacts archive: %s" %str(e))
      exit(1)
  if os.path.exists(www_dir):
    shutil.rmtree(www_dir)
  os.mkdir(www_dir)
  with zipfile.ZipFile(out_fn, "r") as zf:
    zf.extractall(www_dir)
  with open(last_job_fn, "w+") as f:
    f.write(str(job_id))
  print("Done")
