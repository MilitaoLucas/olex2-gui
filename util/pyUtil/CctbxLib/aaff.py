import datetime
import itertools
import json
import os, shutil, sys
import olex, olx
from olexex import OlexRefinementModel

from olexFunctions import OV
from variableFunctions import nsa2_get_param, nsa2_set_param
from RunPrg import RunPrg, RunRefinementPrg
from NoSpherA2.utilities import nsa2_validate_tsc_file_integrity, nsa2_check_tsc_origin_known, write_precise_model_file


def _format_screen_value(value):
    return f"{float(value):+.6f}".replace("+", "p").replace("-", "m").replace(".", "_")


def _build_screen_values(low, high, step):
    low = float(low)
    high = float(high)
    step = float(step)
    if step == 0:
        raise ValueError("ORCA libxc screening step size must not be zero")
    if high > low and step < 0:
        raise ValueError("ORCA libxc screening step must be positive when high > low")
    if high < low and step > 0:
        raise ValueError("ORCA libxc screening step must be negative when high < low")
    values = []
    current = low
    epsilon = max(abs(step) * 1e-9, 1e-12)
    if step > 0:
        while current <= high + epsilon:
            values.append(round(current, 12))
            current += step
    else:
        while current >= high - epsilon:
            values.append(round(current, 12))
            current += step
    return values


def _copy_if_exists(src, dst):
    if os.path.exists(src):
        shutil.copy2(src, dst)


def _copy_tree_if_exists(src, dst, ignore=None):
    if os.path.exists(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=ignore)


def _write_screen_metadata(metadata_path, params, result, point_dir):
    with open(metadata_path, "w", encoding="utf-8", errors="replace") as meta:
        meta.write("ORCA LibXC screening point\n")
        meta.write(f"timestamp = {datetime.datetime.now()}\n")
        meta.write(f"output_folder = {point_dir}\n")
        meta.write(f"parameter_1 = {params[0]}\n")
        meta.write(f"parameter_2 = {params[1]}\n")
        meta.write(f"parameter_3 = {params[2]}\n")
        keys = [
            'snum.NoSpherA2.source',
            'snum.NoSpherA2.method',
            'snum.NoSpherA2.basis_name',
            'snum.NoSpherA2.charge',
            'snum.NoSpherA2.multiplicity',
            'snum.NoSpherA2.ncpus',
            'snum.NoSpherA2.mem',
            'snum.NoSpherA2.Relativistic',
            'snum.NoSpherA2.ORCA_Relativistic',
            'snum.NoSpherA2.ORCA_SCF_Conv',
            'snum.NoSpherA2.ORCA_SCF_Strategy',
            'snum.NoSpherA2.becke_accuracy',
            'snum.NoSpherA2.file',
            'snum.NoSpherA2.file_origin',
            'snum.NoSpherA2.file_hash',
        ]
        for key in keys:
            meta.write(f"{key} = {OV.GetParam(key)}\n")
        meta.write(f"converged = {result.get('converged')}\n")
        meta.write(f"success = {result.get('success')}\n")
        meta.write(f"cycles = {result.get('cycles')}\n")
        meta.write(f"r1 = {result.get('r1')}\n")
        meta.write(f"wr2 = {result.get('wr2')}\n")
        meta.write(f"max_peak = {result.get('max_peak')}\n")
        meta.write(f"max_hole = {result.get('max_hole')}\n")
        meta.write(f"res_rms = {result.get('res_rms')}\n")
        meta.write(f"goof = {result.get('goof')}\n")
        if result.get('error'):
            meta.write(f"error = {result.get('error')}\n")


def _snapshot_screen_point(self, point_dir, params, result, point_log_path):
    structure_dir = OV.FilePath()
    model_name = self.original_filename
    os.makedirs(point_dir, exist_ok=True)
    snapshot_dir = os.path.join(point_dir, "structure")
    os.makedirs(snapshot_dir, exist_ok=True)

    for ext in (".ins", ".res", ".cif", ".fcf", ".hkl", ".lst", ".tsc", ".tscb", ".wfn", ".wfx", ".gbw", ".fchk", ".molden", ".ffn", ".xtb", ".wfnlog"):
        _copy_if_exists(os.path.join(structure_dir, model_name + ext), os.path.join(snapshot_dir, model_name + ext))

    table_file = str(OV.GetParam('snum.NoSpherA2.file') or "").strip()
    if table_file:
        table_src = os.path.join(structure_dir, os.path.basename(table_file))
        _copy_if_exists(table_src, os.path.join(snapshot_dir, os.path.basename(table_src)))

    olex2_src = os.path.join(structure_dir, "olex2")
    olex2_dst = os.path.join(point_dir, "olex2")
    _copy_tree_if_exists(
        olex2_src,
        olex2_dst,
        ignore=shutil.ignore_patterns("NoSpherA2_history", "backup_*"),
    )

    _write_screen_metadata(os.path.join(point_dir, "screen_point_metadata.txt"), params, result, point_dir)


