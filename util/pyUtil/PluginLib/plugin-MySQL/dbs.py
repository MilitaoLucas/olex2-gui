import olex_core
from elixir import *
import sqlalchemy.types as types

metadata.bind = "sqlite:///:memory:"
#metadata.bind = "sqlite:///t.sqlite"

#metadata.bind = "mysql://DIMAS:fddd-anode@dimas.dur.ac.uk:3306/Olex2Docu"
metadata.bind.echo = True

#metadata.bind.echo = True


class Command(Entity):
  using_options(tablename='commands')
  name = Field(Unicode(30),)
  builtin_doc = Field(Unicode(128),)
  parameters = Field(Unicode(512),)
  type = ManyToOne('Type')
  state = ManyToOne('State')
  scope = ManyToOne('Scope')
  parameters = OneToMany('Parameter')

  def __repr__(self):
    return '<Command "%s">' % (self.name)

class Parameter(Entity):
  using_options(tablename='parameters')
  name = Field(Unicode(60))
  builtin_doc = Field(Unicode(128),)
  commands = ManyToOne('Command')

  def __repr__(self):
    return '<Parameter "%s">' % self.name

class Type(Entity):
  using_options(tablename='types')
  name = Field(Unicode(60), primary_key=True)
  commands = OneToMany('Command')

  def __repr__(self):
    return '<Type "%s">' % self.name

class Scope(Entity):
  using_options(tablename='scopes')
  name = Field(Unicode(60), primary_key=True)
  commands = OneToMany('Command')

  def __repr__(self):
    return '<Type "%s">' % self.name


class State(Entity):
  using_options(tablename='states')
  name = Field(Unicode(60), primary_key=True)
  commands = OneToMany('Command')

  def __repr__(self):
    return '<State "%s">' % self.name


class XInserts():
  def __init__(self):
    pass
#    from helpers import *
#    self.helpers = Helpers()

  def run(self):
    #self.types()
    self.commands()

  def types(self):
    Type(name="fun")
    Type(name="mac")

  def commands(self):

    types_d = {}
    states_d = {}
    scopes_d = {}

    for c in ["fun", "mac"]:
      d = self.export_help(c)
      for items in d:
        item = d[items]

        type=item['type']
        if type not in types_d:
          types_d.setdefault(type, Type(name=type))

        state = item['state']
        if state not in states_d:
          states_d.setdefault(state, State(name=state))

        scope = item['scope']
        if scope not in scopes_d:
          scopes_d.setdefault(scope, Scope(name=scope))


        cmd = Command(name=item['name'].strip("'"),
#                      arguments=item['arguments'].strip("'"),
                      builtin_doc=item['builtin_doc'].strip("'"),
                      arguments=item['arguments'].strip("'"),
                      )

        for parameter in item['parameters']:
          p = Parameter(name=parameter,builtin_doc=item['parameters'][parameter])
          cmd.parameters.append(p)


        type = types_d[type]
        type.commands.append(cmd)

        state = states_d[state]
        state.commands.append(cmd)

        scope = scopes_d[scope]
        scope.commands.append(cmd)


  def export_help(self, which_type):

    if which_type == "fun":
      l = olex_core.ExportFunctionList()
      type = 'fun'
    elif which_type == "mac":
      l = olex_core.ExportMacroList()
      type = 'mac'

    print "Olex Functions"
    d = {}
    total = len(l)
    i = 0
    for item in l:
      o_type = type
      arguments = ''
      state = ''
      parameters = ''
      scope = ''
      
      i += 1
      command = "%s" %item[0]

      if 'spy' in command:
        o_type = type
        type = 'spy'

      if 'html.' in command:
        scope = 'html'
      if 'xf.' in command:
        scope = 'xf'
      if 'hkl.' in command:
        scope = 'hkl'
      if 'console.' in command:
        scope = 'console'
      if 'gl.' in command:
        scope = 'gl'
      if 'file.' in command:
        scope = 'file'
      if 'xgrid.' in command:
        scope = 'xgrid'


      arguments_full = "'%s'" %item[1]
      if ' arguments ' in arguments_full:
        arguments = arguments_full.split(' arguments ')[1]
        if ' states - ' in arguments:
          arguments = arguments.split(' states - ')[0]
      if ' states - ' in arguments_full:
        state = arguments_full.split(' states - ')[1]
        if '; valid options - ' in state:
          state = state.split('; valid options - ')[0]
      if '; valid options - ' in arguments_full:
        parameters = item[-1:][0]
      if not arguments:
        arguments = arguments_full

      builtin_doc = "'%s'" %item[2].replace(r"'",r"\'")
      d.setdefault(command, {})

      state = state.strip("'").strip('[').strip(']')

      d[command].setdefault("name", "'%s'" %command)
      d[command].setdefault("arguments", arguments)
      d[command].setdefault("builtin_doc", builtin_doc)
      d[command].setdefault("parameters", parameters)
      d[command].setdefault("type", type)
      d[command].setdefault("state", state)
      d[command].setdefault("scope", scope)
      
      type = o_type

    return d
  
  def get_scope(self, scope='html'):
    cmds = session.query(Command).\
         filter(Command.scope_name==scope).\
         all()
    cmd_l = []
    for cmd in cmds:
      cmd_l.append((cmd.name, cmd))
      
    cmd_l.sort()
    for cmd[1] in cmd_l:
      print cmd.name, cmd.state_name, cmd.builtin_doc
    


if __name__ == "__main__":
  print "Setup All"
  setup_all(True)

  print "Create All"
  create_all()
  insert = XInserts()
  print "Running Inserts"
  insert.run()
  #session.commit()
  insert.get_scope('gl')
  
         
  print "Done."