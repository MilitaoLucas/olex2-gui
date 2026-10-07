import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


NOSPHERA2_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "NoSpherA2")


def _load(name):
  spec = importlib.util.spec_from_file_location(
    "_test_" + name, os.path.join(NOSPHERA2_DIR, name + ".py"))
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


class XCWBasisTestCase(unittest.TestCase):
  def setUp(self):
    self.params = {"basis_name": "STO-3G", "XCW.basis_name": "def2-SVP"}
    self.http = Mock()
    self.modules = {
      "olexFunctions": SimpleNamespace(OV=Mock()),
      "olex": Mock(),
      "olex_core": Mock(),
      "olx": Mock(),
      "threads": SimpleNamespace(ThreadEx=type("ThreadEx", (), {}),
                                 ThreadRegistry=Mock()),
      "utilities": SimpleNamespace(
        ELEMENTS={1: "H", 6: "C", 8: "O", 78: "Pt"},
        ELEMENTS_BY_SYMBOL={"H": 1, "C": 6, "O": 8, "Pt": 78}),
      "variableFunctions": SimpleNamespace(
        nsa2_get_param=lambda key: self.params.get(key), nsa2_set_param=Mock()),
      "HttpTools": SimpleNamespace(make_url_call=self.http),
      "olexex": SimpleNamespace(
        OlexRefinementModel=lambda: SimpleNamespace(_atoms=[{"type": "Pt"}, {"type": "H"}])),
    }
    self.modules["olexFunctions"].OV.GetVar.return_value = "NoSpherA2.exe"
    modules = patch.dict(sys.modules, self.modules)
    modules.start()
    self.addCleanup(modules.stop)
    self.api = _load("basis_set_api")
    sys.modules["basis_set_api"] = self.api
    self.xcw = _load("xcw")
    self.temp = tempfile.TemporaryDirectory()
    self.addCleanup(self.temp.cleanup)
    self.settings = os.path.join(self.temp.name, "settings.txt")
    self.element = {"electron_shells": [
      {"function_type": "gto_spherical", "angular_momentum": [0],
       "exponents": ["1.0"], "coefficients": [["1.0"]]}]}
    self.http.side_effect = lambda *args, **kwargs: io.BytesIO(
      json.dumps({"elements": {"78": self.element}}).encode("utf-8"))

  def _settings(self):
    self.xcw._write_settings(self.settings, 42)
    with open(self.settings) as source:
      return source.read()

  def test_pairs_accept_symbols_numbers_and_separators(self):
    self.assertEqual(self.api.parse_basis_overrides("pt SARC-DKH2; 8 def2-TZVP"),
                     {78: "SARC-DKH2", 8: "def2-TZVP"})

  def test_invalid_and_duplicate_pairs_are_rejected(self):
    for text in ("", "Pt", "Unknown SARC-DKH2", "0 SARC-DKH2",
                 "Pt SARC-DKH2; 78 def2-SVP"):
      with self.subTest(text=text), self.assertRaises(ValueError):
        self.api.parse_basis_overrides(text)

  def test_bse_request_and_shells_are_preserved(self):
    with patch.dict(os.environ, {"BSE_API_URL": "https://bse.example/"}):
      data = self.api.get_basis_overrides_json("Pt SARC-DKH2", {1, 78})
    self.assertEqual(data["elements"]["78"], self.element)
    self.http.assert_called_once_with(
      "https://bse.example/api/basis/SARC-DKH2/format/json/?version=0&elements=78",
      http_timeout=30)

  def test_absent_element_is_rejected_before_download(self):
    with self.assertRaisesRegex(ValueError, "not in the XCW model"):
      self.api.get_basis_overrides_json("Pt SARC-DKH2", {1})
    self.http.assert_not_called()

  def test_missing_shells_and_ecps_are_rejected(self):
    for element in ({}, {"electron_shells": []},
                    dict(self.element, ecp_electrons=60),
                    dict(self.element, ecp_potentials=[{}])):
      self.http.side_effect = lambda *args, element=element, **kwargs: io.BytesIO(
        json.dumps({"elements": {"78": element}}).encode("utf-8"))
      with self.subTest(element=element), self.assertRaises(ValueError):
        self.api.get_basis_overrides_json("Pt SARC-DKH2", {78})

  def test_download_failure_is_not_silently_ignored(self):
    self.http.side_effect = OSError("BSE unavailable")
    with self.assertRaisesRegex(OSError, "BSE unavailable"):
      self.api.get_basis_overrides_json("Pt SARC-DKH2", {78})

  def test_standard_settings_unchanged_by_har_advanced_basis(self):
    self.params.update({"basis_adv": True, "basis_adv_string": "Pt SARC-DKH2"})
    text = self._settings()
    self.assertIn("basis_set def2-SVP\n", text)
    self.assertNotIn("basis_overrides", text)
    self.http.assert_not_called()

  def test_advanced_settings_write_json_and_backend_keyword(self):
    self.params.update({"XCW.basis_adv": True,
                        "XCW.basis_adv_string": "Pt SARC-DKH2"})
    with patch.object(self.xcw.subprocess, "run", return_value=SimpleNamespace(
        stdout=b"basis_overrides <file>")):
      text = self._settings()
    self.assertIn("basis_set def2-SVP\n", text)
    self.assertIn("basis_overrides xcw_basis_overrides.json\n", text)
    with open(os.path.join(self.temp.name, "xcw_basis_overrides.json")) as source:
      self.assertEqual(json.load(source), {"elements": {"78": self.element}})

  def test_old_backend_is_rejected_before_download(self):
    self.params.update({"XCW.basis_adv": True,
                        "XCW.basis_adv_string": "Pt SARC-DKH2"})
    with patch.object(self.xcw.subprocess, "run", return_value=SimpleNamespace(
        stdout=b"old backend")), self.assertRaisesRegex(RuntimeError, "does not support"):
      self._settings()
    self.http.assert_not_called()
    self.assertFalse(os.path.exists(self.settings))

  def test_advanced_backend_is_used_only_for_advanced_xcw(self):
    standard = os.path.join(self.temp.name, "NoSpherA2.exe")
    advanced = os.path.join(self.temp.name, "NoSpherA2_XCW.exe")
    self.modules["olexFunctions"].OV.GetVar.return_value = standard
    with open(advanced, "w"):
      pass
    self.assertEqual(self.xcw._executable(), standard)
    self.params["XCW.basis_adv"] = True
    self.assertEqual(self.xcw._executable(), advanced)
    os.remove(advanced)
    self.assertEqual(self.xcw._executable(), standard)


def TestSuite():
  return unittest.TestLoader().loadTestsFromTestCase(XCWBasisTestCase)


if __name__ == "__main__":
  unittest.main()
