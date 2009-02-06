""" Classes to interact with the file system """



from __future__ import generators

import os
import os.path
import stat
import errno
import shutil
import fnmatch
import re
import time

#from mx.DateTime import localtime

from time import localtime

import OOPatterns as OOP


class FileSystemError(Exception):
  """ An error in the FileSystem module """

class InvalidPath(FileSystemError):
  """ Invalid attempt to construct a path with a non-string """

class NoSuchNode(FileSystemError):
  """ Invalid attempt to access an non-existing file system node """

class NotADirectory(FileSystemError):
  """ Invalid attempt to access an non-existing directory """

class NotAFile(FileSystemError):
  """ Invalid attempt to access a non-existing file """

class NotEmptyADirectory(FileSystemError):
  """ Attempt to remove a non-empty directory """

class ExistingNode(FileSystemError):
  """ Attempt to create an existing node """

class OperationNotPermitted(FileSystemError):
  """ Failed operation (likely insufficient user rights) """

class AccessDenied(FileSystemError):
  """ Access denied to a file (likely insufficient permissions) """


class Path(object):
  """ A string (immutable) representation of a path

    In addition to the method commented inline it supports the following
    string operation: len, slice, index, iteration and concatenation
    (with operator '/' instead of the usual '+' though) but instead of operating
    on a character by character basis they operate on the parts of a path
    (e.g. 'a', 'b' for 'a/b' and '/', 'a' for '/a')
  """

  _translate = {'..': os.pardir}


  def __init__(self, path='', expand_user=True, expand_vars=False):
    """ Construct an instance with the string or the Path 'path'
    """
    try:
      if isinstance(path, Path):
        self._str = path._str
      else:
        if expand_user: path = os.path.expanduser(path)
        if expand_vars: path = os.path.expandvars(path)
        self._str = os.path.normpath(path)
    except:
      raise InvalidPath("%s is not a valid path" % path)

  # to make it a good immutable citizen

  def __hash__(self):
    return hash(self._str)

  def __eq__(self, other):
    return str(self) == str(other)

  # string operations

  def __str__(self):
    return self._str

  def __repr__(self):
    return "Path(%s)" % self._str

  def __div__(self, other):
    other = self._translate.get(other, other)
    return Path(os.path.normpath(os.path.join(str(self), str(other))))

  def __len__(self):
    splitted = self.splitted()
    if splitted == [os.curdir]:
      return 0
    else:
      return len(splitted)

  def __getitem__(self, i):
    return Path(self.splitted()[i])

  def __getslice__(self, start, stop):
    return Path(os.path.join(*self.splitted()[start:stop]))

  def __iter__(self):
    return iter([Path(p) for p in self.splitted()])

  # More queries

  def itersplitted(self):
    """ self.itersplitted() is a wordy alterative to iter(self) """
    return self.__iter__()

  def splitted(self):
    """ all the parts of self, as mere strings, from left to right """
    allparts = []
    path = str(self)
    while True:
      dir, base = os.path.split(path)
      if len(base) == 0:
        allparts.insert(0, dir)
        break
      elif len(dir) == 0:
        allparts.insert(0, base)
        break
      else:
        path = dir
        allparts.insert(0, base)
    return allparts

  def common(self, other):
    """ the triplet (c, ls, lo) where c is the common leftmost part of self
      and other whereas ls and lo are the leftover in respectively self
      and other
    """
    common = []
    self_leftover = self.splitted()
    other_leftover = other.splitted()
    idx = 0
    for this, that in zip(self_leftover, other_leftover):
      if this != that: break
      common.append(this)
      idx += 1
    self_leftover = self_leftover[idx:]
    other_leftover = other_leftover[idx:]
    result = []
    for l in (common, self_leftover, other_leftover):
      if l:
        result.append(Path(os.path.join(*l)))
      else:
        result.append(Path())
    return tuple(result)

  def relative(self, other):
    """ the path of self relatively to other """
    common, self_leftover, other_leftover = self.common(other)
    back = [os.curdir,] + [os.pardir,]*len(other_leftover)
    back = Path(os.path.join(*back))
    return  back / self_leftover

  def absolute(self):
    """ the absolute path of self """
    return Path(os.path.abspath(str(self)))

  def basename(self):
    return Path(self.splitted()[-1])
  basename = property(basename, doc=
    """ the basename of self """
  )

  def dirname(self):
    dir = self.splitted()[:-1]
    if dir:
      return Path(os.path.join(*dir))
    else:
      return Path('.')
  dirname = property(dirname, doc=
    """ the directory part of self """
  )

  def parent(self):
    """ the basename of the directory part """
    try:
      return Path(self.splitted()[-2])
    except IndexError:
      raise FileSystemError("The parent of node '%s' is unknown" % str(self))

  def is_absolute(self):
    return os.path.isabs(str(self))
  is_absolute = property(is_absolute, doc=
    """ whether self is absolute or not """
  )

  def match(self, pattern):
    """ Whether self matches the given shell-like pattern (c.f. module fnmatch) """
    return fnmatch.fnmatch(str(self), pattern)

  def drive(self):
    return os.path.splitdrive(str(self))[0]
  drive =  property(drive, doc=
    """ the drive part of self on platform supporting that feature,
      or '' otherwise
    """
  )

  def root_extension(self):
    (root, extension) = os.path.splitext(str(self))
    return (Path(root), extension)
  root_extension = property(root_extension, doc=
    """ the pair (root, extension),
      the latter conserve its leading '.' and the former is a Path
    """
  )

  def extension(self):
    return self.root_extension[1]
  extension = property(extension, doc=
    """ the extension with its leading '.' """
  )

  def replace_extension(self, ext):
    """ make and return a new Path obtained by replacing self's extension by 'ext' """
    name, old = self.root_extension
    return Path(str(name) + ext)


