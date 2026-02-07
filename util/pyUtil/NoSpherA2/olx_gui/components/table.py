from dataclasses import dataclass
from math import floor

import htmlTools
from ..dominate.tags import tr, td, table, comment
from typing import List, Optional, Union
import copy

DISABLE_PYGMENTS = False
try:
    from pygments import highlight
    from pygments.lexers import HtmlLexer
    from pygments.formatters import TerminalFormatter
    LEXER = HtmlLexer()
    FORMATTER = TerminalFormatter()
except:
    DISABLE_PYGMENTS = True
from .item_component import include_comment, LabeledGeneralComponent, ignore, Cycle
from ..dominate.util import raw, text


class Pars:
    def __init__(self, par: dict):
        for key in par:
            setattr(self, key, par[key])

    def __repr__(self):
        return str(self.__dict__)

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def pop(self, key):
        if key in self.__dict__:
            self.__dict__.pop(key)


@dataclass
class RowConfig:
    """
    A table compiles to something like this:
    <tr ALIGN='left' NAME='SNUM_REFINEMENT_NSFF' width='100%'> <!-- configurable with tr1_parameters, this being the default -->
        <td colspan="#colspan> <!-- configurable with td1_parameters -->
          <table border="0" width="100%" cellpadding="0" cellspacing="0" Xbgcolor="#ffaaaa"> <!-- configurable with table1_parameters -->
            <tr Xbgcolor="#ffffaa"> <!-- configurable with tr2_parameters -->
            <!-- those bellow are part of the TableGroup Class
              <td width='#width%' align='left'> <!-- configurable with td2_parameters --> 
                <table width='100%'cellpadding="0" cellspacing="2"> <!-- configurable with table2_parameters -->
                  <tr bgcolor="GetVar(HtmlTableGroupBgColour)"> <!-- configurable with tr3_parameters -->
                      <!-- Any content -->
                  </tr>
                </table>
              </td>
            <!-- those above are part of the TableGroup Class
            </tr>
          </table>
        </td>
    </tr>
    """
    tr1_parameters: Optional[Union[dict, Pars]] = None
    td1_parameters: Optional[Union[dict, Pars]] = None
    table1_parameters: Optional[Union[dict, Pars]] = None
    tr2_parameters: Optional[Union[dict, Pars]] = None
    td2_parameters: Optional[Union[dict, Pars]] = None
    table2_parameters: Optional[Union[dict, Pars]] = None
    tr3_parameters: Optional[Union[dict, Pars]] = None
    children_width: Optional[str] = None
    
    def __post_init__(self):
        if self.tr1_parameters is None:
            self.tr1_parameters = Pars({"ALIGN": "left", "NAME": "NAME", "width": "100%"})
        
        if self.td1_parameters is None:
            self.td1_parameters = Pars({"colspan": "#colspan"})
            
        if self.table1_parameters is None:
            self.table1_parameters = Pars({"border": "0", "width": "100%", "cellpadding": "0", "cellspacing": "0", "Xbgcolor": "#ffaaaa"})
        
        if self.tr2_parameters is None:
            self.tr2_parameters = Pars({"Xbgcolor": "#ffffaa"})
        
        if self.td2_parameters is None:
            self.td2_parameters = Pars({"width": "100", "align": "left"})
        
        if self.table2_parameters is None:
            self.table2_parameters = Pars({"width": "100%", "cellpadding": "0", "cellspacing": "2"})

        if self.tr3_parameters is None:
            self.tr3_parameters = Pars({"bgcolor": "$GetVar(HtmlTableGroupBgColour)"})

    def to_dict(self):
        """
        Convert every config to a dic for dominate access.
        """
        for at, val in self.__dict__.items():
            if isinstance(val, Pars):
                self.__dict__[at] = val.__dict__

    def to_pars(self):
        """
        Convert every config to Pars
        """
        for at, val in self.__dict__.items():
            if isinstance(val, dict):
                self.__dict__[at] = Pars(val)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)


_ACTIVE_MANAGER: Optional['RowManager'] = None
class RowManager:
    def __init__(self):
        self.rows = []
        self.combined_strings = ""

    def __enter__(self):
        global _ACTIVE_MANAGER
        if _ACTIVE_MANAGER is not None:
            raise RuntimeError("Nesting LineManagers is not allowed!")

        _ACTIVE_MANAGER = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        global _ACTIVE_MANAGER
        _ACTIVE_MANAGER = None

        for row in self.rows:
            self.combined_strings += str(row)

    def __str__(self):
        return self.combined_strings

    def __repr__(self):
        return str(self)


