import unittest

import test_utils

import bruker_frames
import bruker_saint
import bruker_smart
import cif_reader
import ires_reader
import lst_reader
import p4p_reader
import pcf_reader
import sadabs


class FileReaderTestCase(unittest.TestCase):
  def exercise_FileReader(self, reader, filename, expected):
    FileReader = reader(filename)
    if hasattr(FileReader, 'cifItems'):
      self.assertEqual(FileReader.cifItems(), expected)
    else:
      self.assertEqual(FileReader.values(), expected)
    return FileReader

  def test_sadabs(self):
    # test sad.abs
    self.exercise_FileReader(
      sadabs.reader, 'test_files/sad.abs', {
        '_exptl_absorpt_correction_T_max': '0.9703',
        'ratiominmax': '0.503349479542',
        'Rint_before': '0.0728',
        'lambda_correction': '0.0015',
        'parameter_ratio': '4.47',
        'prog_version': '2006/1',
        '_exptl_absorpt_correction_type': 'multi-scan',
        'Rint_after': '0.0180',
        '_exptl_absorpt_correction_T_min': '0.4884'})
    # test older sadabs version
    self.exercise_FileReader(
      sadabs.reader, 'test_files/sad1.abs', {
        '_exptl_absorpt_correction_type': 'multi-scan',
        '_exptl_absorpt_correction_T_max': '1',
        'prog_version': 'Bruker area detector absorption corrections',
        'parameter_ratio': '5.58'})

  def test_bruker_frames(self):
    reader = self.exercise_FileReader(
      bruker_frames.reader, 'test_files/bruker_frame_header.001', {
        '_diffrn_orient_matrix_UB_22': '0.001444',
        '_diffrn_orient_matrix_UB_23': '-0.054885',
        '_diffrn_source_voltage': '50',
        '_diffrn_detector_area_resol_mean': '8',
        '_diffrn_source_current': '35',
        '_diffrn_orient_matrix_UB_13': '-0.026127',
        '_diffrn_orient_matrix_UB_12': '-0.023488',
        '_diffrn_orient_matrix_UB_11': '0.067579',
        '_diffrn_orient_matrix_UB_31': '0.027196',
        '_diffrn_radiation_monochromator': 'Parallel,graphite',
        '_diffrn_orient_matrix_UB_32': '0.060551',
        '_diffrn_measurement_device_type': 'BRUKER SMART CCD 6000',
        '_diffrn_orient_matrix_UB_21': '-0.036906',
        '_diffrn_orient_matrix_UB_33': '-0.008568',
        'time': '15.16', 'formula': 'C30H31O8N3S1Cl2',
        '_diffrn_radiation_wavelength': '0.710730',
        '_diffrn_refln_scan_width': '0.30',
        '_exptl_crystal_description': '?',
        '_exptl_crystal_colour': '?'})
    self.assertEqual(reader.saint_cfg(), {
      'CM_TO_GRID': '0.800000',
      'BRASS_SPACING': '0.254000',
      'EPERADU': '2.4000001',
      'EPERPHOTON': '60.0000000',
      'PIXPERCM': '56.020000',
      'READNOISE': '13.0000000',
      'D_ATTENUATION': '31.1977'})

  def test_bruker_saint(self):
    self.exercise_FileReader(
      bruker_saint.reader, 'test_files/saint.ini', {'prog_version': 'V6.02A'})

  def test_lst(self):
    self.exercise_FileReader(
      lst_reader.reader, 'test_files/Co110_patt.lst', {
        'program': 'XS',
        'wR2': 'n/a',
        'version': 'SHELXTL Ver. 6.12 W95/98/NT/2000/ME', # bruker XS version
        'R1': 'n/a',
        'method': 'Patterson Method'})
    self.exercise_FileReader(
      lst_reader.reader, 'test_files/sucrose_direct_methods.lst', {
        'version': '97-2', # shelxs version
        'Nqual': -0.81200000000000006,
        'CFOM': 0.052999999999999999,
        'program': 'SHELXS',
        'wR2': 'n/a',
        'Ralpha': 0.052999999999999999,
        'method': 'Direct Methods',
        'R1': 'n/a'})
    self.exercise_FileReader(
      lst_reader.reader, 'test_files/Co110_shelxl.lst', {
        'program': 'XL',
        'wR2': '0.0819',
        'version': 'SHELXTL Ver. 6.12 W95/98/NT/2000/ME',
        'R1': '0.0312',
        'method': 'Least Squares'})

def TestSuite():
  return unittest.TestLoader().loadTestsFromTestCase(FileReaderTestCase)

if __name__ == '__main__':
  unittest.TextTestRunner(verbosity=2).run(TestSuite())
