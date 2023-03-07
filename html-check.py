
import sys
import os

def extract_tag(line, idx):
  tag_name = ""
  for i in range(idx, len(line)):
    if line[i] in (' ', '\t', '>'):
      tag_name = line[idx:i]
      return tag_name
  return line[idx:]


#def skip_comment(line, idx):

def scroll_quote(lines, i, j):
  ch = lines[i][j]
  while i < len(lines):
    l = lines[i]
    ll = len(l)
    while j+1 < ll and l[j+1] != ch:
      j += 1
    if j+1 >= ll:
      if not l or l[-1] != ch:
        i += 1
        j = 0
        continue
      return (i+1, 0)
    elif l[j+1] == ch:
      return (i, j+2)
  return (len(lines), 0)

def check_predecent(lines, i, j, ch):
  if check_predecent_1(lines[i], j, ch):
    return True
  i -= 1
  while i >= 0:
    if check_predecent_1(lines[i], 0, ch):
      return True
    i -= 1
  return False

def check_predecent_1(line, i, ch):
  i -= 1
  while i >= 0:
    if line[i] == ch:
      return True
    if line[i] in (' ', '\t'):
      i -= 1
      continue
    else:
      return False


stack = []
def check(fn):
  with open(fn, "r") as f:
    lines = f.readlines()
    lines = [l.strip() for l in lines]
    line_cnt = len(lines)
    li = 0
    while li < line_cnt:
      l = lines[li]
      line_len = len(l)
      i = 0
      while i < line_len:
        if l[i] == '"' or l[i] == "'":
          if not check_predecent(lines, li, i, '='):
            i += 1
            continue
          n_li, i = scroll_quote(lines, li, i)
          if n_li != li:
            li = n_li
            l = lines[li]
            line_len = len(l)
          continue
        if l[i] == '<':
          if i+1 < line_len and l[i+1] == '!':
            i += 1
            continue
          tag = extract_tag(l, i+1)
          if tag in ("zimg","input") or tag.startswith("SWITCHINFO"):
            i += len(tag)
            continue
          if tag in ("font", "td", "tr", "table"):
            if stack:
              lt = stack[-1]
              if tag == "td":
                if lt[0] != "tr":
                  print("Inserting %s into %s at (%s, %s)" %(tag, lt[0], lt[1]+1, li+1))
              elif tag == "tr":
                if lt[0] != "table":
                  print("Inserting %s into %s at (%s, %s)" %(tag, lt[0], lt[1]+1, li+1))
              elif tag == "table":
                if lt[0] != "td" and lt[0] != "font":
                  print("Inserting %s into %s at (%s, %s)" %(tag, lt[0], lt[1]+1, li+1))
            stack.append((tag, li))
          elif tag in ("/font", "/td", "/tr", "/table"):
            if not stack:
              print("CLosing unopened %s at %s" %(tag, li))
            else:
              lt = stack[-1]
              if lt[0] == "td":
                if tag != "/td":
                  print("Broken %s at %s closed at %s with %s" %(lt[0], lt[1]+1, li+1, tag))
                else:
                  del stack[-1]
              elif lt[0] == "tr":
                if tag != "/tr":
                  print("Broken %s at %s closed at %s with %s" %(lt[0], lt[1]+1, li+1, tag))
                else:
                  del stack[-1]
              elif lt[0] == "table":
                if tag != "/table":
                  print("Broken %s at %s closed at %s with %s" %(lt[0], lt[1]+1, li+1, tag))
                else:
                  del stack[-1]
              elif lt[0] == "font":
                if tag != "/font":
                  print("Broken %s at %s closed at %s with %s" %(lt[0], lt[1]+1, li+1, tag))
                else:
                  del stack[-1]
          else:
            if tag[0] == '/':
                while len(stack) and stack[-1][0] != tag[1:]:
                  print("Removing unballanced %s at %s" %stack[-1])
                  del stack[-1]
                if stack:
                  del stack[-1]
            else:
              stack.append((tag, li))
          i += len(tag)
        i += 1
      li += 1




if __name__ =="__main__":
  if len(sys.argv) == 2:
    fn = sys.argv[1]
  else:
    import olx
    bd = olx.DataDir()
    fn = os.path.join(bd, "html.htm")
    print("Dumping HTML...")
    olx.html.Dump(fn, a=False)
  check(fn)
  if stack:
    print("There is something left in the stack:")
    for r in stack:
      print("%s at %s" %r)
  print("Done")