import os
import sys
import shutil

def run(argv):
  if not os.path.exists(argv[0]):
    print('Please provide valid HKL file...')
    return
  inf = open(argv[0], 'rb')
  all_data = []
  max_value = 0
  recovered_cnt = 0
  skipped_cnt = 0
  for i, line in enumerate(inf):
    line = line.rstrip('\r\n')
    try:
      if len(line) < 28:
        print('Skipping line %i - line too short'%(i))
        skipped_cnt += 1
      elif len(line) > 28:
        print('Trying to recover line %i - line too long'%(i))
        hkl = (int(line[0:4]), int(line[4:8]), int(line[8:12]))
        ffpi = line.find('.', 12)
        hkl += (float(line[12:ffpi+3]), float(line[ffpi+3:]))
        max_value = max(hkl[3], max_value)
        all_data.append(hkl)
        recovered_cnt += 1
      else:
        hkl = (int(line[0:4]), int(line[4:8]), int(line[8:12]),
               float(line[12:20]), float(line[20:]))
        max_value = max(hkl[3], max_value)
        all_data.append(hkl)
        pass
    except:
      print('Warning: failed at line: %i - skipping'%(i))
     
  inf.close()
  if recovered_cnt > 0 and max_value < 99999.99:
    print('Although some lines were recovered, the result might be incorrect, aborting')
    return 1
  if recovered_cnt == 0 and skipped_cnt == 0:
    print('Nothing to do - the output file is a copy of the source file')
    shutil.copyfile(argv[0], argv[1])
    return 0
  scale = 99999.99/max_value
  
  out = open(argv[1], 'w')
  for h in all_data:
    print('%4d%4d%4d%8.2f%8.2f'%(h[0],h[1],h[2], h[3]*scale,h[4]*scale), file=out)
  out.close()
  print('Completed: lines reovered %i, lines skipped %i'%(recovered_cnt, skipped_cnt))
  print('Output file: %s'%(argv[1]))
  return 0

if __name__ == '__main__':
  print('HKL (HKLF4) float point format overflow recovery utility')
  print('(c) 2011, OlexSys')
  if len(sys.argv) != 3:
    print('Please provide input and output HKL file names...')
    exit(1)
  exit(run(sys.argv[1:]))