class Row(tr):
    """
    A line consists of a single table containing help information.
    """
    tagname = "tr"
    def __init__(self, name: str, help_ext: Optional["str"]="#help_ext", **kwargs):
        self.help_ext = help_ext
        if "config" in kwargs and isinstance(kwargs["config"], RowConfig):
            self.config = kwargs["config"]
            kwargs.pop("config")
        else:
            self.config = RowConfig()
        self.config.tr1_parameters["NAME"] = name
        self.config.to_dict()
        super().__init__(self.config.tr1_parameters, **kwargs)
        help = td(valign='top', width="$GetVar(HtmlTableFirstcolWidth)", align='center', bgcolor="$GetVar(HtmlTableFirstcolColour)")
        with help:
            raw(htmlTools.MakeHoverButton(f"btn-info@{help_ext}1",f"spy.make_help_box -name='{help_ext}' -popout='False' -helpTxt='Options'"))

        self.add(help)
        self.td1 = td(self.config.td1_parameters)
        self.table1 = table(self.config.table1_parameters)
        self.tr2 = tr(self.config.tr2_parameters)
        self.td2 = td(self.config.td2_parameters)
        self.table2 = table(self.config.table2_parameters)
        self.tr3 = tr(self.config.tr3_parameters)
        self.table2.add(self.tr3)
        self.td2.add(self.table2)
        self.tr2.add(self.td2)
        self.table1.add(self.tr2)
        self.td1.add(self.table1)
        self.add(self.td1)
        self.add = self._add
        _ACTIVE_MANAGER.rows.append(self)

    @property
    def pretty(self):
        if not DISABLE_PYGMENTS:
            return highlight(str(self), LEXER, FORMATTER)
        else:
            return str(self)

    @property
    def last_component(self):
        return self.tr3

    def _repr_html_(self):
        return str(self)

    def _add(self, *args):
        children = self.tr3.children + list(args)
        self.children_width = calculate_useful_size(children)
        for k in range(len(self.tr3.children)):
            self.tr3[k].set_attribute("width", self.children_width)

        for k in args:
            if isinstance(k, LabeledGeneralComponent) and not "width" in k.attributes:
                k["width"] = self.children_width
            self.tr3.add(k)


def calculate_useful_size(objs: list) -> str:
    total_nitems = len(objs)
    already_set = 0
    used_perc = 0
    if total_nitems == 1:
        k = objs[0]
        if isinstance(k, ignore):
            k = k[0]
        elif isinstance(k, Cycle):
            k = k[0][0]
        if not "width" in k.attributes:
            return "100%"
        return k.attributes["width"]

    for k in objs:
        if isinstance(k, ignore):
            k = k[0]
        elif isinstance(k, Cycle):
            k = k[0][0]
        elif not isinstance(k, LabeledGeneralComponent):
            return "100%"
        if "width" in k.attributes and not k.resizable:
            used_perc += float(k.attributes["width"].replace("%", ""))/100
            already_set += 1
    remaining = total_nitems - already_set
    return f"{floor((1-used_perc)*100/remaining)}%"



class H3Section:
    """This represents a group of Row's that form a section in the GUI. One example is the NoSpherA2 Options section."""
    def __init__(self):
        self.lines: List[Union[Row, comment]] = []
        inc_comment = include_comment("tool-h3", r"gui\blocks\tool-h3.htm", ["1"],
                                      image="#image", colspan="1")
        self.lines.append(inc_comment)
        self.preview_width = "50%"

    def add(self, line: Row):
        self.lines.append(line)

    def __str__(self):
        strs = ""
        for line in self.lines:
            strs += "\n" + str(line)
        return strs

    def html_preview(self, highlighting: bool = True):
        """Previews the entire HTML of the section
        """
        if DISABLE_PYGMENTS:
            highlighting = False
        if highlighting:
            print(highlight(str(self), LEXER, FORMATTER))
        else:
            print(str(self))

    @property
    def include_comment(self):
        return self.lines[0]

    @include_comment.setter
    def include_comment(self, ic_comment: comment):
        if isinstance(ic_comment, comment):
            self.lines[0] = ic_comment
        else:
            raise TypeError("The comment should be of type comment.")

    def _repr_html_(self):
        selfrepr = copy.deepcopy(self)
        for line in selfrepr.lines:
            if isinstance(line, Row):
                line.table1["width"] = self.preview_width
                for k, component in enumerate(line.last_component):
                    if isinstance(component, Cycle):
                        component = component.children[0][0]
                        line.last_component.children[k] = component
        return str(selfrepr)