class NodeInfo(object):
  """ The filesystem information associated with a path

    It is fine for the path not to correspond to any actual node: all the queries of this
    class would then return false or OOPatterns.Null()

    Attributes [public]:
      self.path [r/w]: the path, as a string
  """

  "Permissions"
  owner_readable = stat.S_IRUSR # readable by owner
  owner_writable = stat.S_IWUSR # writable by owner
  owner_executable = stat.S_IXUSR # executable by owner

  group_readable = stat.S_IRGRP # readable by group
  group_writable = stat.S_IWGRP # writable by group
  group_executable = stat.S_IXGRP # executable by group

  other_readable = stat.S_IROTH # readable by other
  other_writable = stat.S_IWOTH # writable by other
  other_executable = stat.S_IXOTH # executable by other

  "Types"
  isdir = stat.S_IFDIR
  isfile = stat.S_IFREG

  def __init__(self,path):
    """ Construct the info for the specified path
      (any object convertible to a string)
    """
    self.path = path
    try:
      self._info = os.stat(str(path))
    except OSError:
      self._info = None

  def exists(self):
    return self._info != None
  exists = property(exists, doc=
    """ whereas the node exists or not """
  )

  def is_file(self):
    return self._info and stat.S_ISREG(self._info.st_mode)
  is_file = property(is_file, doc=
    """ whether the node is a mere file or not """
  )

  def is_directory(self):
    return self._info and stat.S_ISDIR(self._info.st_mode)
  is_directory = property(is_directory, doc=
    """ whether the node is a directory or not """
  )

  def is_link(self):
    return self._info and stat.S_ISLNK(self._info.st_mode)
  is_link = property(is_link, doc=
    """ whether the node is a symbolic link or not """
  )

  def has_permissions(self, mode):
    """ whether the node has all of the permission encoded in integer mode
      (which can be any bitwise-OR'ed combination of the class variable above)
    """
    return self._info and stat.S_IMODE(self._info.st_mode) & mode

  def has_stat_mode(self, mode):
    """ whether the node has the specified "st_mode" in the manner of the stat module
      (for UNIX geeks only!)
    """
    return self._info and self._info.st_mode & mode

  def last_access(self):
    if self._info:
      return localtime(self._info.st_atime)
    else:
      return OOP.Null()
  last_access = property(last_access, doc=
    """ Time of last access """
  )

  def last_modification(self):
    if self._info:
      return localtime(self._info.st_mtime)
    else:
      return OOP.Null()
  last_modification = property(last_modification, doc=
    """ Time of last modification """
  )

  def last_status_change(self):
    if self._info:
      return localtime(self._info.st_ctime)
    else:
      return OOP.Null()
  last_status_change = property(last_status_change, doc=
    """ Time of last status change """
  )

  def size(self):
    if self._info:
      return self._info.st_size
    else:
      return OOP.Null()
  size = property(size, doc=
    """ Size """
    )


