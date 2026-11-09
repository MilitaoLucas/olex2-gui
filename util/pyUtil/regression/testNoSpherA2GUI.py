import ast
import importlib.util
import os
import re
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


class _GridRows(HTMLParser):
  """The widths of the cells of every grid table (Xgrid="1": the row tables of
  grid_row and the rows inside its group boxes). A cell belongs to the
  innermost open table, so the cells of nested tables are not counted twice."""
  def __init__(self, html):
    super().__init__()
    self.rows = []
    self._tables = []
    self.feed(html)

  def handle_starttag(self, tag, attrs):
    attrs = dict(attrs)
    if tag == "table":
      self._tables.append([] if attrs.get("xgrid") == "1" else None)
    elif tag == "td" and self._tables and self._tables[-1] is not None:
      self._tables[-1].append(attrs.get("width", ""))

  def handle_endtag(self, tag):
    if tag == "table" and self._tables:
      cells = self._tables.pop()
      if cells is not None:
        self.rows.append(cells)


class NoSpherA2GridTestCase(unittest.TestCase):
  """Every program block of NoSpherA2 Options lays its rows out on the common
  grid: each row and each row inside a group box fills exactly 100%, never
  runs past its columns, and its help button has a section in the help file."""

  BUILDERS = ("make_ORCA_GUI", "make_OCC_GUI", "make_xtb_GUI", "make_ptb_GUI",
              "make_SALTED_GUI", "make_Thakkar_GUI", "make_ELMOdb_GUI", "make_wfn_GUI",
              "make_tonto_GUI", "make_frag_HAR_GUI", "make_pySCF_GUI",
              "make_discambMATT_GUI", "make_xHARPY_GUI")
  WITH_PTB = ("make_ORCA_GUI", "make_OCC_GUI", "make_pySCF_GUI")

  def setUp(self):
    self.params = {}
    self.disordered = False
    self.ov = SimpleNamespace(GetParam=lambda key: self.params.get(key),
                              ListParts=lambda: self.params.get("parts", [0]))
    modules = {
      "htmlTools": SimpleNamespace(MakeHoverButton=lambda name, onclick, *args: "<a %s>%s</a>" % (name, onclick)),
      "olexFunctions": SimpleNamespace(OV=self.ov),
      "variableFunctions": SimpleNamespace(nsa2_get_param=lambda key: self.params.get(key)),
      "utilities": SimpleNamespace(make_quick_button_gui=lambda: "<td>quick</td>",
                                   is_disordered=lambda: self.disordered),
    }
    spec = importlib.util.spec_from_file_location(
      "_test_hybrid_GUI_grid", os.path.join(NOSPHERA2_DIR, "hybrid_GUI.py"))
    self.gui = importlib.util.module_from_spec(spec)
    self.modules = patch.dict(sys.modules, modules)
    self.modules.start()
    self.addCleanup(self.modules.stop)
    spec.loader.exec_module(self.gui)
    with open(os.path.join(NOSPHERA2_DIR, "NoSpherA2.help.md"), encoding="utf-8") as f:
      self.help_ids = {line[1:].strip().replace(" ", "_").upper()
                       for line in f if line.startswith("# ")}

  def assertGrid(self, html, context):
    rows = _GridRows(html).rows
    self.assertTrue(rows, context)
    for cells in rows:
      total = sum(int(w.rstrip("%")) for w in cells)
      self.assertEqual(total, 100, "%s: %s" % (context, cells))
    for name in re.findall(r"make_help_box -name='([^']+)'", html):
      self.assertIn(name.replace(" ", "_").upper(), self.help_ids, context)

  def render(self, name, **kwargs):
    with patch("builtins.print") as printed:
      html = getattr(self.gui, name)(**kwargs)
    printed.assert_not_called()   # _cells_html reports a row with too many columns
    return html

  def test_all_blocks_fill_the_grid(self):
    switches = ("full_HAR", "basis_adv", "ORCA_USE_CRYSTAL_QMMM", "user.NoSpherA2.show_broken_sym",
                "ORCA_use_broken_sym", "user.NoSpherA2.show_partitioning", "user.NoSpherA2.basis_adv")
    for on in (False, True):
      for disordered in (False, True):
        self.params = {key: on for key in switches}
        self.params.update({"ORCA_Solvation": "Custom" if on else "Water",
                            "ORCA_CRYSTAL_QMMM_TYPE": "Ion" if on else "Mol",
                            "NoSpherA2_Partition": "RI-Fit", "RI_restraint": "MBIS",
                            "PTB_PREREFINE": on})
        self.disordered = disordered
        for name in self.BUILDERS:
          kwargs = {"ptb": True} if name in self.WITH_PTB else {}
          self.assertGrid(self.render(name, **kwargs), "%s on=%s disordered=%s" % (name, on, disordered))

  def test_hybrid_parts_fill_the_grid(self):
    for software in ("  ORCA", "  pySCF", "ELMOdb", "  discamb"):
      self.params = {"parts": [0, 1, 2], "Hybrid.software_Part1": software,
                     "Hybrid.software_Part2": "  ORCA", "user.NoSpherA2.discamb_exe": "discamb"}
      self.assertGrid(self.render("make_hybrid_GUI", softwares_list_string="Hybrid;ORCA;pySCF", ptb=True), software)

  def test_overfull_row_is_reported(self):
    cell = self.gui.g_text("x")
    with patch("builtins.print") as printed:
      html = self.gui.grid_row([cell] * 5)
    printed.assert_called_once()
    self.assertEqual(sum(int(w.rstrip("%")) for w in _GridRows(html).rows[0]), 100)

  def test_help_buttons_look_up_their_section(self):
    # no -helpTxt: make_help_box would show it verbatim instead of the help section
    html = self.render("make_ORCA_GUI")
    self.assertIn("make_help_box -name='NoSpherA2_Wavefunction'", html)
    self.assertNotIn("helpTxt", html)

  def test_orca_groups_and_controls(self):
    self.params = {"ORCA_USE_CRYSTAL_QMMM": True, "user.NoSpherA2.show_broken_sym": True}
    html = self.render("make_ORCA_GUI", new_ORCA=True, ptb=True)
    inputs = _Inputs(html).inputs
    for name in ("NoSpherA2_basis@refine", "NoSpherA2_method@refine", "NoSpherA2_cpus@refine",
                 "NosPherA2_Memory", "NoSpherA2_Charge@refine", "NoSpherA2_Multiplicity@refine",
                 "NoSpherA2_Iterative@refine", "Update_TSC", "NoSpherA2_becke_accuracy@refine",
                 "NoSpherA2_ORCA_SCF_Conv@refine", "NoSpherA2_ORCA_SCF_Strategy@refine",
                 "NoSpherA2_ORCA_damp@refine", "NoSpherA2_ORCA_embedding@refine",
                 "NoSpherA2_ORCA_embedding_type@refine", "NoSpherA2_ORCA_embedding_radius@refine",
                 "NoSpherA2_ORCA_HF_Layers@refine", "NoSpherA2_baseset_adv@refine",
                 "NoSpherA2_ORCA_use_brok_sym@refine", "NoSpherA2_ptb_prerefine@refine",
                 "NoSpherA2_H_Aniso@refine", "NoSpherA2_Afix_remove@refine"):
      self.assertIn(name, inputs)
    # embedding replaces the solvent model
    self.assertNotIn("NoSpherA2_ORCA_Solvation@refine", inputs)
    for title in ("Wavefunction", "Integration", "Molecule", "Resources", "SCF Convergence",
                  "Crystal Environment", "HAR", "Model"):
      self.assertIn("<b>%s&nbsp;</b>" % title, html)
    # H Aniso and No Afix sit in the Model box, not with Relativistic
    model = html.index("<b>Model&nbsp;</b>")
    self.assertGreater(html.index('name="NoSpherA2_H_Aniso@refine"'), model)
    self.assertLess(html.index('name="NoSpherA2_Relativistics@refine"'), model)

  def test_pyscf_damping_is_the_parameter_the_job_reads(self):
    inputs = _Inputs(self.render("make_pySCF_GUI")).inputs
    self.assertEqual(inputs["NoSpherA2_Hybrid_pySCF_Damping@refine"]["value"],
                     "spy.nsa2_get_param('pySCF_Damping')")

  def test_three_item_box_uses_three_wider_columns(self):
    # SCF Convergence: Thresh. | Strategy | Damping -> label, control, gap, label, control, gap, check
    scf = _GridRows(self.gui.orca_scf_row(damping=True)).rows[0]
    widths = [int(w.rstrip("%")) for w in scf]
    self.assertEqual(len(widths), 7, scf)
    four = self.gui._Frame()
    self.assertGreater(widths[1], four.span(0, 1) - four.label(0))
    self.assertGreater(widths[2], 0)   # the gap between the columns
    # a box needing four columns stays on the common grid
    self.params = {"ORCA_USE_CRYSTAL_QMMM": True}
    env = _GridRows(self.gui.orca_environment_row(embedding=True)).rows[0]
    self.assertEqual(len(env), 4 * 2 + 3, env)


