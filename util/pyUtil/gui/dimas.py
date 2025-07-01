from olexFunctions import OV
import olx
import requests
import os, shutil

class NoAuthException(Exception):
  def __init__(self, *args):
    super().__init__(*args)

def api_call(func):
  """
  Decorator to handle API calls with error handling.
  """
  def wrapper(self, *args, **kwargs):
    try:
      return func(self, *args, **kwargs)
    except NoAuthException as e:
      olx.Echo("Not authenticated, please login", m="error")
      return None
    except requests.HTTPError as he:
      if "application/json" in he.response.headers["content-type"]:
        err = OV.dict_obj(he.response.json())
        if "expired" in err.message:
          print("Refreshing token")
          self.refresh_jwt_token()
          return func(self, *args, **kwargs)
        else:
          print(str(err))
          return None
      if he.response.status_code == 401:
        print("Creating new token")
        self.create_jwt_token()
        return func(self, *args, **kwargs)
      print(f"An HTTP error occurred: {he}")
      return None
    except Exception as e:
      print(f"An error occurred: {e}")
      return None
  return wrapper

class RestClient:
  def __init__(self, base_url, headers=None):
    self.base_url = base_url.rstrip('/')
    self.headers = headers or {}

  def get(self, endpoint, params=None):
    url = f"{self.base_url}/{endpoint.lstrip('/')}"
    with requests.get(url, headers=self.headers, params=params) as response:
      response.raise_for_status()
      return response.json()

  def post(self, endpoint, data=None, json=None):
    url = f"{self.base_url}/{endpoint.lstrip('/')}"
    with requests.post(url, headers=self.headers, data=data, json=json) as response:
      response.raise_for_status()
      return response.json()

  def put(self, endpoint, data=None, json=None):
    url = f"{self.base_url}/{endpoint.lstrip('/')}"
    with requests.put(url, headers=self.headers, data=data, json=json) as response:
      response.raise_for_status()
      return response.json()

  def delete(self, endpoint):
    url = f"{self.base_url}/{endpoint.lstrip('/')}"
    with requests.delete(url, headers=self.headers) as response:
      response.raise_for_status()
      return response.json()