class NodeInfoFilter(object):
  """ A pattern-based filter of lists of NodeInfo's

    The shell-like pattern which can contain
    the fnmatch wildcards *,?,[seq],[!seq] as well as end with the following
    quantifiers:
        *(/) - is this a directory?
        *(.) - is this a regular file?
        *(r) - is this readable?
        *(w) - is this writable?
        *(x) - is this executable?
    or combinations thereof

    Attributes [public]:
      self.pattern: the pattern
  """

  def __init__(self, pattern):
    """ Construct a filter with the given pattern """
    try:
      self.pattern = pattern
      mode = None
      if pattern:
        amatch = self._qualifier_pat.search(pattern)
        if amatch:
          pattern = amatch.group(1)
          quantifiers =amatch.group(2)
          if quantifiers:
            mode = 0
            for q in quantifiers:
              mode |= self._qualifier_to_mode[q]
      self._fnmatch = pattern
      self._mode = mode
    except KeyError:
      raise ValueError("Invalid quantifiers '%s' in pattern '%s'" % (q, self.pattern))

  def filter(self, nodes):
    """ Those items in the list of NodeInfo's 'nodes' whose basename matches self.pattern """
    if not self._fnmatch:
      if not self._mode:
        return nodes
      else:
        return [ info for info in nodes if info.has_stat_mode(mode) ]
    else:
      if not self._mode:
        return [ info for info in nodes if fnmatch.fnmatch(str(info.path.basename), self._fnmatch) ]
      else:
        return [ info for info in nodes
                 if info.has_stat_mode(self._mode)
                 and fnmatch.fnmatch(str(info.path.basename), self._fnmatch) ]

  def glob(self):
    """ A list of NodeInfo's matching self.pattern interpreted as "glob" """
    import glob
    pattern = os.path.expanduser(self._fnmatch)
    result = [ NodeInfo(f) for f in glob.glob(str(pattern)) ]
    if self._mode:
      result = [ info for info in result if info.has_stat_mode(self._mode) ]
    return result

  _qualifier_pat = re.compile(r'(.*)\(([/.rwx]+)\)$')

  _qualifier_to_mode = {'/': NodeInfo.isdir,\
              '.': NodeInfo.isfile,\
              'r': NodeInfo.owner_readable,\
              'w': NodeInfo.owner_writable,\
              'x': NodeInfo.owner_executable,\
              }


