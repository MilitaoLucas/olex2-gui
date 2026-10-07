import ast
import importlib.util
import os
import sys
import unittest
from html.parser import HTMLParser
from types import SimpleNamespace
from unittest.mock import Mock, patch


NOSPHERA2_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "NoSpherA2")


class _Inputs(HTMLParser):
  def __init__(self, html):
    super().__init__()
    self.inputs = {}
    self.feed(html)

  def handle_starttag(self, tag, attrs):
    attrs = dict(attrs)
    if tag == "input":
      self.inputs[attrs["name"]] = attrs


class NoSpherA2GUITestCase(unittest.TestCase):
  def setUp(self):
    self.ov = Mock()
    self.ov.GetParam.return_value = True
    modules = {
      "htmlTools": SimpleNamespace(MakeHoverButton=lambda *args: ""),
      "olexFunctions": SimpleNamespace(OV=self.ov),
      "variableFunctions": SimpleNamespace(nsa2_get_param=lambda key: None),
      "utilities": SimpleNamespace(make_quick_button_gui=Mock(),
                                   is_disordered=lambda: False),
      "xcw": SimpleNamespace(xcw_status=lambda: "Idle",
                             xcw_tscb_list=lambda: ""),
    }
    spec = importlib.util.spec_from_file_location(
      "_test_hybrid_GUI", os.path.join(NOSPHERA2_DIR, "hybrid_GUI.py"))
    self.gui = importlib.util.module_from_spec(spec)
    self.modules = patch.dict(sys.modules, modules)
    self.modules.start()
    self.addCleanup(self.modules.stop)
    spec.loader.exec_module(self.gui)

  def test_xcw_basis_callback(self):
    inputs = _Inputs(self.gui.make_XCW_GUI()).inputs
    basis = inputs["NoSpherA2_XCW_basis@refine"]
    call = ast.parse(basis["items"], mode="eval").body
    self.assertIsInstance(call, ast.Call)
    self.assertEqual(ast.dump(call.func), ast.dump(ast.parse(
      "spy.NoSpherA2.getBasisListStr", mode="eval").body))
    self.assertEqual(call.keywords, [])

    # Load the production method without importing the Olex2 runtime.
    with open(os.path.join(NOSPHERA2_DIR, "NoSpherA2.py"),
              encoding="utf-8") as source:
      tree = ast.parse(source.read())
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == "NoSpherA2")
    method = next(node for node in cls.body
                  if isinstance(node, ast.FunctionDef) and node.name == "getBasisListStr")
    namespace = {
      "software": lambda: "ORCA",
      "olexex": SimpleNamespace(OlexRefinementModel=lambda: SimpleNamespace(
        _atoms=[{"type": "C"}])),
      "ELEMENTS_BY_SYMBOL": {"C": 6},
      "nsa2_get_param": lambda key: False,
    }
    exec(compile(ast.Module(body=[method], type_ignores=[]),
                 "NoSpherA2.py", "exec"), namespace)
    provider = type("BasisProvider", (), {
      "getBasisListStr": namespace["getBasisListStr"],
      "basis_list_str": "STO-3G;def2-SVP",
      "check_for_atom_in_basis_set": lambda self, basis, atoms: True,
    })()
    args = [arg.id if isinstance(arg, ast.Name) else ast.literal_eval(arg)
            for arg in call.args]
    self.assertEqual(provider.getBasisListStr(*args), "STO-3G;def2-SVP;")
    self.assertEqual(basis["value"], "spy.nsa2_get_param('XCW.basis_name')")
    self.assertIn("spy.nsa2_set_param('XCW.basis_name'", basis["onchange"])

  def test_xcw_hidden_by_default(self):
    self.ov.GetParam.return_value = False
    self.assertEqual(self.gui.make_XCW_GUI(), "")

  def test_xcw_advanced_basis_controls_use_separate_parameters(self):
    self.gui.nsa2_get_param = lambda key: key == "XCW.basis_adv"
    html = self.gui.make_XCW_GUI()
    self.assertIn("non-relativistic SCF, no DKH2 Hamiltonian", html)
    inputs = _Inputs(html).inputs
    self.assertEqual(inputs["NoSpherA2_XCW_basis@refine"]["items"],
                     "spy.NoSpherA2.xcw_basis_list()")
    self.assertEqual(inputs["NoSpherA2_XCW_basis_adv_string@refine"]["value"],
                     "spy.nsa2_get_param('XCW.basis_adv_string')")
    self.assertIn("XCW.basis_adv", inputs["NoSpherA2_XCW_basis_adv@refine"]["oncheck"])


def TestSuite():
  return unittest.TestLoader().loadTestsFromTestCase(NoSpherA2GUITestCase)


if __name__ == "__main__":
  unittest.main()