def _write_screen_summary(summary_path, rows):
    with open(summary_path, "w", encoding="utf-8", errors="replace") as summary:
        summary.write("Point\tP1\tP2\tP3\tConverged\tSuccess\tCycles\tR1\twR2\tResidualMax\tResidualMin\tResidualRMS\tOutputFolder\n")
        for row in rows:
            summary.write(
                f"{row['point']}\t{row['p1']}\t{row['p2']}\t{row['p3']}\t{row['converged']}\t{row['success']}\t{row['cycles']}\t{row['r1']}\t{row['wr2']}\t{row['max_peak']}\t{row['max_hole']}\t{row['res_rms']}\t{row['output_dir']}\n"
            )


def _append_screen_summary_table(log_handle, rows):
    log_handle.write("\nLibXC screening summary\n")
    log_handle.write("Point        P1        P2        P3  Conv  Ok  Cycles      R1     wR2   ResMax   ResMin   ResRMS  Output\n")
    log_handle.write("-" * 160 + "\n")
    for row in rows:
        log_handle.write(
            f"{row['point']:>5} {float(row['p1']):>9.4f} {float(row['p2']):>9.4f} {float(row['p3']):>9.4f}"
            f" {str(row['converged']):>5} {str(row['success']):>3} {int(row['cycles']):>7}"
            f" {str(row['r1']):>7} {str(row['wr2']):>7} {str(row['max_peak']):>8} {str(row['max_hole']):>8} {str(row['res_rms']):>8}  {row['output_dir']}\n"
        )


def _screen_point_key(params):
    return "|".join(f"{float(v):.12g}" for v in params)


