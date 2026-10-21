"""Table labels against model labels in tsc_scatterer_resync, no Olex2 needed
(cctbx is: run under libtbx.python)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "CctbxLib"))

from tsc_scatterer_resync import convert_labels_to_ids, ScattererResolutionError

# a protein written chain first by Olex2, with a water outside any residue
MODEL = ["O1", "H1a", "A:N_1", "A:Ha_1", "A:CA_1", "A:N1_1", "A:OXT_46"]


class TscResyncTestCase(unittest.TestCase):
  def test_exact_labels(self):
    self.assertEqual(convert_labels_to_ids(["A:CA_1", "o1"], MODEL, list(range(7))), [4, 0])

  def test_atom_first_table_with_solvent(self):
    # the CIF handed to NoSpherA2 names residue atoms atom first; 1EJG with its
    # waters stopped here, the fallback gave up on the first atom without a residue
    table = ["O1", "H1a", "N_A:1", "Ha_A:1", "CA_A:1", "N1_A:1", "OXT_A:46"]
    self.assertEqual(convert_labels_to_ids(table, MODEL, list(range(7))), list(range(7)))

  def test_unmatched_atom_refuses_all(self):
    table = ["O1", "N_A:1", "CB_A:1"]
    with self.assertRaises(ScattererResolutionError):
      convert_labels_to_ids(table, MODEL, list(range(7)))

  def test_ambiguous_model_refuses(self):
    # the same atom in both naming orders: no unique answer
    model = ["A:N_1", "N_A:1"]
    with self.assertRaises(ScattererResolutionError):
      convert_labels_to_ids(["N_B:1"], model, [0, 1])


def TestSuite():
  return unittest.TestLoader().loadTestsFromTestCase(TscResyncTestCase)


if __name__ == '__main__':
  unittest.TextTestRunner(verbosity=2).run(TestSuite())
