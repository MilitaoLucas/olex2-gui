""" Common Object Oriented Patterns """



class Proxy(object):
  """ A proxy automatically delegating those operations
    not in its dictionary
  """

  def __init__(self, subject, alias=None, others={}):
    """ Construct a proxy for the given object, which can also be referred
      by the given alias (i.e. self.subject is getattr(self, alias)).
      The dictionary of this instance is also updated with the dictionary others
    """
    self.__dict__['subject'] = subject
    if alias is not None: self.__dict__[alias] = subject
    self.__dict__.update(others)

  #def __call__(self, *args, **kwds):
    #""" Delegate function calls to the proxied object """
    #return self.__dict__['subject'].__call__(*args, **kwds)

  #def __getitem__(self, i):
    #""" Delegate item access to the proxied object """
    #return self.__dict__['subject'].__getitem__(i)

  def __getattr__(self, attr):
    """ When the given attribute is accessed but not found in self,
      try to access it in the proxied object
    """
    return getattr(self.__dict__['subject'], attr)

  def __setattr__(self, attr, val):
    """ When an attempt is made to set the given attribute,
      set it in self if it is already in the instance or class dictionary
      (the latter is to take advantage of properties);
      if it is not, set the attribute on the proxied object
    """
    if attr in self.__dict__ or attr in self.__class__.__dict__:
      super(Proxy,self).__setattr__(attr,val)
    else:
      setattr(self.__dict__['subject'], attr, val)


class Null(object):
  """ Null objects always and reliably "do nothing".

    Reference: Python Cookbook, 5.23
  """

  def __init__(self, *args, **kwargs):
    pass
  def __call__(self, *args, **kwargs): return self
  def __str__(self): return 'Null'
  def __repr__(self): return 'Null()'
  def __bool__(self): return False
  def __eq__(self, other): return isinstance(other,Null)
  def __gt__(self, other): return False
  def __lt__(self, other): return False
  def __ge__(self, other): return False
  def __le__(self, other): return False

  def __getattr__(self, name): return self
  def __setattr__(self, name, value): return self
  def __delattr__(self, name): return self

  def __getitem__(self, i): return self
  def __setitem__(self, i, v): return self

  def __add__(self, x): return self


if __name__ == '__main__':

  # Test Proxy #
  class DummySubject(object):
    def __init__(self):
      self.x = "x"
      self.y = "y"

  class Dummy(object):
    def msg(self):
      return "foo!"

  class DummyProxy(Proxy, Dummy):
    def __init__(self, subject):
      super(DummyProxy,self).__init__(subject)
    def getx(self):
      return (1, self.subject.x)
    def setx(self, x):
      self.subject.x = x*2
    x = property(getx, setx)

  subject=DummySubject()
  proxy = DummyProxy(subject)
  assert(proxy.x == (1,'x'))
  assert(proxy.y == 'y')
  proxy.x = "xx"
  assert(subject.x == 'xxxx')
  assert(subject.y == 'y')
  proxy.y = "yy"
  assert(subject.y == 'yy')
  assert(proxy.msg() == "foo!")
  print("**** Proxy test succeeded!!! ****")
  proxy=Proxy("toto", alias="titi", others={'ga':'bo'})
  assert(proxy.titi == "toto")
  assert(proxy.ga == 'bo')
  print()

  # Test Null #

  null = Null()
  if(not null):
    print("An instance of Null has a boolean value of 0: fine!")
  else:
    print("Eeekk!!")
  print("String representation: %s" % null)
  print("Return value of non-existing method as string: %s" % null.foo(1,4,5))
  print("Comparison (equality): %s, %s" % (null == [5,6], null == Null("??")))
  print("Comparison (strict): %s, %s" % (null > 3, null < 4))
  print("Comparison : %s, %s" % (null >= 3, null <= 4))
  print()