class Node(object):
  """ A filesystem node (directory, file, link, etc)

    Attributes [public]:
      self.path [r/w]: its path (an instance of Path)
  """

  def __init__(self, path):
    """ Construct an instance of specified 'path' (either an instance of Path or a string)
    """
    self.path = Path(path)

  def __repr__(self):
    """ For the built-in 'repr' function """
    return "Node(%s)" % self.path

  def info(self):
    return NodeInfo(self.path)
  info = property(info, doc=
    """ The file information about this node """
  )

  def set_permissions(self, mode):
    """ Set its permission to the encoded integer mode
      (which can be any bitwise-OR'ed combination of the InfoNode constants)
    """
    try:
      os.chmod(self.path, mode)
    except OSError, err:
      self._dispatch_exception(err)

  def make_directory(self, mode=0777):
    """ Make a directory at 'path' in the filesystem
      or raise NotADirectory if there is already a node of a different kind
      Note: returns self to make room for the syntaxic sugar
        node = Node("foo").make_directory()
    """
    try:
      os.makedirs(str(self.path), mode)
      return self
    except OSError, err:
      if err.errno == errno.EEXIST:
        return self
      else:
        self._dispatch_exception(err)


  def make_file(self):
    """ Make a regular file at 'path' in the file system
      or raise NotAFile if there is already a node of a different kind
      Note: returns self to make room for the syntaxic sugar
        node = Node("foo/bar").make_file()
    """
    try:
      open(str(self.path),'a')
      return self
    except OSError, err:
      if err.errno == errno.EEXIST:
        return self
      else:
        self._dispatch_exception(err)

  def list(self, pattern=None, afilter=None):
    """ Those direct children of this node which match 'pattern' or 'afilter'
    """
    try:
      if not NodeInfo(self.path).is_directory: return []
      if not afilter:
        afilter = NodeInfoFilter(pattern)
      import dircache
      nodes = [ NodeInfo(self.path / name) for name in dircache.listdir(str(self.path)) ]
      nodes = afilter.filter(nodes)
      return [ Node(info.path) for info in nodes ]
    except OSError, err:
      self._dispatch_exception(err)

  def walk(self, pattern=None, afilter=None):
    """ An iterator over all direct and indirect children of this node
      which match 'pattern' or 'afilter' (breath-first)
    """
    try:
      if not afilter:
        afilter = NodeInfoFilter(pattern)
      for child in self.list(afilter=afilter):
        yield child
      for child in self.list('*(/)'):
        for grandchild in child.walk(afilter=afilter):
          yield grandchild
    except OSError, err:
      self._dispatch_exception(err)

  def rename(self, path):
    """ Changes the path of self to 'path' """
    try:
      os.renames(str(self.path), path)
    except OSError, err:
      self._dispatch_exception(err)
    else:
      self.path = path

  def remove(self):
    """ Removes this node from the filesystem
      If the node is a directory, this is equivalent to remove_dir(empty=1)
    """
    try:
      try:
        os.remove(str(self.path))
      except OSError, err:
        if err.errno == errno.EPERM:
          self.remove_dir(empty=1)
        else:
          self._dispatch_exception(err)
    except NoSuchNode:
      pass

  def remove_dir(self, empty=False):
    """ Remove this node if it is a directory or raise NotADirectory
      If empty is true, the directory is first emptied and then removed;
      otherwise, if the directory is not empty, NotEmptyADirectory is raised
    """
    try:
      if not empty:
        os.rmdir(str(self.path))
      else:
        shutil.rmtree(str(self.path))
    except OSError, err:
      self._dispatch_exception(err)

  def copy_file(self, path, overwrite=False, copy_access_times=False):
    """ Create a copy of this file in the file system at the specified path
      (access times are copied only if specified so) and return the copy Node
      Preconditions:
        - self and the node at 'path' (if it exists) must both be files;
        otherwise NotAFile is raised
        - the node at 'path' must not exists if overwrite is False;
        otherwise ExistingNode is raised
    """
    try:
      info = self.info
      if not info.is_file:
        raise NotAFile(str(info.path))
      if info.path == path:
        return
      dst = NodeInfo(path)
      if dst.exists:
        if not dst.is_file:
          raise NotAFile(str(dst.path))
        if not overwrite:
          raise ExistingNode(path)
      shutil.copy(str(info.path), str(path))
      if copy_access_times:
        shutil.copymode(str(info.path), str(path))
      return Node(dst.path)
    except OSError, err:
      self._dispatch_exception(err)

  def copy_into(self, path, copy_access_times=False):
    """ Create a copy of this node into the directory at the specified path;
      if the latter is not a directory, raise NotADirectory
    """
    try:
      if not NodeInfo(path).is_directory:
        raise NotADirectory(str(path))
      info = self.info
      if info.is_directory:
        shutil.copytree(str(info.path), str(path))
      else:
        shutil.copy(str(info.path), str(path))
      if copy_access_times:
        shutil.copystat(str(info.path), str(path))
    except OSError, err:
      self._dispatch_exception(err)

  def change_working_directory(self):
    """ Changes the current working directory of the main program to self
      (if it holds a relative path, the working directory is set up
      relatively to the one when the method got called)
      Raises NotADirectory if this is not a directory
    """
    try:
      self._restoration = Path(os.getcwd())
      if self.path.is_absolute:
        os.chdir(str(self.path))
      else:
        os.chdir(str(self._restoration / self.path))
    except OSError, err:
      self._dispatch_exception(err)

  def restore_working_directory(self):
    """ Restores the working directory to its value before the last
      call to 'change_working_directory' or does nothing if there has
      been no such call
      Raises NotADirectory if this is not a directory
    """
    try:
      if hasattr(self, '_restoration'):
        os.chdir(str(self._restoration))
        delattr(self, '_restoration')
    except OSError, err:
      self._dispatch_exception(err)

  def open(self, mode='r', bufsize=-1, retry_after=0):
    """ A file object to handle I/O to/from this file
      Raise if this is not a regular file
      If the file cannot be opened, this method will retry after the number of
      seconds specified by the argument "retry_after"
    """
    try:
      return open(str(self.path), mode, bufsize)
    except OSError, err:
      if retry_after > 0:
        time.sleep(retry_after)
        self.open(mode, bufsize, 0)
      self._dispatch_exception(err)

  def _dispatch_exception(self, err):
    """ Dispatch the exception from the os module to our own ones """
    if err.errno == errno.ENOTDIR:
      raise NotADirectory("at path: %s" % self)
    elif err.errno == errno.ENOTEMPTY:
      raise NotEmptyADirectory("at path: %s" % self)
    elif err.errno == errno.EEXIST:
      raise ExistingNode("at path: %s" % self)
    elif err.errno == errno.ENOENT:
      raise NoSuchNode("at path %s" % self.path)
    elif err.errno == errno.EACCES:
      raise AccessDenied("at path %s" % self.path)
    elif err.errno == errno.EPERM:
      raise OperationNotPermitted("at path %s" % self.path)
    else:
      raise FileSystemError(err)


