from urllib.request import urlopen
import os
import glob
import pickle
import re
from time import strptime, strftime

def run(filterString='index.ind',
        filterNumber=1,
        start_date='0001-01-01-01-01-01',
        end_date='9999-12-31-23-59-61',
        directory=''):
  a = access_log_stats(
    filterString=filterString,
    filterNumber=filterNumber,
    start_date=start_date,
    end_date=end_date,
    directory=directory)
  return a.html

class access_log_stats:
  def __init__(self,
               filterString,
               filterNumber,
               start_date,
               end_date,
               directory):
    self.time_string_format = '%Y-%m-%d-%H-%M-%S'
    self.start_date = parse_timeStr(start_date)
    self.end_date = parse_timeStr(end_date)
    self.filterString = filterString
    self.filterNumber = filterNumber
    self.olex_users = {}
    if not directory:
      self.write_directory = '/opt/Plone-3.1/olex2/parts/instance/Extensions'
      #self.write_directory = '/var/distro/bin'
      self.read_directory = '/var/distro/bin'
    else:
      self.write_directory = directory
      self.read_directory = directory

    self.geocodeIP_cache = self.load_geocodeIP_cache()
    #logFiles = glob.glob('%s/*access_log*' %self.read_directory)
    logFiles = ['%s/cds.log' %self.read_directory]

    search_caches = self.load_search_cache()
    search_cache = search_caches.setdefault(filterString,{})

    for log in logFiles:
      logName = os.path.basename(log)
      if logName in search_cache and 0:
        users = search_cache[logName]
      else:
        a = reader(open(log, 'r'), filterString=self.filterString, write_directory=self.write_directory)
        users = a.users
        if not logName.endswith('access_log'):
          search_cache.setdefault(logName, users)
      for user, info in list(users.items()):
        if user in self.olex_users:
          self.olex_users[user].update(info)
        else:
          self.olex_users.setdefault(user,info)
    search_caches[self.filterString] = search_cache
    self.save_search_cache(search_caches)

    print(self.html_hit_stats())

    #print self.user_stats()

    self.html = self.output_html_map(self.olex_users)

  def load_search_cache(self):
    pickle_path = '%s/search_cache.pickle' %self.write_directory
    if os.path.exists(pickle_path):
      pickle_file = open(pickle_path,'r')
      try:
        return pickle.load(pickle_file)
      except:
        return {}
    else: return {}

  def save_search_cache(self, cache):
    pickle_file = open('%s/search_cache.pickle' %self.write_directory,'w')
    pickle.dump(cache, pickle_file)

  def geocodeIP(self, addr):
    if addr in self.geocodeIP_cache:
      return self.geocodeIP_cache[addr]
    elif 0:
      url = "http://freegeoip.appspot.com/json/%s" % (addr)
      proxies = {'http': 'http://wwwcache.dur.ac.uk:8080'}
      data = urlopen(url, proxies=proxies).read()
      import json
      data_dict = json.loads(data)
      self.geocodeIP_cache.setdefault(addr, data_dict)
      self.save_geocodeIP_cache()
      return data_dict
    elif 1:
      url = "http://freegeoip.appspot.com/csv/%s" % (addr)
