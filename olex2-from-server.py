import sys, os
import platform
import zipfile

src_folder = 'distro@10.8.0.1:/var/distro/bin_dir_trunk/'

if platform.architecture()[0][:2] == '64':
  fn = "olex2-win64.zip"
else:
  fn = "olex2-win32-sse2.zip"

if sys.platform[:3] == 'win':
  downloader = r'"C:\Program Files\PuTTY\pscp.exe"'
  tmp_dir = "c:/temp"
else:
  downloader = r'scp'
  tmp_dir = "/tmp"

if __name__ == '__main__':
  download_str = "%s %s%s %s" %(downloader, src_folder, fn, tmp_dir)
  if os.system(download_str):
    print("Failed to download new ZIP file")
    exit(1)
  with zipfile.ZipFile(os.path.join(tmp_dir, fn), "r") as zf:
    zf.extract("olex2.dll")
  print("Extracted olex2.dll to: %s" %os.path.join(os.curdir))
