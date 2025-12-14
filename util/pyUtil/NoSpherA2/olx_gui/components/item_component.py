from typing import Optional, Iterable, Union
from ..dominate.tags import *
from ..dominate.util import raw
from ..dominate.tags import comment
SPACING = 4

def to_dict(obj, exclude_fields = None):
    if exclude_fields is None:
        exclude_fields = []
    result = dict()
    for key, value in obj.__dict__.items():
        if key in exclude_fields:
            continue
        result[key] = value

    return result

def add_default(pardict, kwargs):
    for k in pardict:
        if k not in kwargs:
            kwargs[k] = pardict[k]
    return kwargs

def include_comment(name: str, path: str, other_pars: Optional[Iterable[str]] = None, **kwargs):
    pars = []
    for key, value in kwargs.items():
        pars.append(f"{key}={value}")

    if not other_pars is None:
        for i in other_pars:
            if not '=' in i:
                pars.append(i)
            else:
                pars.insert(0, i)
    final_str = f"{path};" + ";".join(pars)
    return comment(f" #include {name} {final_str} ", **kwargs)

def text_bold(text: str, width: str="100%", align: str="center"):
    return td({"width": width, "align": align}, b(text))


class ignore(html_tag):
    """
    Represents an <ignore> custom HTML tag.
    """
    tagname = 'ignore'

def verify_functions(args: dict) -> None:
    args2 = {k: str(v).strip() for k, v in args.items()}
    function_starts = ["spy", "snum", "strcmp"]
    for k, v in args2.items():
        if any([v.startswith(x) for x in function_starts]):
            if v.count("(") != v.count(")"):
                raise ValueError(f"Olex2 functions have to be closed to be valid. {k} contains an invalid amount of "
                                 f"brackets.")


class LabeledGeneralComponent(td):
    """
    Use label_left = True to change the label position.
    """
    tagname = "td"
    def __init__(self, inp: html_tag, txt_label: Optional[Union[str, html_tag]] = None, label_left: bool = False,
                 label_top: bool = True, **kwargs):
        kwargs = add_default({"cellpadding": "2",  "cellspacing": "0"}, kwargs)
        super().__init__()
        self.label_left = label_left
        self.tr = tr(valign="middle")
        input_width = "100%"
        if "input_width" in kwargs:
            input_width = kwargs["input_width"]
            kwargs.pop("input_width")

        label_width = None
        if "label_width" in kwargs:
            label_width = kwargs["label_width"]
            kwargs.pop("label_width")

        self.td_input = td(valign="middle", width=input_width)
        self.font = font(size="$GetVar('HtmlFontSizeControls')", valign="middle")
        self.input = inp
        if not txt_label is None:
            self._add_label(txt_label, label_top, label_width=label_width)
        else:
            self.tr.add(self.td_input)
        verify_functions(kwargs)
        self.font.add(self.input)
        self.td_input.add(self.font)
        self.table = table(kwargs)
        self.table.add(self.tr)
        self.add(self.table)
        self.is_resizable = True
        self.precise_width = 0.0

    def _add_label(self, txt_label: Union[str, html_tag], label_top: bool = True, label_width: Optional[str] = None):
        if isinstance(txt_label, str):
            self.label = b(txt_label)
        else:
            self.label = txt_label
        if not label_top:
            self.td_label = td(align="left", valign="middle", width=label_width)
            self.td_label.add(self.label)
            if self.label_left:
                self.tr.add(self.td_label)
                self.tr.add(self.td_input)
            else:
                self.tr.add(self.td_input)
                self.tr.add(self.td_label)
        else:
            self.td_input.add(self.label)
            self.tr.add(self.td_input)

    def _repr_html_(self):
        return str(self)

    @property
    def resizable(self):
        return self.is_resizable

    @resizable.setter
    def resizable(self, other: bool):
        self.is_resizable = other

class InputCheckbox(LabeledGeneralComponent):
    """
    Use label_left = True to change the label position.
    """
    def __init__(self, name: str, txt_label: Union[str, html_tag] = "", label_left: bool = False,
                 label_top: bool = False, **kwargs):
        pardict = dict(name=name,
                       type="checkbox",
                       height=20,
                       fgcolor="GetVar(HtmlFontColour)",
                       bgcolor="GetVar(HtmlTableBgColour)",
                       valign="middle",
                       )
        verify_functions(kwargs)
        tdwidth = None
        if "tdwidth" in kwargs:
            tdwidth = kwargs["tdwidth"]
            kwargs.pop("tdwidth")

        label_width = None
        if "label_width" in kwargs:
            label_width = kwargs["label_width"]
            kwargs.pop("label_width")
        pardict = add_default(pardict, kwargs)
        self.input = input_(pardict)
        super().__init__(self.input, txt_label, label_left, label_top, label_width=label_width, cellpadding="2",
                         cellspacing="0", input_width=None)
        if not tdwidth is None:
            self["width"] = tdwidth
            self.resizable = False
        self["align"] = "center"

class ComboBox(LabeledGeneralComponent):
    """
    Use label_left = True to change the label position.
    """
    def __init__(self, name: str, txt_label: Union[str, html_tag] = "", label_left: bool = False,
                 label_top: bool = True, **kwargs):
        pardict = dict(
            name=name,
            type="combo",
            width="100%",
            height="GetVar(HtmlComboHeight)",
            readonly="true",
            fgcolor="GetVar(HtmlFontColour)",
            bgcolor="GetVar(HtmlInputBgColour)",
            valign="middle",
            setdefault='false',
            disabled='false',
            manage='false',
            onchangealways='false',
            custom='GetVar(custom_button)'
        )

        verify_functions(kwargs)
        tdwidth = None
        if "tdwidth" in kwargs:
            tdwidth = kwargs["tdwidth"]
            kwargs.pop("tdwidth")
        pardict = add_default(pardict, kwargs)
        self.input = input_(pardict)
        super().__init__(self.input, txt_label, label_left, label_top)
        if not tdwidth is None:
            self["width"] = tdwidth
            self.resizable = False