#      url = "http://www.ip2location.com/%s" % (addr)
      proxies = {'http': 'http://wwwcache.dur.ac.uk:8080'}
      data = urlopen(url, proxies=proxies).read()
      if "Over Quota" in data:
        return {}
      data = data.split(',')
      data_dict = {}
      fields = ['status','ip','countrycode','countryname','regioncode',
                'regionname','city','zipcode','latitude','longitude']
      for i in range(min(len(data),len(fields))):
        data_dict.setdefault(fields[i],data[i])
      self.geocodeIP_cache.setdefault(addr, data_dict)
      self.save_geocodeIP_cache()
      return data_dict
    else:
      url = "http://api.hostip.info/rough.php?ip=%s&position=true" % (addr)  # geolocate ip address
      proxies = {'http': 'http://wwwcache.dur.ac.uk:8080'}
      data = urlopen(url, proxies=proxies).read()
      data = data.split('\n')
      data_dict = {}
      for field in data:
        name, value = field.split(':')
        data_dict.setdefault(name.lower(), value.strip())
      self.geocodeIP_cache.setdefault(addr, data_dict)
      self.save_geocodeIP_cache()
      return data_dict

  def load_geocodeIP_cache(self):
    pickle_path = '%s/geocodeIP_cache.pickle' %self.write_directory
    if os.path.exists(pickle_path):
      pickle_file = open(pickle_path, 'r')
      geocodeIP_cache = pickle.load(pickle_file)
    else:
      geocodeIP_cache = {}
    return geocodeIP_cache

  def save_geocodeIP_cache(self):
    pickle_file = open('%s/geocodeIP_cache.pickle' %self.write_directory, 'w')
    pickle.dump(self.geocodeIP_cache, pickle_file)

  def output_html_map(self, users):
    markers = []
    for user, access_log in list(users.items()):
      geocode = self.geocodeIP(user)
      if not geocode:
        continue
      if "Over Quota" in repr(geocode):
        try:
          del self.geocodeIP_cache[user]
          self.save_geocodeIP_cache()
        except:
          pass
        continue
      latitude = geocode['latitude']
      longitude = geocode['longitude']
      num_hits, first_access, last_access = self.get_num_hits(user)
      if latitude and longitude and num_hits >= int(self.filterNumber):
        first_access = strftime(self.time_string_format, first_access)
        last_access = strftime(self.time_string_format, last_access)
        if num_hits == 1:
          icon = 'greyIcon'
          zindex = '3'
        elif num_hits >= 10:
          icon = 'redIcon'
          zindex = '1'
        else:
          icon = 'orangeIcon'
          zindex = '2'
        country = geocode.get('country', geocode.get('countryname'))
        userInfo = "IP: %s<br>No. hits: %s<br>Location: %s, %s<br>Last access: %s" %(user,num_hits,geocode['city'],country,last_access)
        markers.append("""
        var marker = new GMarker(new GLatLng(%s, %s),{title:"%s", icon:%s});
        marker.html = "%s";
        map.addOverlay(marker);
        gmarkers.push(marker);
        """ %(latitude,longitude,user,icon,userInfo))
    if markers:
      markers_html = '\n        '.join(markers)
    else:
      markers_html = ''

    html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
  <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
      <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
      <title>Olex2 User Map</title>

      <STYLE type="text/css">
      H1 {text-align: center; color: #ff8f00; font-family: Courier}
      </STYLE>


      <script src="http://maps.google.com/maps?file=api&amp;v=2&amp;key=ABQIAAAAWYsMNksHxyZ1nTR9cMAj-hQQSsONx3yoT9qajHkD6DdltYiy9BTKqloAGrfU9_zugGdfQzA1N91GhA"
        type="text/javascript"></script>
      <script type="text/javascript">

      //<![CDATA[

      function load() {
        var map = new GMap2(document.getElementById("map_canvas"));
        map.setMapType(G_SATELLITE_MAP);
        map.enableScrollWheelZoom();
        map.addControl(new GLargeMapControl());
        map.addControl(new GMapTypeControl());
        map.setCenter(new GLatLng(15.0, 0.0), 1);

        var redIcon = new GIcon(G_DEFAULT_ICON);
        redIcon.image = "http://gmaps-samples.googlecode.com/svn/trunk/markers/red/blank.png";
        var orangeIcon = new GIcon(G_DEFAULT_ICON);
        orangeIcon.image = "http://gmaps-samples.googlecode.com/svn/trunk/markers/orange/blank.png";
        var greyIcon = new GIcon(G_DEFAULT_ICON);
        greyIcon.image = "http://gmaps-samples.googlecode.com/svn/trunk/markers/blue/blank.png";
        var greenIcon = new GIcon(G_DEFAULT_ICON);
        greenIcon.image = "green.png";

        var gmarkers = [];
        %s

        function myclick(i) {
        gmarkers[i].openInfoWindowHtml('<div style="white-space:nowrap;">' + gmarkers[i].html + '</div>');
        }

        GEvent.addListener(map, "click", function(overlay, point) {
          if (overlay) {
            if (overlay.html) {
              overlay.openInfoWindowHtml('<div style="white-space:nowrap;">'+overlay.html+'</div>');
            }
          }
        });

      }

      //]]>
      </script>
    </head>
    <center>
    <body onload="load()" onunload="GUnload()" bgcolor='#000000'>

      <h1>Olex2 Access Statistics</h1>
      <div class='body' id="map_canvas" style="width: 650px; height: 450px"></div>
      filterString=%s
      filterNumber=%s
      <div id="stats">
        %s
      </div>
    </body>
    </center>
  </html>""" %(markers_html,self.filterString,self.filterNumber,self.html_hit_stats())
    return html

  def get_num_hits(self, user):
    first_access = self.end_date
    last_access = self.start_date
    num_hits = 0
    for access_date in self.olex_users[user]:
      if access_date >= self.start_date and access_date <= self.end_date:
        num_hits += 1
      first_access = min(first_access, access_date)
      last_access = max(last_access, access_date)
    return num_hits, first_access, last_access

  def html_hit_stats(self, number_results=200):
    hit_stats_dict = {}

    stats_list = []
    total_num_hits = 0
    total_num_users = 0
    exclude_list = ['129.234.13.99', '81.157.18.58', '129.234.13.105', '86.136.54.118', '129.234.13.129', '86.151.228.39']
    for user in list(self.olex_users.keys()):
      if user in exclude_list:
        continue
      num_hits, first_access, last_access = self.get_num_hits(user)
      if num_hits > 0:
        total_num_users += 1
      else:
        continue

      stats_list.append((num_hits, user, first_access, last_access))
      total_num_hits += num_hits
    stats_list.sort()
    stats_list.reverse()

    table_rows = []
    for n_hits, ip, first, last in stats_list[:number_results]:
      geo = self.geocodeIP(ip)
      if not geo:
        try:
          del self.geocodeIP_cache[ip]
        except:
          pass
        continue
      country = geo.get('country', geo.get('countryname'))
      table_rows.append("""
      <tr>
        <td>%s</td>
        <td align='center'><font color='#ababab'><b>%s</b></font></td>
        <td>%s, %s</td>
        <td>%s</td>
        <td>%s</td>
      </tr>"""%(
                ip,
                n_hits,
                geo['city'],
                country,
                strftime('%Y-%m-%d', first) + "&nbsp;-&nbsp;",
                strftime('%Y-%m-%d', last),
              ))
    table_html = """
    <font face='Courier' color='#ff8f00' size='4'><b>
    Total number of hits:%s, Total number of users: %s
    </b></font><br><br>
    <font face='Courier' color='#888888' size='2'>
    <table>
      <th>IP</th>
      <th>No. hits</th>
      <th>Location</th>
      <th>First access</th>
      <th>Last access</th>
      %s
    </table>
    </font>
    """ %(total_num_hits, total_num_users, ''.join(table_rows))
    return table_html

  def user_stats(self):
    out = []
    txt =  "Number of users: %s" %len(self.olex_users)
    out.append(txt)
    for olex_user in list(self.olex_users.values()):
      ip = olex_user.ip
      location = olex_user.geocodeIP['Country'] + ' ' + olex_user.geocodeIP['City']
      num_visits = str(len(olex_user.user_access_log))
      txt = ip + (17-len(ip))*' ' \
          + num_visits\
          + (4 - len(num_visits))*' '\
          + location
      out.append(txt)
    return "\n".join(out)

def searchString(string, regex):
  match = re.match(regex, string)

  if match:
    print()

  return match

class Olex_user(object):
  def __init__(self, ip):
    self.ip = ip
    self.geocodeIP = None
    self.user_access_log = {}

  def __iadd__(self, new_access_time):
    self.user_access_log.setdefault(new_access_time)
    return self

class reader(object):
  def __init__(self, file_object, filterString='index.ind', write_directory=''):
    users = {}
    self.write_directory = write_directory
    gets = ['.zip', '1.0', 'installer']

    for line in file_object:
      for get in gets:
        if get in filterString:
          head_get = "HEAD"
          break
        else:
          head_get = 'GET'
      if filterString in line and head_get not in line:
        ip = self.get_IP_address(line)
        url = self.get_url(line)
        if url:
          keywords = self.get_url_keywords(url)
          if 'google' in url and 'q' in keywords:
            print('%s\t%s' %(ip,keywords['q']))
        access_time = self.get_access_time(line)

        if ip not in users:
          users.setdefault(ip, {})
        users[ip].setdefault(access_time)
          #users.setdefault(ip,Olex_user(ip))
          #if ip in self.geocodeIP_cache.keys():
            #data_dict = self.geocodeIP_cache.get(ip)
          #else:
            #data_dict = self.geocodeIP(ip)
            #self.geocodeIP_cache.setdefault(ip,data_dict)
            #self.save_geocodeIP_cache()
          #users[ip].geocodeIP = data_dict

        #users[ip] += access_time
    self.users = users

  def get_access_time(self, line):
    #start = line.find('[')
    #end = line.find(']')
    #return strptime(line[start+1:end].split()[0], "%d/%b/%Y:%H:%M:%S")
    start = line.find(' at ')
    end = line.find(': ')
    if start and end and end > start:
      return strptime(line[start+4:end], "%Y.%m.%d %H:%M:%S")

  def format_access_time(self, time):
    months = {
      'Jan':'01',
      'Feb':'02',
      'Mar':'03',
      'Apr':'04',
      'May':'05',
      'Jun':'06',
      'Jul':'07',
      'Aug':'08',
      'Sep':'09',
      'Oct':'10',
      'Nov':'11',
      'Dec':'12',
    }

    i = time.find(':')
    dd, MM, yyyy = time[0:i].split('/')

    return '%s/%s/%s %s' %(yyyy,months[MM],dd,time[i+1:])

  def get_IP_address(self, line):
    for frag in line.split():
      i = 0
      while i < len(frag) and self.valid_ip_char(frag[i]):
        i += 1

      if i:
        return frag[0:i]

  def valid_ip_char(self, char):
    return char in '0123456789.'

  def get_url(self, line=''):
    for i in range(len(line)):
      url_sep = '://'
      if line[i:i+len(url_sep)] == url_sep:
        for j in range(i-1, 0, -1):
          if not line[j].isalpha():
            break
        break
    if i+1 == len(line):
      return ''
    for k in range(i+len(url_sep),len(line)):
      if not self.urlchar(line[k]):
        break
    return line[j+1:k]

  def urlchar(self,char):
    return char.isalnum() or char in "~;/?@=&$-_.+!*'(),"

  def get_url_keywords(self, url):
    keywords_dict = {}
    if '?' in url:
      keywords = url.split('?')[1].split('&')
      for keyword in keywords:
        key, value = keyword.split('=')
        keywords_dict.setdefault(key, value)
    return keywords_dict

def parse_timeStr(timeStr):
  if len(timeStr.split('-')) < 6:
    timeStr.append('-00'* 6-len(timeStr.split('-')))
  return strptime(timeStr, "%Y-%m-%d-%H-%M-%S")


if __name__ == '__main__':
  html = run(directory='C:/tmp',
             filterNumber=1,
             #filterString="installer.exe"
             )
  html_file = open('C:/tmp/access_log.html', 'w')
  html_file.write(html)
  html_file.close()