if __name__ == '__main__':
  def test_Path():
    import sys
    p = Path('~/foo/bar')
    print "~/foo/bar == %s" % p
    p = Path(sys.prefix)
    p = p / '..' / 'foo' / '.'
    print "%s / .. / foo / . = %s" % (sys.prefix, p)
    for p in [Path("a/b/c/d/e/f"), Path("/a/b/c")]:
      print
      print "With p=%s," % p
      print "p[0]=%s" % p[0]
      print "p[1:3]=%s" % p[1:3]
      print "... and all parts:"
      for q in p:
        print q
    p = Path("a/b/c/d/e/f")
    q1 = Path("a/b/c/d/e/f/g/h/i")
    q2 = Path("a/b/c")
    q3 = Path("a/b/c/dd/ee")
    for q in (q1,q2,q3):
    #for q in (q2,):
      print
      print "With p=%s and q=%s:" % (p,q)
      common, p_leftover, q_leftover = p.common(q)
      print "p = {%s} / {%s}" % (common, p_leftover)
      print "q = idem / {%s}" % q_leftover
      print "p from q = %s" % p.relative(q)
    print

  def test_Path_Immutability():
    p = Path('foo')
    q = Path('foo')
    d = {}
    d[p] = 1
    d[q] = 2
    for (k,v) in d.iteritems():
      print "%s: %s" % (k,v)
    print

  def test_Node(path):
    n = Node(path)
    print "%s:" % n.path
    def yesno(flag):
      if flag: return 'yes'
      return 'no'
    info = n.info
    print "\tdirectory?\t%s" % yesno(info.is_directory)
    print "\treadable?\t%s" % yesno(info.has_permissions(NodeInfo.owner_readable))
    print "\twritable?\t%s" % yesno(info.has_permissions(NodeInfo.owner_writable))

  def test_Node_removal(path):
    import sys
    d = Node(path).make_directory()
    print "Root: %s" % d.path
    d1 = Node(d.path / 'foo').make_directory()
    Node(d1.path / 'bar').make_directory()
    Node(d1.path / 'foo.txt').make_file()
    Node(d1.path / 'bar' / 'bar.txt').make_file()
    d2 = Node(d.path / 'bar').make_directory()
    print "Created hierarchy:"
    for n in d.walk():
      if n.info.is_directory:
        print "%s :" % n.path
      else:
        print "\t%s" % n.path

    print "\nLet's try remove() on %s ..." % d2.path
    d2.remove()
    print "Success!!"
    print "Let's try remove_dir() on %s ..." % d1.path
    try:
      d1.remove_dir()
    except NotEmptyADirectory:
      print "Caught NotEmptyADirectory: fine!!"
      print "Let's try remove_dir(empty=True) now ..."
      d1.remove_dir(empty=True)
      print "Success!!"

    print "\nPruned hierarchy:"
    for n in d.walk():
      if n.info.is_directory:
        print "%s :" % n.path
      else:
        print "\t%s" % n.path


  def test_Directory_chdir(path):
    print "Starting in '%s'" % path
    working = Node(".")
    working.change_working_directory()
    d = Node(path)
    print "Working directory: %s" % os.getcwd()
    d.change_working_directory()
    print "Working directory is now %s" % os.getcwd()
    d.restore_working_directory()
    print "Working directory back to its original value: %s" % os.getcwd()

  def test_Directory_walk(dir, pattern):
    print "Nodes %s in this directory:" % pattern
    for n in Node(dir).list(pattern):
      if n.info.is_directory:
        print "%s [Directory]" % n.path
      else:
        print "%s" % n.path
    print "\nNodes and subnodes %s in this directory:" % pattern
    for n in Node(dir).walk(pattern):
      if n.info.is_directory:
        print "%s :" % n.path
      else:
        print "\t%s" % n.path

  def test_time():
    n = NodeInfo("aljfaljffa")
    print "date and time (inexistant file): %s" % n.last_access
    n = NodeInfo("./FileSystem.py")
    print "last access of this module: %s" % n.last_access
    print "last access of this module: %s" % n.last_modification
    print "last access of this module: %s" % n.last_status_change

  def test_copy(dir):
    d = Node(dir)
    d.change_working_directory()
    try:
      try:
        d1 = Node("orig")
        d1.make_directory()
        d1.copy_file("copy")
      except NotAFile:
        print "NotAFile raised: OK!"
      else:
        print "Eeek!!"
    finally:
      d1.remove()
    try:
      try:
        d1 = Node("orig")
        d1.make_file()
        d2 = Node("copy")
        d2.make_directory()
        d1.copy_file("copy", overwrite=True)
      except NotAFile:
        print "NotAFile raised: OK!"
      else:
        print "Eeek!!"
    finally:
      d1.remove()
      d2.remove()
    try:
      try:
        d1 = Node("orig")
        d1.make_file()
        d2 = Node("copy")
        d2.make_file()
        d1.copy_file("copy", overwrite=False)
      except ExistingNode:
        print "ExistingNode raised: OK!"
      else:
        print "Eeek!"
    finally:
      d1.remove()
      d2.remove()
    try:
      try:
        d1 = Node("orig")
        d1.make_file()
        d2 = Node("copy")
        d2.make_file()
        s = d2.open('w')
        s.write("coucou!!")
        s.close()
        before = d2.info.size
        d1.copy_file("copy", overwrite=True)
      except ExistingNode:
        print "Eeek!"
      else:
        after = d2.info.size
        if before > after:
          print "OK!"
        else:
          print "Eeek!"
    finally:
      d1.remove()
      d2.remove()
    try:
      try:
        d1 = Node("orig")
        d1.make_file()
        d1.copy_file("copy")
      except FileSystemError:
        print "Eeek!"
      else:
        if NodeInfo("copy").exists:
          print "OK!"
        else:
          print "Eeek!"
    finally:
      d1.remove()
      d2.remove()
    try:
      try:
        d1 = Node("orig")
        d1.make_file()
        d1.copy_file("orig")
      except SystemError:
        print "Eeek!!"
      else:
        print "Copied onto itself. Nothing done."
    finally:
      d1.remove()

  def test_glob(pattern):
    print "**[%s]**" % pattern
    for p in NodeInfoFilter(pattern).glob():
      print p.path

  def test_open():
    tmp = Node("~/Developer/Tests/toto.txt").make_file()
    reader = tmp.open('r')
    print reader.readline()
    writer2 = tmp.open('w')
    writer2.write("something else")
    reader = tmp.open('r')
    print reader.readline()
    print reader.readline()
    reader.close()
    writer2.close()
    os.system("open ~/Developer/Tests/toto.txt")

  #test_Path()
  #test_Node("FileSystem.py")
  #test_Directory_walk("~/Developer/Tests/A", "*")
  #test_Directory_chdir("~/Tests")
  #test_Node_removal("~/Tests/TEST")
  #test_Directory_chdir("~/Tests")
  #test_time()
  #test_copy("~/Tests")
  #test_Path_Immutability()
  test_open()
  print