class NoSpherA2RestoreTestCase(unittest.TestCase):
  """A failed run gets back the table _launch moved to the history (the
  structure would otherwise refine, and plot, against a missing file)."""

  def setUp(self):
    import shutil
    import tempfile
    with open(os.path.join(NOSPHERA2_DIR, "NoSpherA2.py"), encoding="utf-8") as f:
      tree = ast.parse(f.read())
    node = next(n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == "_restore_archived")
    ns = {"os": os, "shutil": shutil}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "NoSpherA2.py", "exec"), ns)
    self.restore = ns["_restore_archived"]
    self.dir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, self.dir)
    self.history = os.path.join(self.dir, "history")
    os.mkdir(self.history)

  def write(self, path, text):
    with open(path, "w") as f:
      f.write(text)

  def test_missing_table_is_copied_back_and_a_new_one_kept(self):
    old, new = os.path.join(self.dir, "x.tscb"), os.path.join(self.dir, "x.wfnlog")
    self.write(os.path.join(self.history, "x.tscb"), "old table")
    self.write(os.path.join(self.history, "x.wfnlog"), "old log")
    self.write(new, "new log")   # written by the failed run: stays
    nsa2 = SimpleNamespace(_archived=[(os.path.join(self.history, "x.tscb"), old),
                                      (os.path.join(self.history, "x.wfnlog"), new)])
    with patch("builtins.print"):
      self.restore(nsa2)
    with open(old) as f:
      self.assertEqual(f.read(), "old table")
    with open(new) as f:
      self.assertEqual(f.read(), "new log")
    self.assertTrue(os.path.exists(os.path.join(self.history, "x.tscb")))

  def test_nothing_archived(self):
    self.restore(SimpleNamespace(_archived=[]))


def TestSuite():
  suite = unittest.TestLoader().loadTestsFromTestCase(NoSpherA2GUITestCase)
  suite.addTests(unittest.TestLoader().loadTestsFromTestCase(NoSpherA2GridTestCase))
  suite.addTests(unittest.TestLoader().loadTestsFromTestCase(NoSpherA2RestoreTestCase))
  return suite


if __name__ == "__main__":
  unittest.main()
