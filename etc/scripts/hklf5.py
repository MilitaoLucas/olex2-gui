import olex_hkl
import olex
import os

# reads an HKL file and returns a tuple of tuples x7 

input_file_name = olex.f('fileOpen("Choose input HKL file", "HKL files|*.hkl",filepath())')
output_file_name = olex.f('fileOpen("Choose output HKL file", "HKL files|*.hkl",filepath())')
if not input_file_name or not os.path.exists(input_file_name) or not output_file_name:
  exit
if os.path.exists(output_file_name):
  res = olex.f('alert("Warning", "Destination file exists.\nOverwrite?", "YCQ")')
  if not res or res == 'C':
    exit
hkl_file = olex_hkl.Read(input_file_name) 


# (h,k,l, F, sig(F), batch [default value is 61690 (0xF0FA) - unused], used_flag)
# used_flag specifies if a given reflection is beyond the (0,0,0) reflection

output = []  #list of tuples x5 (h,k,l,F.sig(f), batch)

for hkl in hkl_file:
  sum = hkl[0]+hkl[2]
  if sum%3 == 0:
    n = int(sum/3)
    # post a transformed reflection with batch number equal -2
    output.append( (2*n-hkl[0], -hkl[1], 4*n-hkl[2], hkl[3], hkl[4], -2) )
  # post the original reflection with batch number equal to 1
  output.append( hkl[:5] + (1,) )

# write the result to a new HKL file
olex_hkl.Write(output_file_name, output)