def _load_screen_state(state_path):
    if not os.path.exists(state_path):
        return {}
    try:
        with open(state_path, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _save_screen_state(state_path, state):
    temp = state_path + ".tmp"
    with open(temp, "w", encoding="utf-8", errors="replace") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    os.replace(temp, state_path)


def _summary_rows_from_state(state):
    rows = []
    for key in sorted(state.keys()):
        item = state[key]
        rows.append({
            'point': item.get('point', 0),
            'p1': item.get('p1', 'n/a'),
            'p2': item.get('p2', 'n/a'),
            'p3': item.get('p3', 'n/a'),
            'converged': item.get('converged', False),
            'success': item.get('success', False),
            'cycles': item.get('cycles', 0),
            'r1': item.get('r1', 'n/a'),
            'wr2': item.get('wr2', 'n/a'),
            'max_peak': item.get('max_peak', 'n/a'),
            'max_hole': item.get('max_hole', 'n/a'),
            'res_rms': item.get('res_rms', 'n/a'),
            'output_dir': item.get('output_dir', ''),
        })
    return rows


def _is_orca_source(source_value):
    source = str(source_value or "").strip()
    return source == "ORCA" or source.startswith("ORCA ")


def _resolve_orca_source_for_screening():
    selected_source = str(OV.GetParam('snum.NoSpherA2.source') or "").strip()
    if _is_orca_source(selected_source):
        return selected_source
    origin_source = str(OV.GetParam('snum.NoSpherA2.file_origin') or "").strip()
    if _is_orca_source(origin_source):
        return origin_source
    return None


def _run_aaff_point(
    self: RunRefinementPrg,
    har_log_path,
    print_log=True,
    finalize_source=True,
    enforce_r1_convergence=False,
):
    HAR_log = None
    try:
        from cctbx import adptbx
        Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
        old_model = OlexRefinementModel()
        converged = False
        run = 0
        HAR_log = open(har_log_path, "w", encoding="utf-8", errors="replace")
        HAR_log.write("NoSpherA2 in Olex2 for structure %s\n\n" % (OV.ModelSrc()))
        HAR_log.write("Refinement startet at: ")
        HAR_log.write(str(datetime.datetime.now()) + "\n")
        HAR_log.write("Cycle     SCF Energy    Max shift:  xyz/ESD     Label   Uij/ESD       Label   Max/ESD       Label    R1    wR2\n" + "*" * 110 + "\n")
        HAR_log.write("{:3d}".format(run))
        energy = None
        source = str(OV.GetParam('snum.NoSpherA2.source')).lstrip()
        update = ".tsc" not in source and ".tscb" not in source
        if "Please S" in source and update:
            olx.Alert("No tsc generator selected", \
"""Error: No generator for tsc files selected.
Please select one of the generators from the drop-down menu.""", "O", False)
            OV.SetVar('NoSpherA2-Error', "TSC Generator unselected")
            return {'success': False, 'converged': False, 'cycles': run, 'error': 'TSC Generator unselected'}
        HAR_log.write("{:^24}".format("---") if energy is None else "{:^24.10f}".format(energy))
        HAR_log.write("{:>70}".format(" "))
        r1_old = OV.GetParam('snum.refinement.last_R1')
        wr2_old = OV.GetParam('snum.refinement.last_wR2')
        if r1_old != "n/a" and r1_old is not None:
            HAR_log.write("{:>6.2f}".format(float(r1_old) * 100))
        else:
            HAR_log.write("{:>6}".format("N/A"))
        if wr2_old != "n/a" and wr2_old is not None:
            HAR_log.write("{:>7.2f}".format(float(wr2_old) * 100))
        else:
            HAR_log.write("{:>7}".format("N/A"))
        HAR_log.write("\n")
        HAR_log.flush()
        max_cycles = int(OV.GetParam('snum.NoSpherA2.Max_HAR_Cycles'))
        if update:
            if OV.GetParam('snum.NoSpherA2.h_aniso'):
                olx.Anis("$D", h=True)
                olx.Anis("$H", h=True)
            if OV.GetParam('snum.NoSpherA2.h_afix'):
                olex.m("Afix 0 $H")
            else:
                print("Setting all AFIX H Atoms to Neutron distances")
                olex.m("NeutronHDist")
        prev_cycle_r1 = None
        r1_stable_count = 0
        r1_tol = 5e-4
        while not converged:
            run += 1
            HAR_log.write("{:3d}".format(run))
            old_model = OlexRefinementModel()
            OV.SetVar('Run_number', run)
            self.refinement_has_failed = []
            try:
                from NoSpherA2.NoSpherA2 import NoSpherA2_instance as nsp2
                v = nsp2.launch()
                if not v:
                    print("Error during NoSpherA2! Abnormal Ending of program!")
                    HAR_log.close()
                    return {'success': False, 'converged': False, 'cycles': run, 'error': 'NoSpherA2 launch failed'}
            except NameError as error:
                print("Error during NoSpherA2:")
                print(error)
                RunRefinementPrg.running = None
                RunRefinementPrg.Terminate = True
                HAR_log.close()
                return {'success': False, 'converged': False, 'cycles': run, 'error': str(error)}
            Error_Status = OV.GetVar('NoSpherA2-Error')
            if Error_Status != "None":
                print("Error in NoSpherA2: %s" % Error_Status)
                return {'success': False, 'converged': False, 'cycles': run, 'error': Error_Status}
            tsc_exists = False
            wfn_file = None
            table_file_name = OV.GetParam('snum.NoSpherA2.file').lstrip().rstrip()
            for file in os.listdir(olx.FilePath()):
                if file == os.path.basename(table_file_name):
                    tsc_exists = True
                elif file.endswith(".wfn") or file.endswith(".wfx") or file.endswith(".gbw"):
                    wfn_file = file
                elif file.endswith(".tscb"):
                    tsc_exists = True
            if not tsc_exists:
                print("Error during NoSpherA2: No .tsc file found")
                RunRefinementPrg.running = None
                HAR_log.close()
                return {'success': False, 'converged': False, 'cycles': run, 'error': 'No .tsc file found'}
            energy = None
            if source == "fragHAR" or source == "Hybdrid" or "discamb" in source.lower() or "hakkar" in source:
                HAR_log.write("{:^24}".format("---"))
            else:
                if (wfn_file is not None) and update and ".gbw" not in wfn_file:
                    with open(wfn_file, "rb") as f:
                        f.seek(-2000, os.SEEK_END)
                        fread = f.readlines()[-1].decode()
                        if "THE VIRIAL" in fread:
                            source = OV.GetParam('snum.NoSpherA2.source').lstrip()
                            if "Gaussian" in source:
                                energy = float(fread.split()[3])
                            elif "ORCA" in source or "pySCF" in source or "Tonto" in source:
                                energy = float(fread.split()[4])
                            elif ".wfn" in source:
                                energy = float(fread[17:38])
                            else:
                                energy = 0.0
                HAR_log.write("{:^24.10f}".format(energy) if energy is not None else "{:^24}".format("---"))
            if OV.GetParam('snum.NoSpherA2.run_refine'):
                self.startRun()
                try:
                    self.setupRefine()
                    OV.File("%s/%s.ins" % (OV.FilePath(), self.original_filename))
                    self.setupFiles()
                except Exception as err:
                    sys.stderr.formatExceptionInfo()
                    print(err)
                    self.endRun()
                    HAR_log.close()
                    return {'success': False, 'converged': False, 'cycles': run, 'error': str(err)}
                if self.terminate:
                    self.endRun()
                    return {'success': False, 'converged': False, 'cycles': run, 'error': 'Terminated'}
                if self.params.snum.refinement.graphical_output and self.HasGUI:
                    self.method.observe(self)
                try:
                    RunPrg.run(self)
                except Exception as e:
                    e_str = str(e)
                    if "stoks.size() == scatterer" in e_str:
                        print("Insufficient number of scatterers in .tsc file!\nDid you forget to recalculate after adding or deleting atoms?")
                    elif "Error during building of normal equations using OpenMP" in e_str:
                        print("Error initializing OpenMP refinement, try disabling it!")
                    elif "fsci != sc_map.end()" in e_str:
                        print("An Atom was not found in the .tsc file!\nHave you renamed some and not recalcualted the tsc file?")
                    return {'success': False, 'converged': False, 'cycles': run, 'error': e_str}
            else:
                break
            new_model = OlexRefinementModel()

            class results():
                def __init__(self):
                    self.max_dxyz = 0
                    self.max_duij = 0
                    self.label_uij = None
                    self.label_xyz = None
                    self.r1 = 0
                    self.wr2 = 0
                    self.max_overall = 0
                    self.label_overall = None

                def update_xyz(self, dxyz, label):
                    if dxyz > self.max_dxyz:
                        self.max_dxyz = dxyz
                        self.label_xyz = label
                        if dxyz > self.max_overall:
                            self.max_overall = dxyz
                            self.label_overall = label

                def update_uij(self, duij, label):
                    if duij > self.max_duij:
                        self.max_duij = duij
                        self.label_uij = label
                        if duij > self.max_overall:
                            self.max_overall = duij
                            self.label_overall = label

                def update_overall(self, d, label):
                    if d > self.max_overall:
                        self.max_overall = d
                        self.label_overall = label

            try:
                jac_tr = self.cctbx.normal_eqns.reparametrisation.jacobian_transpose_matching_grad_fc()
                from scitbx.array_family import flex
                cov_matrix = flex.abs(flex.sqrt(self.cctbx.normal_eqns.covariance_matrix().matrix_packed_u_diagonal()))
                esds = jac_tr.transpose() * flex.double(cov_matrix)
                jac_tr = None
                annotations = self.cctbx.normal_eqns.reparametrisation.component_annotations
            except Exception:
                HAR_log.close()
                print("Could not obtain cctbx object and calculate ESDs!\n")
                return {'success': False, 'converged': False, 'cycles': run, 'error': 'Could not calculate ESDs'}
            from decors import run_with_bitmap

            @run_with_bitmap('Analyzing shifts', update_model_after=False)
            def analyze_shifts(results):
                try:
                    uc = self.cctbx.normal_eqns.xray_structure.unit_cell()
                    atoms_lookup = {}
                    _new_atoms = new_model._atoms
                    _old_atoms = old_model._atoms
                    for i, atom in enumerate(_new_atoms):
                        atoms_lookup[atom['label']] = i
                    _annotations = annotations
                    _esds = esds
                    n_annotations = len(_annotations)
                    matrix_run = 0
                    while matrix_run < n_annotations:
                        an = _annotations[matrix_run]
                        atom_idx = atoms_lookup[an.partition('.')[0]]
                        new_atom = _new_atoms[atom_idx]
                        old_atom = _old_atoms[atom_idx]
                        if '.occ' in an:
                            matrix_run += 1
                        elif '.x' in an:
                            xyz = new_atom['crd'][0]
                            xyz2 = old_atom['crd'][0]
                            esd = _esds[matrix_run]
                            if esd > 0:
                                for x in range(3):
                                    res = abs(xyz[x] - xyz2[x]) / esd
                                    if res > results.max_dxyz:
                                        results.update_xyz(res, an)
                            matrix_run += 3
                        elif '.uiso' in an:
                            esd = _esds[matrix_run]
                            if esd > 0:
                                res = abs(new_atom['uiso'][0] - old_atom['uiso'][0]) / esd
                                if res > results.max_duij:
                                    results.update_uij(res, an)
                            matrix_run += 1
                        elif 'fp' in an:
                            disp_esd = _esds[matrix_run]
                            if disp_esd > 0:
                                res = abs(new_atom['disp'][0] - old_atom['disp'][0]) / disp_esd
                                if res > results.max_overall:
                                    results.update_overall(res, an)
                            matrix_run += 1
                        elif 'fdp' in an:
                            disp_esd = _esds[matrix_run]
                            if disp_esd > 0:
                                res = abs(new_atom['disp'][0] - old_atom['disp'][0]) / disp_esd
                                if res > results.max_overall:
                                    results.update_overall(res, an)
                            matrix_run += 1
                        elif '.u' in an:
                            adp = new_atom['adp'][0]
                            adp = (adp[0], adp[1], adp[2], adp[5], adp[4], adp[3])
                            adp2 = old_atom['adp'][0]
                            adp2 = (adp2[0], adp2[1], adp2[2], adp2[5], adp2[4], adp2[3])
                            adp = adptbx.u_cart_as_u_cif(uc, adp)
                            adp2 = adptbx.u_cart_as_u_cif(uc, adp2)
                            adp_esds = (_esds[matrix_run], _esds[matrix_run + 1], _esds[matrix_run + 2],
                                        _esds[matrix_run + 3], _esds[matrix_run + 4], _esds[matrix_run + 5])
                            adp_esds = adptbx.u_star_as_u_cif(uc, adp_esds)
                            for u in range(6):
                                if adp_esds[u] > 0:
                                    res = abs(adp[u] - adp2[u]) / adp_esds[u]
                                    if res > results.max_duij:
                                        results.update_uij(res, _annotations[matrix_run + u])
                            matrix_run += 6
                        elif '.C' in an or '.D' in an:
                            order = new_atom['anharmonic_adp']['order']
                            if order == 3:
                                size = 10
                            elif order == 4:
                                size = 25
                            else:
                                size = 0
                            if order >= 3:
                                adp_C = new_atom['anharmonic_adp']['C']
                                adp2_C = old_atom['anharmonic_adp']['C']
                                for u in range(10):
                                    esd_u = _esds[matrix_run + u]
                                    if esd_u > 0:
                                        res = abs(adp_C[u] - adp2_C[u]) / esd_u
                                        if res > results.max_overall:
                                            results.update_overall(res, _annotations[matrix_run + u])
                            if order >= 4:
                                adp_D = new_atom['anharmonic_adp']['D']
                                adp2_D = old_atom['anharmonic_adp']['D']
                                for u in range(14):
                                    esd_u = _esds[matrix_run + 10 + u]
                                    if esd_u > 0:
                                        res = abs(adp_D[u] - adp2_D[u]) / esd_u
                                        if res > results.max_overall:
                                            results.update_overall(res, _annotations[matrix_run + 10 + u])
                            matrix_run += size

                    HAR_log.write("{:>16.4f}".format(results.max_dxyz))
                    HAR_log.write("{:>10}".format(results.label_xyz if results.label_xyz is not None else "N/A"))
                    HAR_log.write("{:>10.4f}".format(results.max_duij))
                    HAR_log.write("{:>12}".format(results.label_uij if results.label_uij is not None else "N/A"))
                    HAR_log.write("{:>10.4f}".format(results.max_overall))
                    HAR_log.write("{:>12}".format(results.label_overall if results.label_overall is not None else "N/A"))
                    results.r1 = OV.GetParam('snum.refinement.last_R1')
                    results.wr2 = OV.GetParam('snum.refinement.last_wR2')
                    HAR_log.write("{:>6.2f}".format(float(results.r1) * 100))
                    HAR_log.write("{:>7.2f}".format(float(results.wr2) * 100))
                    HAR_log.write("\n")
                    HAR_log.flush()
                except Exception as e:
                    HAR_log.write("!!!ERROR!!!\n")
                    HAR_log.close()
                    print("Error during analysis of shifts!")
                    raise e

            r = results()
            analyze_shifts(r)
            current_r1 = None
            try:
                current_r1 = float(r.r1)
            except Exception:
                current_r1 = None
            if current_r1 is not None and prev_cycle_r1 is not None:
                if abs(current_r1 - prev_cycle_r1) <= r1_tol:
                    r1_stable_count += 1
                else:
                    r1_stable_count = 0
            prev_cycle_r1 = current_r1

            if not update or not Full_HAR:
                converged = True
                break
            if enforce_r1_convergence:
                if run >= 2 and r1_stable_count >= 1:
                    converged = True
                    break
            elif r.max_overall <= 0.01:
                converged = True
                break
            if run == max_cycles:
                break
            if r1_old != "n/a":
                if (float(r.r1) > float(r1_old) + 0.1) and (run > 1):
                    HAR_log.write("      !! R1 increased by more than 0.1, aborting before things explode !!\n")
                    self.refinement_has_failed.append("Error: R1 is not behaving nicely! Stopping!")
                    break
            else:
                r1_old = r.r1
                wr2_old = r.wr2
    except Exception as e:
        if HAR_log is not None:
            HAR_log.close()
        raise e
    if finalize_source:
        OV.SetParam('snum.NoSpherA2.source', "  " + OV.GetParam('snum.NoSpherA2.file'))
    ext_name = "h3-NoSpherA2-extras"
    if OV.IsHtmlItem(ext_name):
        olex.m(f"html.ItemState {ext_name} 2")
    if not converged:
        HAR_log.write(" !!! WARNING: UNCONVERGED MODEL! PLEASE INCREASE MAX_CYCLE OR CHECK FOR MISTAKES !!!\n")
        self.refinement_has_failed.append("Warning: Unconverged Model!")
    if "DISCAMB" in source or "MATTS" in source:
        unknown_sources = False
        fn = os.path.join("olex2", "Wfn_job", "discambMATTS2tsc.log")
        if not os.path.exists(fn):
            fn = os.path.join("olex2", "Wfn_job", "discamb2tsc.log")
        if not os.path.exists(fn):
            HAR_log.write("                   !!! WARNING: No output file found! !!!\n")
            self.refinement_has_failed.append("Output file not found!")
        else:
            with open(fn) as discamb_log:
                for line in discamb_log.readlines():
                    if "unassigned atom types" in line:
                        unknown_sources = True
                    if unknown_sources:
                        HAR_log.write(line)
        if unknown_sources:
            HAR_log.write("                   !!! WARNING: Unassigned Atom Types! !!!\n")
            self.refinement_has_failed.append("Unassigned Atom Types!")
    HAR_log.write("*" * 110 + "\n")
    HAR_log.write("Residual density Max:{:+8.3f}\n".format(OV.GetParam('snum.refinement.max_peak')))
    HAR_log.write("Residual density Min:{:+8.3f}\n".format(OV.GetParam('snum.refinement.max_hole')))
    HAR_log.write("Residual density RMS:{:+8.3f}\n".format(OV.GetParam('snum.refinement.res_rms')))
    HAR_log.write("Goodness of Fit:     {:8.4f}\n".format(OV.GetParam('snum.refinement.goof')))
    HAR_log.write("Refinement finished at: ")
    HAR_log.write(str(datetime.datetime.now()))
    HAR_log.write("\n")
    precise = OV.GetParam('snum.NoSpherA2.precise_output')
    if precise:
        from NoSpherA2.utilities import write_precise_model_file
        write_precise_model_file()
    HAR_log.flush()
    HAR_log.close()
    if print_log:
        with open(har_log_path, 'r', encoding='utf-8', errors='replace') as f:
            print(f.read())
    return {
        'success': True,
        'converged': converged,
        'cycles': run,
        'r1': OV.GetParam('snum.refinement.last_R1'),
        'wr2': OV.GetParam('snum.refinement.last_wR2'),
        'max_peak': OV.GetParam('snum.refinement.max_peak'),
        'max_hole': OV.GetParam('snum.refinement.max_hole'),
        'res_rms': OV.GetParam('snum.refinement.res_rms'),
        'goof': OV.GetParam('snum.refinement.goof'),
        'error': None,
    }


def deal_with_AAFF(self: RunRefinementPrg):
    original_source = str(OV.GetParam('snum.NoSpherA2.source'))
    screen_enabled = bool(OV.GetParam('snum.NoSpherA2.ORCA_screen_libxc'))
    default_log_path = os.path.join(OV.FilePath(), f"{self.original_filename}.NoSpherA2")
    if not screen_enabled:
        result = _run_aaff_point(
            self,
            default_log_path,
            print_log=True,
            finalize_source=True,
            enforce_r1_convergence=False,
        )
        return bool(result.get('success'))

    orca_source = _resolve_orca_source_for_screening()
    if not orca_source:
        message = "ORCA LibXC screening requires ORCA as the selected source. Please select ORCA/ORCA 5.0/ORCA 6.0/ORCA 6.1 and run again."
        print(message)
        OV.SetVar('NoSpherA2-Error', 'LibXC screening requires ORCA source')
        return False

    try:
        screen_values = [
            _build_screen_values(
                OV.GetParam(f'snum.NoSpherA2.ORCA_B97_Parameter_{idx}_low'),
                OV.GetParam(f'snum.NoSpherA2.ORCA_B97_Parameter_{idx}_high'),
                OV.GetParam(f'snum.NoSpherA2.ORCA_B97_Parameter_{idx}_step')
            )
            for idx in range(1, 4)
        ]
    except ValueError as error:
        print(error)
        OV.SetVar('NoSpherA2-Error', 'ORCA LibXC screening range invalid')
        return False

    screen_root = os.path.join(OV.FilePath(), f"{self.original_filename}_libxc_screen")
    os.makedirs(screen_root, exist_ok=True)
    master_log_path = os.path.join(screen_root, f"{self.original_filename}.NoSpherA2")
    summary_tsv_path = os.path.join(screen_root, "libxc_screen_summary.tsv")
    state_path = os.path.join(screen_root, "libxc_screen_state.json")
    screen_state = _load_screen_state(state_path)
    summary_rows = _summary_rows_from_state(screen_state)
    overall_success = True

    with open(master_log_path, "a", encoding="utf-8", errors="replace") as master_log:
        master_log.write("\n")
        master_log.write("=" * 90 + "\n")
        master_log.write(f"LibXC screening for {OV.ModelSrc()}\n")
        master_log.write(f"Started at: {datetime.datetime.now()}\n")
        master_log.write(f"ORCA source: {orca_source}\n")
        master_log.write(f"Points: {len(screen_values[0])} x {len(screen_values[1])} x {len(screen_values[2])} = {len(screen_values[0]) * len(screen_values[1]) * len(screen_values[2])}\n\n")

        for point_index, params in enumerate(itertools.product(*screen_values), start=1):
            point_key = _screen_point_key(params)
            point_name = (
                f"p1_{_format_screen_value(params[0])}"
                f"__p2_{_format_screen_value(params[1])}"
                f"__p3_{_format_screen_value(params[2])}"
            )
            point_dir = os.path.join(screen_root, point_name)
            os.makedirs(point_dir, exist_ok=True)
            point_log_path = os.path.join(point_dir, f"{self.original_filename}.NoSpherA2")
            existing = screen_state.get(point_key)
            if existing and existing.get('success') and os.path.exists(point_dir):
                master_log.write(f"[{point_index}] P1={params[0]} P2={params[1]} P3={params[2]} -> SKIP (already completed)\n")
                master_log.flush()
                continue
            master_log.write(f"[{point_index}] P1={params[0]} P2={params[1]} P3={params[2]} -> {point_dir}\n")
            master_log.flush()

            OV.SetParam('snum.NoSpherA2.source', orca_source)
            OV.SetVar('ORCA_B97_Parameter_1', str(params[0]))
            OV.SetVar('ORCA_B97_Parameter_2', str(params[1]))
            OV.SetVar('ORCA_B97_Parameter_3', str(params[2]))

            try:
                result = _run_aaff_point(
                    self,
                    point_log_path,
                    print_log=False,
                    finalize_source=False,
                    enforce_r1_convergence=True,
                )
            except Exception as error:
                result = {
                    'success': False,
                    'converged': False,
                    'cycles': 0,
                    'r1': 'n/a',
                    'wr2': 'n/a',
                    'max_peak': 'n/a',
                    'max_hole': 'n/a',
                    'res_rms': 'n/a',
                    'goof': 'n/a',
                    'error': str(error),
                }
            row = {
                'point': point_index,
                'p1': params[0],
                'p2': params[1],
                'p3': params[2],
                'converged': result.get('converged', False),
                'success': result.get('success', False),
                'cycles': result.get('cycles', 0),
                'r1': result.get('r1', 'n/a'),
                'wr2': result.get('wr2', 'n/a'),
                'max_peak': result.get('max_peak', 'n/a'),
                'max_hole': result.get('max_hole', 'n/a'),
                'res_rms': result.get('res_rms', 'n/a'),
                'output_dir': point_dir,
            }
            screen_state[point_key] = dict(row)
            screen_state[point_key]['updated_at'] = str(datetime.datetime.now())
            _save_screen_state(state_path, screen_state)
            summary_rows = _summary_rows_from_state(screen_state)
            _write_screen_summary(summary_tsv_path, summary_rows)
            _snapshot_screen_point(self, point_dir, params, result, point_log_path)
            if not result.get('success', False):
                overall_success = False
                master_log.write(f"    FAILED: {result.get('error')}\n")
            elif not result.get('converged', False):
                overall_success = False
                master_log.write("    WARNING: unconverged refinement\n")
            master_log.flush()

        summary_rows = _summary_rows_from_state(screen_state)
        _append_screen_summary_table(master_log, summary_rows)
        _write_screen_summary(summary_tsv_path, summary_rows)
        master_log.write(f"State JSON: {state_path}\n")
        master_log.write(f"\nSummary TSV: {summary_tsv_path}\n")
        master_log.write(f"Finished at: {datetime.datetime.now()}\n")

    if summary_rows:
        OV.SetParam('snum.NoSpherA2.source', "  " + OV.GetParam('snum.NoSpherA2.file'))
    with open(master_log_path, 'r', encoding='utf-8', errors='replace') as f:
        print(f.read())
    return overall_success

def make_fcf(self: RunRefinementPrg):
  from refinement import FullMatrixRefine
  table = str(nsa2_get_param('file'))
  table = table.lstrip().rstrip()
  self.startRun()
  try:
    self.setupRefine()
    OV.File("%s/%s.ins" %(OV.FilePath(),self.original_filename))
    self.setupFiles()
  except Exception as err:
    sys.stderr.formatExceptionInfo()
    print(err)
    self.endRun()
    return False
  if self.terminate:
    self.endRun()
    return False
  if self.params.snum.refinement.graphical_output and self.HasGUI:
    self.method.observe(self)
  FM = FullMatrixRefine(
        max_cycles=0,
        max_peaks=1)
  FM.run(False,table)

  fcf_cif, fmt_str = FM.create_fcf_content(list_code = 6)
  with open(OV.file_ChangeExt(OV.FileFull(), 'fcf'), 'w') as f:
    fcf_cif.show(out=f, loop_format_strings={'_refln':fmt_str})
  return True

def get_refinement_details(cif_block, acta_stuff):
  t = nsa2_get_param('file')
  t = t.lstrip().rstrip()
  tsc_file_name = os.path.join(nsa2_get_param('dir'),t)
  if not os.path.exists(tsc_file_name):
    t = os.path.join(OV.FilePath(), t)
    if os.path.exists(t):
      tsc_file_name = t

  if os.path.exists(tsc_file_name):
    #tsc = open(tsc_file_name, 'r').readlines()
    #cif_block_found = False
    tsc_info = """;\n"""
    #for line in tsc:
    #  if "CIF:" in line:
    #    cif_block_found = True
    #    continue
    #  if ":CIF" in line:
    #    break
    #  if cif_block_found == True:
    #    tsc_info = tsc_info + line
    #if not cif_block_found:
    details_text = """Refinement using NoSpherA2, an implementation of
NOn-SPHERical Atom-form-factors in Olex2.
Please cite:
F. Kleemiss et al. Chem. Sci. DOI 10.1039/D0SC05526C - 2021
NoSpherA2 implementation of HAR makes use of
tailor-made aspherical atomic form factors calculated
on-the-fly from a Hirshfeld-partitioned electron density (ED) - not from
spherical-atom form factors.

The ED is calculated from a gaussian basis set single determinant SCF
wavefunction - either Hartree-Fock or DFT using selected funtionals
- for a fragment of the crystal.
This fragment can be embedded in an electrostatic crystal field by employing cluster charges
or modelled using implicit solvation models, depending on the software used.
The following options were used:
"""
    software = nsa2_get_param('source').lstrip()
    # Use the stored origin (set at calculation time) if available; fall back to source param
    origin = nsa2_get_param('file_origin')
    if not origin:
      origin = software
    details_text = details_text + "   SOFTWARE:       %s\n"%origin
    if software != OV.GetParam('user.NoSpherA2.discamb_exe'):
      charge = nsa2_get_param('charge')
      mult = nsa2_get_param('multiplicity')
      relativistic = nsa2_get_param('Relativistic')
      partitioning = nsa2_get_param('NoSpherA2_SF')
      accuracy = nsa2_get_param('becke_accuracy')
      if partitioning == True:
        details_text += "   PARTITIONING:   NoSpherA2\n"
        details_text += f"   INT ACCURACY:   {accuracy}\n"
      else:
        details_text += "   PARTITIONING:   Tonto\n"
      if software == "SALTED":
        salted_model = nsa2_get_param('selected_salted_model')
        details_text += f"   MODEL:          {os.path.basename(str(salted_model))}\n"
      elif software == "Thakkar IAM":
        cations = nsa2_get_param('Thakkar_Cations')
        anions = nsa2_get_param('Thakkar_Anions')
        if cations:
          details_text += f"   CATIONS:        {cations}\n"
        if anions:
          details_text += f"   ANIONS:         {anions}\n"
      elif software == "pTB":
        pass  # pTB does not use method or basis set
      else:
        method = nsa2_get_param('method')
        details_text += f"   METHOD:         {method}\n"
        if software != "xTB":
          basis_set = nsa2_get_param('basis_name')
          details_text += f"   BASIS SET:      {basis_set}\n"
      details_text += f"   CHARGE:         {charge}\n"
      details_text += f"   MULTIPLICITY:   {mult}\n"
      solv = nsa2_get_param('ORCA_Solvation')
      if solv != "Vacuum":
        details_text += f"   SOLVATION:      {solv}\n"
      if relativistic == True:
        if "ORCA" in software:
          ORCA_Relativistic = nsa2_get_param('ORCA_Relativistic')
          details_text += f"   RELATIVISTIC:   {ORCA_Relativistic}\n"
        else:
          details_text += "   RELATIVISTIC:   DKH2\n"
      if software == "Tonto":
        radius = nsa2_get_param('cluster_radius')
        details_text += f"   CLUSTER RADIUS: {radius}\n"
        complete = nsa2_get_param('cluster_grow')
        details_text += f"   CLUSTER GROW:   {complete}\n"
    if os.path.exists(tsc_file_name):
      f_time = os.path.getctime(tsc_file_name)
    import datetime
    f_date = datetime.datetime.fromtimestamp(f_time).strftime('%Y-%m-%d_%H-%M-%S')
    details_text = details_text + "   DATE:           %s\n"%f_date
    tsc_info = tsc_info + details_text + ";\n"
    cif_block['_olex2_refine_details'] = tsc_info
    if acta_stuff:
      # remove IAM scatterer reference
      for sl in ['a', 'b']:
        for sn in range(1, 5):
          key = '_atom_type_scat_Cromer_Mann_%s%s' % (sl, sn)
          cif_block.pop(key, None)
      cif_block.pop('_atom_type_scat_Cromer_Mann_c', None)
      if '_atom_type_scat_source' in cif_block:
        for i in range(cif_block['_atom_type_scat_source'].size()):
          cif_block['_atom_type_scat_source'][i] = "NoSpherA2: Chem.Sci. 2021, DOI:10.1039/D0SC05526C"
