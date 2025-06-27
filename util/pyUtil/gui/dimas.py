from olexFunctions import OV
import olx
import requests

class JsonException(requests.HTTPError):
  def __init__(self, jsn):
    self.err = OV.dict_obj(jsn)
    super().__init__(self.err.message)

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
    except JsonException as e:
      if 'expired' in str(e):
        print("Refreshing token")
        self.refresh_jwt_token()
        return func(self, *args, **kwargs)
      else:
        print(f"Json error occurred: {e}")
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
    response = requests.get(url, headers=self.headers, params=params)
    if response.status_code != 200:
      if "application/json" in response.headers["content-type"]:
        raise JsonException(response.json())
      response.raise_for_status()
    return response.json()

  def post(self, endpoint, data=None, json=None):
    url = f"{self.base_url}/{endpoint.lstrip('/')}"
    response = requests.post(url, headers=self.headers, data=data, json=json)
    if response.status_code != 200:
      if "application/json" in response.headers["content-type"]:
        raise JsonException(response.json())
      response.raise_for_status()
    return response.json()

  def put(self, endpoint, data=None, json=None):
    url = f"{self.base_url}/{endpoint.lstrip('/')}"
    response = requests.put(url, headers=self.headers, data=data, json=json)
    if response.status_code != 200:
      if "application/json" in response.headers["content-type"]:
        raise JsonException(response.json())
      response.raise_for_status()
    return response.json()

  def delete(self, endpoint):
    url = f"{self.base_url}/{endpoint.lstrip('/')}"
    response = requests.delete(url, headers=self.headers)
    if response.status_code != 200:
      if "application/json" in response.headers["content-type"]:
        raise JsonException(response.json())
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
    except JsonException as e: # may need special handling?
      print(f"JSON error occurred: {e}")
    except requests.HTTPError as e:
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
      print(f"HTTP error occurred: {e}")
      self.jwt = None

  @api_call
  def list_experiments(self):
    self.raise_auth()
    try:
      self.headers['Authorization'] = self.jwt
      return RestClient(self.base_url, self.headers).get("/lims/experiment-list",
         params={"start": 0, "size": 10})
    except requests.HTTPError as e:
      print(f"HTTP error occurred: {e}")
      return None

  @api_call
  def get_experiment(self, endpoint, data=None, json=None):
    self.raise_auth()
    try:
      self.headers['Authorization'] = self.jwt
      return RestClient(self.base_url, self.headers).get(endpoint, params=data)
    except requests.HTTPError as e:
      print(f"HTTP error occurred: {e}")
      return None

  def ready(self):
    self.read_def()
    if self.base_url and self.username and self.passwdd:
      return True
    return False

dc = DimasClient()

def connect(passwd):
  from hashlib import sha256
  import base64
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
  rv = "<table>"
  for e in exps:
    rv += "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" %(e.get("userRef"), e.get("operatorRef"), e.get("formula"))
  return rv + "</table>"

OV.registerFunction(connect, False, "dimas")
OV.registerFunction(dc.ready, False, "dimas")
OV.registerFunction(settings_status, False, "dimas")
OV.registerFunction(list_experiments, False, "dimas")

