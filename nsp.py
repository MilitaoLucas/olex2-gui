import os
import shutil
import zipfile

download = r"P:\Downloads\executables.zip"
p_name = "NoSpherA2"

zips_dir = r"D:\tmp\NoSpherA2"
downloads = [
  (p_name, "hart-lin64", p_name),
  (p_name + "_Mac_universal", "hart-mac64", p_name),
  (p_name+".exe", "hart-win64", p_name + ".exe"),
]

zips_dir = os.path.join(r"D:\tmp", p_name)
zexes = zipfile.ZipFile(download, mode="r")
if len(zexes.infolist()) < 3:
  print("Invalid archive - 3 file is expected")
  exit(1)

zmap = {}
for r in zexes.infolist():
  zmap[r.filename] = r

for z in downloads:
  oz = os.path.join(zips_dir, z[1]) + ".zip"
  oz_t = os.path.join(zips_dir, z[1]) + "_t.zip"
  with zipfile.ZipFile(oz, mode="r") as t:
    with zipfile.ZipFile(oz_t, mode="w") as out:
      for zi in t.infolist():
        if zi.filename == z[2]:
          continue
        out.writestr(zi, t.read(zi.filename))
      ezi = zmap[z[0]]
      newe = zexes.read(ezi)
      nezi = zipfile.ZipInfo(z[2])
      nezi.date_time = ezi.date_time
      out.writestr(nezi, newe)
zexes.close()
win32_d = os.path.join(zips_dir, "hart-win32") + ".zip"
if os.path.exists(win32_d):
  os.remove(win32_d)
shutil.copyfile(os.path.join(zips_dir, "hart-win64") + "_t.zip",
  os.path.join(zips_dir, "hart-win32") + ".zip")
for z in downloads:
  oz = os.path.join(zips_dir, z[1]) + ".zip"
  oz_t = os.path.join(zips_dir, z[1]) + "_t.zip"
  os.remove(oz)
  os.rename(oz_t, oz)
  print("%s completed" %oz)
print("Done updating NoSpherA2")