class Button(LabeledGeneralComponent):
    def __init__(self, name: str, **kwargs):
        pardict = dict(
            name=name,
            type="button",
            value="#value",
            width="100%",
            onclick="#onclick",
            bgcolor="#bgcolor",
            fgcolor="#fgcolor",
            fit="false",
            flat="fasle",
            disabled="false",
        )
        verify_functions(kwargs)
        tdwidth = None
        if "tdwidth" in kwargs:
            tdwidth = kwargs["tdwidth"]
            kwargs.pop("tdwidth")
        pardict = add_default(pardict, kwargs)
        self.input = input_(pardict)
        super().__init__(self.input)

        if not tdwidth is None:
            self["width"] = tdwidth
            self.resizable = False


class InputText(LabeledGeneralComponent):
    def __init__(self, name: str, txt_label: Union[str, html_tag] = "", label_left: bool = False,
                 label_top: bool = True, **kwargs):
        pardict = dict(
            name = name,
            height = "GetVar('HtmlInputHeight')",
            manage = "false",
            password = "false",
            multiline = "false",
            disabled = "false",
            bgcolor = "GetVar('HtmlInputBgColour')",
            fgcolor = "GetVar(HtmlFontColour)",
            value = "#value",
            width = "100%",
            onclick = "#onclick",
            fit = "false",
            flat = "fasle",
            type = "text",
            valign = "center",
        )
        verify_functions(kwargs)
        tdwidth = None
        if "tdwidth" in kwargs:
            tdwidth = kwargs["tdwidth"]
            kwargs.pop("tdwidth")
        pardict = add_default(pardict, kwargs)
        self.input = input_(pardict)
        super().__init__(self.input, txt_label, label_left, label_top)
        if not tdwidth is None:
            self["width"] = tdwidth
            self.resizable = False

class InputSpinner(LabeledGeneralComponent):
    def __init__(self, name: str, txt_label: Union[str, html_tag] = "", label_left: bool = False,
                 label_top: bool = True, **kwargs):
        pardict = dict(
            type="spin",
            height="GetVar('HtmlComboHeight')",
            bgcolor="GetVar(HtmlInputBgColour)",
            fgcolor="GetVar(HtmlFontColour)",
            valign="center",
            min="-1000",
            max="1000",
            name=name,
            setdefault="false",
            disabled="false",
            readonly="false",
            onchangealways="false",
            manage="false",
            custom="arrow_width: -10",
        )
        verify_functions(kwargs)
        tdwidth = None
        if "tdwidth" in kwargs:
            tdwidth = kwargs["tdwidth"]
            kwargs.pop("tdwidth")
        pardict = add_default(pardict, kwargs)
        self.input = input_(pardict)
        super().__init__(self.input, txt_label, label_left, label_top)
        if not tdwidth is None:
            self["width"] = tdwidth
            self.resizable = False

class InputLinkButton(LabeledGeneralComponent):
    def __init__(self, name: str, txt_label: Union[str, html_tag] = "", label_left: bool = False,
                 label_top: bool = True, **kwargs):
        pardict = dict(
            type="button",
            name=name,
            bgcolor="GetVar(linkButton.bgcolor)",
            fgcolor="GetVar(linkButton.fgcolor)",
            fit="false",
            flat="GetVar(linkButton.flat)",
            custom="GetVar(custom_button)",
        )
        verify_functions(kwargs)
        tdwidth = None
        if "tdwidth" in kwargs:
            tdwidth = kwargs["tdwidth"]
            kwargs.pop("tdwidth")

        align = None
        if "align" in kwargs:
            align = kwargs["align"]
            kwargs.pop("align")
        pardict = add_default(pardict, kwargs)
        # for k, it in pardict.items():
        #     pardict[k] = raw(it)
        self.input = b(input_(pardict))
        # self.input = font(b(input_(pardict)), size="$GetVar('HtmlFontSizeControls')")
        super().__init__(self.input, txt_label, label_left, label_top, align=align)
        if not tdwidth is None:
            self["width"] = tdwidth
            self.resizable = False

class Filler(td):
    def __init__(self):
        super().__init__()
        with self:
            with td():
                p()
        self.is_resizable = False

class Fill(td):
    tagname = "td"
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Cycle(div):
    """
    This works by cycling between components when ignore is active. This will keep track of the width so the autoresizing
    works.
    """
    tagname="cycle"
    def __init__(self, componentA: html_tag, componentB: html_tag, condition: str):
        """
        componentA is shown if the condition is evaluated to true. If not, componentB is shown.
        """
        verify_functions({"condition": condition})
        super().__init__()
        greater_width = 0
        if componentA.tagname == "td":
            if "width" in componentA.attributes:
                greater_width = int(componentA.attributes["width"].replace("%", ""))
                componentA.attributes.pop("width")

        if "tagname" in componentB.attributes:
            if componentB.tagname == "td":
                widthb = int(componentB["width"].replace("%", ""))
                if "width" in componentB.attributes and ( widthb > greater_width):
                    componentB.attributes.pop("width")
                    greater_width = widthb
        if greater_width > 0:
            self["width"] = f"{greater_width}"
            self.is_resizable = False
        with self:
            ignore(componentA, test=condition)
            ignore(componentB, test=f"not {condition}")

def Ignore(component: html_tag, condition: str):
    """
    This gracefully ignores a component in a way that its space is filled by nothingness. It makes the layout consistent.
    """
    componentB = LabeledGeneralComponent(p())
    return Cycle(component, componentB, condition)
