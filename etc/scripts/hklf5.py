import olex_hkl

# reads an HKL file and returns a tuple of tuples x7 

hkl_file = olex_hkl.Read("e:/1.hkl")

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
olex_hkl.Write("e:/1a.hkl", output)