class DimasClient(object):
  def __init__(self):
    self.jwt, self.refresh_token = None, None
    self.headers = {
      'Content-Type': 'application/json'
    }
    self.read_def()

  def raise_auth(self):
    if self.jwt is None:
      try:
        if self.create_jwt_token():
          return
      except:
        pass
      raise NoAuthException()

  def read_def(self):
    self.base_url = OV.GetParam("olex2.dimas.url", None)
    self.api_token = OV.GetParam("olex2.dimas.apiKey", None)
    self.username = OV.GetParam("olex2.dimas.username", None)
    self.passwdd = OV.GetParam("olex2.dimas.passwdd", None)

  def create_jwt_token(self):
    self.read_def()
    if not self.api_token:
      olx.Echo("No API key is set!", m="error")
      return False
    try:
      self.jwt, self.refresh_token = None, None
      self.headers['Authorization'] = f"{self.api_token}"
      login_response = RestClient(self.base_url, self.headers).get("/user/auth/token-issue",
         params={"username": self.username, "password": self.passwdd})
      self.jwt = login_response["token"]
      self.refresh_token = login_response["refreshToken"]
      return True
    except requests.HTTPError as e:
      if "application/json" in e.response.headers["content-type"]:
        print(e.response.json())
      else:
        print(f"HTTP error occurred: {e}")
    return False

  def refresh_jwt_token(self):
    try:
      self.headers['Authorization'] = f"{self.api_token}"
      login_response = RestClient(self.base_url, self.headers).get("/user/auth/token-refresh",
        params={"refreshToken": self.refresh_token})
      self.jwt = login_response["token"]
      self.refresh_token = login_response["refreshToken"]
    except requests.HTTPError as e:
      if "application/json" in e.response.headers["content-type"]:
        print(e.response.json())
      else:
        print(f"HTTP error occurred: {e}")
      self.jwt = None

  @api_call
  def list_experiments(self):
    self.raise_auth()
    self.headers['Authorization'] = self.jwt
    return RestClient(self.base_url, self.headers).get("/lims/experiment/list",
        params={"start": 0, "size": 10})

  @api_call
  def list_experiment_files(self, exp_id):
    self.raise_auth()
    self.headers['Authorization'] = self.jwt
    return RestClient(self.base_url, self.headers).get("/lims/experiment/files/list",
        params={"id": exp_id})

  @api_call
  def get_experiment(self, endpoint):
    self.raise_auth()
    self.headers['Authorization'] = self.jwt
    return RestClient(self.base_url, self.headers).get(endpoint)

  @api_call
  def get_experiment_files(self, url, id):
    self.raise_auth()
    self.headers['Authorization'] = self.jwt
    with requests.get(url, headers=self.headers, stream=True) as response:
      path = os.path.join(OV.DataDir(), "dimas", str(id))
      if not os.path.exists(path):
        os.makedirs(path)
      out_fn = os.path.join(path, "data.zip")
      with open(out_fn, "wb") as out:
        for ch in response.iter_content(16*1024):
          out.write(ch)
      return out_fn

  @api_call
  def upload_experiment_file(self, exp_id, filename):
    self.raise_auth()
    # !!! DO NOT SET Content-Type HERE, spends almost a day hunting it down!!!!
    headers = {'Authorization': self.jwt}

    url = f"{self.base_url}" + "/lims/experiment/files/put"
    with open(filename, "rb") as f:
      with requests.put(url, headers=headers,
                        files = {"stream": f},
                        params={"id": exp_id, "replace": 2}) as response:
        response.raise_for_status()
        return response.json()

  def ready(self):
    self.read_def()
    if self.base_url and self.username and self.passwdd:
      return True
    return False

  def get_jwt(self):
    return self.jwt

dc = DimasClient()

def connect(passwd):
  from hashlib import sha256
  import base64
  if passwd:
    passwdd = base64.b64encode(sha256(passwd.encode("utf8")).digest()).decode()
    OV.SetParam("olex2.dimas.passwdd", passwdd)
  dc.create_jwt_token()
  if dc.jwt:
    print("Successfully created an access token")
  else:
    print("Failed to create an access token")

def have_access():
  return dc.jwt != None

def settings_status():
  return 2 if dc.ready() else 1

def list_experiments():
  exps = dc.list_experiments()
  if exps is None:
    return "<b><font color='red'>Error has occurred</font></b>"
  rv = "<table>"
  for e in exps:
    rv += "<tr><td>%s</td><td>%s</td><td>%s</td><td><a href='spy.dimas.get_experiment_files(%s,%s)'>Files</a></td></tr>" %(
      e.get("userRef"), e.get("operatorRef"), e.get("formula"),
      e.get("files"), e.get("operatorRef"))
  return rv + "</table>"

def get_experiment_files(url, id):
  out_fn = dc.get_experiment_files(url, id)
  print(f"Files have been saved to {out_fn}")

def list_experiment_files(id):
  fs = dc.list_experiment_files(id)
  for f in fs:
    print(f)

def upload_current_file(exp_id):
  # retunns 3 if file already exists, 0 - if added/updated
  dc.upload_experiment_file(exp_id, OV.FileFull())

OV.registerFunction(connect, False, "dimas")
OV.registerFunction(dc.ready, False, "dimas")
OV.registerFunction(dc.get_jwt, False, "dimas")
OV.registerFunction(settings_status, False, "dimas")
OV.registerFunction(list_experiments, False, "dimas")
OV.registerFunction(get_experiment_files, False, "dimas")
OV.registerFunction(list_experiment_files, False, "dimas")
OV.registerFunction(upload_current_file, False, "dimas")
